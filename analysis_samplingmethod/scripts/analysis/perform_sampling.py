#!/usr/bin/env python3
"""
MIMIC-IV 데이터 샘플링 스크립트
- 병원 내 사망: 300건
- 병원 후 사망: 300건  
- 생존: 600건
총 1,200건의 균형잡힌 admission 샘플 추출
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 설정
RANDOM_STATE = 42
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'

# 샘플 크기
N_IN_HOSPITAL_DEATH = 300
N_POST_HOSPITAL_DEATH = 300
N_SURVIVED = 600

def load_main_data():
    """메인 데이터 로드 (admissions, patients)"""
    print("=" * 80)
    print("📊 MIMIC-IV 데이터 샘플링")
    print("=" * 80)
    print("\n1. 데이터 로딩 중...")
    
    # 데이터 로드
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/core/admissions.csv'))
    patients = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/core/patients.csv'))
    
    print(f"✅ Admissions 로드: {len(admissions):,} 건")
    print(f"✅ Patients 로드: {len(patients):,} 명")
    
    return admissions, patients

def prepare_sampling_data(admissions, patients):
    """샘플링을 위한 데이터 준비"""
    print("\n2. 데이터 병합 및 전처리...")
    
    # 데이터 병합
    df = admissions.merge(patients[['subject_id', 'anchor_age', 'dod']], 
                         on='subject_id', how='left')
    
    # 0세 제외
    df_filtered = df[df['anchor_age'] > 0].copy()
    excluded_count = len(df) - len(df_filtered)
    
    print(f"✅ 데이터 병합 완료")
    print(f"✅ 0세 환자 제외: {excluded_count:,} 건")
    print(f"✅ 샘플링 대상: {len(df_filtered):,} 건")
    
    return df_filtered

def categorize_admissions(df):
    """입원 데이터를 세 그룹으로 분류"""
    print("\n3. 데이터 분류 중...")
    
    # 병원 내 사망 (hospital_expire_flag = 1)
    in_hospital_death = df[df['hospital_expire_flag'] == 1]
    
    # 병원 후 사망 (hospital_expire_flag = 0 & dod is not null)
    post_hospital_death = df[(df['hospital_expire_flag'] == 0) & 
                             (df['dod'].notna())]
    
    # 생존 (dod is null)
    survived = df[df['dod'].isna()]
    
    print(f"\n분류 결과:")
    print(f"• 병원 내 사망: {len(in_hospital_death):,} 건")
    print(f"• 병원 후 사망: {len(post_hospital_death):,} 건")
    print(f"• 생존: {len(survived):,} 건")
    
    # 검증
    total = len(in_hospital_death) + len(post_hospital_death) + len(survived)
    if total != len(df):
        print(f"⚠️ 경고: 분류 합계({total})가 전체({len(df)})와 다름")
    
    return in_hospital_death, post_hospital_death, survived

def perform_sampling(in_hospital_death, post_hospital_death, survived):
    """각 그룹에서 랜덤 샘플링"""
    print("\n4. 샘플링 수행 중...")
    
    samples = {}
    
    # 병원 내 사망 샘플링
    n_in_hospital = min(N_IN_HOSPITAL_DEATH, len(in_hospital_death))
    samples['in_hospital_death'] = in_hospital_death.sample(
        n=n_in_hospital, random_state=RANDOM_STATE
    )
    print(f"✅ 병원 내 사망: {n_in_hospital}/{N_IN_HOSPITAL_DEATH} 샘플")
    
    # 병원 후 사망 샘플링
    n_post_hospital = min(N_POST_HOSPITAL_DEATH, len(post_hospital_death))
    samples['post_hospital_death'] = post_hospital_death.sample(
        n=n_post_hospital, random_state=RANDOM_STATE
    )
    print(f"✅ 병원 후 사망: {n_post_hospital}/{N_POST_HOSPITAL_DEATH} 샘플")
    
    # 생존 샘플링
    n_survived = min(N_SURVIVED, len(survived))
    samples['survived'] = survived.sample(
        n=n_survived, random_state=RANDOM_STATE
    )
    print(f"✅ 생존: {n_survived}/{N_SURVIVED} 샘플")
    
    # 전체 샘플 합치기
    sampled_admissions = pd.concat([
        samples['in_hospital_death'],
        samples['post_hospital_death'],
        samples['survived']
    ], ignore_index=True)
    
    print(f"\n✅ 총 샘플 수: {len(sampled_admissions):,} 건")
    
    return sampled_admissions, samples

def extract_related_data(sampled_admissions):
    """샘플된 admission과 관련된 모든 데이터 추출"""
    print("\n5. 관련 데이터 추출 중...")
    
    # 샘플된 ID들
    sampled_subject_ids = sampled_admissions['subject_id'].unique()
    sampled_hadm_ids = sampled_admissions['hadm_id'].unique()
    
    print(f"• 고유 환자 수: {len(sampled_subject_ids):,} 명")
    print(f"• 고유 입원 수: {len(sampled_hadm_ids):,} 건")
    
    extracted_data = {}
    
    # Core 테이블 추출
    print("\n5.1 Core 테이블 추출...")
    
    # patients
    patients_full = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/core/patients.csv'))
    extracted_data['patients'] = patients_full[
        patients_full['subject_id'].isin(sampled_subject_ids)
    ]
    print(f"✅ patients: {len(extracted_data['patients']):,} 행")
    
    # admissions (이미 샘플링됨)
    extracted_data['admissions'] = sampled_admissions
    print(f"✅ admissions: {len(extracted_data['admissions']):,} 행")
    
    # transfers
    transfers = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/core/transfers.csv'))
    extracted_data['transfers'] = transfers[
        transfers['hadm_id'].isin(sampled_hadm_ids)
    ]
    print(f"✅ transfers: {len(extracted_data['transfers']):,} 행")
    
    # Hosp 테이블 추출 (주요 테이블만)
    print("\n5.2 Hosp 테이블 추출...")
    hosp_tables = [
        'diagnoses_icd', 'procedures_icd', 'labevents', 
        'prescriptions', 'services'
    ]
    
    for table in hosp_tables:
        try:
            file_path = os.path.join(BASE_PATH, f'dataset2/hosp/{table}.csv')
            if os.path.exists(file_path):
                # 첫 줄을 읽어 컬럼 확인
                temp_df = pd.read_csv(file_path, nrows=1)
                
                if 'subject_id' in temp_df.columns:
                    df = pd.read_csv(file_path)
                    extracted_data[f'hosp_{table}'] = df[
                        df['subject_id'].isin(sampled_subject_ids)
                    ]
                elif 'hadm_id' in temp_df.columns:
                    df = pd.read_csv(file_path)
                    extracted_data[f'hosp_{table}'] = df[
                        df['hadm_id'].isin(sampled_hadm_ids)
                    ]
                else:
                    print(f"⚠️ {table}: subject_id/hadm_id 컬럼 없음")
                    continue
                    
                print(f"✅ {table}: {len(extracted_data[f'hosp_{table}']):,} 행")
            else:
                print(f"⚠️ {table}: 파일 없음")
        except Exception as e:
            print(f"❌ {table} 처리 중 오류: {e}")
    
    # ICU 테이블 추출 (주요 테이블만)
    print("\n5.3 ICU 테이블 추출...")
    
    # icustays 먼저 추출
    try:
        icustays = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/icu/icustays.csv'))
        extracted_data['icu_icustays'] = icustays[
            icustays['hadm_id'].isin(sampled_hadm_ids)
        ]
        sampled_stay_ids = extracted_data['icu_icustays']['stay_id'].unique()
        print(f"✅ icustays: {len(extracted_data['icu_icustays']):,} 행")
        print(f"• ICU stays: {len(sampled_stay_ids):,} 건")
    except Exception as e:
        print(f"❌ icustays 처리 중 오류: {e}")
        sampled_stay_ids = []
    
    return extracted_data, sampled_subject_ids, sampled_hadm_ids

def save_extracted_data(extracted_data):
    """추출된 데이터를 processed_data 폴더에 저장"""
    print("\n6. 데이터 저장 중...")
    
    # Core 테이블 저장
    core_path = os.path.join(BASE_PATH, 'processed_data/core')
    
    extracted_data['patients'].to_csv(
        os.path.join(core_path, 'patients_sampled.csv'), index=False
    )
    print(f"✅ patients_sampled.csv 저장")
    
    extracted_data['admissions'].to_csv(
        os.path.join(core_path, 'admissions_sampled.csv'), index=False
    )
    print(f"✅ admissions_sampled.csv 저장")
    
    extracted_data['transfers'].to_csv(
        os.path.join(core_path, 'transfers_sampled.csv'), index=False
    )
    print(f"✅ transfers_sampled.csv 저장")
    
    # Hosp 테이블 저장
    hosp_path = os.path.join(BASE_PATH, 'processed_data/hosp')
    hosp_saved = 0
    
    for key, df in extracted_data.items():
        if key.startswith('hosp_'):
            table_name = key.replace('hosp_', '')
            df.to_csv(
                os.path.join(hosp_path, f'{table_name}_sampled.csv'), 
                index=False
            )
            hosp_saved += 1
    
    print(f"✅ Hosp 테이블 {hosp_saved}개 저장")
    
    # ICU 테이블 저장
    icu_path = os.path.join(BASE_PATH, 'processed_data/icu')
    
    if 'icu_icustays' in extracted_data:
        extracted_data['icu_icustays'].to_csv(
            os.path.join(icu_path, 'icustays_sampled.csv'), index=False
        )
        print(f"✅ icustays_sampled.csv 저장")

def analyze_sample_statistics(sampled_admissions, samples):
    """샘플 통계 분석 및 시각화"""
    print("\n7. 샘플 통계 분석...")
    
    stats = {}
    
    # 기본 통계
    stats['total_samples'] = len(sampled_admissions)
    stats['in_hospital_death'] = len(samples['in_hospital_death'])
    stats['post_hospital_death'] = len(samples['post_hospital_death'])
    stats['survived'] = len(samples['survived'])
    
    # 연령 통계
    for group_name, group_df in samples.items():
        stats[f'{group_name}_age_mean'] = group_df['anchor_age'].mean()
        stats[f'{group_name}_age_std'] = group_df['anchor_age'].std()
        stats[f'{group_name}_age_median'] = group_df['anchor_age'].median()
    
    # 성별 분포
    stats['gender_distribution'] = {}
    for group_name, group_df in samples.items():
        # subject_id로 patients 정보 가져오기
        patients = pd.read_csv(os.path.join(BASE_PATH, 'dataset2/core/patients.csv'))
        group_with_gender = group_df.merge(
            patients[['subject_id', 'gender']], 
            on='subject_id', 
            how='left'
        )
        gender_counts = group_with_gender['gender'].value_counts()
        stats['gender_distribution'][group_name] = gender_counts.to_dict()
    
    # 시각화
    create_visualizations(samples, stats)
    
    # 결과 저장
    save_results(stats, sampled_admissions)
    
    return stats

def create_visualizations(samples, stats):
    """샘플링 결과 시각화"""
    print("\n8. 시각화 생성 중...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 1. 샘플 크기 비교
    sample_sizes = [stats['in_hospital_death'], 
                   stats['post_hospital_death'], 
                   stats['survived']]
    labels = ['In-Hospital\nDeath', 'Post-Hospital\nDeath', 'Survived']
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    
    axes[0, 0].bar(labels, sample_sizes, color=colors, edgecolor='black')
    axes[0, 0].set_title('Sample Size by Group', fontsize=12, fontweight='bold')
    axes[0, 0].set_ylabel('Number of Admissions')
    for i, v in enumerate(sample_sizes):
        axes[0, 0].text(i, v + 10, str(v), ha='center', fontweight='bold')
    
    # 2. 연령 분포 박스플롯
    age_data = []
    for group_name, group_df in samples.items():
        age_data.append(group_df['anchor_age'].values)
    
    bp = axes[0, 1].boxplot(age_data, labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[0, 1].set_title('Age Distribution by Group', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylabel('Age (years)')
    
    # 3. 전체 연령 히스토그램
    for group_name, group_df, color, label in zip(
        samples.keys(), samples.values(), colors, labels
    ):
        axes[0, 2].hist(group_df['anchor_age'], bins=20, alpha=0.5, 
                       color=color, label=label, edgecolor='black')
    axes[0, 2].set_title('Age Distribution (Histogram)', fontsize=12, fontweight='bold')
    axes[0, 2].set_xlabel('Age (years)')
    axes[0, 2].set_ylabel('Frequency')
    axes[0, 2].legend()
    
    # 4. 성별 분포 - 병원 내 사망
    plot_gender_pie(axes[1, 0], stats['gender_distribution']['in_hospital_death'],
                   'Gender Distribution:\nIn-Hospital Death')
    
    # 5. 성별 분포 - 병원 후 사망
    plot_gender_pie(axes[1, 1], stats['gender_distribution']['post_hospital_death'],
                   'Gender Distribution:\nPost-Hospital Death')
    
    # 6. 성별 분포 - 생존
    plot_gender_pie(axes[1, 2], stats['gender_distribution']['survived'],
                   'Gender Distribution:\nSurvived')
    
    plt.suptitle('MIMIC-IV Sampling Results', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(BASE_PATH, 
                              'analysis_samplingmethod/figures/sampling_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 시각화 저장: figures/sampling_distribution.png")

def plot_gender_pie(ax, gender_dict, title):
    """성별 파이 차트 그리기"""
    if gender_dict:
        sizes = list(gender_dict.values())
        labels = [f"{k}\n({v})" for k, v in gender_dict.items()]
        colors = ['#3498db', '#e91e63']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=90)
        ax.set_title(title, fontsize=10, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
        ax.set_title(title, fontsize=10, fontweight='bold')

def save_results(stats, sampled_admissions):
    """분석 결과 저장"""
    print("\n9. 결과 저장 중...")
    
    output_path = os.path.join(BASE_PATH, 'analysis_samplingmethod/data')
    
    # 통계 결과 JSON으로 저장
    stats['sampling_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['random_state'] = RANDOM_STATE
    
    with open(os.path.join(output_path, 'sampling_results.json'), 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ sampling_results.json 저장")
    
    # 샘플링된 ID 저장
    sampled_ids = sampled_admissions[['subject_id', 'hadm_id', 'hospital_expire_flag']].copy()
    sampled_ids['mortality_group'] = sampled_admissions.apply(
        lambda x: 'in_hospital_death' if x['hospital_expire_flag'] == 1
        else 'post_hospital_death' if pd.notna(x['dod'])
        else 'survived', axis=1
    )
    
    sampled_ids.to_csv(os.path.join(output_path, 'sampled_ids.csv'), index=False)
    print(f"✅ sampled_ids.csv 저장")
    
    # 요약 통계 CSV 저장
    summary_stats = pd.DataFrame([
        {'Group': 'In-Hospital Death', 'Count': stats['in_hospital_death'],
         'Mean Age': stats['in_hospital_death_age_mean'],
         'Median Age': stats['in_hospital_death_age_median']},
        {'Group': 'Post-Hospital Death', 'Count': stats['post_hospital_death'],
         'Mean Age': stats['post_hospital_death_age_mean'],
         'Median Age': stats['post_hospital_death_age_median']},
        {'Group': 'Survived', 'Count': stats['survived'],
         'Mean Age': stats['survived_age_mean'],
         'Median Age': stats['survived_age_median']}
    ])
    
    summary_stats.to_csv(os.path.join(output_path, 'sampling_statistics.csv'), 
                        index=False)
    print(f"✅ sampling_statistics.csv 저장")

def main():
    """메인 실행 함수"""
    try:
        # 1. 데이터 로드
        admissions, patients = load_main_data()
        
        # 2. 데이터 준비
        df_filtered = prepare_sampling_data(admissions, patients)
        
        # 3. 데이터 분류
        in_hospital_death, post_hospital_death, survived = categorize_admissions(df_filtered)
        
        # 4. 샘플링
        sampled_admissions, samples = perform_sampling(
            in_hospital_death, post_hospital_death, survived
        )
        
        # 5. 관련 데이터 추출
        extracted_data, sampled_subject_ids, sampled_hadm_ids = extract_related_data(
            sampled_admissions
        )
        
        # 6. 데이터 저장
        save_extracted_data(extracted_data)
        
        # 7. 통계 분석 및 시각화
        stats = analyze_sample_statistics(sampled_admissions, samples)
        
        print("\n" + "=" * 80)
        print("✅ 샘플링 완료!")
        print("=" * 80)
        print(f"\n최종 결과:")
        print(f"• 총 샘플: {stats['total_samples']:,} 건")
        print(f"• 병원 내 사망: {stats['in_hospital_death']:,} 건")
        print(f"• 병원 후 사망: {stats['post_hospital_death']:,} 건")
        print(f"• 생존: {stats['survived']:,} 건")
        print(f"\n저장 위치:")
        print(f"• 샘플 데이터: processed_data/")
        print(f"• 분석 결과: analysis_samplingmethod/data/")
        print(f"• 시각화: analysis_samplingmethod/figures/")
        
        return stats
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    stats = main()