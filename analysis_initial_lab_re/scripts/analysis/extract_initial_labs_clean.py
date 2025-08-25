#!/usr/bin/env python3
"""
MIMIC-IV 초기 혈액검사 데이터 추출 스크립트 (정리된 버전)
- 87개 inclusion=1 itemid 모두 개별 처리
- offset 정보는 별도 파일로 분리 저장
- itemid 기반 처리 (중복 라벨 방지)
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 경로 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
OUTPUT_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab_re')
FIGURE_PATH = os.path.join(OUTPUT_PATH, 'figures')
DATA_PATH = os.path.join(OUTPUT_PATH, 'data')

# 출력 폴더 생성
os.makedirs(FIGURE_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

def load_inclusion_items():
    """inclusion=1인 모든 검사 항목 로드 및 정리"""
    print("=" * 70)
    print("1. INCLUSION=1 검사 항목 로딩")
    print("=" * 70)
    
    # d_labitems_inclusion.csv 로드
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    # itemid별 고유 라벨 생성
    LAB_ITEMS = {}
    LAB_METADATA = {}
    
    for _, row in included_labs.iterrows():
        itemid = row['itemid']
        original_label = row['label']
        
        # 라벨 정리 (특수문자 제거)
        clean_label = (original_label
                      .replace(' ', '_')
                      .replace(',', '_')
                      .replace('(', '')
                      .replace(')', '')
                      .replace('/', '_')
                      .replace('-', '_'))
        
        # itemid 포함한 고유 라벨
        unique_label = f"{clean_label}_{itemid}"
        
        LAB_ITEMS[itemid] = unique_label
        LAB_METADATA[itemid] = {
            'original_label': original_label,
            'clean_label': clean_label,
            'unique_label': unique_label,
            'category': row.get('category', ''),
            'fluid': row.get('fluid', ''),
            'loinc_code': row.get('loinc_code', '')
        }
    
    print(f"✅ {len(LAB_ITEMS)}개 검사 항목 로드 완료")
    
    # 중복 라벨 통계
    label_counts = {}
    for meta in LAB_METADATA.values():
        label = meta['original_label']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    duplicates = {k: v for k, v in label_counts.items() if v > 1}
    if duplicates:
        print(f"\n📊 중복 라벨 현황: {len(duplicates)}개 라벨이 여러 itemid 보유")
        for label, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {label}: {count}개 itemid")
    
    return LAB_ITEMS, LAB_METADATA

def load_data():
    """샘플 데이터 로드"""
    print("\n" + "=" * 70)
    print("2. 데이터 로딩")
    print("=" * 70)
    
    # 입원 데이터
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['admit_date'] = admissions['admittime'].dt.date
    
    # 환자 데이터
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['chart_date'] = labevents['charttime'].dt.date
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 전체 검사: {len(labevents):,}건")
    
    return admissions, patients, labevents

def extract_labs_with_window(admissions, labevents, LAB_ITEMS):
    """시간 윈도우를 적용한 검사 데이터 추출"""
    print("\n" + "=" * 70)
    print("3. 시간 윈도우 검사 추출 (Day -1, 0, +1)")
    print("=" * 70)
    
    # inclusion=1 itemid만 필터링
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    print(f"✅ Inclusion=1 필터링: {len(labevents_filtered):,}건")
    
    # 실제 데이터가 있는 itemid 확인
    available_itemids = set(labevents_filtered['itemid'].unique())
    missing_itemids = set(lab_itemids) - available_itemids
    
    print(f"   - 데이터 있는 itemid: {len(available_itemids)}개")
    print(f"   - 데이터 없는 itemid: {len(missing_itemids)}개")
    
    results = []
    offset_info = []
    
    total = len(admissions)
    print(f"\n⏳ {total}개 입원 처리 중...")
    
    for idx, admission in admissions.iterrows():
        if idx % 200 == 0 and idx > 0:
            print(f"   처리 진행: {idx}/{total} ({idx/total*100:.1f}%)")
            
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_date = pd.to_datetime(admission['admit_date']).date()
        
        # 3일 윈도우 날짜
        date_minus1 = admit_date - timedelta(days=1)
        date_plus1 = admit_date + timedelta(days=1)
        
        # 각 날짜별 검사 데이터
        labs_by_day = {
            0: labevents_filtered[
                ((labevents_filtered['hadm_id'] == hadm_id) | 
                 (labevents_filtered['subject_id'] == subject_id)) & 
                (labevents_filtered['chart_date'] == admit_date)
            ],
            -1: labevents_filtered[
                (labevents_filtered['subject_id'] == subject_id) & 
                (labevents_filtered['chart_date'] == date_minus1)
            ],
            1: labevents_filtered[
                ((labevents_filtered['hadm_id'] == hadm_id) | 
                 (labevents_filtered['subject_id'] == subject_id)) & 
                (labevents_filtered['chart_date'] == date_plus1)
            ]
        }
        
        # 각 itemid별 처리
        for itemid, lab_name in LAB_ITEMS.items():
            # 우선순위: Day 0 > Day -1 > Day +1
            selected_data = None
            selected_day = None
            
            for day in [0, -1, 1]:
                day_labs = labs_by_day[day]
                item_labs = day_labs[day_labs['itemid'] == itemid]
                if len(item_labs) > 0:
                    selected_data = item_labs.iloc[0]
                    selected_day = day
                    break
            
            # 데이터가 있으면 저장
            if selected_data is not None:
                results.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'admit_date': admit_date,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'charttime': selected_data['charttime'],
                    'chart_date': selected_data['chart_date'],
                    'valuenum': selected_data['valuenum'],
                    'value': selected_data.get('value', ''),
                    'valueuom': selected_data.get('valueuom', ''),
                    'flag': selected_data.get('flag', ''),
                    'ref_range_lower': selected_data.get('ref_range_lower', np.nan),
                    'ref_range_upper': selected_data.get('ref_range_upper', np.nan)
                })
                
                # Offset 정보 별도 저장
                offset_info.append({
                    'hadm_id': hadm_id,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'day_offset': selected_day,
                    'source': f"Day{selected_day:+d}" if selected_day != 0 else "Day0"
                })
    
    print(f"\n✅ 추출 완료")
    print(f"   - 추출된 검사: {len(results):,}건")
    print(f"   - Offset 정보: {len(offset_info):,}건")
    
    # DataFrame 생성
    long_df = pd.DataFrame(results) if results else pd.DataFrame()
    offset_df = pd.DataFrame(offset_info) if offset_info else pd.DataFrame()
    
    # 데이터 출처 통계
    if not offset_df.empty:
        source_stats = offset_df.groupby('source').size()
        print(f"\n📊 데이터 출처 분포:")
        for source, count in source_stats.sort_index().items():
            pct = count / len(offset_df) * 100
            print(f"   - {source}: {count:,}건 ({pct:.1f}%)")
    
    return long_df, offset_df

def create_wide_format(admissions, long_df, LAB_ITEMS):
    """Wide format 변환 (offset 제외)"""
    print("\n" + "=" * 70)
    print("4. Wide Format 변환")
    print("=" * 70)
    
    # 기본 입원 정보로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 
                          'hospital_expire_flag', 'deathtime']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 모든 87개 검사 컬럼을 NaN으로 초기화
    print("⏳ 87개 검사 컬럼 초기화 중...")
    for itemid, lab_name in LAB_ITEMS.items():
        wide_df[lab_name] = np.nan
    
    # 실제 데이터로 채우기
    if not long_df.empty:
        print("⏳ 실제 검사 데이터 채우기 중...")
        
        # Pivot table 생성
        pivot_df = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'  # 중복 시 첫 번째 값 사용
        )
        
        # Wide format에 병합
        for hadm_id in pivot_df.index:
            if hadm_id in wide_df['hadm_id'].values:
                idx = wide_df[wide_df['hadm_id'] == hadm_id].index[0]
                for col in pivot_df.columns:
                    if col in wide_df.columns:
                        wide_df.loc[idx, col] = pivot_df.loc[hadm_id, col]
    
    # 통계 계산
    lab_columns = [col for col in wide_df.columns 
                   if col not in ['hadm_id', 'subject_id', 'admittime', 
                                 'hospital_expire_flag', 'deathtime', 'admit_date']]
    
    print(f"\n✅ Wide format 생성 완료")
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {len(lab_columns)} 검사")
    print(f"   - 전체 컬럼 수: {len(wide_df.columns)}개")
    
    # 데이터 가용성 분석
    non_null_counts = {}
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        if non_null > 0:
            non_null_counts[col] = non_null
    
    print(f"\n📊 데이터 가용성:")
    print(f"   - 데이터 있는 컬럼: {len(non_null_counts)}개")
    print(f"   - 완전 비어있는 컬럼: {len(lab_columns) - len(non_null_counts)}개")
    
    # Top 5 검사
    if non_null_counts:
        top_labs = sorted(non_null_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n📈 데이터 최다 검사 Top 5:")
        for lab, count in top_labs:
            print(f"   - {lab}: {count}건 ({count/len(wide_df)*100:.1f}%)")
    
    # 입원별 통계
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    print(f"\n📊 입원별 검사 보유율:")
    print(f"   - 검사 있음: {has_any_lab.sum()}건 ({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    print(f"   - 검사 없음: {(~has_any_lab).sum()}건")
    
    return wide_df, lab_columns

def save_results(long_df, wide_df, offset_df, LAB_ITEMS, LAB_METADATA, lab_columns):
    """결과 저장"""
    print("\n" + "=" * 70)
    print("5. 결과 저장")
    print("=" * 70)
    
    # CSV 파일 저장
    print("💾 CSV 파일 저장 중...")
    
    # 메인 데이터 (offset 제외)
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_initial_wide.csv'), index=False)
    long_df.to_csv(os.path.join(DATA_PATH, 'labs_initial_long.csv'), index=False)
    
    # Offset 정보 별도 저장
    offset_df.to_csv(os.path.join(DATA_PATH, 'labs_offset_info.csv'), index=False)
    
    # 검사 항목 요약
    lab_summary = []
    for itemid, unique_label in LAB_ITEMS.items():
        meta = LAB_METADATA[itemid]
        if unique_label in lab_columns:
            non_null = wide_df[unique_label].notna().sum()
        else:
            non_null = 0
            
        lab_summary.append({
            'itemid': itemid,
            'unique_label': unique_label,
            'original_label': meta['original_label'],
            'category': meta['category'],
            'fluid': meta['fluid'],
            'has_data': non_null > 0,
            'data_count': non_null,
            'coverage_pct': non_null / len(wide_df) * 100
        })
    
    lab_summary_df = pd.DataFrame(lab_summary)
    lab_summary_df = lab_summary_df.sort_values('data_count', ascending=False)
    lab_summary_df.to_csv(os.path.join(DATA_PATH, 'lab_items_summary.csv'), index=False)
    
    # 메타데이터 생성
    print("📝 메타데이터 생성 중...")
    
    # 컬럼별 통계
    column_stats = {}
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        column_stats[col] = {
            'non_null_count': int(non_null),
            'null_count': int(len(wide_df) - non_null),
            'coverage_rate': float(non_null / len(wide_df) * 100)
        }
    
    # 전체 메타데이터
    metadata = {
        'extraction_info': {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'itemid_based_individual_columns',
            'time_window': 'Day -1, 0, +1 priority',
            'offset_handling': 'separated_to_different_file'
        },
        'data_summary': {
            'total_admissions': len(wide_df),
            'total_patients': wide_df['subject_id'].nunique(),
            'total_lab_items': len(LAB_ITEMS),
            'columns_with_data': len([c for c in column_stats if column_stats[c]['non_null_count'] > 0]),
            'empty_columns': len([c for c in column_stats if column_stats[c]['non_null_count'] == 0])
        },
        'coverage': {
            'admissions_with_any_lab': int((~wide_df[lab_columns].isna().all(axis=1)).sum()),
            'coverage_rate': float((~wide_df[lab_columns].isna().all(axis=1)).sum() / len(wide_df) * 100),
            'total_lab_records': len(long_df)
        },
        'source_distribution': offset_df.groupby('source').size().to_dict() if not offset_df.empty else {},
        'file_info': {
            'labs_initial_wide.csv': {
                'rows': len(wide_df),
                'columns': len(wide_df.columns),
                'description': 'Wide format with all 87 lab columns (no offset)'
            },
            'labs_initial_long.csv': {
                'rows': len(long_df),
                'description': 'Long format with all lab records'
            },
            'labs_offset_info.csv': {
                'rows': len(offset_df),
                'description': 'Day offset information for each lab'
            }
        }
    }
    
    with open(os.path.join(DATA_PATH, 'labs_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ 모든 파일 저장 완료")
    print(f"   - labs_initial_wide.csv: {wide_df.shape}")
    print(f"   - labs_initial_long.csv: {len(long_df):,} records")
    print(f"   - labs_offset_info.csv: {len(offset_df):,} records")
    print(f"   - lab_items_summary.csv: {len(lab_summary_df)} items")
    print(f"   - labs_metadata.json: Complete metadata")
    
    return metadata

def print_final_summary(metadata):
    """최종 요약 출력"""
    print("\n" + "=" * 70)
    print("📊 최종 요약")
    print("=" * 70)
    
    print(f"\n✅ 추출 완료")
    print(f"   - 처리 방식: itemid 기반 개별 컬럼")
    print(f"   - 검사 항목: {metadata['data_summary']['total_lab_items']}개")
    print(f"   - 입원 건수: {metadata['data_summary']['total_admissions']:,}건")
    print(f"   - 검사 기록: {metadata['coverage']['total_lab_records']:,}건")
    print(f"   - 커버리지: {metadata['coverage']['coverage_rate']:.1f}%")
    
    print(f"\n💡 주요 특징:")
    print(f"   - 모든 87개 inclusion=1 itemid 포함")
    print(f"   - 중복 라벨 방지 (itemid별 고유 컬럼)")
    print(f"   - Offset 정보 별도 파일 분리")
    print(f"   - 데이터 없는 항목도 컬럼 유지 (NaN)")

def main():
    """메인 실행 함수"""
    print("\n" + "🏥 " * 20)
    print(" MIMIC-IV 초기 혈액검사 데이터 추출 (Clean Version)")
    print("🏥 " * 20)
    
    # 1. Inclusion=1 검사 항목 로드
    LAB_ITEMS, LAB_METADATA = load_inclusion_items()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 3. 시간 윈도우 검사 추출
    long_df, offset_df = extract_labs_with_window(admissions, labevents, LAB_ITEMS)
    
    # 4. Wide format 변환
    wide_df, lab_columns = create_wide_format(admissions, long_df, LAB_ITEMS)
    
    # 5. 결과 저장
    metadata = save_results(long_df, wide_df, offset_df, LAB_ITEMS, LAB_METADATA, lab_columns)
    
    # 6. 최종 요약
    print_final_summary(metadata)
    
    print("\n" + "=" * 70)
    print("🎉 모든 처리가 성공적으로 완료되었습니다!")
    print("=" * 70)

if __name__ == "__main__":
    main()