import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (12, 8)

print("MIMIC-IV 데이터 종합 분석 시작...")
print("전체 데이터를 읽는 중입니다. 시간이 소요될 수 있습니다...")

print("admissions.csv 읽는 중...")
admissions_df = pd.read_csv('/Users/hyungjun/Desktop/fast campus_lecture/dataset2/core/admissions.csv')
print(f"  - {len(admissions_df):,}개 레코드 로드 완료")

print("patients.csv 읽는 중...")
patients_df = pd.read_csv('/Users/hyungjun/Desktop/fast campus_lecture/dataset2/core/patients.csv')
print(f"  - {len(patients_df):,}개 레코드 로드 완료")

print("transfers.csv 읽는 중...")
transfers_df = pd.read_csv('/Users/hyungjun/Desktop/fast campus_lecture/dataset2/core/transfers.csv')
print(f"  - {len(transfers_df):,}개 레코드 로드 완료")

admissions_df['admittime'] = pd.to_datetime(admissions_df['admittime'])
admissions_df['dischtime'] = pd.to_datetime(admissions_df['dischtime'])
admissions_df['deathtime'] = pd.to_datetime(admissions_df['deathtime'])
admissions_df['edregtime'] = pd.to_datetime(admissions_df['edregtime'])
admissions_df['edouttime'] = pd.to_datetime(admissions_df['edouttime'])

transfers_df['intime'] = pd.to_datetime(transfers_df['intime'])
transfers_df['outtime'] = pd.to_datetime(transfers_df['outtime'])

patients_df['dod'] = pd.to_datetime(patients_df['dod'])

admissions_df['los_days'] = (admissions_df['dischtime'] - admissions_df['admittime']).dt.total_seconds() / 86400

admissions_df['ed_los_hours'] = (admissions_df['edouttime'] - admissions_df['edregtime']).dt.total_seconds() / 3600

results = {}

results['basic_stats'] = {
    'unique_patients_in_admissions': admissions_df['subject_id'].nunique(),
    'unique_patients_in_patients': patients_df['subject_id'].nunique(),
    'unique_patients_in_transfers': transfers_df['subject_id'].nunique(),
    'total_admissions': admissions_df['hadm_id'].nunique(),
    'total_admission_records': len(admissions_df),
    'total_transfers': len(transfers_df),
    'unique_transfer_patients': transfers_df['subject_id'].nunique()
}

results['patient_demographics'] = {
    'gender_distribution': patients_df['gender'].value_counts().to_dict(),
    'age_stats': {
        'mean': patients_df['anchor_age'].mean(),
        'median': patients_df['anchor_age'].median(),
        'std': patients_df['anchor_age'].std(),
        'min': patients_df['anchor_age'].min(),
        'max': patients_df['anchor_age'].max()
    },
    'age_groups': pd.cut(patients_df['anchor_age'], 
                         bins=[0, 18, 40, 60, 80, 100],
                         labels=['Pediatric (0-18)', 'Young Adult (19-40)', 
                                'Middle Age (41-60)', 'Elderly (61-80)', 
                                'Very Elderly (80+)']).value_counts().to_dict()
}

results['admission_patterns'] = {
    'admission_types': admissions_df['admission_type'].value_counts().to_dict(),
    'admission_locations': admissions_df['admission_location'].value_counts().head(10).to_dict(),
    'discharge_locations': admissions_df['discharge_location'].value_counts().head(10).to_dict(),
    'insurance_types': admissions_df['insurance'].value_counts().to_dict(),
    'los_stats': {
        'mean_days': admissions_df['los_days'].mean(),
        'median_days': admissions_df['los_days'].median(),
        'percentile_25': admissions_df['los_days'].quantile(0.25),
        'percentile_75': admissions_df['los_days'].quantile(0.75),
        'percentile_95': admissions_df['los_days'].quantile(0.95)
    }
}

results['mortality_analysis'] = {
    'hospital_mortality_rate': (admissions_df['hospital_expire_flag'].sum() / len(admissions_df)) * 100,
    'hospital_deaths': admissions_df['hospital_expire_flag'].sum(),
    'overall_mortality_rate': (patients_df['dod'].notna().sum() / len(patients_df)) * 100,
    'total_deaths': patients_df['dod'].notna().sum()
}

readmission_df = admissions_df.sort_values(['subject_id', 'admittime'])
readmission_df['prev_dischtime'] = readmission_df.groupby('subject_id')['dischtime'].shift(1)
readmission_df['days_since_discharge'] = (readmission_df['admittime'] - readmission_df['prev_dischtime']).dt.total_seconds() / 86400
readmission_df['readmission_30'] = (readmission_df['days_since_discharge'] <= 30) & (readmission_df['days_since_discharge'] > 0)

