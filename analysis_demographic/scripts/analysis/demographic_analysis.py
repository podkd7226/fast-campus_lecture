#!/usr/bin/env python3
"""
MIMIC 데이터셋의 Demographic Analysis
- 전체 사망률 분석
- 연령별 사망률 분석
- 샘플링 전략 수립을 위한 기초 통계
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """patients와 admissions 데이터 로드"""
    print("=" * 80)
    print("📊 MIMIC Demographic Analysis")
    print("=" * 80)
    print("\n1. 데이터 로딩 중...")
    
    # 데이터 로드
    import os
    base_path = '/Users/hyungjun/Desktop/fast campus_lecture'
    patients = pd.read_csv(os.path.join(base_path, 'dataset2/core/patients.csv'))
    admissions = pd.read_csv(os.path.join(base_path, 'dataset2/core/admissions.csv'))
    
    print(f"✅ Patients 데이터: {len(patients):,} 명")
    print(f"✅ Admissions 데이터: {len(admissions):,} 건")
    
    return patients, admissions

def basic_statistics(patients, admissions):
    """기본 통계 분석"""
    print("\n2. 기본 통계 분석")
    print("-" * 50)
    
    results = {}
    
    # 전체 환자 수
    total_patients = len(patients)
    results['total_patients'] = total_patients
    print(f"• 전체 환자 수: {total_patients:,} 명")
    
    # 전체 입원 건수
    total_admissions = len(admissions)
    results['total_admissions'] = total_admissions
    print(f"• 전체 입원 건수: {total_admissions:,} 건")
    
    # 환자당 평균 입원 횟수
    avg_admissions = total_admissions / total_patients
    results['avg_admissions_per_patient'] = round(avg_admissions, 2)
    print(f"• 환자당 평균 입원 횟수: {avg_admissions:.2f} 회")
    
    # 성별 분포
    gender_dist = patients['gender'].value_counts()
    results['gender_distribution'] = gender_dist.to_dict()
    print(f"\n• 성별 분포:")
    for gender, count in gender_dist.items():
        pct = (count / total_patients) * 100
        print(f"  - {gender}: {count:,} 명 ({pct:.1f}%)")
    
    return results

def mortality_analysis(patients, admissions):
    """사망률 분석"""
    print("\n3. 사망률 분석")
    print("-" * 50)
    
    results = {}
    
    # 병원 내 사망 (hospital_expire_flag)
    hospital_deaths = admissions['hospital_expire_flag'].sum()
    hospital_mortality_rate = (hospital_deaths / len(admissions)) * 100
    results['hospital_deaths'] = int(hospital_deaths)
    results['hospital_mortality_rate'] = round(hospital_mortality_rate, 2)
    print(f"• 병원 내 사망: {hospital_deaths:,} 건 ({hospital_mortality_rate:.2f}%)")
    
    # 사망 시간 정보가 있는 환자
    patients_with_dod = patients[patients['dod'].notna()]
    total_deaths = len(patients_with_dod)
    overall_mortality_rate = (total_deaths / len(patients)) * 100
    results['total_deaths'] = total_deaths
    results['overall_mortality_rate'] = round(overall_mortality_rate, 2)
    print(f"• 전체 사망 환자: {total_deaths:,} 명 ({overall_mortality_rate:.2f}%)")
    
    return results

def age_based_analysis(patients, admissions):
    """연령별 분석"""
    print("\n4. 연령별 분석")
    print("-" * 50)
    
    # MIMIC-IV는 anchor_age를 제공 (첫 입원 시점의 나이)
    # anchor_year는 환자의 기준 연도
    patient_age = patients.copy()
    patient_age['age_at_first_admission'] = patient_age['anchor_age']
    
    # 연령 그룹 생성
    age_bins = [0, 18, 30, 40, 50, 60, 70, 80, 90, 200]
    age_labels = ['0-17', '18-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+']
    patient_age['age_group'] = pd.cut(patient_age['age_at_first_admission'], 
                                      bins=age_bins, labels=age_labels)
    
    # 연령 그룹별 통계
    age_stats = []
    print("\n연령 그룹별 분포 및 사망률:")
    print(f"{'연령대':<10} {'환자수':<10} {'비율':<10} {'사망자수':<10} {'사망률':<10}")
    print("-" * 50)
    
    for age_group in age_labels:
        group_data = patient_age[patient_age['age_group'] == age_group]
        total = len(group_data)
        if total > 0:
            deaths = group_data['dod'].notna().sum()
            mortality_rate = (deaths / total) * 100
            pct = (total / len(patient_age)) * 100
            
            age_stats.append({
                'age_group': age_group,
                'count': total,
                'percentage': round(pct, 2),
                'deaths': int(deaths),
                'mortality_rate': round(mortality_rate, 2)
            })
            
            print(f"{age_group:<10} {total:<10,} {pct:<9.1f}% {deaths:<10,} {mortality_rate:<9.2f}%")
    
    # 평균 연령
    mean_age = patient_age['age_at_first_admission'].mean()
    median_age = patient_age['age_at_first_admission'].median()
    print(f"\n• 평균 연령: {mean_age:.1f} 세")
    print(f"• 중간 연령: {median_age:.1f} 세")
    
    results = {
        'age_distribution': age_stats,
        'mean_age': round(mean_age, 1),
        'median_age': round(median_age, 1)
    }
    
    return results, patient_age

def sampling_strategy(patients, admissions, patient_age):
    """샘플링 전략 제안"""
    print("\n5. 샘플링 전략 제안")
    print("-" * 50)
    
    total_patients = len(patients)
    recommendations = []
    
    # 1. 대표 샘플 크기 계산 (95% 신뢰수준, 5% 오차범위)
    confidence_level = 0.95
    margin_error = 0.05
    z_score = 1.96  # 95% 신뢰수준
    
    # 샘플 크기 공식: n = (Z^2 * p * (1-p)) / E^2
    p = 0.5  # 최대 변동성 가정
    sample_size = int((z_score**2 * p * (1-p)) / (margin_error**2))
    
    print(f"\n📌 통계적 대표 샘플 크기:")
    print(f"• 95% 신뢰수준, 5% 오차범위: {sample_size:,} 명")
    
    recommendations.append({
        'strategy': 'Statistical Representative Sample',
        'sample_size': sample_size,
        'confidence_level': '95%',
        'margin_error': '5%'
    })
    
    # 2. 층화 샘플링 (Stratified Sampling) 제안
    print(f"\n📌 층화 샘플링 전략:")
    
    # 연령별 층화
    age_strata_size = int(sample_size * 1.2)  # 20% 추가 샘플
    print(f"• 연령 그룹별 비례 샘플링: {age_strata_size:,} 명")
    
    # 사망률 균형 샘플링
    mortality_balanced = int(sample_size * 1.5)
    print(f"• 사망/생존 균형 샘플링: {mortality_balanced:,} 명")
    
    recommendations.append({
        'strategy': 'Age-Stratified Sampling',
        'sample_size': age_strata_size,
        'method': 'Proportional to age distribution'
    })
    
    recommendations.append({
        'strategy': 'Mortality-Balanced Sampling',
        'sample_size': mortality_balanced,
        'method': '50% survived, 50% deceased'
    })
    
    # 3. 용도별 샘플 크기 제안
    print(f"\n📌 분석 목적별 권장 샘플 크기:")
    print(f"• 탐색적 분석 (EDA): 1,000 - 5,000 명")
    print(f"• 모델 개발: 10,000 - 20,000 명")
    print(f"• 검증 연구: 30,000 - 50,000 명")
    print(f"• 전체 데이터: {total_patients:,} 명")
    
    recommendations.append({
        'strategy': 'Purpose-based Sampling',
        'eda_sample': '1,000 - 5,000',
        'model_development': '10,000 - 20,000',
        'validation_study': '30,000 - 50,000',
        'full_dataset': total_patients
    })
    
    return recommendations

def create_visualizations(patient_age, results):
    """시각화 생성"""
    print("\n6. 시각화 생성 중...")
    
    # 스타일 설정
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Figure 1: 연령 분포 히스토그램
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1-1: 연령 분포
    valid_ages = patient_age['age_at_first_admission'].dropna()
    valid_ages = valid_ages[(valid_ages >= 0) & (valid_ages <= 120)]
    axes[0, 0].hist(valid_ages, bins=30, edgecolor='black', alpha=0.7)
    axes[0, 0].set_xlabel('Age at First Admission')
    axes[0, 0].set_ylabel('Number of Patients')
    axes[0, 0].set_title('Age Distribution of MIMIC Patients')
    axes[0, 0].axvline(valid_ages.mean(), color='red', linestyle='--', 
                       label=f'Mean: {valid_ages.mean():.1f}')
    axes[0, 0].axvline(valid_ages.median(), color='green', linestyle='--', 
                       label=f'Median: {valid_ages.median():.1f}')
    axes[0, 0].legend()
    
    # 1-2: 성별 분포
    gender_data = results['basic_stats']['gender_distribution']
    axes[0, 1].pie(gender_data.values(), labels=gender_data.keys(), 
                   autopct='%1.1f%%', startangle=90)
    axes[0, 1].set_title('Gender Distribution')
    
    # 1-3: 연령별 사망률
    age_data = results['age_analysis']['age_distribution']
    age_groups = [d['age_group'] for d in age_data]
    mortality_rates = [d['mortality_rate'] for d in age_data]
    
    axes[1, 0].bar(age_groups, mortality_rates, color='coral', edgecolor='black')
    axes[1, 0].set_xlabel('Age Group')
    axes[1, 0].set_ylabel('Mortality Rate (%)')
    axes[1, 0].set_title('Mortality Rate by Age Group')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # 1-4: 연령별 환자 수
    patient_counts = [d['count'] for d in age_data]
    axes[1, 1].bar(age_groups, patient_counts, color='skyblue', edgecolor='black')
    axes[1, 1].set_xlabel('Age Group')
    axes[1, 1].set_ylabel('Number of Patients')
    axes[1, 1].set_title('Patient Distribution by Age Group')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    import os
    base_path = '/Users/hyungjun/Desktop/fast campus_lecture'
    plt.savefig(os.path.join(base_path, 'analysis_demographic/figures/demographic_overview.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 시각화 저장 완료: figures/demographic_overview.png")
    
    # Figure 2: 사망률 상세 분석
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 2-1: 생존 vs 사망 비율
    survival_data = {
        'Survived': len(patient_age) - results['mortality']['total_deaths'],
        'Deceased': results['mortality']['total_deaths']
    }
    axes[0].pie(survival_data.values(), labels=survival_data.keys(), 
                autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
    axes[0].set_title('Overall Survival Status')
    
    # 2-2: 연령과 사망률의 관계
    age_groups_sorted = sorted(age_data, key=lambda x: x['age_group'])
    ages = [d['age_group'] for d in age_groups_sorted]
    rates = [d['mortality_rate'] for d in age_groups_sorted]
    
    axes[1].plot(ages, rates, marker='o', linewidth=2, markersize=8, color='darkred')
    axes[1].set_xlabel('Age Group')
    axes[1].set_ylabel('Mortality Rate (%)')
    axes[1].set_title('Mortality Rate Trend by Age')
    axes[1].grid(True, alpha=0.3)
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, 'analysis_demographic/figures/mortality_analysis.png'), 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 시각화 저장 완료: figures/mortality_analysis.png")

def save_results(results):
    """결과 저장"""
    print("\n7. 결과 저장 중...")
    
    # JSON으로 저장
    import os
    base_path = '/Users/hyungjun/Desktop/fast campus_lecture'
    with open(os.path.join(base_path, 'analysis_demographic/data/demographic_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ 분석 결과 저장 완료: data/demographic_results.json")

def main():
    """메인 실행 함수"""
    # 데이터 로드
    patients, admissions = load_data()
    
    # 분석 수행
    basic_stats = basic_statistics(patients, admissions)
    mortality_stats = mortality_analysis(patients, admissions)
    age_stats, patient_age = age_based_analysis(patients, admissions)
    sampling_recs = sampling_strategy(patients, admissions, patient_age)
    
    # 결과 통합
    results = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'basic_stats': basic_stats,
        'mortality': mortality_stats,
        'age_analysis': age_stats,
        'sampling_recommendations': sampling_recs
    }
    
    # 시각화 생성
    create_visualizations(patient_age, results)
    
    # 결과 저장
    save_results(results)
    
    print("\n" + "=" * 80)
    print("✅ Demographic Analysis 완료!")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    results = main()