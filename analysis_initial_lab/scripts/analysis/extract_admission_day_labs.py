#!/usr/bin/env python3
"""
입원 당일 혈액검사 데이터 추출 스크립트
입원 첫날 시행된 주요 혈액검사 결과를 추출합니다.
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
    
    # 입원 데이터
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    
    # 환자 데이터 (나이, 성별 등)
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 검사: {len(labevents):,}건")
    
    return admissions, patients, labevents

def extract_admission_day_labs(admissions, labevents):
    """입원 당일 검사 추출 (최적화 버전)"""
    print("\n2. 입원 당일 검사 추출 중...")
    
    # 주요 검사 항목만 필터링
    common_lab_ids = list(COMMON_LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(common_lab_ids)].copy()
    
    print(f"   주요 검사 항목 필터링: {len(labevents_filtered):,}건")
    
    # 날짜 컬럼 추가 (더 빠른 매칭을 위해)
    labevents_filtered['chart_date'] = labevents_filtered['charttime'].dt.date
    admissions['admit_date'] = admissions['admittime'].dt.date
    
    # hadm_id가 있는 검사와 없는 검사 분리
    labs_with_hadm = labevents_filtered[labevents_filtered['hadm_id'].notna()]
    labs_without_hadm = labevents_filtered[labevents_filtered['hadm_id'].isna()]
    
    # 1. hadm_id로 직접 매칭
    merged_with_hadm = labs_with_hadm.merge(
        admissions[['hadm_id', 'subject_id', 'admit_date', 'admittime', 'hospital_expire_flag']],
        on='hadm_id',
        how='inner',
        suffixes=('', '_adm')
    )
    
    # 입원 당일 검사만 필터링
    admission_day_labs_1 = merged_with_hadm[
        merged_with_hadm['chart_date'] == merged_with_hadm['admit_date']
    ].copy()
    
    # 2. subject_id와 날짜로 매칭 (hadm_id가 없는 경우)
    if len(labs_without_hadm) > 0:
        merged_without_hadm = labs_without_hadm.merge(
            admissions[['hadm_id', 'subject_id', 'admit_date', 'admittime', 'hospital_expire_flag']],
            left_on=['subject_id', 'chart_date'],
            right_on=['subject_id', 'admit_date'],
            how='inner'
        )
        admission_day_labs_2 = merged_without_hadm.copy()
    else:
        admission_day_labs_2 = pd.DataFrame()
    
    # 결과 합치기
    if not admission_day_labs_1.empty or not admission_day_labs_2.empty:
        result_df = pd.concat([admission_day_labs_1, admission_day_labs_2], ignore_index=True)
        
        # 필요한 컬럼만 선택
        keep_columns = ['labevent_id', 'subject_id', 'hadm_id', 'itemid', 'charttime', 
                       'value', 'valuenum', 'valueuom', 'ref_range_lower', 'ref_range_upper',
                       'flag', 'admittime', 'hospital_expire_flag']
        
        # subject_id_adm이 있으면 제거
        if 'subject_id_adm' in result_df.columns:
            result_df['subject_id'] = result_df['subject_id'].fillna(result_df['subject_id_adm'])
            
        result_df = result_df[[col for col in keep_columns if col in result_df.columns]]
        
        print(f"\n✅ 입원 당일 검사 추출 완료: {len(result_df):,}건")
        
        # 중복 제거 (같은 검사를 여러 번 한 경우 첫 번째만)
        result_df = result_df.sort_values(['hadm_id', 'itemid', 'charttime'])
        result_df = result_df.drop_duplicates(subset=['hadm_id', 'itemid'], keep='first')
        print(f"   중복 제거 후: {len(result_df):,}건")
        
        # 입원별 검사 수 확인
        labs_per_admission = result_df.groupby('hadm_id').size()
        print(f"   입원 당일 검사가 있는 입원: {len(labs_per_admission):,}건")
        print(f"   입원당 평균 검사 수: {labs_per_admission.mean():.1f}개")
        
        return result_df
    else:
        print("⚠️ 입원 당일 검사 데이터 없음")
        return pd.DataFrame()

def create_wide_format(admission_day_labs):
    """Wide format으로 변환 (환자별 행, 검사별 열)"""
    print("\n3. Wide format 변환 중...")
    
    if admission_day_labs.empty:
        return pd.DataFrame()
    
    # 검사명 추가
    admission_day_labs['lab_name'] = admission_day_labs['itemid'].map(COMMON_LAB_ITEMS)
    
    # Pivot table 생성
    wide_df = admission_day_labs.pivot_table(
        index=['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag'],
        columns='lab_name',
        values='valuenum',
        aggfunc='first'
    ).reset_index()
    
    print(f"✅ Wide format 변환 완료: {len(wide_df)} 입원 × {len(wide_df.columns)-4} 검사")
    
    return wide_df

def calculate_statistics(wide_df):
    """기본 통계 계산"""
    print("\n4. 통계 계산 중...")
    
    if wide_df.empty:
        return {}
    
    stats = {}
    
    # 전체 통계
    stats['total_admissions'] = len(wide_df)
    stats['admissions_with_labs'] = len(wide_df)
    
    # 검사별 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']]
    
    stats['lab_statistics'] = {}
    for lab in lab_columns:
        if lab in wide_df.columns:
            lab_data = wide_df[lab].dropna()
            if len(lab_data) > 0:
                stats['lab_statistics'][lab] = {
                    'count': int(len(lab_data)),
                    'missing_pct': float((len(wide_df) - len(lab_data)) / len(wide_df) * 100),
                    'mean': float(lab_data.mean()),
                    'std': float(lab_data.std()),
                    'min': float(lab_data.min()),
                    'q1': float(lab_data.quantile(0.25)),
                    'median': float(lab_data.median()),
                    'q3': float(lab_data.quantile(0.75)),
                    'max': float(lab_data.max())
                }
    
    # 사망률별 통계
    if 'hospital_expire_flag' in wide_df.columns:
        stats['mortality_rate'] = float(wide_df['hospital_expire_flag'].mean() * 100)
        
        # 생존/사망 그룹별 검사 수
        survived = wide_df[wide_df['hospital_expire_flag'] == 0]
        died = wide_df[wide_df['hospital_expire_flag'] == 1]
        
        stats['survived_count'] = len(survived)
        stats['died_count'] = len(died)
        
        # 각 그룹의 검사 완성도
        stats['lab_completeness'] = {
            'survived': {},
            'died': {}
        }
        
        for lab in lab_columns:
            if lab in wide_df.columns:
                stats['lab_completeness']['survived'][lab] = float((~survived[lab].isna()).mean() * 100)
                stats['lab_completeness']['died'][lab] = float((~died[lab].isna()).mean() * 100)
    
    print("✅ 통계 계산 완료")
    
    return stats

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 입원 당일 혈액검사 데이터 추출")
    print("=" * 80)
    
    # 1. 데이터 로드
    admissions, patients, labevents = load_data()
    
    # 2. 입원 당일 검사 추출
    admission_day_labs = extract_admission_day_labs(admissions, labevents)
    
    if not admission_day_labs.empty:
        # 3. Wide format 변환
        wide_df = create_wide_format(admission_day_labs)
        
        # 4. 통계 계산
        stats = calculate_statistics(wide_df)
        
        # 5. 결과 저장
        print("\n5. 결과 저장 중...")
        
        # 원본 형태 저장
        output_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/admission_day_labs.csv')
        admission_day_labs.to_csv(output_path, index=False)
        print(f"   ✅ 원본 데이터: admission_day_labs.csv")
        
        # Wide format 저장
        wide_output_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/admission_day_labs_wide.csv')
        wide_df.to_csv(wide_output_path, index=False)
        print(f"   ✅ Wide format: admission_day_labs_wide.csv")
        
        # 통계 저장
        stats_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/lab_statistics.json')
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"   ✅ 통계: lab_statistics.json")
        
        # 6. 요약 출력
        print("\n" + "=" * 80)
        print("✅ 추출 완료!")
        print("=" * 80)
        
        print(f"\n[추출 요약]")
        print(f"• 총 입원: {stats['total_admissions']}건")
        print(f"• 입원 당일 검사 있음: {stats['admissions_with_labs']}건")
        if 'mortality_rate' in stats:
            print(f"• 사망률: {stats['mortality_rate']:.1f}%")
        
        print(f"\n[검사 항목별 데이터 수]")
        for lab, lab_stats in sorted(stats['lab_statistics'].items(), 
                                    key=lambda x: x[1]['count'], 
                                    reverse=True)[:10]:
            print(f"  - {lab}: {lab_stats['count']}건 (결측 {lab_stats['missing_pct']:.1f}%)")
        
        print(f"\n💾 저장 위치: analysis_initial_lab/data/")
        
        return wide_df, stats
    else:
        print("\n⚠️ 입원 당일 검사 데이터가 없습니다.")
        return pd.DataFrame(), {}

if __name__ == "__main__":
    wide_df, stats = main()