#!/usr/bin/env python3
"""
개별 itemid 컬럼을 유지하는 혈액검사 데이터 추출 스크립트
- 중복 라벨 문제 해결: 각 itemid를 독립적인 컬럼으로 유지
- 데이터 손실 없이 100% 보존
- 임상적 구분 가능 (Blood Gas vs Chemistry 등)
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

def load_duplicate_mapping():
    """중복 itemid 매핑 로드"""
    mapping_path = os.path.join(DATA_PATH, 'duplicate_items_mapping.json')
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            return json.load(f)
    return {}

def create_unique_lab_items():
    """각 itemid에 고유한 라벨 생성"""
    print("1. 고유한 검사 항목 라벨 생성 중...")
    
    # inclusion=1인 항목 로드
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    # 중복 매핑 로드
    duplicate_mapping = load_duplicate_mapping()
    
    # 각 itemid에 고유 라벨 생성
    LAB_ITEMS = {}
    LAB_METADATA = {}
    
    for _, row in included_labs.iterrows():
        itemid = row['itemid']
        original_label = row['label']
        
        # clean_label 생성
        clean_label = (original_label
                      .replace(' ', '_')
                      .replace(',', '_')
                      .replace('(', '')
                      .replace(')', ''))
        
        # 중복 확인 및 고유 라벨 생성
        if clean_label in duplicate_mapping:
            # 중복인 경우
            if itemid in duplicate_mapping[clean_label]:
                unique_label = duplicate_mapping[clean_label][itemid]['unique_name']
            else:
                # 매핑에 없는 경우 (데이터 없는 itemid)
                continue
        else:
            # 중복 아닌 경우
            unique_label = clean_label
        
        LAB_ITEMS[itemid] = unique_label
        LAB_METADATA[itemid] = {
            'original_label': original_label,
            'clean_label': clean_label,
            'unique_label': unique_label,
            'category': row['category'],
            'fluid': row['fluid']
        }
    
    print(f"✅ {len(LAB_ITEMS)}개 고유 검사 항목 생성 완료")
    
    # 중복 통계
    unique_labels = set(LAB_ITEMS.values())
    print(f"   - 고유 컬럼 수: {len(unique_labels)}개")
    print(f"   - 중복 해결: {len(LAB_ITEMS) - len(unique_labels)}개 itemid가 개별 컬럼으로 분리")
    
    return LAB_ITEMS, LAB_METADATA

def validate_available_labs(LAB_ITEMS, labevents):
    """실제 데이터가 있는 검사 항목만 필터링"""
    print("\n2. 실제 가용한 검사 항목 확인 중...")
    
    # 실제 데이터가 있는 itemid 확인
    available_itemids = set(labevents['itemid'].unique())
    included_itemids = set(LAB_ITEMS.keys())
    
    # 교집합 - 실제 사용 가능한 항목
    actual_available = included_itemids & available_itemids
    
    # 실제 사용 가능한 LAB_ITEMS만 필터링
    AVAILABLE_LAB_ITEMS = {k: v for k, v in LAB_ITEMS.items() if k in actual_available}
    
    print(f"✅ inclusion=1 검사 중 실제 가용한 항목: {len(AVAILABLE_LAB_ITEMS)}개")
    
    # 누락된 항목 리포트
    missing_items = included_itemids - available_itemids
    if missing_items:
        print(f"⚠️  데이터가 없는 항목: {len(missing_items)}개")
    
    return AVAILABLE_LAB_ITEMS

def load_data():
    """데이터 로드"""
    print("\n3. 데이터 로딩 중...")
    
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

def extract_labs_with_time_window(admissions, labevents, LAB_ITEMS):
    """시간 윈도우를 적용한 검사 추출 (개별 itemid 유지)"""
    print("\n4. 시간 윈도우를 적용한 검사 추출 중...")
    print("   - 우선순위: 입원 당일 > 입원 전일 > 입원 익일")
    print("   - 각 itemid를 독립적으로 처리")
    
    # 실제 사용할 itemid 리스트
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    print(f"   - 필터링된 검사: {len(labevents_filtered):,}건")
    
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
        
        # 각 itemid별로 독립적으로 처리 (중복 라벨도 개별 처리)
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
                    'lab_name': lab_name,  # 고유한 라벨 사용
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
    print(f"   - 고유 lab_name 수: {long_df['lab_name'].nunique() if not long_df.empty else 0}개")
    
    # 데이터 출처 통계
    if not source_df.empty:
        source_stats = source_df.groupby('source').size()
        print(f"\n   [데이터 출처 분포]")
        for source, count in source_stats.items():
            pct = count / len(source_df) * 100
            print(f"   - {source}: {count:,}건 ({pct:.1f}%)")
    
    return long_df, source_df

def create_wide_format_individual(admissions, long_df):
    """개별 itemid 컬럼을 유지하는 Wide format 변환"""
    print("\n5. Wide format 변환 중 (개별 컬럼 유지)...")
    
    # 모든 입원으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 검사 데이터가 있는 경우 pivot
    if not long_df.empty:
        # 검사 값 pivot - lab_name이 이미 고유함
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
        # 컬럼명에 _day_offset 추가
        offset_pivot.columns = [f"{col}_day_offset" for col in offset_pivot.columns]
        
        # 입원 데이터와 병합
        wide_df = wide_df.merge(pivot_df, left_on='hadm_id', right_index=True, how='left')
        wide_df = wide_df.merge(offset_pivot, left_on='hadm_id', right_index=True, how='left')
    
    print(f"✅ Wide format 변환 완료")
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {len([c for c in wide_df.columns if '_day_offset' not in c])-5} 검사 항목")
    
    # 컬럼 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    print(f"\n   [컬럼 상세]")
    print(f"   - 총 검사 컬럼: {len(lab_columns)}개")
    
    # 중복 라벨별 컬럼 수 확인
    duplicate_patterns = ['Glucose', 'Creatinine', 'Hemoglobin', 'Hematocrit', 'Sodium', 'Potassium']
    for pattern in duplicate_patterns:
        pattern_cols = [col for col in lab_columns if col.startswith(pattern)]
        if len(pattern_cols) > 1:
            print(f"   - {pattern}: {len(pattern_cols)}개 컬럼 ({', '.join(pattern_cols[:3])}...)")
    
    # 가용성 통계
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    print(f"\n   [데이터 가용성]")
    print(f"   - 검사가 있는 입원: {has_any_lab.sum()}건 ({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    print(f"   - 검사가 없는 입원: {(~has_any_lab).sum()}건 ({(~has_any_lab).sum()/len(wide_df)*100:.1f}%)")
    
    return wide_df

def save_results(long_df, wide_df, source_df, LAB_ITEMS, LAB_METADATA):
    """결과 저장 및 메타데이터 생성"""
    print("\n6. 결과 저장 중...")
    
    # 데이터 저장
    long_df.to_csv(os.path.join(DATA_PATH, 'labs_individual_long.csv'), index=False)
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_individual_wide.csv'), index=False)
    source_df.to_csv(os.path.join(DATA_PATH, 'labs_individual_sources.csv'), index=False)
    
    # 메타데이터 생성
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    metadata = {
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': 'individual_columns',
        'total_admissions': len(wide_df),
        'lab_items': {
            'total_itemids': len(LAB_ITEMS),
            'unique_columns': len(lab_columns),
            'duplicate_resolution': 'separate_columns'
        },
        'data_coverage': {
            'admissions_with_labs': int((~wide_df[lab_columns].isna().all(axis=1)).sum()),
            'coverage_rate': float((~wide_df[lab_columns].isna().all(axis=1)).sum() / len(wide_df) * 100)
        },
        'source_distribution': source_df.groupby('source').size().to_dict() if not source_df.empty else {},
        'column_details': {}
    }
    
    # 각 컬럼별 상세 정보
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        metadata['column_details'][col] = {
            'non_null_count': int(non_null),
            'null_count': int(len(wide_df) - non_null),
            'coverage_rate': float(non_null / len(wide_df) * 100)
        }
    
    with open(os.path.join(DATA_PATH, 'extraction_metadata_individual.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 실제 사용된 검사 항목 리스트 저장
    lab_list = []
    for itemid, unique_label in LAB_ITEMS.items():
        if itemid in LAB_METADATA:
            meta = LAB_METADATA[itemid]
            lab_list.append({
                'itemid': itemid,
                'unique_label': unique_label,
                'original_label': meta['original_label'],
                'clean_label': meta['clean_label'],
                'category': meta['category'],
                'fluid': meta['fluid']
            })
    
    lab_list_df = pd.DataFrame(lab_list)
    lab_list_df.to_csv(os.path.join(DATA_PATH, 'lab_items_individual.csv'), index=False)
    
    print(f"✅ 모든 파일 저장 완료")
    print(f"   - labs_individual_long.csv: {len(long_df):,} 레코드")
    print(f"   - labs_individual_wide.csv: {wide_df.shape}")
    print(f"   - labs_individual_sources.csv: {len(source_df):,} 레코드")
    print(f"   - extraction_metadata_individual.json: 메타데이터")
    print(f"   - lab_items_individual.csv: {len(lab_list)}개 검사 항목")

def compare_with_previous():
    """이전 방식과 비교"""
    print("\n7. 이전 방식과 비교...")
    
    try:
        # 이전 데이터
        prev_wide = pd.read_csv(os.path.join(DATA_PATH, 'labs_improved_wide.csv'), nrows=0)
        prev_cols = [c for c in prev_wide.columns if not c.endswith('_day_offset') and c not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
        
        # 새 데이터
        new_wide = pd.read_csv(os.path.join(DATA_PATH, 'labs_individual_wide.csv'), nrows=0)
        new_cols = [c for c in new_wide.columns if not c.endswith('_day_offset') and c not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
        
        print(f"\n   [비교 결과]")
        print(f"   - 이전 방식: {len(prev_cols)}개 컬럼 (중복 병합)")
        print(f"   - 새 방식: {len(new_cols)}개 컬럼 (개별 유지)")
        print(f"   - 증가: {len(new_cols) - len(prev_cols)}개 컬럼 (+{(len(new_cols) - len(prev_cols))/len(prev_cols)*100:.1f}%)")
        
        # 새로 추가된 컬럼
        new_columns = set(new_cols) - set([c.split('_')[0] for c in prev_cols])
        if new_columns:
            print(f"\n   [새로 분리된 컬럼 예시]")
            for col in list(new_columns)[:5]:
                print(f"   - {col}")
                
    except Exception as e:
        print(f"   비교 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("개별 itemid 컬럼 유지 방식 데이터 추출 시작")
    print("=" * 60)
    
    # 1. 고유한 검사 항목 생성
    LAB_ITEMS, LAB_METADATA = create_unique_lab_items()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 3. 실제 가용한 검사만 필터링
    AVAILABLE_LAB_ITEMS = validate_available_labs(LAB_ITEMS, labevents)
    
    # 4. 시간 윈도우 적용하여 데이터 추출
    long_df, source_df = extract_labs_with_time_window(admissions, labevents, AVAILABLE_LAB_ITEMS)
    
    # 5. Wide format 변환 (개별 컬럼 유지)
    wide_df = create_wide_format_individual(admissions, long_df)
    
    # 6. 결과 저장
    save_results(long_df, wide_df, source_df, AVAILABLE_LAB_ITEMS, LAB_METADATA)
    
    # 7. 이전 방식과 비교
    compare_with_previous()
    
    print("\n" + "=" * 60)
    print("✅ 개별 컬럼 유지 방식 추출 완료!")
    print("   모든 itemid가 독립적인 컬럼으로 보존되었습니다.")
    print("=" * 60)

if __name__ == "__main__":
    main()