#!/usr/bin/env python3
"""
예측 모델을 위한 통합 데이터셋 준비
- 입원 당일 혈액검사 데이터
- 사망 구분 (병원 내/외)
- 입원기간 계산
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
LAB_DATA_DIR = BASE_DIR / 'analysis_initial_lab_re' / 'data'
OUTPUT_DIR = BASE_DIR / 'analysis_prediction'
FIGURES_DIR = OUTPUT_DIR / 'figures'
DATA_OUTPUT_DIR = OUTPUT_DIR / 'data'

# 디렉토리 생성
FIGURES_DIR.mkdir(exist_ok=True)
DATA_OUTPUT_DIR.mkdir(exist_ok=True)

def load_data():
    """필요한 데이터 로드"""
    print("데이터 로딩 중...")
    
    # 1. 입원 당일 혈액검사 데이터
    labs_df = pd.read_csv(LAB_DATA_DIR / 'labs_initial_merged_wide.csv')
    print(f"  - 혈액검사 데이터: {len(labs_df):,}건")
    
    # 2. 입원 정보 (입원기간 계산용)
    admissions_df = pd.read_csv(DATA_DIR / 'core' / 'admissions.csv')
    print(f"  - 입원 데이터: {len(admissions_df):,}건")
    
    # 3. 환자 정보 (사망일, 나이, 성별)
    patients_df = pd.read_csv(DATA_DIR / 'core' / 'patients.csv')
    print(f"  - 환자 데이터: {len(patients_df):,}건")
    
    return labs_df, admissions_df, patients_df

def add_death_categories(df, patients_df):
    """사망 구분 카테고리 추가"""
    print("\n사망 구분 추가 중...")
    
    # patients 테이블의 dod (Date of Death) 병합
    df = df.merge(patients_df[['subject_id', 'dod']], on='subject_id', how='left')
    
    # 사망 구분 생성
    df['death_type'] = 'alive'  # 기본값: 생존
    df.loc[df['hospital_expire_flag'] == 1, 'death_type'] = 'hospital'  # 병원 내 사망
    df.loc[(df['hospital_expire_flag'] == 0) & (df['dod'].notna()), 'death_type'] = 'outside'  # 병원 외 사망
    
    # 이진 변수 생성
    df['death_binary'] = (df['dod'].notna()).astype(int)  # 전체 사망 여부
    df['hospital_death'] = df['hospital_expire_flag']  # 병원 내 사망 여부 (기존 변수 유지)
    
    # 통계 출력
    print(f"  - 생존: {(df['death_type'] == 'alive').sum():,}건 ({(df['death_type'] == 'alive').mean()*100:.2f}%)")
    print(f"  - 병원 내 사망: {(df['death_type'] == 'hospital').sum():,}건 ({(df['death_type'] == 'hospital').mean()*100:.2f}%)")
    print(f"  - 병원 외 사망: {(df['death_type'] == 'outside').sum():,}건 ({(df['death_type'] == 'outside').mean()*100:.2f}%)")
    
    return df

def add_los_and_demographics(df, admissions_df, patients_df):
    """입원기간 및 인구통계학적 정보 추가"""
    print("\n입원기간 및 인구통계 정보 추가 중...")
    
    # admittime이 이미 있으므로 제외하고 병합
    admission_cols = ['hadm_id', 'dischtime', 'admission_type', 
                      'admission_location', 'discharge_location']
    df = df.merge(admissions_df[admission_cols], on='hadm_id', how='left')
    
    # 입원기간 계산
    df['admittime'] = pd.to_datetime(df['admittime'])
    df['dischtime'] = pd.to_datetime(df['dischtime'])
    df['los_hours'] = (df['dischtime'] - df['admittime']).dt.total_seconds() / 3600
    df['los_days'] = df['los_hours'] / 24
    
    # 음수 입원기간 체크
    negative_los = df['los_hours'] < 0
    if negative_los.sum() > 0:
        print(f"  ⚠️ 음수 입원기간 발견: {negative_los.sum()}건 (0으로 대체)")
        df.loc[negative_los, 'los_hours'] = 0
        df.loc[negative_los, 'los_days'] = 0
    
    # 인구통계학적 정보 추가
    patient_cols = ['subject_id', 'gender', 'anchor_age', 'anchor_year']
    df = df.merge(patients_df[patient_cols], on='subject_id', how='left', suffixes=('', '_y'))
    
    # 중복 컬럼 제거
    df = df.loc[:, ~df.columns.str.endswith('_y')]
    
    # 정확한 입원 시 나이 계산
    # 공식: 입원 시 나이 = 입원연도 - (anchor_year - anchor_age)
    df['birth_year'] = df['anchor_year'] - df['anchor_age']
    df['admit_year'] = pd.to_datetime(df['admittime']).dt.year
    df['age_at_admission'] = df['admit_year'] - df['birth_year']
    
    # 89세 이상은 모두 91세로 그룹화되어 있음을 표시
    df.loc[df['anchor_age'] >= 89, 'age_group_note'] = '>89 (grouped)'
    
    # age_at_admission을 age로 사용
    df['age'] = df['age_at_admission']
    
    print(f"  - 평균 입원기간: {df['los_days'].mean():.2f}일 (표준편차: {df['los_days'].std():.2f})")
    print(f"  - 평균 나이 (입원 시): {df['age'].mean():.1f}세 (표준편차: {df['age'].std():.1f})")
    print(f"  - anchor_age 평균: {df['anchor_age'].mean():.1f}세 (참고용)")
    print(f"  - 성별 분포: 남성 {(df['gender'] == 'M').mean()*100:.1f}%, 여성 {(df['gender'] == 'F').mean()*100:.1f}%")
    
    return df

def validate_data(df):
    """데이터 검증 및 정리"""
    print("\n데이터 검증 중...")
    
    # 결측치 확인
    missing_cols = []
    for col in ['death_type', 'los_hours', 'age', 'gender']:
        missing = df[col].isna().sum()
        if missing > 0:
            missing_cols.append(f"{col}: {missing}건")
    
    if missing_cols:
        print("  - 결측치 발견:")
        for item in missing_cols:
            print(f"    • {item}")
    else:
        print("  - 결측치 없음")
    
    # 이상치 확인
    print("\n이상치 확인:")
    
    # 극단적인 입원기간
    extreme_los = df['los_days'] > 365
    if extreme_los.sum() > 0:
        print(f"  - 1년 초과 입원: {extreme_los.sum()}건")
    
    # 극단적인 나이
    extreme_age = (df['age'] > 100) | (df['age'] < 0)
    if extreme_age.sum() > 0:
        print(f"  - 비정상적 나이: {extreme_age.sum()}건")
    
    return df

def generate_statistics(df):
    """통계 정보 생성 및 저장"""
    print("\n통계 정보 생성 중...")
    
    # 혈액검사 컬럼 식별
    lab_columns = [col for col in df.columns 
                   if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag',
                                 'deathtime', 'admit_date', 'dod', 'death_type', 'death_binary',
                                 'hospital_death', 'dischtime', 'admission_type', 'admission_location',
                                 'discharge_location', 'los_hours', 'los_days', 'gender', 'age',
                                 'anchor_year']]
    
    statistics = {
        'total_records': len(df),
        'dataset_info': {
            'n_lab_features': len(lab_columns),
            'n_total_features': len(df.columns),
            'date_created': datetime.now().isoformat()
        },
        'target_variables': {
            'death_type': {
                'alive': int((df['death_type'] == 'alive').sum()),
                'hospital': int((df['death_type'] == 'hospital').sum()),
                'outside': int((df['death_type'] == 'outside').sum())
            },
            'death_binary': {
                'alive': int((df['death_binary'] == 0).sum()),
                'dead': int((df['death_binary'] == 1).sum())
            },
            'hospital_death': {
                'no': int((df['hospital_death'] == 0).sum()),
                'yes': int((df['hospital_death'] == 1).sum())
            }
        },
        'los_statistics': {
            'mean_days': float(df['los_days'].mean()),
            'median_days': float(df['los_days'].median()),
            'std_days': float(df['los_days'].std()),
            'min_days': float(df['los_days'].min()),
            'max_days': float(df['los_days'].max()),
            'q1_days': float(df['los_days'].quantile(0.25)),
            'q3_days': float(df['los_days'].quantile(0.75))
        },
        'demographics': {
            'age': {
                'mean': float(df['age'].mean()),
                'std': float(df['age'].std()),
                'min': float(df['age'].min()),
                'max': float(df['age'].max())
            },
            'gender': {
                'M': int((df['gender'] == 'M').sum()),
                'F': int((df['gender'] == 'F').sum())
            }
        },
        'lab_missing_rates': {}
    }
    
    # 혈액검사 결측률 계산
    for col in lab_columns[:10]:  # 상위 10개만 표시
        missing_rate = df[col].isna().mean()
        statistics['lab_missing_rates'][col] = round(float(missing_rate), 4)
    
    # JSON 저장
    with open(DATA_OUTPUT_DIR / 'data_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2, ensure_ascii=False)
    
    print(f"  - 통계 정보 저장: data_statistics.json")
    
    return statistics

def create_visualizations(df):
    """시각화 생성"""
    print("\n시각화 생성 중...")
    
    # 1. 타겟 변수 분포
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 사망 유형 분포
    death_counts = df['death_type'].value_counts()
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    axes[0, 0].pie(death_counts.values, labels=death_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
    axes[0, 0].set_title('사망 유형 분포', fontsize=12, fontweight='bold')
    
    # 전체 사망 여부
    death_binary_counts = df['death_binary'].value_counts()
    axes[0, 1].bar(['생존', '사망'], death_binary_counts.values, color=['#3498db', '#e74c3c'])
    axes[0, 1].set_title('전체 사망 여부', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylabel('환자 수')
    
    # 입원기간 분포
    axes[1, 0].hist(df['los_days'][df['los_days'] <= 30], bins=30, color='#9b59b6', edgecolor='black')
    axes[1, 0].set_title('입원기간 분포 (30일 이하)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('입원 일수')
    axes[1, 0].set_ylabel('빈도')
    
    # 사망 유형별 입원기간
    death_types = ['alive', 'hospital', 'outside']
    los_by_death = [df[df['death_type'] == dt]['los_days'].dropna() for dt in death_types]
    axes[1, 1].boxplot(los_by_death, labels=['생존', '병원 내 사망', '병원 외 사망'])
    axes[1, 1].set_title('사망 유형별 입원기간', fontsize=12, fontweight='bold')
    axes[1, 1].set_ylabel('입원 일수')
    axes[1, 1].set_ylim(0, 50)  # 시각화를 위해 제한
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'target_distributions.png', dpi=300, bbox_inches='tight')
    print("  - 타겟 변수 분포 저장: target_distributions.png")
    
    # 2. 상관관계 매트릭스 (주요 변수만)
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 수치형 변수 선택
    numeric_cols = ['age', 'los_days', 'death_binary', 'hospital_death']
    
    # 혈액검사 중 결측률이 낮은 상위 10개 추가
    lab_cols = [col for col in df.columns 
                if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag',
                              'deathtime', 'admit_date', 'dod', 'death_type', 'death_binary',
                              'hospital_death', 'dischtime', 'admission_type', 'admission_location',
                              'discharge_location', 'los_hours', 'los_days', 'gender', 'age',
                              'anchor_year']]
    
    missing_rates = [(col, df[col].isna().mean()) for col in lab_cols]
    missing_rates.sort(key=lambda x: x[1])
    top_labs = [col for col, _ in missing_rates[:10]]
    
    corr_cols = numeric_cols + top_labs
    corr_matrix = df[corr_cols].corr()
    
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})
    ax.set_title('주요 변수 간 상관관계', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
    print("  - 상관관계 매트릭스 저장: correlation_matrix.png")
    
    plt.close('all')

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("예측 모델용 데이터셋 준비")
    print("=" * 80)
    
    # 1. 데이터 로드
    labs_df, admissions_df, patients_df = load_data()
    
    # 2. 사망 구분 추가
    df = add_death_categories(labs_df, patients_df)
    
    # 3. 입원기간 및 인구통계 추가
    df = add_los_and_demographics(df, admissions_df, patients_df)
    
    # 4. 데이터 검증
    df = validate_data(df)
    
    # 5. 통계 생성
    statistics = generate_statistics(df)
    
    # 6. 시각화 생성
    create_visualizations(df)
    
    # 7. 최종 데이터셋 저장
    print("\n최종 데이터셋 저장 중...")
    
    # 불필요한 컬럼 제거
    columns_to_drop = ['deathtime', 'admit_date', 'dod', 'admittime', 'dischtime',
                      'admission_location', 'discharge_location', 'anchor_year',
                      'birth_year', 'admit_year', 'age_at_admission', 'anchor_age', 'age_group_note']
    df_final = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    # CSV 저장
    output_path = DATA_OUTPUT_DIR / 'prediction_dataset.csv'
    df_final.to_csv(output_path, index=False)
    print(f"  - 최종 데이터셋 저장: {output_path}")
    print(f"  - 데이터 크기: {df_final.shape[0]:,} x {df_final.shape[1]:,}")
    
    # 컬럼 정보 출력
    print("\n데이터셋 컬럼 정보:")
    print(f"  - 식별자: hadm_id, subject_id")
    print(f"  - 타겟 변수: death_type, death_binary, hospital_death, los_hours, los_days")
    print(f"  - 인구통계: age, gender, admission_type")
    print(f"  - 혈액검사: {len([col for col in df_final.columns if col not in ['hadm_id', 'subject_id', 'hospital_expire_flag', 'death_type', 'death_binary', 'hospital_death', 'los_hours', 'los_days', 'age', 'gender', 'admission_type']])}개 변수")
    
    print("\n✅ 데이터 준비 완료!")

if __name__ == "__main__":
    main()