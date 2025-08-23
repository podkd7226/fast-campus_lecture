#!/usr/bin/env python3
"""
MIMIC-IV 데이터 샘플링 테스트 스크립트
메모리 최적화 버전
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 설정
RANDOM_STATE = 42
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'

# 샘플 크기
N_IN_HOSPITAL_DEATH = 300
N_POST_HOSPITAL_DEATH = 300
N_SURVIVED = 600

def main():
    print("=" * 80)
    print("📊 MIMIC-IV 데이터 샘플링 (최적화 버전)")
    print("=" * 80)
    
    # 1. 데이터 로드
    print("\n1. 데이터 로딩 중...")
    admissions_path = os.path.join(BASE_PATH, 'dataset2/core/admissions.csv')
    patients_path = os.path.join(BASE_PATH, 'dataset2/core/patients.csv')
    
    # 필요한 컬럼만 로드
    admissions = pd.read_csv(admissions_path, 
                            usecols=['hadm_id', 'subject_id', 'hospital_expire_flag'])
    patients = pd.read_csv(patients_path,
                          usecols=['subject_id', 'anchor_age', 'gender', 'dod'])
    
    print(f"✅ Admissions 로드: {len(admissions):,} 건")
    print(f"✅ Patients 로드: {len(patients):,} 명")
    
    # 2. 데이터 병합
    print("\n2. 데이터 병합 및 전처리...")
    df = admissions.merge(patients[['subject_id', 'anchor_age', 'dod']], 
                         on='subject_id', how='left')
    
    # 0세 제외
    df_filtered = df[df['anchor_age'] > 0].copy()
    print(f"✅ 0세 제외 후: {len(df_filtered):,} 건")
    
    # 3. 데이터 분류
    print("\n3. 데이터 분류 중...")
    
    # 병원 내 사망
    in_hospital_death = df_filtered[df_filtered['hospital_expire_flag'] == 1]
    print(f"• 병원 내 사망: {len(in_hospital_death):,} 건")
    
    # 병원 후 사망
    post_hospital_death = df_filtered[
        (df_filtered['hospital_expire_flag'] == 0) & 
        (df_filtered['dod'].notna())
    ]
    print(f"• 병원 후 사망: {len(post_hospital_death):,} 건")
    
    # 생존
    survived = df_filtered[df_filtered['dod'].isna()]
    print(f"• 생존: {len(survived):,} 건")
    
    # 4. 샘플링
    print("\n4. 샘플링 수행 중...")
    
    # 각 그룹에서 샘플링
    sample_in_hospital = in_hospital_death.sample(
        n=min(N_IN_HOSPITAL_DEATH, len(in_hospital_death)), 
        random_state=RANDOM_STATE
    )
    print(f"✅ 병원 내 사망 샘플: {len(sample_in_hospital)} 건")
    
    sample_post_hospital = post_hospital_death.sample(
        n=min(N_POST_HOSPITAL_DEATH, len(post_hospital_death)), 
        random_state=RANDOM_STATE
    )
    print(f"✅ 병원 후 사망 샘플: {len(sample_post_hospital)} 건")
    
    sample_survived = survived.sample(
        n=min(N_SURVIVED, len(survived)), 
        random_state=RANDOM_STATE
    )
    print(f"✅ 생존 샘플: {len(sample_survived)} 건")
    
    # 전체 샘플 합치기
    sampled_admissions = pd.concat([
        sample_in_hospital,
        sample_post_hospital,
        sample_survived
    ], ignore_index=True)
    
    print(f"\n✅ 총 샘플 수: {len(sampled_admissions):,} 건")
    
    # 5. 샘플된 ID 저장
    print("\n5. 샘플 ID 저장 중...")
    
    # 샘플된 ID들
    sampled_subject_ids = sampled_admissions['subject_id'].unique()
    sampled_hadm_ids = sampled_admissions['hadm_id'].unique()
    
    print(f"• 고유 환자 수: {len(sampled_subject_ids):,} 명")
    print(f"• 고유 입원 수: {len(sampled_hadm_ids):,} 건")
    
    # ID 저장
    output_path = os.path.join(BASE_PATH, 'analysis_samplingmethod/data')
    
    sampled_ids = sampled_admissions[['subject_id', 'hadm_id', 'hospital_expire_flag']].copy()
    sampled_ids['mortality_group'] = sampled_admissions.apply(
        lambda x: 'in_hospital_death' if x['hospital_expire_flag'] == 1
        else 'post_hospital_death' if pd.notna(x['dod'])
        else 'survived', axis=1
    )
    
    sampled_ids.to_csv(os.path.join(output_path, 'sampled_ids.csv'), index=False)
    print(f"✅ sampled_ids.csv 저장")
    
    # 6. 전체 admissions 데이터 다시 로드하여 샘플 추출
    print("\n6. 전체 admission 데이터 추출 중...")
    admissions_full = pd.read_csv(admissions_path)
    sampled_admissions_full = admissions_full[
        admissions_full['hadm_id'].isin(sampled_hadm_ids)
    ]
    
    # 7. Core 테이블 저장
    print("\n7. Core 테이블 저장 중...")
    core_path = os.path.join(BASE_PATH, 'processed_data/core')
    
    # admissions 저장
    sampled_admissions_full.to_csv(
        os.path.join(core_path, 'admissions_sampled.csv'), index=False
    )
    print(f"✅ admissions_sampled.csv 저장 ({len(sampled_admissions_full)} 행)")
    
    # patients 저장
    patients_full = pd.read_csv(patients_path)
    sampled_patients = patients_full[
        patients_full['subject_id'].isin(sampled_subject_ids)
    ]
    sampled_patients.to_csv(
        os.path.join(core_path, 'patients_sampled.csv'), index=False
    )
    print(f"✅ patients_sampled.csv 저장 ({len(sampled_patients)} 행)")
    
    # transfers 저장
    print("\n8. Transfers 테이블 추출 중...")
    transfers_path = os.path.join(BASE_PATH, 'dataset2/core/transfers.csv')
    
    # 청크로 읽어서 필터링 (메모리 절약)
    chunk_size = 100000
    transfers_filtered = []
    
    for chunk in pd.read_csv(transfers_path, chunksize=chunk_size):
        filtered = chunk[chunk['hadm_id'].isin(sampled_hadm_ids)]
        if not filtered.empty:
            transfers_filtered.append(filtered)
    
    if transfers_filtered:
        transfers_sampled = pd.concat(transfers_filtered, ignore_index=True)
        transfers_sampled.to_csv(
            os.path.join(core_path, 'transfers_sampled.csv'), index=False
        )
        print(f"✅ transfers_sampled.csv 저장 ({len(transfers_sampled)} 행)")
    
    # 9. 통계 저장
    print("\n9. 통계 정보 저장 중...")
    stats = {
        'sampling_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'random_state': RANDOM_STATE,
        'total_samples': len(sampled_admissions),
        'in_hospital_death': len(sample_in_hospital),
        'post_hospital_death': len(sample_post_hospital),
        'survived': len(sample_survived),
        'unique_patients': len(sampled_subject_ids),
        'unique_admissions': len(sampled_hadm_ids)
    }
    
    with open(os.path.join(output_path, 'sampling_results.json'), 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ sampling_results.json 저장")
    
    print("\n" + "=" * 80)
    print("✅ 샘플링 완료!")
    print("=" * 80)
    print(f"\n최종 결과:")
    print(f"• 총 샘플: {stats['total_samples']:,} 건")
    print(f"• 병원 내 사망: {stats['in_hospital_death']:,} 건")
    print(f"• 병원 후 사망: {stats['post_hospital_death']:,} 건")
    print(f"• 생존: {stats['survived']:,} 건")

if __name__ == "__main__":
    main()