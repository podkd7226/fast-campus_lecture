#!/usr/bin/env python3
"""
사망 데이터 불일치 사례 상세 분석
hospital_expire_flag=1이지만 deathtime이 없는 13건의 특징을 분석합니다.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import platform
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:  # Linux
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / 'dataset2'
OUTPUT_DIR = BASE_DIR / 'analysis_death'
FIGURES_DIR = OUTPUT_DIR / 'figures'
DATA_OUTPUT_DIR = OUTPUT_DIR / 'data'

def analyze_inconsistent_cases():
    """불일치 사례 상세 분석"""
    
    print("=" * 80)
    print("사망 데이터 불일치 사례 상세 분석")
    print("=" * 80)
    
    # 데이터 로딩
    print("\n1. 데이터 로딩 중...")
    admissions = pd.read_csv(DATA_DIR / 'core' / 'admissions.csv')
    patients = pd.read_csv(DATA_DIR / 'core' / 'patients.csv')
    transfers = pd.read_csv(DATA_DIR / 'core' / 'transfers.csv')
    
    # ICU 데이터 로딩
    icustays = pd.read_csv(DATA_DIR / 'icu' / 'icustays.csv')
    
    # 불일치 사례 찾기
    print("\n2. 불일치 사례 식별")
    print("-" * 40)
    
    # hospital_expire_flag=1이지만 deathtime이 없는 경우
    inconsistent_mask = (admissions['hospital_expire_flag'] == 1) & (admissions['deathtime'].isna())
    inconsistent_cases = admissions[inconsistent_mask].copy()
    
    print(f"발견된 불일치 사례: {len(inconsistent_cases)}건")
    
    # 환자 정보 병합
    inconsistent_cases = inconsistent_cases.merge(
        patients[['subject_id', 'gender', 'anchor_age', 'dod']], 
        on='subject_id', 
        how='left'
    )
    
    # 불일치 사례 ID 목록
    print("\n3. 불일치 사례 ID 목록")
    print("-" * 40)
    
    case_ids = []
    for idx, row in inconsistent_cases.iterrows():
        case_info = {
            'subject_id': int(row['subject_id']),
            'hadm_id': int(row['hadm_id']),
            'gender': row['gender'],
            'age': int(row['anchor_age']) if pd.notna(row['anchor_age']) else None,
            'admission_type': row['admission_type'],
            'admission_location': row['admission_location'],
            'discharge_location': row['discharge_location'],
            'insurance': row['insurance'],
            'ethnicity': row['ethnicity'],
            'admittime': str(row['admittime']),
            'dischtime': str(row['dischtime']),
            'dod': str(row['dod']) if pd.notna(row['dod']) else None
        }
        case_ids.append(case_info)
        
        print(f"  Subject ID: {case_info['subject_id']:8d}, "
              f"Admission ID: {case_info['hadm_id']:8d}, "
              f"Age: {case_info['age'] if case_info['age'] else 'N/A':3}, "
              f"Gender: {case_info['gender']}")
    
    # 4. 특징 분석
    print("\n4. 불일치 사례들의 특징 분석")
    print("-" * 40)
    
    # 4.1 인구통계학적 특징
    print("\n[인구통계학적 특징]")
    print(f"  성별 분포:")
    gender_counts = inconsistent_cases['gender'].value_counts()
    for gender, count in gender_counts.items():
        print(f"    - {gender}: {count}명 ({count/len(inconsistent_cases)*100:.1f}%)")
    
    # 나이 통계
    ages = inconsistent_cases['anchor_age'].dropna()
    if len(ages) > 0:
        print(f"  연령 분포:")
        print(f"    - 평균: {ages.mean():.1f}세")
        print(f"    - 중앙값: {ages.median():.1f}세")
        print(f"    - 범위: {ages.min():.0f}세 - {ages.max():.0f}세")
    
    # 4.2 입원 관련 특징
    print("\n[입원 관련 특징]")
    print(f"  입원 유형:")
    admission_types = inconsistent_cases['admission_type'].value_counts()
    for atype, count in admission_types.items():
        print(f"    - {atype}: {count}건 ({count/len(inconsistent_cases)*100:.1f}%)")
    
    print(f"\n  입원 경로:")
    admission_locs = inconsistent_cases['admission_location'].value_counts()
    for loc, count in admission_locs.items():
        if pd.notna(loc):
            print(f"    - {loc}: {count}건")
    
    print(f"\n  퇴원 위치:")
    discharge_locs = inconsistent_cases['discharge_location'].value_counts()
    for loc, count in discharge_locs.items():
        if pd.notna(loc):
            print(f"    - {loc}: {count}건")
    
    # 4.3 보험 및 민족성
    print("\n[보험 및 민족성]")
    print(f"  보험 유형:")
    insurance_types = inconsistent_cases['insurance'].value_counts()
    for ins, count in insurance_types.items():
        print(f"    - {ins}: {count}건")
    
    print(f"\n  민족성:")
    ethnicities = inconsistent_cases['ethnicity'].value_counts()
    for eth, count in ethnicities.items():
        if pd.notna(eth):
            print(f"    - {eth}: {count}건")
    
    # 4.4 DOD 존재 여부 확인
    print("\n[사망일(dod) 정보]")
    has_dod = inconsistent_cases['dod'].notna().sum()
    print(f"  - dod 있음: {has_dod}건 ({has_dod/len(inconsistent_cases)*100:.1f}%)")
    print(f"  - dod 없음: {len(inconsistent_cases)-has_dod}건 ({(len(inconsistent_cases)-has_dod)/len(inconsistent_cases)*100:.1f}%)")
    
    # 5. ICU 입실 여부 확인
    print("\n5. ICU 입실 여부 확인")
    print("-" * 40)
    
    # ICU 입실 확인
    icu_admissions = []
    for hadm_id in inconsistent_cases['hadm_id']:
        icu_stay = icustays[icustays['hadm_id'] == hadm_id]
        if len(icu_stay) > 0:
            icu_admissions.append(hadm_id)
    
    print(f"  ICU 입실: {len(icu_admissions)}건 ({len(icu_admissions)/len(inconsistent_cases)*100:.1f}%)")
    print(f"  일반 병동: {len(inconsistent_cases)-len(icu_admissions)}건 ({(len(inconsistent_cases)-len(icu_admissions))/len(inconsistent_cases)*100:.1f}%)")
    
    # 6. 재원 기간 분석
    print("\n6. 재원 기간 분석")
    print("-" * 40)
    
    # 재원 기간 계산
    inconsistent_cases['admittime'] = pd.to_datetime(inconsistent_cases['admittime'])
    inconsistent_cases['dischtime'] = pd.to_datetime(inconsistent_cases['dischtime'])
    inconsistent_cases['los_days'] = (inconsistent_cases['dischtime'] - inconsistent_cases['admittime']).dt.total_seconds() / 86400
    
    los_stats = inconsistent_cases['los_days'].describe()
    print(f"  재원 기간 통계:")
    print(f"    - 평균: {los_stats['mean']:.1f}일")
    print(f"    - 중앙값: {los_stats['50%']:.1f}일")
    print(f"    - 최소: {los_stats['min']:.1f}일")
    print(f"    - 최대: {los_stats['max']:.1f}일")
    
    # 7. 정상 사례와 비교
    print("\n7. 정상 사례와 비교")
    print("-" * 40)
    
    # 정상 사례 (hospital_expire_flag=1이고 deathtime도 있는 경우)
    normal_mask = (admissions['hospital_expire_flag'] == 1) & (admissions['deathtime'].notna())
    normal_cases = admissions[normal_mask].copy()
    normal_cases = normal_cases.merge(
        patients[['subject_id', 'gender', 'anchor_age']], 
        on='subject_id', 
        how='left'
    )
    
    print(f"\n[정상 사례와 비교]")
    print(f"  정상 사례: {len(normal_cases)}건")
    print(f"  불일치 사례: {len(inconsistent_cases)}건")
    
    # 연령 비교
    normal_age_mean = normal_cases['anchor_age'].mean()
    inconsistent_age_mean = inconsistent_cases['anchor_age'].mean()
    print(f"\n  평균 연령:")
    print(f"    - 정상: {normal_age_mean:.1f}세")
    print(f"    - 불일치: {inconsistent_age_mean:.1f}세")
    
    # 입원 유형 비교
    print(f"\n  응급 입원 비율:")
    normal_emergency = (normal_cases['admission_type'] == 'EMERGENCY').sum() / len(normal_cases) * 100
    inconsistent_emergency = (inconsistent_cases['admission_type'] == 'EMERGENCY').sum() / len(inconsistent_cases) * 100
    print(f"    - 정상: {normal_emergency:.1f}%")
    print(f"    - 불일치: {inconsistent_emergency:.1f}%")
    
    # 8. 시각화
    print("\n8. 시각화 생성 중...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 연령 분포 비교
    axes[0, 0].hist(normal_cases['anchor_age'].dropna(), bins=20, alpha=0.5, label='정상', color='blue')
    axes[0, 0].hist(inconsistent_cases['anchor_age'].dropna(), bins=20, alpha=0.5, label='불일치', color='red')
    axes[0, 0].set_xlabel('연령')
    axes[0, 0].set_ylabel('빈도')
    axes[0, 0].set_title('연령 분포 비교')
    axes[0, 0].legend()
    
    # 입원 유형 비교
    admission_comparison = pd.DataFrame({
        '정상': normal_cases['admission_type'].value_counts(),
        '불일치': inconsistent_cases['admission_type'].value_counts()
    }).fillna(0)
    admission_comparison.plot(kind='bar', ax=axes[0, 1])
    axes[0, 1].set_title('입원 유형 비교')
    axes[0, 1].set_xlabel('입원 유형')
    axes[0, 1].set_ylabel('건수')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 재원 기간 분포
    axes[1, 0].boxplot([inconsistent_cases['los_days'].dropna()], labels=['불일치 사례'])
    axes[1, 0].set_ylabel('재원 기간 (일)')
    axes[1, 0].set_title('불일치 사례 재원 기간 분포')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 보험 유형 분포
    insurance_counts = inconsistent_cases['insurance'].value_counts()
    axes[1, 1].pie(insurance_counts.values, labels=insurance_counts.index, autopct='%1.1f%%')
    axes[1, 1].set_title('불일치 사례 보험 유형 분포')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'inconsistent_cases_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  - 분석 차트 저장: figures/inconsistent_cases_analysis.png")
    
    # 9. 결과 저장
    analysis_results = {
        'total_inconsistent_cases': len(inconsistent_cases),
        'case_ids': case_ids,
        'demographics': {
            'gender_distribution': gender_counts.to_dict(),
            'age_stats': {
                'mean': float(ages.mean()) if len(ages) > 0 else None,
                'median': float(ages.median()) if len(ages) > 0 else None,
                'min': float(ages.min()) if len(ages) > 0 else None,
                'max': float(ages.max()) if len(ages) > 0 else None
            }
        },
        'admission_characteristics': {
            'admission_types': admission_types.to_dict(),
            'emergency_rate': float(inconsistent_emergency),
            'icu_admission_rate': float(len(icu_admissions)/len(inconsistent_cases)*100)
        },
        'los_stats': {
            'mean': float(los_stats['mean']),
            'median': float(los_stats['50%']),
            'min': float(los_stats['min']),
            'max': float(los_stats['max'])
        },
        'comparison_with_normal': {
            'normal_cases_count': int(len(normal_cases)),
            'age_difference': float(inconsistent_age_mean - normal_age_mean),
            'emergency_rate_difference': float(inconsistent_emergency - normal_emergency)
        }
    }
    
    # JSON 저장
    with open(DATA_OUTPUT_DIR / 'inconsistent_cases_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    # CSV 저장 (불일치 사례 상세 정보)
    inconsistent_cases_export = inconsistent_cases[['subject_id', 'hadm_id', 'gender', 'anchor_age', 
                                                    'admission_type', 'admission_location', 
                                                    'discharge_location', 'insurance', 'ethnicity',
                                                    'admittime', 'dischtime', 'los_days', 'dod']]
    inconsistent_cases_export.to_csv(DATA_OUTPUT_DIR / 'inconsistent_cases_details.csv', index=False)
    
    print(f"\n결과 파일 저장:")
    print(f"  - JSON: data/inconsistent_cases_analysis.json")
    print(f"  - CSV: data/inconsistent_cases_details.csv")
    
    return analysis_results

if __name__ == "__main__":
    results = analyze_inconsistent_cases()
    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)