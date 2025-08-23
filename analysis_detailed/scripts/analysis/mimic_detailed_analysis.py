import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

print("="*80)
print("MIMIC-IV 데이터셋 상세 분석 보고서")
print("="*80)

admissions_df = pd.read_csv('dataset2/core/admissions.csv', nrows=10000)
patients_df = pd.read_csv('dataset2/core/patients.csv', nrows=10000)
transfers_df = pd.read_csv('dataset2/core/transfers.csv', nrows=10000)

print("\n## 1. 데이터셋 개요")
print("-" * 60)

print("\n### admissions.csv (입원 정보)")
print("- 환자의 병원 입원 정보를 담고 있는 테이블")
print("- 주요 필드:")
print("  * subject_id: 환자 고유 ID")
print("  * hadm_id: 입원 고유 ID (한 환자가 여러 번 입원 가능)")
print("  * admittime/dischtime: 입원/퇴원 시간")
print("  * deathtime: 사망 시간 (사망한 경우)")
print("  * admission_type: 입원 유형 (응급, 예약 등)")
print("  * admission_location: 입원 경로 (응급실, 외래 등)")
print("  * discharge_location: 퇴원 장소 (집, 재활시설 등)")
print("  * hospital_expire_flag: 병원 내 사망 여부 (0=생존, 1=사망)")

print("\n### patients.csv (환자 기본 정보)")
print("- 환자의 인구통계학적 기본 정보")
print("- 주요 필드:")
print("  * subject_id: 환자 고유 ID")
print("  * gender: 성별 (M/F)")
print("  * anchor_age: 기준 시점의 나이")
print("  * anchor_year: 기준 연도")
print("  * dod: 사망일 (Date of Death)")

print("\n### transfers.csv (병동 이동 정보)")
print("- 환자의 병원 내 이동 기록")
print("- 주요 필드:")
print("  * subject_id: 환자 고유 ID")
print("  * hadm_id: 입원 고유 ID")
print("  * transfer_id: 이동 고유 ID")
print("  * eventtype: 이벤트 유형 (입원, 전동, 퇴원)")
print("  * careunit: 진료 부서 (ICU, 일반병동 등)")
print("  * intime/outtime: 입실/퇴실 시간")

print("\n## 2. 주요 통계")
print("-" * 60)

print(f"\n### 환자 수")
unique_patients_admissions = admissions_df['subject_id'].nunique()
unique_patients_patients = patients_df['subject_id'].nunique()
unique_patients_transfers = transfers_df['subject_id'].nunique()
print(f"- admissions 테이블의 고유 환자 수: {unique_patients_admissions:,}명")
print(f"- patients 테이블의 고유 환자 수: {unique_patients_patients:,}명")
print(f"- transfers 테이블의 고유 환자 수: {unique_patients_transfers:,}명")

print(f"\n### 입원 통계")
unique_admissions = admissions_df['hadm_id'].nunique()
avg_admissions_per_patient = admissions_df.groupby('subject_id')['hadm_id'].count().mean()
print(f"- 총 입원 건수: {unique_admissions:,}건")
print(f"- 환자당 평균 입원 횟수: {avg_admissions_per_patient:.2f}회")

print(f"\n### 사망률")
hospital_deaths = admissions_df['hospital_expire_flag'].sum()
total_admissions = len(admissions_df)
mortality_rate = (hospital_deaths / total_admissions) * 100
print(f"- 병원 내 사망 건수: {hospital_deaths}건")
print(f"- 병원 내 사망률: {mortality_rate:.2f}%")

patients_with_dod = patients_df['dod'].notna().sum()
total_patients = len(patients_df)
overall_mortality = (patients_with_dod / total_patients) * 100
print(f"- 전체 사망 환자 수: {patients_with_dod}명")
print(f"- 전체 사망률: {overall_mortality:.2f}%")

print(f"\n### 입원 유형 분포")
admission_types = admissions_df['admission_type'].value_counts()
for atype, count in admission_types.head(5).items():
    percentage = (count / total_admissions) * 100
    print(f"- {atype}: {count}건 ({percentage:.1f}%)")

