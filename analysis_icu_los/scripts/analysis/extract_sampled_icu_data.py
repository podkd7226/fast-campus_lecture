#!/usr/bin/env python3
"""
샘플링된 환자들의 ICU 데이터 추출 및 저장
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

def extract_sampled_icu_data():
    """샘플링된 환자들의 ICU 데이터를 추출하고 저장"""
    
    print("=" * 60)
    print("샘플링된 환자 ICU 데이터 추출")
    print("=" * 60)
    
    # 경로 설정
    base_path = Path.cwd()
    
    # 1. 샘플링된 입원 데이터 로드
    print("\n1. 샘플링된 데이터 로딩...")
    admissions = pd.read_csv(base_path / 'processed_data/core/admissions_sampled.csv')
    patients = pd.read_csv(base_path / 'processed_data/core/patients_sampled.csv')
    
    print(f"   - 입원 건수: {len(admissions):,}")
    print(f"   - 환자 수: {len(patients):,}")
    
    # 2. 원본 ICU 데이터에서 샘플링된 환자 추출
    print("\n2. ICU 데이터에서 샘플링된 환자 추출...")
    icustays = pd.read_csv(base_path / 'dataset2/icu/icustays.csv')
    
    # 샘플링된 입원 ID로 필터링
    hadm_ids = admissions['hadm_id'].unique()
    sampled_icu = icustays[icustays['hadm_id'].isin(hadm_ids)].copy()
    
    print(f"   - 전체 ICU 입실: {len(icustays):,}")
    print(f"   - 샘플링된 ICU 입실: {len(sampled_icu):,}")
    print(f"   - ICU 입실한 입원 건수: {sampled_icu['hadm_id'].nunique():,}")
    
    # 3. 추가 정보 병합
    print("\n3. 환자 및 입원 정보 병합...")
    
    # 입원 정보 병합
    sampled_icu = sampled_icu.merge(
        admissions[['hadm_id', 'hospital_expire_flag', 'admission_type', 
                   'admission_location', 'discharge_location']],
        on='hadm_id',
        how='left'
    )
    
    # 환자 정보 병합
    sampled_icu = sampled_icu.merge(
        patients[['subject_id', 'gender', 'anchor_age', 'dod']],
        on='subject_id',
        how='left'
    )
    
    # 사망 분류 추가
    sampled_icu['mortality_group'] = sampled_icu.apply(
        lambda row: 'hospital_death' if row['hospital_expire_flag'] == 1
        else 'post_discharge_death' if pd.notna(row['dod'])
        else 'alive', axis=1
    )
    
    # 4. 데이터 저장
    print("\n4. 데이터 저장...")
    
    # processed_data/icu 폴더 생성
    icu_path = base_path / 'processed_data/icu'
    icu_path.mkdir(exist_ok=True)
    
    # CSV 저장
    output_file = icu_path / 'icustays_sampled.csv'
    sampled_icu.to_csv(output_file, index=False)
    print(f"   - 저장 위치: {output_file}")
    print(f"   - 저장된 레코드: {len(sampled_icu):,}")
    
    # 5. 기본 통계 출력
    print("\n5. ICU 데이터 기본 통계")
    print("-" * 40)
    
    # ICU별 분포
    print("\n[ICU 유닛별 분포]")
    icu_counts = sampled_icu['first_careunit'].value_counts()
    for icu, count in icu_counts.items():
        print(f"   {icu}: {count} ({count/len(sampled_icu)*100:.1f}%)")
    
    # 재원기간 통계
    print("\n[재원기간 통계]")
    print(f"   평균: {sampled_icu['los'].mean():.2f} 일")
    print(f"   중앙값: {sampled_icu['los'].median():.2f} 일")
    print(f"   표준편차: {sampled_icu['los'].std():.2f} 일")
    print(f"   최소: {sampled_icu['los'].min():.2f} 일")
    print(f"   최대: {sampled_icu['los'].max():.2f} 일")
    
    # 사망률
    print("\n[사망률 분석]")
    mortality_counts = sampled_icu['mortality_group'].value_counts()
    for group, count in mortality_counts.items():
        print(f"   {group}: {count} ({count/len(sampled_icu)*100:.1f}%)")
    
    # 6. 요약 정보 JSON 저장
    summary = {
        'total_icu_stays': len(sampled_icu),
        'unique_patients': sampled_icu['subject_id'].nunique(),
        'unique_admissions': sampled_icu['hadm_id'].nunique(),
        'icu_units': sampled_icu['first_careunit'].nunique(),
        'los_stats': {
            'mean': float(sampled_icu['los'].mean()),
            'median': float(sampled_icu['los'].median()),
            'std': float(sampled_icu['los'].std()),
            'min': float(sampled_icu['los'].min()),
            'max': float(sampled_icu['los'].max())
        },
        'mortality': {
            'hospital_death': int(mortality_counts.get('hospital_death', 0)),
            'post_discharge_death': int(mortality_counts.get('post_discharge_death', 0)),
            'alive': int(mortality_counts.get('alive', 0))
        }
    }
    
    # analysis_icu_los/data 폴더에도 요약 저장
    data_path = base_path / 'analysis_icu_los/data'
    data_path.mkdir(exist_ok=True)
    
    with open(data_path / 'extraction_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 60)
    print("데이터 추출 완료!")
    print("=" * 60)
    
    return sampled_icu

if __name__ == "__main__":
    extract_sampled_icu_data()