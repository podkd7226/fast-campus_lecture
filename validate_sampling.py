import pandas as pd
import numpy as np
import json
from datetime import datetime

print("=" * 80)
print("MIMIC 데이터 샘플링 검증 분석")
print("=" * 80)

# 결과 저장용 딕셔너리
validation_results = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'data_sizes': {},
    'sample_vs_full': {},
    'sampling_bias': {},
    'key_metrics_comparison': {}
}

# 1. 데이터 크기 확인
print("\n1. 데이터 크기 확인")
print("-" * 40)

files = {
    'admissions': 'dataset2/core/admissions.csv',
    'patients': 'dataset2/core/patients.csv', 
    'transfers': 'dataset2/core/transfers.csv'
}

for name, filepath in files.items():
    # 전체 행 수 계산 (메모리 효율적)
    with open(filepath, 'r') as f:
        total_rows = sum(1 for line in f) - 1  # 헤더 제외
    
    validation_results['data_sizes'][name] = {
        'total_rows': total_rows,
        'sample_rows': 50000,
        'sample_percentage': (50000 / total_rows * 100)
    }
    
    print(f"{name}:")
    print(f"  - 전체 데이터: {total_rows:,}행")
    print(f"  - 샘플 데이터: 50,000행")
    print(f"  - 샘플 비율: {50000/total_rows*100:.1f}%")

# 2. Admissions 테이블 상세 비교 (가장 중요)
print("\n2. Admissions 테이블 상세 분석")
print("-" * 40)

# 샘플 데이터 (처음 50,000행)
print("샘플 데이터 로딩 중...")
sample_df = pd.read_csv('dataset2/core/admissions.csv', nrows=50000)
sample_df['admittime'] = pd.to_datetime(sample_df['admittime'])
sample_df['dischtime'] = pd.to_datetime(sample_df['dischtime'])

# 전체 데이터 통계를 위한 청크 단위 분석
print("전체 데이터 분석 중 (청크 단위)...")
chunk_size = 50000
chunks_stats = []

for chunk in pd.read_csv('dataset2/core/admissions.csv', chunksize=chunk_size):
    stats = {
        'rows': len(chunk),
        'unique_patients': chunk['subject_id'].nunique(),
        'unique_admissions': chunk['hadm_id'].nunique(),
        'deaths': chunk['hospital_expire_flag'].sum(),
        'emergency_admissions': (chunk['admission_type'].str.contains('EMER', case=False, na=False)).sum()
    }
    chunks_stats.append(stats)

# 전체 통계 집계
total_stats = {
    'total_rows': sum(c['rows'] for c in chunks_stats),
    'total_deaths': sum(c['deaths'] for c in chunks_stats),
    'total_emergency': sum(c['emergency_admissions'] for c in chunks_stats)
}

# 고유 환자 수 계산 (전체)
print("전체 고유 환자 수 계산 중...")
all_patients = set()
for chunk in pd.read_csv('dataset2/core/admissions.csv', chunksize=chunk_size, usecols=['subject_id']):
    all_patients.update(chunk['subject_id'].unique())
total_unique_patients = len(all_patients)

# 비교 결과
sample_stats = {
    'unique_patients': sample_df['subject_id'].nunique(),
    'unique_admissions': sample_df['hadm_id'].nunique(),
    'mortality_rate': (sample_df['hospital_expire_flag'].sum() / len(sample_df)) * 100,
    'emergency_rate': (sample_df['admission_type'].str.contains('EMER', case=False, na=False).sum() / len(sample_df)) * 100
}

full_stats = {
    'unique_patients': total_unique_patients,
    'total_admissions': total_stats['total_rows'],
    'mortality_rate': (total_stats['total_deaths'] / total_stats['total_rows']) * 100,
    'emergency_rate': (total_stats['total_emergency'] / total_stats['total_rows']) * 100
}

validation_results['sample_vs_full']['admissions'] = {
    'sample': sample_stats,
    'full': full_stats,
    'differences': {
        'mortality_rate_diff': abs(sample_stats['mortality_rate'] - full_stats['mortality_rate']),
        'emergency_rate_diff': abs(sample_stats['emergency_rate'] - full_stats['emergency_rate'])
    }
}

print(f"\n샘플 데이터 (처음 50,000행):")
print(f"  - 고유 환자: {sample_stats['unique_patients']:,}명")
print(f"  - 고유 입원: {sample_stats['unique_admissions']:,}건")
print(f"  - 사망률: {sample_stats['mortality_rate']:.2f}%")
print(f"  - 응급 입원율: {sample_stats['emergency_rate']:.2f}%")

