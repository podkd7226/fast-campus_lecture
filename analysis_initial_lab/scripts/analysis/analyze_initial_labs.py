#!/usr/bin/env python3
"""
입원 당일 혈액검사 분석 및 시각화 스크립트
추출된 데이터를 분석하고 시각화합니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
FIGURE_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/figures')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """데이터 로드"""
    print("1. 데이터 로딩 중...")
    
    # Wide format 데이터
    wide_df = pd.read_csv(os.path.join(BASE_PATH, 'analysis_initial_lab/data/admission_day_labs_wide.csv'))
    
    # 통계 데이터
    with open(os.path.join(BASE_PATH, 'analysis_initial_lab/data/lab_statistics.json'), 'r') as f:
        stats_data = json.load(f)
    
    print(f"✅ 데이터 로드 완료: {len(wide_df)} 입원")
    
    return wide_df, stats_data

def plot_lab_frequency(stats_data):
    """검사 빈도 시각화"""
    print("\n2. 검사 빈도 시각화...")
    
    # 검사별 수집 개수 추출
    lab_counts = {lab: info['count'] for lab, info in stats_data['lab_statistics'].items()}
    
    # 정렬 및 데이터프레임 생성
    lab_df = pd.DataFrame(list(lab_counts.items()), columns=['Lab Test', 'Count'])
    lab_df = lab_df.sort_values('Count', ascending=True)
    
    # 시각화
    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(lab_df['Lab Test'], lab_df['Count'])
    
    # 색상 그라데이션
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(bars)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    ax.set_xlabel('Number of Tests', fontsize=12)
    ax.set_ylabel('Lab Test', fontsize=12)
    ax.set_title('Frequency of Lab Tests on Admission Day', fontsize=14, fontweight='bold')
    
    # 값 표시
    for i, (lab, count) in enumerate(zip(lab_df['Lab Test'], lab_df['Count'])):
        ax.text(count + 5, i, str(count), va='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'lab_frequency.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   ✅ lab_frequency.png 저장 완료")

def plot_missing_pattern(wide_df):
    """결측값 패턴 시각화"""
    print("\n3. 결측값 패턴 시각화...")
    
    # 검사 컬럼만 선택
    lab_columns = [col for col in wide_df.columns 
                  if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']]
    
    # 결측값 비율 계산
    missing_pct = (wide_df[lab_columns].isna().sum() / len(wide_df) * 100).sort_values()
    
    # 시각화
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 1. 결측값 비율 막대 그래프
    bars = ax1.bar(range(len(missing_pct)), missing_pct.values)
    colors = ['green' if x < 10 else 'orange' if x < 20 else 'red' for x in missing_pct.values]
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    ax1.set_xticks(range(len(missing_pct)))
    ax1.set_xticklabels(missing_pct.index, rotation=45, ha='right')
    ax1.set_ylabel('Missing Percentage (%)')
    ax1.set_title('Missing Data Pattern by Lab Test')
    ax1.axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='10% threshold')
    ax1.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='20% threshold')
    ax1.legend()
    
    # 2. 결측값 히트맵 (샘플 50개)
    sample_size = min(50, len(wide_df))
    sample_df = wide_df[lab_columns].head(sample_size)
    
    # 결측값을 1, 아닌 것을 0으로
    missing_matrix = sample_df.isna().astype(int)
    
    sns.heatmap(missing_matrix.T, cmap='RdYlGn_r', cbar_kws={'label': 'Missing (1) / Present (0)'},
                ax=ax2, xticklabels=False, yticklabels=True)
    ax2.set_xlabel(f'Admissions (first {sample_size})')
    ax2.set_ylabel('Lab Tests')
    ax2.set_title('Missing Data Pattern Heatmap')
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'missing_pattern.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   ✅ missing_pattern.png 저장 완료")

def plot_lab_distributions(wide_df):
    """주요 검사 결과 분포 시각화"""
    print("\n4. 검사 결과 분포 시각화...")
    
    # 주요 검사 8개 선택
    key_labs = ['Sodium', 'Potassium', 'Creatinine', 'Glucose', 
                'Hemoglobin', 'White_Blood_Cells', 'Platelet_Count', 'Hematocrit']
    
    # 존재하는 검사만 필터링
    available_labs = [lab for lab in key_labs if lab in wide_df.columns]
    
    # 시각화
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    for i, lab in enumerate(available_labs):
        ax = axes[i]
        
        # 데이터 준비
        lab_data = wide_df[lab].dropna()
        
        if len(lab_data) > 0:
            # 히스토그램
            ax.hist(lab_data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            
            # 평균과 중앙값 표시
            mean_val = lab_data.mean()
            median_val = lab_data.median()
            
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
            ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.1f}')
            
            ax.set_title(lab, fontsize=12, fontweight='bold')
            ax.set_xlabel('Value')
            ax.set_ylabel('Frequency')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
    
    # 빈 subplot 숨기기
    for i in range(len(available_labs), 8):
        axes[i].set_visible(False)
    
    plt.suptitle('Distribution of Key Lab Tests on Admission Day', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'lab_distributions.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   ✅ lab_distributions.png 저장 완료")

def plot_mortality_comparison(wide_df):
    """사망률별 검사 결과 비교"""
    print("\n5. 사망률별 검사 결과 비교...")
    
    if 'hospital_expire_flag' not in wide_df.columns:
        print("   ⚠️ 사망률 정보 없음")
        return
    
    # 생존/사망 그룹 분리
    survived = wide_df[wide_df['hospital_expire_flag'] == 0]
    died = wide_df[wide_df['hospital_expire_flag'] == 1]
    
    # 비교할 검사 항목
    compare_labs = ['Creatinine', 'Urea_Nitrogen', 'Sodium', 'White_Blood_Cells']
    available_labs = [lab for lab in compare_labs if lab in wide_df.columns]
    
    # 시각화
    fig, axes = plt.subplots(1, len(available_labs), figsize=(4*len(available_labs), 5))
    if len(available_labs) == 1:
        axes = [axes]
    
    for i, lab in enumerate(available_labs):
        ax = axes[i]
        
        # 데이터 준비
        survived_data = survived[lab].dropna()
        died_data = died[lab].dropna()
        
        # 박스플롯
        bp = ax.boxplot([survived_data, died_data], 
                        labels=['Survived', 'Died'],
                        patch_artist=True,
                        notch=True)
        
        # 색상 설정
        colors = ['lightgreen', 'lightcoral']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # 통계 검정 (Mann-Whitney U test)
        if len(survived_data) > 0 and len(died_data) > 0:
            statistic, pvalue = stats.mannwhitneyu(survived_data, died_data, alternative='two-sided')
            
            # p-value 표시
            if pvalue < 0.001:
                sig_text = '***'
            elif pvalue < 0.01:
                sig_text = '**'
            elif pvalue < 0.05:
                sig_text = '*'
            else:
                sig_text = 'ns'
            
            ax.text(1.5, ax.get_ylim()[1] * 0.95, f'p={pvalue:.3f} {sig_text}', 
                   ha='center', fontsize=10)
        
        ax.set_title(lab, fontsize=12, fontweight='bold')
        ax.set_ylabel('Value')
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Lab Values Comparison: Survived vs Died', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'mortality_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   ✅ mortality_comparison.png 저장 완료")

def create_summary_table(wide_df, stats_data):
    """요약 테이블 생성"""
    print("\n6. 요약 테이블 생성...")
    
    # 검사별 요약 통계
    summary_data = []
    
    lab_columns = [col for col in wide_df.columns 
                  if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']]
    
    for lab in lab_columns:
        if lab in stats_data['lab_statistics']:
            lab_stats = stats_data['lab_statistics'][lab]
            
            # 생존/사망 그룹별 평균
            if 'hospital_expire_flag' in wide_df.columns:
                survived_mean = wide_df[wide_df['hospital_expire_flag'] == 0][lab].mean()
                died_mean = wide_df[wide_df['hospital_expire_flag'] == 1][lab].mean()
            else:
                survived_mean = died_mean = np.nan
            
            summary_data.append({
                'Lab Test': lab,
                'N': lab_stats['count'],
                'Missing %': f"{lab_stats['missing_pct']:.1f}",
                'Mean ± SD': f"{lab_stats['mean']:.1f} ± {lab_stats['std']:.1f}",
                'Median [Q1-Q3]': f"{lab_stats['median']:.1f} [{lab_stats['q1']:.1f}-{lab_stats['q3']:.1f}]",
                'Survived Mean': f"{survived_mean:.1f}" if not np.isnan(survived_mean) else '-',
                'Died Mean': f"{died_mean:.1f}" if not np.isnan(died_mean) else '-'
            })
    
    # DataFrame 생성 및 저장
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('N', ascending=False)
    
    output_path = os.path.join(BASE_PATH, 'analysis_initial_lab/data/summary_table.csv')
    summary_df.to_csv(output_path, index=False)
    
    print("   ✅ summary_table.csv 저장 완료")
    print("\n[요약 테이블 - 상위 10개]")
    print(summary_df.head(10).to_string(index=False))
    
    return summary_df

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 입원 당일 혈액검사 분석 및 시각화")
    print("=" * 80)
    
    # 1. 데이터 로드
    wide_df, stats_data = load_data()
    
    # 2. 시각화
    plot_lab_frequency(stats_data)
    plot_missing_pattern(wide_df)
    plot_lab_distributions(wide_df)
    plot_mortality_comparison(wide_df)
    
    # 3. 요약 테이블
    summary_df = create_summary_table(wide_df, stats_data)
    
    print("\n" + "=" * 80)
    print("✅ 분석 완료!")
    print("=" * 80)
    
    print(f"\n[분석 요약]")
    print(f"• 총 입원: {stats_data['total_admissions']}건")
    print(f"• 사망률: {stats_data.get('mortality_rate', 0):.1f}%")
    print(f"• 생존: {stats_data.get('survived_count', 0)}명")
    print(f"• 사망: {stats_data.get('died_count', 0)}명")
    
    print(f"\n💾 저장된 파일:")
    print(f"• 그래프: analysis_initial_lab/figures/")
    print(f"• 요약 테이블: analysis_initial_lab/data/summary_table.csv")
    
    return summary_df

if __name__ == "__main__":
    summary_df = main()