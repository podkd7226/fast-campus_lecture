#!/usr/bin/env python3
"""
모든 inclusion=1 itemid를 개별적으로 처리하는 스크립트
- itemid 기반 처리 (라벨 기반 X)
- 87개 모든 inclusion=1 항목 포함
- 데이터 없어도 컬럼 생성 (NaN)
- 컬럼명: label(itemid) 형식
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
FIGURE_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/figures')
DATA_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/data')

# 폴더 생성
os.makedirs(FIGURE_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

def create_all_lab_items():
    """모든 inclusion=1 itemid에 대한 고유 라벨 생성"""
    print("1. 모든 inclusion=1 검사 항목 로딩 중...")
    
    # inclusion=1인 모든 항목 로드
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    # itemid 기반 딕셔너리 생성
    LAB_ITEMS = {}
    LAB_METADATA = {}
    
    for _, row in included_labs.iterrows():
        itemid = row['itemid']
        original_label = row['label']
        category = row['category']
        fluid = row['fluid']
        
        # 컬럼명: label(itemid) 형식
        # 특수문자 처리
        clean_label = (original_label
                      .replace(' ', '_')
                      .replace(',', '_')
                      .replace('(', '')
                      .replace(')', ''))
        
        # itemid를 포함한 고유 라벨
        unique_label = f"{clean_label}_{itemid}"
        
        LAB_ITEMS[itemid] = unique_label
        LAB_METADATA[itemid] = {
            'original_label': original_label,
            'clean_label': clean_label,
            'unique_label': unique_label,
            'category': category,
            'fluid': fluid
        }
    
    print(f"✅ {len(LAB_ITEMS)}개 검사 항목 생성 완료 (모든 inclusion=1)")
    
    # 중복 라벨 통계
    label_counts = {}
    for meta in LAB_METADATA.values():
        label = meta['original_label']
        if label not in label_counts:
            label_counts[label] = 0
        label_counts[label] += 1
    
    duplicates = {k: v for k, v in label_counts.items() if v > 1}
    if duplicates:
        print(f"\n   [중복 라벨 현황]")
        for label, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {label}: {count}개 itemid")
    
    return LAB_ITEMS, LAB_METADATA

def load_data():
    """데이터 로드"""
    print("\n2. 데이터 로딩 중...")
    
    # 입원 데이터 (1,200건)
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['admit_date'] = pd.to_datetime(admissions['admittime']).dt.date
    
    # 환자 데이터
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['chart_date'] = pd.to_datetime(labevents['charttime']).dt.date
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 전체 검사: {len(labevents):,}건")
    
    return admissions, patients, labevents

def extract_labs_all_itemids(admissions, labevents, LAB_ITEMS):
    """모든 itemid에 대해 시간 윈도우 적용하여 추출"""
    print("\n3. 시간 윈도우를 적용한 검사 추출 중...")
    print("   - 모든 87개 itemid 처리")
    print("   - 우선순위: 입원 당일 > 입원 전일 > 입원 익일")
    
    # inclusion=1 itemid만 필터링
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    # 실제 데이터가 있는 itemid 확인
    available_itemids = set(labevents_filtered['itemid'].unique())
    missing_itemids = set(lab_itemids) - available_itemids
    
    print(f"   - 필터링된 검사: {len(labevents_filtered):,}건")
    print(f"   - 데이터가 있는 itemid: {len(available_itemids)}개")
    print(f"   - 데이터가 없는 itemid: {len(missing_itemids)}개 (컬럼은 생성됨)")
    
    results = []
    source_tracking = []
    
    total_admissions = len(admissions)
    
    for idx, admission in admissions.iterrows():
        if idx % 100 == 0:
            print(f"   - 처리 중: {idx}/{total_admissions}")
            
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_date = pd.to_datetime(admission['admit_date']).date()
        
        # 3일 윈도우 날짜 계산
        date_minus1 = admit_date - timedelta(days=1)
        date_plus1 = admit_date + timedelta(days=1)
        
        # 각 날짜별 검사 추출
        labs_day0 = labevents_filtered[
            ((labevents_filtered['hadm_id'] == hadm_id) | 
             (labevents_filtered['subject_id'] == subject_id)) & 
            (labevents_filtered['chart_date'] == admit_date)
        ].copy()
        labs_day0['day_offset'] = 0
        
        labs_day_minus1 = labevents_filtered[
            (labevents_filtered['subject_id'] == subject_id) & 
            (labevents_filtered['chart_date'] == date_minus1)
        ].copy()
        labs_day_minus1['day_offset'] = -1
        
        labs_day_plus1 = labevents_filtered[
            ((labevents_filtered['hadm_id'] == hadm_id) | 
             (labevents_filtered['subject_id'] == subject_id)) & 
            (labevents_filtered['chart_date'] == date_plus1)
        ].copy()
        labs_day_plus1['day_offset'] = 1
        
        # 모든 87개 itemid에 대해 처리
        for itemid, lab_name in LAB_ITEMS.items():
            # 우선순위 1: 입원 당일
            lab_data = labs_day0[labs_day0['itemid'] == itemid]
            selected_day = 0
            
            # 우선순위 2: 입원 전일
            if len(lab_data) == 0:
                lab_data = labs_day_minus1[labs_day_minus1['itemid'] == itemid]
                selected_day = -1
            
            # 우선순위 3: 입원 익일
            if len(lab_data) == 0:
                lab_data = labs_day_plus1[labs_day_plus1['itemid'] == itemid]
                selected_day = 1
            
            # 데이터가 있으면 첫 번째 값 사용
            if len(lab_data) > 0:
                first_lab = lab_data.iloc[0]
                results.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'admit_date': admit_date,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'charttime': first_lab['charttime'],
                    'chart_date': first_lab['chart_date'],
                    'valuenum': first_lab['valuenum'],
                    'value': first_lab.get('value', ''),
                    'valueuom': first_lab.get('valueuom', ''),
                    'flag': first_lab.get('flag', ''),
                    'ref_range_lower': first_lab.get('ref_range_lower', np.nan),
                    'ref_range_upper': first_lab.get('ref_range_upper', np.nan),
                    'day_offset': selected_day
                })
                
                # 데이터 출처 추적
                source_tracking.append({
                    'hadm_id': hadm_id,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'day_offset': selected_day,
                    'source': 'Day-1' if selected_day == -1 else ('Day0' if selected_day == 0 else 'Day+1')
                })
    
    # Long format DataFrame 생성
    long_df = pd.DataFrame(results) if results else pd.DataFrame()
    source_df = pd.DataFrame(source_tracking) if source_tracking else pd.DataFrame()
    
    print(f"\n✅ 시간 윈도우 검사 추출 완료")
    print(f"   - 추출된 검사 레코드: {len(long_df):,}건")
    if not long_df.empty:
        print(f"   - 실제 데이터가 있는 itemid: {long_df['itemid'].nunique()}개")
        print(f"   - 고유 lab_name: {long_df['lab_name'].nunique()}개")
    
    # 데이터 출처 통계
    if not source_df.empty:
        source_stats = source_df.groupby('source').size()
        print(f"\n   [데이터 출처 분포]")
        for source, count in source_stats.items():
            pct = count / len(source_df) * 100
            print(f"   - {source}: {count:,}건 ({pct:.1f}%)")
    
    return long_df, source_df

def create_wide_format_all_itemids(admissions, long_df, LAB_ITEMS):
    """모든 itemid에 대한 컬럼을 포함하는 Wide format 생성"""
    print("\n4. Wide format 변환 중 (모든 87개 itemid 컬럼 생성)...")
    
    # 모든 입원으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 1. 먼저 모든 87개 컬럼을 NaN으로 초기화
    for itemid, lab_name in LAB_ITEMS.items():
        wide_df[lab_name] = np.nan
        wide_df[f"{lab_name}_day_offset"] = np.nan
    
    # 2. 실제 데이터가 있는 경우 값 채우기
    if not long_df.empty:
        # 검사 값 pivot
        pivot_df = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'
        )
        
        # day_offset pivot
        offset_pivot = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='day_offset',
            aggfunc='first'
        )
        
        # 실제 데이터로 업데이트
        for hadm_id in pivot_df.index:
            if hadm_id in wide_df['hadm_id'].values:
                idx = wide_df[wide_df['hadm_id'] == hadm_id].index[0]
                for col in pivot_df.columns:
                    wide_df.loc[idx, col] = pivot_df.loc[hadm_id, col]
                    if col in offset_pivot.columns:
                        wide_df.loc[idx, f"{col}_day_offset"] = offset_pivot.loc[hadm_id, col]
    
    print(f"✅ Wide format 변환 완료")
    
    # 컬럼 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {len(lab_columns)} 검사 항목")
    print(f"   - 모든 inclusion=1 컬럼 포함: {len(lab_columns) == len(LAB_ITEMS)}")
    
    # 데이터 가용성 통계
    non_null_counts = {}
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        if non_null > 0:
            non_null_counts[col] = non_null
    
    print(f"\n   [데이터 가용성]")
    print(f"   - 데이터가 있는 컬럼: {len(non_null_counts)}개 / {len(lab_columns)}개")
    print(f"   - 완전히 비어있는 컬럼: {len(lab_columns) - len(non_null_counts)}개")
    
    # 가장 많은 데이터가 있는 검사 Top 5
    if non_null_counts:
        top_labs = sorted(non_null_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n   [데이터가 많은 검사 Top 5]")
        for lab, count in top_labs:
            print(f"   - {lab}: {count}건 ({count/len(wide_df)*100:.1f}%)")
    
    # 입원별 검사 수
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    print(f"\n   [입원별 통계]")
    print(f"   - 검사가 있는 입원: {has_any_lab.sum()}건 ({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    print(f"   - 검사가 없는 입원: {(~has_any_lab).sum()}건 ({(~has_any_lab).sum()/len(wide_df)*100:.1f}%)")
    
    return wide_df

def save_results(long_df, wide_df, source_df, LAB_ITEMS, LAB_METADATA):
    """결과 저장 및 메타데이터 생성"""
    print("\n5. 결과 저장 중...")
    
    # 데이터 저장
    long_df.to_csv(os.path.join(DATA_PATH, 'labs_all_itemids_long.csv'), index=False)
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_all_itemids_wide.csv'), index=False)
    source_df.to_csv(os.path.join(DATA_PATH, 'labs_all_itemids_sources.csv'), index=False)
    
    # 메타데이터 생성
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    # 각 컬럼의 데이터 가용성 계산
    column_stats = {}
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        column_stats[col] = {
            'non_null_count': int(non_null),
            'null_count': int(len(wide_df) - non_null),
            'coverage_rate': float(non_null / len(wide_df) * 100)
        }
    
    metadata = {
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': 'all_itemids_individual',
        'total_admissions': len(wide_df),
        'lab_items': {
            'total_inclusion_1': len(LAB_ITEMS),
            'total_columns': len(lab_columns),
            'columns_with_data': len([c for c in column_stats if column_stats[c]['non_null_count'] > 0]),
            'empty_columns': len([c for c in column_stats if column_stats[c]['non_null_count'] == 0])
        },
        'data_coverage': {
            'admissions_with_labs': int((~wide_df[lab_columns].isna().all(axis=1)).sum()),
            'coverage_rate': float((~wide_df[lab_columns].isna().all(axis=1)).sum() / len(wide_df) * 100)
        },
        'source_distribution': source_df.groupby('source').size().to_dict() if not source_df.empty else {},
        'column_statistics': column_stats
    }
    
    with open(os.path.join(DATA_PATH, 'extraction_metadata_all_itemids.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 실제 사용된 검사 항목 리스트 저장
    lab_list = []
    for itemid, unique_label in LAB_ITEMS.items():
        if itemid in LAB_METADATA:
            meta = LAB_METADATA[itemid]
            has_data = unique_label in column_stats and column_stats[unique_label]['non_null_count'] > 0
            lab_list.append({
                'itemid': itemid,
                'unique_label': unique_label,
                'original_label': meta['original_label'],
                'category': meta['category'],
                'fluid': meta['fluid'],
                'has_data': has_data,
                'data_count': column_stats[unique_label]['non_null_count'] if unique_label in column_stats else 0
            })
    
    lab_list_df = pd.DataFrame(lab_list)
    lab_list_df = lab_list_df.sort_values('data_count', ascending=False)
    lab_list_df.to_csv(os.path.join(DATA_PATH, 'lab_items_all_itemids.csv'), index=False)
    
    print(f"✅ 모든 파일 저장 완료")
    print(f"   - labs_all_itemids_long.csv: {len(long_df):,} 레코드")
    print(f"   - labs_all_itemids_wide.csv: {wide_df.shape}")
    print(f"   - labs_all_itemids_sources.csv: {len(source_df):,} 레코드")
    print(f"   - extraction_metadata_all_itemids.json: 메타데이터")
    print(f"   - lab_items_all_itemids.csv: {len(lab_list)}개 검사 항목")

def analyze_duplicates(LAB_ITEMS, LAB_METADATA, long_df):
    """중복 itemid 분석"""
    print("\n6. 중복 itemid 분석...")
    
    # 원본 라벨별로 그룹화
    label_groups = {}
    for itemid, meta in LAB_METADATA.items():
        label = meta['original_label']
        if label not in label_groups:
            label_groups[label] = []
        label_groups[label].append(itemid)
    
    # 중복만 필터
    duplicates = {k: v for k, v in label_groups.items() if len(v) > 1}
    
    if duplicates:
        print(f"\n   [중복 라벨 상세 분석]")
        for label, itemids in sorted(duplicates.items()):
            print(f"\n   {label} ({len(itemids)}개 itemid):")
            for itemid in itemids:
                if not long_df.empty:
                    count = len(long_df[long_df['itemid'] == itemid])
                else:
                    count = 0
                meta = LAB_METADATA[itemid]
                print(f"     - {meta['unique_label']}: {count}건 데이터 ({meta['category']})")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("모든 inclusion=1 itemid 개별 처리")
    print("itemid 기반 처리 (라벨 병합 없음)")
    print("=" * 60)
    
    # 1. 모든 inclusion=1 검사 항목 생성
    LAB_ITEMS, LAB_METADATA = create_all_lab_items()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 3. 모든 itemid에 대해 시간 윈도우 적용하여 추출
    long_df, source_df = extract_labs_all_itemids(admissions, labevents, LAB_ITEMS)
    
    # 4. Wide format 변환 (모든 87개 컬럼 생성)
    wide_df = create_wide_format_all_itemids(admissions, long_df, LAB_ITEMS)
    
    # 5. 결과 저장
    save_results(long_df, wide_df, source_df, LAB_ITEMS, LAB_METADATA)
    
    # 6. 중복 분석
    analyze_duplicates(LAB_ITEMS, LAB_METADATA, long_df)
    
    print("\n" + "=" * 60)
    print("✅ 처리 완료!")
    print(f"   - 모든 {len(LAB_ITEMS)}개 inclusion=1 itemid 처리")
    print(f"   - 각 itemid가 독립적인 컬럼으로 보존")
    print(f"   - 데이터 없는 itemid도 컬럼 생성 (NaN)")
    print("=" * 60)

if __name__ == "__main__":
    main()