print(f"\n전체 데이터:")
print(f"  - 고유 환자: {full_stats['unique_patients']:,}명")
print(f"  - 총 입원: {full_stats['total_admissions']:,}건")
print(f"  - 사망률: {full_stats['mortality_rate']:.2f}%")
print(f"  - 응급 입원율: {full_stats['emergency_rate']:.2f}%")

print(f"\n차이:")
print(f"  - 사망률 차이: {validation_results['sample_vs_full']['admissions']['differences']['mortality_rate_diff']:.2f}%p")
print(f"  - 응급 입원율 차이: {validation_results['sample_vs_full']['admissions']['differences']['emergency_rate_diff']:.2f}%p")

# 3. 시간적 편향 검증
print("\n3. 시간적 편향 검증")
print("-" * 40)

# 샘플의 시간 범위
sample_time_range = {
    'earliest': sample_df['admittime'].min(),
    'latest': sample_df['admittime'].max(),
    'span_days': (sample_df['admittime'].max() - sample_df['admittime'].min()).days
}

# 전체 데이터의 시간 범위 (마지막 청크 확인)
last_chunk = pd.read_csv('dataset2/core/admissions.csv', 
                         skiprows=range(1, 500000),  # 마지막 부분만 읽기
                         usecols=['admittime'])
last_chunk['admittime'] = pd.to_datetime(last_chunk['admittime'])

print(f"샘플 데이터 시간 범위:")
print(f"  - 시작: {sample_time_range['earliest']}")
print(f"  - 종료: {sample_time_range['latest']}")
print(f"  - 기간: {sample_time_range['span_days']:,}일")

print(f"\n전체 데이터 예상 범위:")
print(f"  - 샘플은 처음 50,000행만 포함")
print(f"  - 마지막 부분 최대 시간: {last_chunk['admittime'].max()}")

validation_results['sampling_bias']['temporal'] = {
    'sample_start': str(sample_time_range['earliest']),
    'sample_end': str(sample_time_range['latest']),
    'sample_span_days': sample_time_range['span_days'],
    'bias_type': 'sequential_first_n_rows'
}

# 4. 무작위 샘플링 vs 순차 샘플링 비교
print("\n4. 샘플링 방법 비교 제안")
print("-" * 40)

print("현재 방법: 순차적 샘플링 (처음 50,000행)")
print("  장점: 빠른 로딩, 메모리 효율적")
print("  단점: 시간적 편향, 대표성 부족")

print("\n권장 방법: 무작위 샘플링")
print("  장점: 전체 데이터 대표성")
print("  단점: 느린 로딩, 재현성 위해 시드 필요")

validation_results['recommendations'] = {
    'current_method': 'sequential_first_n',
    'recommended_method': 'random_sampling',
    'alternative_method': 'stratified_sampling_by_year'
}

# 5. 주요 발견사항
print("\n5. 주요 발견사항")
print("-" * 40)

findings = []

# 샘플 크기 평가
if validation_results['data_sizes']['admissions']['sample_percentage'] < 10:
    findings.append(f"⚠️ Admissions 샘플이 전체의 {validation_results['data_sizes']['admissions']['sample_percentage']:.1f}%에 불과")

# 사망률 차이 평가
mort_diff = validation_results['sample_vs_full']['admissions']['differences']['mortality_rate_diff']
if mort_diff > 0.5:
    findings.append(f"⚠️ 사망률 통계에 {mort_diff:.2f}%p 차이 존재")

# 시간적 편향
findings.append("⚠️ 순차적 샘플링으로 인한 시간적 편향 존재")

for i, finding in enumerate(findings, 1):
    print(f"{i}. {finding}")

validation_results['findings'] = findings

# 결과 저장
with open('sampling_validation_results.json', 'w') as f:
    json.dump(validation_results, f, indent=2, default=str)

print("\n" + "=" * 80)
print("검증 완료! 결과가 sampling_validation_results.json에 저장되었습니다.")
print("=" * 80)

# 6. 개선 권장사항
print("\n6. 개선 권장사항")
print("-" * 40)
print("1. 전체 데이터 분석 시도 (메모리 충분 시)")
print("2. 무작위 샘플링 구현")
print("3. 연도별 계층적 샘플링")
print("4. 분석 보고서에 샘플링 한계점 명시")
print("5. 신뢰구간 계산 추가")