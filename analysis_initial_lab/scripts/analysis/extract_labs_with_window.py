#!/usr/bin/env python3
"""
입원 전후 ±1일 혈액검사 데이터 추출 (개선된 버전)
모든 입원 건을 유지하며 결측값 처리를 위한 시간 윈도우 적용
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

# 가장 흔한 혈액검사 항목 (분석 결과 기반)
COMMON_LAB_ITEMS = {
    # Basic Metabolic Panel
    50983: 'Sodium',
    50971: 'Potassium', 
    50902: 'Chloride',
    50882: 'Bicarbonate',
    50912: 'Creatinine',
    51006: 'Urea_Nitrogen',
    50931: 'Glucose',
    50868: 'Anion_Gap',
    
    # Complete Blood Count
    51222: 'Hemoglobin',
    51221: 'Hematocrit',
    51279: 'Red_Blood_Cells',
    51301: 'White_Blood_Cells',
    51265: 'Platelet_Count',
    51250: 'MCV',
    51248: 'MCH',
    51249: 'MCHC',
    51277: 'RDW',
    
    # Other Common Tests
    50893: 'Calcium_Total',
    50960: 'Magnesium',
    50970: 'Phosphate'
}

def load_data():
    """데이터 로드"""
    print("1. 데이터 로딩 중...")
    
    # 입원 데이터 - 모든 1,200건
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    
    # 환자 데이터
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건 (모두 유지)")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 검사: {len(labevents):,}건")
    
    return admissions, patients, labevents

def extract_labs_with_window(admissions, labevents):
    """입원 전후 ±1일 윈도우로 검사 추출"""
    print("\n2. 입원 전후 ±1일 검사 추출 중...")
    
    # 주요 검사 항목만 필터링
    common_lab_ids = list(COMMON_LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(common_lab_ids)].copy()
    
    print(f"   주요 검사 항목 필터링: {len(labevents_filtered):,}건")
    
    # 각 입원별로 데이터 수집
    all_admission_labs = []
    
    for idx, admission in admissions.iterrows():
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_time = admission['admittime']
        
        # 시간 윈도우 설정
        day_before = admit_time - timedelta(days=1)
        day_after = admit_time + timedelta(days=1)
        
        # 해당 기간의 검사 찾기
        patient_labs = labevents_filtered[
            ((labevents_filtered['hadm_id'] == hadm_id) |
             ((labevents_filtered['subject_id'] == subject_id) & 
              (labevents_filtered['hadm_id'].isna()))) &
            (labevents_filtered['charttime'] >= day_before) &
            (labevents_filtered['charttime'] <= day_after)
        ].copy()
        
        # 입원 시간 대비 검사 시간 계산
        if len(patient_labs) > 0:
            patient_labs['hours_from_admission'] = (
                patient_labs['charttime'] - admit_time
            ).dt.total_seconds() / 3600
            
            # 우선순위 설정 (입원일 > 전날 > 다음날)
            patient_labs['priority'] = patient_labs['hours_from_admission'].apply(
                lambda x: 1 if -24 <= x < 0 else (  # 입원일 (0-24시간 전)
                         2 if -48 <= x < -24 else (  # 전날
                         3 if 0 <= x <= 24 else      # 다음날
                         4))                          # 기타
            )
        
        # 입원 정보 추가
        patient_labs['hadm_id'] = hadm_id
        patient_labs['subject_id'] = subject_id
        patient_labs['admittime'] = admit_time
        patient_labs['hospital_expire_flag'] = admission['hospital_expire_flag']
        
        all_admission_labs.append(patient_labs)
        
        if (idx + 1) % 100 == 0:
            print(f"   처리 중... {idx + 1}/{len(admissions)} 입원")
    
    # 결과 합치기
    result_df = pd.concat(all_admission_labs, ignore_index=True)
    
    print(f"\n✅ 검사 추출 완료: {len(result_df):,}건")
    
    # 통계 출력
    admissions_with_labs = result_df['hadm_id'].nunique()
    print(f"   검사가 있는 입원: {admissions_with_labs:,}건 ({admissions_with_labs/len(admissions)*100:.1f}%)")
    
    # 시간대별 분포
    if len(result_df) > 0:
        priority_counts = result_df.groupby('priority').size()
        print("\n   시간대별 검사 분포:")
        if 1 in priority_counts.index:
            print(f"   - 입원일: {priority_counts.get(1, 0):,}건")
        if 2 in priority_counts.index:
            print(f"   - 전날: {priority_counts.get(2, 0):,}건")
        if 3 in priority_counts.index:
            print(f"   - 다음날: {priority_counts.get(3, 0):,}건")
    
    return result_df

def create_wide_format_with_priority(all_labs, admissions):
    """우선순위를 고려한 Wide format 변환 (모든 입원 유지)"""
    print("\n3. Wide format 변환 중 (우선순위 적용)...")
    
    # 모든 입원 건으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    
    if len(all_labs) > 0:
        # 검사명 추가
        all_labs['lab_name'] = all_labs['itemid'].map(COMMON_LAB_ITEMS)
        
        # 각 검사별로 우선순위가 가장 높은 값 선택
        # (priority가 낮을수록 우선순위 높음: 1=입원일, 2=전날, 3=다음날)
        all_labs_sorted = all_labs.sort_values(['hadm_id', 'itemid', 'priority', 'charttime'])
        first_valid = all_labs_sorted.drop_duplicates(subset=['hadm_id', 'itemid'], keep='first')
        
        # Pivot table 생성
        pivot_df = first_valid.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'
        ).reset_index()
        
        # 원본 입원 데이터와 병합
        wide_df = wide_df.merge(pivot_df, on='hadm_id', how='left')
        
        # 각 검사별 우선순위 정보도 저장
        priority_pivot = first_valid.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='priority',
            aggfunc='first'
        ).reset_index()
        
        # 우선순위 컬럼명 변경
        priority_cols = {col: f"{col}_priority" for col in priority_pivot.columns if col != 'hadm_id'}
        priority_pivot = priority_pivot.rename(columns=priority_cols)
        
        # 우선순위 정보 병합
        wide_df = wide_df.merge(priority_pivot, on='hadm_id', how='left')
    
    print(f"✅ Wide format 변환 완료: {len(wide_df)} 입원 (모두 유지)")
    
    # 결측값 통계
    lab_columns = [col for col in wide_df.columns 
                  if col in COMMON_LAB_ITEMS.values()]
    
    if lab_columns:
        missing_stats = wide_df[lab_columns].isna().sum()
        print(f"\n   결측값 현황 (1,200건 중):")
        for lab in sorted(missing_stats.index, key=lambda x: missing_stats[x]):
            missing_count = missing_stats[lab]
            missing_pct = missing_count / len(wide_df) * 100
            print(f"   - {lab}: {missing_count}건 결측 ({missing_pct:.1f}%)")
    
    return wide_df, first_valid if len(all_labs) > 0 else pd.DataFrame()

def calculate_statistics(wide_df, first_valid):
    """통계 계산"""
    print("\n4. 통계 계산 중...")
    
    stats = {
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_admissions': len(wide_df),
        'methodology': 'admission ±1 day window with priority'
    }
    
    # 검사별 통계
    lab_columns = [col for col in wide_df.columns 
                  if col in COMMON_LAB_ITEMS.values()]
    
    stats['lab_statistics'] = {}
    for lab in lab_columns:
        lab_data = wide_df[lab].dropna()
        priority_col = f"{lab}_priority"
        
        if len(lab_data) > 0:
            stats['lab_statistics'][lab] = {
                'count': int(len(lab_data)),
                'missing_count': int(len(wide_df) - len(lab_data)),
                'missing_pct': float((len(wide_df) - len(lab_data)) / len(wide_df) * 100),
                'mean': float(lab_data.mean()),
                'std': float(lab_data.std()),
                'min': float(lab_data.min()),
                'q1': float(lab_data.quantile(0.25)),
                'median': float(lab_data.median()),
                'q3': float(lab_data.quantile(0.75)),
                'max': float(lab_data.max())
            }
            
            # 우선순위별 통계
            if priority_col in wide_df.columns:
                priority_data = wide_df[priority_col].dropna()
                if len(priority_data) > 0:
                    priority_counts = priority_data.value_counts().to_dict()
                    stats['lab_statistics'][lab]['source_distribution'] = {
                        'admission_day': priority_counts.get(1, 0),
                        'day_before': priority_counts.get(2, 0),
                        'day_after': priority_counts.get(3, 0)
                    }
    
    # 사망률별 통계
    stats['mortality_rate'] = float(wide_df['hospital_expire_flag'].mean() * 100)
    stats['survived_count'] = int((wide_df['hospital_expire_flag'] == 0).sum())
    stats['died_count'] = int((wide_df['hospital_expire_flag'] == 1).sum())
    
    # 검사 가용성
    stats['lab_availability'] = {
        'survived': {},
        'died': {}
    }
    
    survived = wide_df[wide_df['hospital_expire_flag'] == 0]
    died = wide_df[wide_df['hospital_expire_flag'] == 1]
    
    for lab in lab_columns:
        stats['lab_availability']['survived'][lab] = float((~survived[lab].isna()).mean() * 100)
        stats['lab_availability']['died'][lab] = float((~died[lab].isna()).mean() * 100)
    
    print("✅ 통계 계산 완료")
    
    return stats

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 입원 전후 ±1일 혈액검사 데이터 추출 (개선된 버전)")
    print("=" * 80)
    
    # 1. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 2. 입원 전후 ±1일 검사 추출
    all_labs = extract_labs_with_window(admissions, labevents)
    
    # 3. Wide format 변환 (모든 입원 유지)
    wide_df, first_valid = create_wide_format_with_priority(all_labs, admissions)
    
    # 4. 통계 계산
    stats = calculate_statistics(wide_df, first_valid)
    
    # 5. 결과 저장
    print("\n5. 결과 저장 중...")
    
    # Wide format 저장 (모든 1,200건)
    wide_output_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/labs_with_window_wide.csv')
    wide_df.to_csv(wide_output_path, index=False)
    print(f"   ✅ Wide format: labs_with_window_wide.csv ({len(wide_df)}건)")
    
    # 원본 검사 데이터 저장
    if len(all_labs) > 0:
        labs_output_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/labs_with_window_long.csv')
        all_labs.to_csv(labs_output_path, index=False)
        print(f"   ✅ Long format: labs_with_window_long.csv ({len(all_labs)}건)")
    
    # 통계 저장
    stats_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/lab_statistics_window.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✅ 통계: lab_statistics_window.json")
    
    # 6. 요약 출력
    print("\n" + "=" * 80)
    print("✅ 추출 완료!")
    print("=" * 80)
    
    print(f"\n[추출 요약]")
    print(f"• 총 입원: {stats['total_admissions']}건 (모두 유지)")
    print(f"• 사망률: {stats['mortality_rate']:.1f}%")
    
    print(f"\n[검사별 결측값 현황 - Top 5 완성도]")
    lab_completeness = [(lab, 100 - stat['missing_pct']) 
                       for lab, stat in stats['lab_statistics'].items()]
    lab_completeness.sort(key=lambda x: x[1], reverse=True)
    
    for lab, completeness in lab_completeness[:5]:
        stat = stats['lab_statistics'][lab]
        print(f"  - {lab}: {completeness:.1f}% 완성 ({stat['count']}/1200건)")
        if 'source_distribution' in stat:
            src = stat['source_distribution']
            print(f"    └─ 입원일: {src['admission_day']}, 전날: {src['day_before']}, 다음날: {src['day_after']}")
    
    print(f"\n💾 저장 위치: analysis_initial_lab/data/")
    
    return wide_df, stats

if __name__ == "__main__":
    wide_df, stats = main()