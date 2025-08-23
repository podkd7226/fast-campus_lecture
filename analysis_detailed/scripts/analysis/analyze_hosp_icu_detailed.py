import pandas as pd
import numpy as np
import json

print("MIMIC-IV hosp/icu 테이블 상세 분석...")
print("=" * 80)

# 주요 테이블만 선택하여 상세 분석
analyses = {}

# 1. 진단 정보 분석 (diagnoses_icd)
print("\n1. 진단 정보 분석 (diagnoses_icd)")
print("-" * 40)
diagnoses_df = pd.read_csv('dataset2/hosp/diagnoses_icd.csv', nrows=10000)
analyses['diagnoses'] = {
    'total_diagnoses': len(diagnoses_df),
    'unique_patients': diagnoses_df['subject_id'].nunique(),
    'unique_admissions': diagnoses_df['hadm_id'].nunique(),
    'unique_icd_codes': diagnoses_df['icd_code'].nunique() if 'icd_code' in diagnoses_df.columns else 0,
    'avg_diagnoses_per_admission': len(diagnoses_df) / diagnoses_df['hadm_id'].nunique() if 'hadm_id' in diagnoses_df.columns else 0,
    'top_diagnoses': diagnoses_df['icd_code'].value_counts().head(10).to_dict() if 'icd_code' in diagnoses_df.columns else {}
}
print(f"- 총 진단 기록: {analyses['diagnoses']['total_diagnoses']:,}개")
print(f"- 고유 환자: {analyses['diagnoses']['unique_patients']:,}명")
print(f"- 고유 입원: {analyses['diagnoses']['unique_admissions']:,}건")
print(f"- 입원당 평균 진단: {analyses['diagnoses']['avg_diagnoses_per_admission']:.1f}개")

# 2. 검사 결과 분석 (labevents)
print("\n2. 검사 결과 분석 (labevents)")
print("-" * 40)
labevents_df = pd.read_csv('dataset2/hosp/labevents.csv', nrows=10000)
analyses['labevents'] = {
    'total_lab_tests': len(labevents_df),
    'unique_patients': labevents_df['subject_id'].nunique(),
    'unique_lab_items': labevents_df['itemid'].nunique() if 'itemid' in labevents_df.columns else 0,
    'null_values_percentage': (labevents_df['value'].isnull().sum() / len(labevents_df) * 100) if 'value' in labevents_df.columns else 0,
    'abnormal_flags': labevents_df['flag'].value_counts().to_dict() if 'flag' in labevents_df.columns else {}
}
print(f"- 총 검사 기록: {analyses['labevents']['total_lab_tests']:,}개")
print(f"- 고유 환자: {analyses['labevents']['unique_patients']:,}명")
print(f"- 검사 항목 종류: {analyses['labevents']['unique_lab_items']:,}개")
print(f"- 결측값 비율: {analyses['labevents']['null_values_percentage']:.1f}%")

# 3. 처방 정보 분석 (prescriptions)
print("\n3. 처방 정보 분석 (prescriptions)")
print("-" * 40)
prescriptions_df = pd.read_csv('dataset2/hosp/prescriptions.csv', nrows=10000)
analyses['prescriptions'] = {
    'total_prescriptions': len(prescriptions_df),
    'unique_patients': prescriptions_df['subject_id'].nunique(),
    'unique_drugs': prescriptions_df['drug'].nunique() if 'drug' in prescriptions_df.columns else 0,
    'unique_routes': prescriptions_df['route'].nunique() if 'route' in prescriptions_df.columns else 0,
    'top_drugs': prescriptions_df['drug'].value_counts().head(10).to_dict() if 'drug' in prescriptions_df.columns else {},
    'top_routes': prescriptions_df['route'].value_counts().head(5).to_dict() if 'route' in prescriptions_df.columns else {}
}
print(f"- 총 처방 기록: {analyses['prescriptions']['total_prescriptions']:,}개")
print(f"- 고유 환자: {analyses['prescriptions']['unique_patients']:,}명")
print(f"- 약물 종류: {analyses['prescriptions']['unique_drugs']:,}개")
print(f"- 투여 경로 종류: {analyses['prescriptions']['unique_routes']:,}개")

