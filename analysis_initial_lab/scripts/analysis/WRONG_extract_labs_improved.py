#!/usr/bin/env python3
"""
개선된 혈액검사 데이터 추출 스크립트
- 쉼표 처리 문제 해결
- 실제 가용한 데이터만 추출
- 명확한 데이터 출처 추적
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

def load_inclusion_labs():
    """inclusion=1인 검사 항목 로드 (개선된 버전)"""
    print("1. inclusion=1인 검사 항목 로딩 중...")
    
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    # 검사명 정리 - 쉼표도 언더스코어로 변환
    included_labs['clean_label'] = (included_labs['label']
                                    .str.replace(' ', '_')
                                    .str.replace(',', '_')  # 쉼표 처리 추가
                                    .str.replace('(', '')
                                    .str.replace(')', ''))
    
    # itemid와 검사명 매핑
    LAB_ITEMS = dict(zip(included_labs['itemid'], included_labs['clean_label']))
    
    print(f"✅ {len(LAB_ITEMS)}개 검사 항목 로드 완료")
    
    return LAB_ITEMS, included_labs

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
    
    print(f"✅ inclusion=1 검사 중 실제 가용한 항목: {len(AVAILABLE_LAB_ITEMS)}개 / {len(LAB_ITEMS)}개")
    
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
    """시간 윈도우를 적용한 검사 추출 (개선된 버전)"""
    print("\n4. 시간 윈도우를 적용한 검사 추출 중...")
    print("   - 우선순위: 입원 당일 > 입원 전일 > 입원 익일")
    
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
        # 1. 입원 당일 (우선순위 1)
        labs_day0 = labevents_filtered[
            ((labevents_filtered['hadm_id'] == hadm_id) | 
             (labevents_filtered['subject_id'] == subject_id)) & 
            (labevents_filtered['chart_date'] == admit_date)
        ].copy()
        labs_day0['day_offset'] = 0
        
        # 2. 입원 전일 (우선순위 2)
        labs_day_minus1 = labevents_filtered[
            (labevents_filtered['subject_id'] == subject_id) & 
            (labevents_filtered['chart_date'] == date_minus1)
        ].copy()
        labs_day_minus1['day_offset'] = -1
        
        # 3. 입원 익일 (우선순위 3)
        labs_day_plus1 = labevents_filtered[
            ((labevents_filtered['hadm_id'] == hadm_id) | 
             (labevents_filtered['subject_id'] == subject_id)) & 
            (labevents_filtered['chart_date'] == date_plus1)
        ].copy()
        labs_day_plus1['day_offset'] = 1
        
        # 각 검사 항목별로 우선순위에 따라 선택
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
    
    # 데이터 출처 통계
    if not source_df.empty:
        source_stats = source_df.groupby('source').size()
        print(f"\n   [데이터 출처 분포]")
        for source, count in source_stats.items():
            pct = count / len(source_df) * 100
            print(f"   - {source}: {count:,}건 ({pct:.1f}%)")
    
    return long_df, source_df

def create_wide_format(admissions, long_df, LAB_ITEMS):
    """Wide format 변환 (개선된 버전)"""
    print("\n5. Wide format 변환 중...")
    
    # 모든 입원으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 검사 데이터가 있는 경우 pivot
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
        # 컬럼명에 _day_offset 추가
        offset_pivot.columns = [f"{col}_day_offset" for col in offset_pivot.columns]
        
        # 입원 데이터와 병합
        wide_df = wide_df.merge(pivot_df, left_on='hadm_id', right_index=True, how='left')
        wide_df = wide_df.merge(offset_pivot, left_on='hadm_id', right_index=True, how='left')
    
    print(f"✅ Wide format 변환 완료")
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {len([c for c in wide_df.columns if '_day_offset' not in c])-5} 검사 항목")
    
    # 가용성 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    print(f"\n   [데이터 가용성]")
    print(f"   - 검사가 있는 입원: {has_any_lab.sum()}건 ({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    print(f"   - 검사가 없는 입원: {(~has_any_lab).sum()}건 ({(~has_any_lab).sum()/len(wide_df)*100:.1f}%)")
    
    return wide_df

def save_results(long_df, wide_df, source_df, LAB_ITEMS, included_labs):
    """결과 저장 및 메타데이터 생성"""
    print("\n6. 결과 저장 중...")
    
    # 데이터 저장
    long_df.to_csv(os.path.join(DATA_PATH, 'labs_improved_long.csv'), index=False)
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_improved_wide.csv'), index=False)
    source_df.to_csv(os.path.join(DATA_PATH, 'labs_improved_sources.csv'), index=False)
    
    # 메타데이터 생성
    metadata = {
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_admissions': len(wide_df),
        'lab_items': {
            'inclusion_1_total': len(included_labs),
            'available_in_sample': len(LAB_ITEMS),
            'actual_columns': len([c for c in wide_df.columns if not c.endswith('_day_offset') and c not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']])
        },
        'data_coverage': {
            'admissions_with_labs': int((~wide_df.iloc[:, 5:].isna().all(axis=1)).sum()),
            'coverage_rate': float((~wide_df.iloc[:, 5:].isna().all(axis=1)).sum() / len(wide_df) * 100)
        },
        'source_distribution': source_df.groupby('source').size().to_dict() if not source_df.empty else {}
    }
    
    with open(os.path.join(DATA_PATH, 'extraction_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 실제 사용된 검사 항목 리스트 저장
    lab_list = pd.DataFrame([
        {'itemid': k, 'clean_label': v, 'original_label': included_labs[included_labs['itemid'] == k]['label'].values[0] if k in included_labs['itemid'].values else ''}
        for k, v in LAB_ITEMS.items()
    ])
    lab_list.to_csv(os.path.join(DATA_PATH, 'actual_lab_items.csv'), index=False)
    
    print(f"✅ 모든 파일 저장 완료")
    print(f"   - labs_improved_long.csv: {len(long_df):,} 레코드")
    print(f"   - labs_improved_wide.csv: {wide_df.shape}")
    print(f"   - labs_improved_sources.csv: {len(source_df):,} 레코드")
    print(f"   - extraction_metadata.json: 메타데이터")
    print(f"   - actual_lab_items.csv: {len(LAB_ITEMS)}개 검사 항목")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("개선된 혈액검사 데이터 추출 시작")
    print("=" * 60)
    
    # 1. inclusion 검사 로드
    LAB_ITEMS, included_labs = load_inclusion_labs()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 3. 실제 가용한 검사만 필터링
    AVAILABLE_LAB_ITEMS = validate_available_labs(LAB_ITEMS, labevents)
    
    # 4. 시간 윈도우 적용하여 데이터 추출
    long_df, source_df = extract_labs_with_time_window(admissions, labevents, AVAILABLE_LAB_ITEMS)
    
    # 5. Wide format 변환
    wide_df = create_wide_format(admissions, long_df, AVAILABLE_LAB_ITEMS)
    
    # 6. 결과 저장
    save_results(long_df, wide_df, source_df, AVAILABLE_LAB_ITEMS, included_labs)
    
    print("\n" + "=" * 60)
    print("✅ 모든 처리가 완료되었습니다!")
    print("=" * 60)

if __name__ == "__main__":
    main()