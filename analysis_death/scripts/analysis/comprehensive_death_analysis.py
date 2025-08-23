#!/usr/bin/env python3
"""
MIMIC-IV 사망 데이터 종합 분석
모든 테이블에서 사망 관련 필드를 찾고 일치성을 검증합니다.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import platform
from pathlib import Path
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
OUTPUT_DIR = BASE_DIR / 'analysis_death'
FIGURES_DIR = OUTPUT_DIR / 'figures'
DATA_OUTPUT_DIR = OUTPUT_DIR / 'data'

# 디렉토리 생성
FIGURES_DIR.mkdir(exist_ok=True)
DATA_OUTPUT_DIR.mkdir(exist_ok=True)

def analyze_death_fields():
    """모든 테이블에서 사망 관련 필드를 찾고 분석"""
    
    print("=" * 80)
    print("MIMIC-IV 사망 데이터 종합 분석")
    print("=" * 80)
    
    results = {}
    
    # 1. Core 테이블 분석
    print("\n1. CORE 테이블 사망 필드 분석")
    print("-" * 40)
    
    # patients 테이블
    patients = pd.read_csv(DATA_DIR / 'core' / 'patients.csv')
    print(f"\n[patients.csv] - 총 {len(patients):,}명")
    print(f"  - dod (Date of Death) 필드 존재")
    print(f"  - 사망자: {patients['dod'].notna().sum():,}명 ({patients['dod'].notna().sum()/len(patients)*100:.2f}%)")
    
    results['patients'] = {
        'total_records': len(patients),
        'death_field': 'dod',
        'deaths': int(patients['dod'].notna().sum()),
        'death_rate': float(patients['dod'].notna().sum()/len(patients)*100)
    }
    
    # admissions 테이블
    admissions = pd.read_csv(DATA_DIR / 'core' / 'admissions.csv')
    print(f"\n[admissions.csv] - 총 {len(admissions):,}건")
    print(f"  - deathtime 필드 존재")
    print(f"  - hospital_expire_flag 필드 존재")
    print(f"  - deathtime 있음: {admissions['deathtime'].notna().sum():,}건")
    print(f"  - hospital_expire_flag=1: {(admissions['hospital_expire_flag']==1).sum():,}건")
    
    results['admissions'] = {
        'total_records': len(admissions),
        'death_fields': ['deathtime', 'hospital_expire_flag'],
        'deathtime_count': int(admissions['deathtime'].notna().sum()),
        'hospital_expire_flag_count': int((admissions['hospital_expire_flag']==1).sum())
    }
    
    # 2. ICU 테이블 분석
    print("\n2. ICU 테이블 사망 필드 분석")
    print("-" * 40)
    
    # icustays 테이블 확인
    icustays_path = DATA_DIR / 'icu' / 'icustays.csv'
    if icustays_path.exists():
        print("\n[icustays.csv] 컬럼 확인 중...")
        icustays_sample = pd.read_csv(icustays_path, nrows=5)
        death_related_cols = [col for col in icustays_sample.columns 
                             if 'death' in col.lower() or 'expire' in col.lower() or 'dod' in col.lower()]
        
        if death_related_cols:
            print(f"  - 사망 관련 필드 발견: {death_related_cols}")
            icustays = pd.read_csv(icustays_path)
            results['icustays'] = {
                'total_records': len(icustays),
                'death_fields': death_related_cols
            }
        else:
            print("  - 사망 관련 필드 없음")
            results['icustays'] = {
                'total_records': pd.read_csv(icustays_path).shape[0],
                'death_fields': []
            }
    
    # 3. HOSP 테이블 분석
    print("\n3. HOSP 테이블 사망 필드 분석")
    print("-" * 40)
    
    # 주요 hosp 테이블들 확인
    hosp_tables = ['diagnoses_icd.csv', 'procedures_icd.csv', 'd_icd_diagnoses.csv', 'd_icd_procedures.csv']
    
    for table_name in hosp_tables:
        table_path = DATA_DIR / 'hosp' / table_name
        if table_path.exists():
            print(f"\n[{table_name}] 확인 중...")
            sample = pd.read_csv(table_path, nrows=100)
            
            # ICD 코드 관련 테이블인 경우 사망 관련 진단/시술 코드 확인
            if 'diagnoses_icd' in table_name:
                df = pd.read_csv(table_path)
                # 사망 관련 ICD 코드 검색 (예: R57 - Shock, R99 - Other ill-defined causes of mortality)
                death_related = df[df['icd_code'].str.contains('R57|R99|I46|R98', na=False)]
                if len(death_related) > 0:
                    print(f"  - 사망 관련 진단 코드 발견: {len(death_related):,}건")
                    results[table_name] = {
                        'death_related_diagnoses': len(death_related)
                    }
    
    # 4. 데이터 일치성 검증
    print("\n4. 사망 데이터 일치성 검증")
    print("-" * 40)
    
    # admissions와 patients 병합
    merged = admissions.merge(patients[['subject_id', 'dod']], on='subject_id', how='left')
    
    # 일치성 검증
    print("\n[deathtime vs hospital_expire_flag 일치성]")
    deathtime_not_null = merged['deathtime'].notna()
    expire_flag_1 = merged['hospital_expire_flag'] == 1
    
    both_true = (deathtime_not_null & expire_flag_1).sum()
    only_deathtime = (deathtime_not_null & ~expire_flag_1).sum()
    only_flag = (~deathtime_not_null & expire_flag_1).sum()
    
    print(f"  - 둘 다 사망 표시: {both_true:,}건")
    print(f"  - deathtime만 있음: {only_deathtime:,}건")
    print(f"  - hospital_expire_flag만 1: {only_flag:,}건")
    
    if only_deathtime > 0 or only_flag > 0:
        print("  ⚠️ 불일치 발견!")
    else:
        print("  ✓ 완벽히 일치")
    
    results['consistency_check'] = {
        'deathtime_vs_flag': {
            'both_true': int(both_true),
            'only_deathtime': int(only_deathtime),
            'only_flag': int(only_flag),
            'consistent': bool(only_deathtime == 0 and only_flag == 0)
        }
    }
    
    print("\n[hospital_expire_flag vs dod 관계]")
    hospital_death = (merged['hospital_expire_flag'] == 1)
    has_dod = merged['dod'].notna()
    
    hospital_with_dod = (hospital_death & has_dod).sum()
    hospital_without_dod = (hospital_death & ~has_dod).sum()
    no_hospital_with_dod = (~hospital_death & has_dod).sum()
    
    print(f"  - 병원 내 사망 & dod 있음: {hospital_with_dod:,}건")
    print(f"  - 병원 내 사망 & dod 없음: {hospital_without_dod:,}건")
    print(f"  - 병원 외 & dod 있음: {no_hospital_with_dod:,}건")
    
    if hospital_without_dod > 0:
        print(f"  ⚠️ 병원 내 사망했지만 dod가 없는 경우: {hospital_without_dod}건")
    
    results['consistency_check']['hospital_vs_dod'] = {
        'hospital_with_dod': int(hospital_with_dod),
        'hospital_without_dod': int(hospital_without_dod),
        'outside_hospital_with_dod': int(no_hospital_with_dod)
    }
    
    # 5. 사망 위치별 분류
    print("\n5. 사망 위치별 통계")
    print("-" * 40)
    
    # 병원 내/외 사망 구분
    hospital_deaths = (merged['hospital_expire_flag'] == 1).sum()
    outside_deaths = ((merged['hospital_expire_flag'] == 0) & merged['dod'].notna()).sum()
    alive = merged['dod'].isna().sum()
    
    print(f"  - 병원 내 사망: {hospital_deaths:,}건 ({hospital_deaths/len(merged)*100:.2f}%)")
    print(f"  - 병원 외 사망: {outside_deaths:,}건 ({outside_deaths/len(merged)*100:.2f}%)")
    print(f"  - 생존: {alive:,}건 ({alive/len(merged)*100:.2f}%)")
    
    results['death_location_stats'] = {
        'hospital_deaths': int(hospital_deaths),
        'outside_deaths': int(outside_deaths),
        'alive': int(alive),
        'hospital_death_rate': float(hospital_deaths/len(merged)*100),
        'outside_death_rate': float(outside_deaths/len(merged)*100),
        'survival_rate': float(alive/len(merged)*100)
    }
    
    # 6. 시각화
    print("\n6. 시각화 생성 중...")
    
    # 사망 위치별 파이 차트
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 파이 차트
    labels = ['생존', '병원 내 사망', '병원 외 사망']
    sizes = [alive, hospital_deaths, outside_deaths]
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    
    axes[0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0].set_title('입원 건별 사망 위치 분포')
    
    # 막대 그래프
    death_data = pd.DataFrame({
        '구분': ['전체 입원', '병원 내 사망', '병원 외 사망', '생존'],
        '건수': [len(merged), hospital_deaths, outside_deaths, alive]
    })
    
    bars = axes[1].bar(death_data['구분'], death_data['건수'], 
                       color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    axes[1].set_title('사망 위치별 건수')
    axes[1].set_ylabel('건수')
    
    # 막대 위에 수치 표시
    for bar in bars:
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'death_location_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  - 사망 위치 분포 차트 저장: figures/death_location_distribution.png")
    
    # 데이터 불일치 시각화 (있는 경우)
    if only_deathtime > 0 or only_flag > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        inconsistency_data = pd.DataFrame({
            '구분': ['일치 (둘 다 사망)', 'deathtime만', 'flag만'],
            '건수': [both_true, only_deathtime, only_flag]
        })
        
        bars = ax.bar(inconsistency_data['구분'], inconsistency_data['건수'],
                      color=['#2ecc71', '#e74c3c', '#f39c12'])
        ax.set_title('deathtime vs hospital_expire_flag 일치성')
        ax.set_ylabel('건수')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'death_data_consistency.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  - 데이터 일치성 차트 저장: figures/death_data_consistency.png")
    
    # 결과 저장
    with open(DATA_OUTPUT_DIR / 'death_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n분석 결과 저장: data/death_analysis_results.json")
    
    return results

if __name__ == "__main__":
    results = analyze_death_fields()
    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)