# 4. ICU 입실 정보 분석 (icustays)
print("\n4. ICU 입실 정보 분석 (icustays)")
print("-" * 40)
icustays_df = pd.read_csv('dataset2/icu/icustays.csv', nrows=10000)
icustays_df['intime'] = pd.to_datetime(icustays_df['intime'])
icustays_df['outtime'] = pd.to_datetime(icustays_df['outtime'])
icustays_df['los_hours'] = (icustays_df['outtime'] - icustays_df['intime']).dt.total_seconds() / 3600

analyses['icustays'] = {
    'total_icu_stays': len(icustays_df),
    'unique_patients': icustays_df['subject_id'].nunique(),
    'unique_admissions': icustays_df['hadm_id'].nunique(),
    'avg_los_hours': icustays_df['los_hours'].mean(),
    'median_los_hours': icustays_df['los_hours'].median(),
    'first_careunit_distribution': icustays_df['first_careunit'].value_counts().to_dict() if 'first_careunit' in icustays_df.columns else {},
    'last_careunit_distribution': icustays_df['last_careunit'].value_counts().to_dict() if 'last_careunit' in icustays_df.columns else {}
}
print(f"- 총 ICU 입실: {analyses['icustays']['total_icu_stays']:,}건")
print(f"- 고유 환자: {analyses['icustays']['unique_patients']:,}명")
print(f"- 평균 ICU 체류시간: {analyses['icustays']['avg_los_hours']:.1f}시간")
print(f"- 중앙값 ICU 체류시간: {analyses['icustays']['median_los_hours']:.1f}시간")

# 5. 활력징후 기록 분석 (chartevents - 샘플)
print("\n5. 활력징후 기록 분석 (chartevents)")
print("-" * 40)
chartevents_df = pd.read_csv('dataset2/icu/chartevents.csv', nrows=10000)
analyses['chartevents'] = {
    'total_chart_records': len(chartevents_df),
    'unique_patients': chartevents_df['subject_id'].nunique(),
    'unique_items': chartevents_df['itemid'].nunique() if 'itemid' in chartevents_df.columns else 0,
    'unique_admissions': chartevents_df['hadm_id'].nunique() if 'hadm_id' in chartevents_df.columns else 0,
    'value_types': chartevents_df['valueuom'].value_counts().head(10).to_dict() if 'valueuom' in chartevents_df.columns else {}
}
print(f"- 총 차트 기록: {analyses['chartevents']['total_chart_records']:,}개")
print(f"- 고유 환자: {analyses['chartevents']['unique_patients']:,}명")
print(f"- 측정 항목 종류: {analyses['chartevents']['unique_items']:,}개")

# 6. 미생물 검사 분석 (microbiologyevents)
print("\n6. 미생물 검사 분석 (microbiologyevents)")
print("-" * 40)
micro_df = pd.read_csv('dataset2/hosp/microbiologyevents.csv', nrows=10000)
analyses['microbiology'] = {
    'total_tests': len(micro_df),
    'unique_patients': micro_df['subject_id'].nunique(),
    'unique_specimens': micro_df['spec_type_desc'].nunique() if 'spec_type_desc' in micro_df.columns else 0,
    'unique_organisms': micro_df['org_name'].nunique() if 'org_name' in micro_df.columns else 0,
    'top_specimens': micro_df['spec_type_desc'].value_counts().head(5).to_dict() if 'spec_type_desc' in micro_df.columns else {},
    'top_organisms': micro_df['org_name'].value_counts().head(10).to_dict() if 'org_name' in micro_df.columns else {}
}
print(f"- 총 미생물 검사: {analyses['microbiology']['total_tests']:,}건")
print(f"- 고유 환자: {analyses['microbiology']['unique_patients']:,}명")
print(f"- 검체 종류: {analyses['microbiology']['unique_specimens']:,}개")
print(f"- 균주 종류: {analyses['microbiology']['unique_organisms']:,}개")

