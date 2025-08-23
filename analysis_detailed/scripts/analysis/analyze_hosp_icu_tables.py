import pandas as pd
import numpy as np
import json
from datetime import datetime

def analyze_table(filepath, tablename, nrows=10000):
    """각 테이블의 기본 정보와 통계를 분석"""
    try:
        # 데이터 로드
        df = pd.read_csv(filepath, nrows=nrows)
        
        result = {
            'table_name': tablename,
            'sample_rows': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'null_percentages': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            'unique_counts': {col: df[col].nunique() for col in df.columns},
            'sample_data': df.head(3).to_dict('records')
        }
        
        # 숫자형 컬럼 통계
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            result['numeric_stats'] = df[numeric_cols].describe().to_dict()
        
        # 카테고리형 컬럼 빈도
        categorical_cols = df.select_dtypes(include=['object']).columns[:5]  # 상위 5개만
        result['categorical_frequency'] = {}
        for col in categorical_cols:
            top_values = df[col].value_counts().head(5).to_dict()
            result['categorical_frequency'][col] = top_values
            
        return result
    except Exception as e:
        return {'table_name': tablename, 'error': str(e)}

print("MIMIC-IV hosp 및 icu 테이블 분석 시작...")
print("=" * 80)

# 분석할 테이블 목록
hosp_tables = {
    'd_hcpcs': 'dataset2/hosp/d_hcpcs.csv',
    'd_icd_diagnoses': 'dataset2/hosp/d_icd_diagnoses.csv', 
    'd_icd_procedures': 'dataset2/hosp/d_icd_procedures.csv',
    'd_labitems': 'dataset2/hosp/d_labitems.csv',
    'diagnoses_icd': 'dataset2/hosp/diagnoses_icd.csv',
    'drgcodes': 'dataset2/hosp/drgcodes.csv',
    'emar': 'dataset2/hosp/emar.csv',
    'emar_detail': 'dataset2/hosp/emar_detail.csv',
    'hcpcsevents': 'dataset2/hosp/hcpcsevents.csv',
    'labevents': 'dataset2/hosp/labevents.csv',
    'microbiologyevents': 'dataset2/hosp/microbiologyevents.csv',
    'pharmacy': 'dataset2/hosp/pharmacy.csv',
    'poe': 'dataset2/hosp/poe.csv',
    'poe_detail': 'dataset2/hosp/poe_detail.csv',
    'prescriptions': 'dataset2/hosp/prescriptions.csv',
    'procedures_icd': 'dataset2/hosp/procedures_icd.csv',
    'services': 'dataset2/hosp/services.csv'
}

icu_tables = {
    'chartevents': 'dataset2/icu/chartevents.csv',
    'd_items': 'dataset2/icu/d_items.csv',
    'datetimeevents': 'dataset2/icu/datetimeevents.csv',
    'icustays': 'dataset2/icu/icustays.csv',
    'inputevents': 'dataset2/icu/inputevents.csv',
    'outputevents': 'dataset2/icu/outputevents.csv',
    'procedureevents': 'dataset2/icu/procedureevents.csv'
}

# 분석 결과 저장
results = {
    'hosp_tables': {},
    'icu_tables': {},
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

# hosp 테이블 분석
print("\n[HOSP 테이블 분석]")
print("-" * 40)
for table_name, filepath in hosp_tables.items():
    print(f"분석 중: {table_name}...")
    results['hosp_tables'][table_name] = analyze_table(filepath, table_name)

# icu 테이블 분석
print("\n[ICU 테이블 분석]")
print("-" * 40)
for table_name, filepath in icu_tables.items():
    print(f"분석 중: {table_name}...")
    results['icu_tables'][table_name] = analyze_table(filepath, table_name)

# 결과 저장
with open('hosp_icu_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n" + "=" * 80)
print("분석 완료! 결과가 hosp_icu_analysis_results.json에 저장되었습니다.")

# 요약 출력
print("\n[분석 요약]")
print(f"- HOSP 테이블 수: {len(hosp_tables)}개")
print(f"- ICU 테이블 수: {len(icu_tables)}개")
print(f"- 총 분석 테이블: {len(hosp_tables) + len(icu_tables)}개")