results['readmission_stats'] = {
    'patients_with_readmissions': readmission_df[readmission_df['days_since_discharge'] > 0]['subject_id'].nunique(),
    'total_readmissions': (readmission_df['days_since_discharge'] > 0).sum(),
    'readmissions_30_days': readmission_df['readmission_30'].sum(),
    'readmission_rate_30_days': (readmission_df['readmission_30'].sum() / len(readmission_df)) * 100
}

ed_patients = admissions_df[admissions_df['edregtime'].notna()]
results['emergency_stats'] = {
    'ed_admissions': len(ed_patients),
    'ed_admission_rate': (len(ed_patients) / len(admissions_df)) * 100,
    'ed_los_hours_mean': ed_patients['ed_los_hours'].mean(),
    'ed_los_hours_median': ed_patients['ed_los_hours'].median()
}

event_type_counts = transfers_df['eventtype'].value_counts().to_dict()
careunit_counts = transfers_df[transfers_df['careunit'].notna()]['careunit'].value_counts().head(15).to_dict()

icu_units = ['MICU', 'SICU', 'CCU', 'CVICU', 'NICU', 'PICU', 'TSICU']
icu_transfers = transfers_df[transfers_df['careunit'].isin(icu_units)]

results['transfer_patterns'] = {
    'event_types': event_type_counts,
    'top_care_units': careunit_counts,
    'icu_admissions': len(icu_transfers),
    'icu_patients': icu_transfers['subject_id'].nunique() if len(icu_transfers) > 0 else 0
}

results['data_quality'] = {
    'admissions_nulls': {
        col: {'count': admissions_df[col].isnull().sum(), 
              'percentage': (admissions_df[col].isnull().sum() / len(admissions_df)) * 100}
        for col in admissions_df.columns if admissions_df[col].isnull().sum() > 0
    },
    'patients_nulls': {
        col: {'count': patients_df[col].isnull().sum(),
              'percentage': (patients_df[col].isnull().sum() / len(patients_df)) * 100}
        for col in patients_df.columns if patients_df[col].isnull().sum() > 0
    },
    'transfers_nulls': {
        col: {'count': transfers_df[col].isnull().sum(),
              'percentage': (transfers_df[col].isnull().sum() / len(transfers_df)) * 100}
        for col in transfers_df.columns if transfers_df[col].isnull().sum() > 0
    }
}

ethnicity_counts = admissions_df['ethnicity'].value_counts().to_dict()
marital_counts = admissions_df['marital_status'].value_counts().to_dict()
language_counts = admissions_df['language'].value_counts().to_dict()

results['demographic_details'] = {
    'ethnicity_distribution': ethnicity_counts,
    'marital_status_distribution': marital_counts,
    'language_distribution': language_counts
}

admissions_per_patient = admissions_df.groupby('subject_id')['hadm_id'].count()
results['admission_frequency'] = {
    'total_unique_patients': admissions_df['subject_id'].nunique(),
    'single_admission': int((admissions_per_patient == 1).sum()),
    'multiple_admissions': int((admissions_per_patient > 1).sum()),
    'frequent_users_5plus': int((admissions_per_patient >= 5).sum()),
    'max_admissions_per_patient': int(admissions_per_patient.max()),
    'mean_admissions_per_patient': float(admissions_per_patient.mean()),
    'median_admissions_per_patient': float(admissions_per_patient.median())
}

mortality_by_age = patients_df[patients_df['dod'].notna()].groupby(
    pd.cut(patients_df[patients_df['dod'].notna()]['anchor_age'], 
           bins=[0, 18, 40, 60, 80, 100],
           labels=['0-18', '19-40', '41-60', '61-80', '80-100'])
).size()

mortality_by_admission_type = admissions_df.groupby('admission_type')['hospital_expire_flag'].agg(['sum', 'count'])
mortality_by_admission_type['rate'] = (mortality_by_admission_type['sum'] / mortality_by_admission_type['count']) * 100

results['mortality_details'] = {
    'mortality_by_age_group': {str(k): int(v) for k, v in mortality_by_age.to_dict().items()} if len(mortality_by_age) > 0 else {},
    'mortality_by_admission_type': {k: float(v) for k, v in mortality_by_admission_type['rate'].to_dict().items()}
}

import json
with open('/Users/hyungjun/Desktop/fast campus_lecture/analysis_comprehensive/data/mimic_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("분석 완료. 결과가 mimic_analysis_results.json에 저장되었습니다.")
print(f"분석된 고유 환자 수: {results['basic_stats']['unique_patients_in_admissions']:,}")
print(f"분석된 입원 건수: {results['basic_stats']['total_admissions']:,}")
print(f"분석된 이동 기록: {results['basic_stats']['total_transfers']:,}")