# 7. 시술 정보 분석 (procedures_icd)
print("\n7. 시술 정보 분석 (procedures_icd)")
print("-" * 40)
procedures_df = pd.read_csv('dataset2/hosp/procedures_icd.csv', nrows=10000)
analyses['procedures'] = {
    'total_procedures': len(procedures_df),
    'unique_patients': procedures_df['subject_id'].nunique(),
    'unique_admissions': procedures_df['hadm_id'].nunique(),
    'unique_procedure_codes': procedures_df['icd_code'].nunique() if 'icd_code' in procedures_df.columns else 0,
    'avg_procedures_per_admission': len(procedures_df) / procedures_df['hadm_id'].nunique() if 'hadm_id' in procedures_df.columns else 0,
    'top_procedures': procedures_df['icd_code'].value_counts().head(10).to_dict() if 'icd_code' in procedures_df.columns else {}
}
print(f"- 총 시술 기록: {analyses['procedures']['total_procedures']:,}개")
print(f"- 고유 환자: {analyses['procedures']['unique_patients']:,}명")
print(f"- 고유 입원: {analyses['procedures']['unique_admissions']:,}건")
print(f"- 입원당 평균 시술: {analyses['procedures']['avg_procedures_per_admission']:.1f}개")

# 8. 약물 투여 기록 분석 (inputevents)
print("\n8. 약물/수액 투여 기록 분석 (inputevents)")
print("-" * 40)
inputevents_df = pd.read_csv('dataset2/icu/inputevents.csv', nrows=10000)
analyses['inputevents'] = {
    'total_inputs': len(inputevents_df),
    'unique_patients': inputevents_df['subject_id'].nunique(),
    'unique_items': inputevents_df['itemid'].nunique() if 'itemid' in inputevents_df.columns else 0,
    'unique_admissions': inputevents_df['hadm_id'].nunique() if 'hadm_id' in inputevents_df.columns else 0,
    'order_category': inputevents_df['ordercategoryname'].value_counts().to_dict() if 'ordercategoryname' in inputevents_df.columns else {}
}
print(f"- 총 투여 기록: {analyses['inputevents']['total_inputs']:,}개")
print(f"- 고유 환자: {analyses['inputevents']['unique_patients']:,}명")
print(f"- 투여 항목 종류: {analyses['inputevents']['unique_items']:,}개")

# 9. 배출량 기록 분석 (outputevents)
print("\n9. 배출량 기록 분석 (outputevents)")
print("-" * 40)
outputevents_df = pd.read_csv('dataset2/icu/outputevents.csv', nrows=10000)
analyses['outputevents'] = {
    'total_outputs': len(outputevents_df),
    'unique_patients': outputevents_df['subject_id'].nunique(),
    'unique_items': outputevents_df['itemid'].nunique() if 'itemid' in outputevents_df.columns else 0,
    'unique_admissions': outputevents_df['hadm_id'].nunique() if 'hadm_id' in outputevents_df.columns else 0
}
print(f"- 총 배출 기록: {analyses['outputevents']['total_outputs']:,}개")
print(f"- 고유 환자: {analyses['outputevents']['unique_patients']:,}명")
print(f"- 배출 항목 종류: {analyses['outputevents']['unique_items']:,}개")

# 결과 저장
with open('hosp_icu_detailed_analysis.json', 'w') as f:
    json.dump(analyses, f, indent=2, default=str)

print("\n" + "=" * 80)
print("상세 분석 완료! 결과가 hosp_icu_detailed_analysis.json에 저장되었습니다.")