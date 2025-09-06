#!/usr/bin/env python3
"""
예측 모델을 위한 변수 선택 및 데이터셋 생성
결측치 분석 결과를 기반으로 3가지 레벨의 데이터셋 생성
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
DATA_DIR = BASE_DIR / 'analysis_prediction' / 'data'
OUTPUT_DIR = BASE_DIR / 'analysis_prediction' / 'data'
FIGURES_DIR = BASE_DIR / 'analysis_prediction' / 'figures'

# 디렉토리 생성
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# 변수 집합 정의 (결측치 분석 기반)
VARIABLE_SETS = {
    'essential': {
        'description': '필수 변수 세트 (결측률 < 30%)',
        'lab_features': [
            'Hematocrit_51221_merged',  # 22.0% 결측
            'Hemoglobin_51222',          # 23.2% 결측
            'Creatinine_50912_merged',   # 23.9% 결측
            'RDW_51277',                  # 24.2% 결측
            'White_Blood_Cells_51301_merged',  # 24.2% 결측
            'Urea_Nitrogen_51006_merged', # 24.2% 결측
            'Potassium_50971_merged',     # 24.3% 결측
            'Sodium_50983_merged',        # 25.0% 결측
            'Glucose_50931'               # 25.9% 결측 (주요 glucose 컬럼 선택)
        ],
        'clinical_relevance': 'CBC, BMP 기본 검사 - 모든 입원 환자의 표준 검사'
    },
    
    'extended': {
        'description': '확장 변수 세트 (결측률 < 70%)',
        'lab_features': [
            # 필수 변수 포함
            'Hematocrit_51221_merged',
            'Hemoglobin_51222',
            'Creatinine_50912_merged',
            'RDW_51277',
            'White_Blood_Cells_51301_merged',
            'Urea_Nitrogen_51006_merged',
            'Potassium_50971_merged',
            'Sodium_50983_merged',
            'Glucose_50931',
            # 추가 변수 (30-70% 결측)
            'Basophils_51146',            # 49.2% 결측
            'Eosinophils_51200',          # 49.2% 결측
            'PT_51274_merged',            # 49.2% 결측
            'PTT_51275_merged',           # 50.1% 결측
            'Calcium__Total_50893',       # 54.4% 결측
            'Bilirubin__Total_50885',     # 64.8% 결측
            'Lactate_50813_merged',       # 66.5% 결측 (중증도 지표)
            'Platelet_Count_51704'        # 추가 CBC 항목
        ],
        'clinical_relevance': 'CBC 상세, 응고검사, 간기능, 중증도 지표 포함'
    },
    
    'comprehensive': {
        'description': '포괄적 변수 세트 (결측률 < 90%, 중요 지표 포함)',
        'lab_features': [
            # 확장 세트 포함
            'Hematocrit_51221_merged',
            'Hemoglobin_51222',
            'Creatinine_50912_merged',
            'RDW_51277',
            'White_Blood_Cells_51301_merged',
            'Urea_Nitrogen_51006_merged',
            'Potassium_50971_merged',
            'Sodium_50983_merged',
            'Glucose_50931',
            'Basophils_51146',
            'Eosinophils_51200',
            'PT_51274_merged',
            'PTT_51275_merged',
            'Calcium__Total_50893',
            'Bilirubin__Total_50885',
            'Lactate_50813_merged',
            'Platelet_Count_51704',
            # 추가 중요 지표 (70-90% 결측)
            'Albumin_50862',              # 73.6% 결측 (영양상태)
            'pH_50820',                   # 80.8% 결측 (산염기)
            'pO2_50821_merged',           # 82.2% 결측 (산소화)
            'pCO2_50818_merged',          # 82.3% 결측 (환기)
            'Creatine_Kinase_CK_50910',   # 82.8% 결측 (근육손상)
            'Troponin_T_51003',           # 87.0% 결측 (심근손상)
            'Chloride__Whole_Blood_50806_merged'  # 전해질
        ],
        'clinical_relevance': '중증 환자 평가를 위한 특수 검사 포함'
    }
}

def load_full_dataset():
    """전체 데이터셋 로드"""
    print("전체 데이터셋 로딩 중...")
    df = pd.read_csv(DATA_DIR / 'prediction_dataset.csv')
    print(f"  - 로드 완료: {len(df):,} x {len(df.columns):,}")
    return df

def calculate_missing_rates(df, lab_features):
    """선택된 변수들의 결측률 계산"""
    missing_rates = {}
    for col in lab_features:
        if col in df.columns:
            missing_rates[col] = df[col].isna().mean() * 100
    return missing_rates

def create_dataset_version(df, variable_set_name, variable_set_info):
    """특정 변수 세트로 데이터셋 생성"""
    print(f"\n{variable_set_name.upper()} 데이터셋 생성 중...")
    print(f"  설명: {variable_set_info['description']}")
    
    # 필수 컬럼 (타겟, 인구통계)
    required_cols = [
        'hadm_id', 'subject_id',
        'death_type', 'death_binary', 'hospital_death',
        'los_hours', 'los_days',
        'age', 'gender', 'admission_type', 'hospital_expire_flag'
    ]
    
    # 실제 존재하는 lab 변수만 선택
    available_lab_features = [col for col in variable_set_info['lab_features'] 
                              if col in df.columns]
    
    # 누락된 변수 확인
    missing_features = [col for col in variable_set_info['lab_features'] 
                        if col not in df.columns]
    
    if missing_features:
        print(f"  ⚠️ 데이터에 없는 변수 {len(missing_features)}개:")
        for feat in missing_features[:5]:  # 처음 5개만 표시
            print(f"    - {feat}")
    
    # 최종 컬럼 리스트
    final_cols = required_cols + available_lab_features
    
    # 데이터셋 생성
    df_subset = df[final_cols].copy()
    
    # 결측률 계산
    missing_rates = calculate_missing_rates(df_subset, available_lab_features)
    
    # 통계 정보
    stats = {
        'dataset_type': variable_set_name,
        'description': variable_set_info['description'],
        'clinical_relevance': variable_set_info['clinical_relevance'],
        'n_samples': len(df_subset),
        'n_features': len(final_cols),
        'n_lab_features': len(available_lab_features),
        'n_demographic_features': len(required_cols) - 5,  # 타겟 변수 제외
        'missing_rates': {
            'mean': np.mean(list(missing_rates.values())),
            'median': np.median(list(missing_rates.values())),
            'max': np.max(list(missing_rates.values())),
            'min': np.min(list(missing_rates.values()))
        },
        'complete_cases': {
            'n_complete': df_subset.dropna().shape[0],
            'percent_complete': (df_subset.dropna().shape[0] / len(df_subset)) * 100
        },
        'lab_features': available_lab_features,
        'missing_features': missing_features
    }
    
    # 결과 출력
    print(f"  - Lab 변수: {len(available_lab_features)}개")
    print(f"  - 평균 결측률: {stats['missing_rates']['mean']:.1f}%")
    print(f"  - 완전한 케이스: {stats['complete_cases']['n_complete']:,}개 ({stats['complete_cases']['percent_complete']:.1f}%)")
    
    return df_subset, stats

def create_missing_indicator_features(df, lab_features):
    """결측 지시자 변수 생성"""
    df_with_indicators = df.copy()
    
    for col in lab_features:
        if col in df.columns:
            # 결측 여부를 나타내는 이진 변수 생성
            df_with_indicators[f'{col}_missing'] = df[col].isna().astype(int)
    
    return df_with_indicators

def visualize_dataset_comparison(all_stats):
    """데이터셋 비교 시각화"""
    print("\n시각화 생성 중...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 변수 수 비교
    datasets = list(all_stats.keys())
    n_features = [stats['n_lab_features'] for stats in all_stats.values()]
    
    axes[0, 0].bar(datasets, n_features, color=['#3498db', '#e74c3c', '#2ecc71'])
    axes[0, 0].set_title('데이터셋별 Lab 변수 수', fontsize=12, fontweight='bold')
    axes[0, 0].set_ylabel('변수 수')
    for i, v in enumerate(n_features):
        axes[0, 0].text(i, v + 0.5, str(v), ha='center')
    
    # 2. 평균 결측률 비교
    missing_rates = [stats['missing_rates']['mean'] for stats in all_stats.values()]
    
    axes[0, 1].bar(datasets, missing_rates, color=['#3498db', '#e74c3c', '#2ecc71'])
    axes[0, 1].set_title('데이터셋별 평균 결측률', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylabel('결측률 (%)')
    for i, v in enumerate(missing_rates):
        axes[0, 1].text(i, v + 1, f'{v:.1f}%', ha='center')
    
    # 3. 완전한 케이스 비교
    complete_cases = [stats['complete_cases']['n_complete'] for stats in all_stats.values()]
    
    axes[1, 0].bar(datasets, complete_cases, color=['#3498db', '#e74c3c', '#2ecc71'])
    axes[1, 0].set_title('완전한 케이스 수', fontsize=12, fontweight='bold')
    axes[1, 0].set_ylabel('케이스 수')
    for i, v in enumerate(complete_cases):
        axes[1, 0].text(i, v + 10, str(v), ha='center')
    
    # 4. 데이터셋 요약 테이블
    axes[1, 1].axis('off')
    table_data = []
    for name, stats in all_stats.items():
        table_data.append([
            name.capitalize(),
            f"{stats['n_lab_features']}",
            f"{stats['missing_rates']['mean']:.1f}%",
            f"{stats['complete_cases']['percent_complete']:.1f}%"
        ])
    
    table = axes[1, 1].table(cellText=table_data,
                            colLabels=['데이터셋', 'Lab 변수', '평균 결측률', '완전 케이스'],
                            cellLoc='center',
                            loc='center',
                            colWidths=[0.25, 0.2, 0.25, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # 헤더 스타일
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_facecolor('#34495e')
            cell.set_text_props(weight='bold', color='white')
    
    plt.suptitle('예측 모델용 데이터셋 비교', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'dataset_comparison.png', dpi=300, bbox_inches='tight')
    print("  - 데이터셋 비교 시각화 저장: dataset_comparison.png")
    
    plt.close()

def save_datasets(datasets_dict):
    """데이터셋 저장"""
    print("\n데이터셋 저장 중...")
    
    for name, (df, stats) in datasets_dict.items():
        # CSV 저장
        output_path = OUTPUT_DIR / f'model_dataset_{name}.csv'
        df.to_csv(output_path, index=False)
        print(f"  - {name}: {output_path}")
        
        # 통계 정보 JSON 저장
        stats_path = OUTPUT_DIR / f'model_dataset_{name}_stats.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            # numpy 타입을 Python 타입으로 변환
            stats_serializable = json.loads(json.dumps(stats, default=lambda x: float(x) if isinstance(x, np.floating) else x))
            json.dump(stats_serializable, f, indent=2, ensure_ascii=False)
        
        # Missing indicator 버전도 생성
        if name != 'comprehensive':  # comprehensive는 너무 많아서 제외
            lab_features = [col for col in df.columns 
                          if col not in ['hadm_id', 'subject_id', 'death_type', 'death_binary', 
                                       'hospital_death', 'los_hours', 'los_days', 'age', 
                                       'gender', 'admission_type', 'hospital_expire_flag']]
            
            df_with_indicators = create_missing_indicator_features(df, lab_features)
            indicator_path = OUTPUT_DIR / f'model_dataset_{name}_with_indicators.csv'
            df_with_indicators.to_csv(indicator_path, index=False)
            print(f"    + Missing indicators: {indicator_path}")

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("예측 모델용 데이터셋 생성")
    print("=" * 80)
    
    # 전체 데이터 로드
    df = load_full_dataset()
    
    # 각 변수 세트별로 데이터셋 생성
    datasets = {}
    all_stats = {}
    
    for set_name, set_info in VARIABLE_SETS.items():
        df_subset, stats = create_dataset_version(df, set_name, set_info)
        datasets[set_name] = (df_subset, stats)
        all_stats[set_name] = stats
    
    # 시각화
    visualize_dataset_comparison(all_stats)
    
    # 저장
    save_datasets(datasets)
    
    # 최종 요약
    print("\n" + "=" * 80)
    print("데이터셋 생성 완료 요약")
    print("=" * 80)
    
    print("\n📊 생성된 데이터셋:")
    for name, stats in all_stats.items():
        print(f"\n{name.upper()}:")
        print(f"  - 설명: {stats['description']}")
        print(f"  - 크기: {stats['n_samples']:,} x {stats['n_features']}")
        print(f"  - Lab 변수: {stats['n_lab_features']}개")
        print(f"  - 평균 결측률: {stats['missing_rates']['mean']:.1f}%")
        print(f"  - 완전 케이스: {stats['complete_cases']['n_complete']:,}개")
    
    print("\n💡 모델링 권장사항:")
    print("1. ESSENTIAL: 빠른 프로토타이핑, 베이스라인 모델")
    print("2. EXTENDED: 실용적 모델, 균형잡힌 성능")
    print("3. COMPREHENSIVE: 고급 모델, 결측값 처리 필수")
    
    print("\n✅ 모든 데이터셋 생성 완료!")

if __name__ == "__main__":
    main()