print(f"\n### 입원 경로 분포")
admission_locations = admissions_df['admission_location'].value_counts()
for loc, count in admission_locations.head(5).items():
    percentage = (count / admissions_df['admission_location'].notna().sum()) * 100
    print(f"- {loc}: {count}건 ({percentage:.1f}%)")

print(f"\n### 보험 유형 분포")
insurance_types = admissions_df['insurance'].value_counts()
for ins, count in insurance_types.items():
    percentage = (count / total_admissions) * 100
    print(f"- {ins}: {count}건 ({percentage:.1f}%)")

print(f"\n### 성별 분포")
gender_dist = patients_df['gender'].value_counts()
for gender, count in gender_dist.items():
    percentage = (count / total_patients) * 100
    print(f"- {gender}: {count}명 ({percentage:.1f}%)")

print(f"\n### 나이 통계")
age_stats = patients_df['anchor_age'].describe()
print(f"- 평균 나이: {age_stats['mean']:.1f}세")
print(f"- 중앙값: {age_stats['50%']:.1f}세")
print(f"- 최소/최대: {age_stats['min']:.0f}세 / {age_stats['max']:.0f}세")

age_groups = pd.cut(patients_df['anchor_age'], 
                    bins=[0, 18, 40, 60, 80, 100],
                    labels=['0-18', '19-40', '41-60', '61-80', '80+'])
print("\n나이 그룹별 분포:")
for group, count in age_groups.value_counts().sort_index().items():
    percentage = (count / total_patients) * 100
    print(f"- {group}세: {count}명 ({percentage:.1f}%)")

print(f"\n### 병동 이동 통계")
event_types = transfers_df['eventtype'].value_counts()
print("이벤트 유형별 분포:")
for event, count in event_types.items():
    percentage = (count / len(transfers_df)) * 100
    print(f"- {event}: {count}건 ({percentage:.1f}%)")

careunit_dist = transfers_df['careunit'].value_counts()
if not careunit_dist.empty:
    print("\n진료 부서별 분포 (상위 5개):")
    for unit, count in careunit_dist.head(5).items():
        percentage = (count / transfers_df['careunit'].notna().sum()) * 100
        print(f"- {unit}: {count}건 ({percentage:.1f}%)")

print("\n## 3. 데이터 품질 분석")
print("-" * 60)

print("\n### 결측값 현황")
print("\nadmissions 테이블:")
for col in ['deathtime', 'admission_location', 'discharge_location', 'marital_status', 'edregtime', 'edouttime']:
    if col in admissions_df.columns:
        null_count = admissions_df[col].isnull().sum()
        null_percent = (null_count / len(admissions_df)) * 100
        if null_percent > 0:
            print(f"- {col}: {null_count}개 ({null_percent:.1f}%)")

print("\npatients 테이블:")
null_dod = patients_df['dod'].isnull().sum()
print(f"- dod: {null_dod}개 ({(null_dod/len(patients_df))*100:.1f}%)")

print("\ntransfers 테이블:")
for col in ['hadm_id', 'careunit', 'outtime']:
    if col in transfers_df.columns:
        null_count = transfers_df[col].isnull().sum()
        null_percent = (null_count / len(transfers_df)) * 100
        if null_percent > 0:
            print(f"- {col}: {null_count}개 ({null_percent:.1f}%)")

print("\n## 4. 데이터 관계 및 활용 방안")
print("-" * 60)

print("\n### 데이터 연결 구조")
print("- subject_id를 통해 모든 테이블 연결 가능")
print("- hadm_id를 통해 입원 관련 정보 연결")
print("- 시간 정보를 통해 환자 journey 추적 가능")

print("\n### 주요 활용 사례")
print("1. **재입원 예측**: 입원 패턴 분석을 통한 재입원 위험도 평가")
print("2. **사망률 예측**: 환자 특성과 입원 정보를 활용한 예후 예측")
print("3. **병동 최적화**: 병동 이동 패턴 분석을 통한 자원 배분")
print("4. **체류 기간 예측**: 입원 유형과 환자 특성별 재원일수 예측")
print("5. **응급실 분석**: 응급실 경유 입원과 직접 입원 비교 분석")

print("\n" + "="*80)
print("분석 완료")
print("="*80)