#!/usr/bin/env python3
"""
ICU별 재원기간 종합 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import platform
from scipy import stats
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

def load_data():
    """샘플링된 ICU 데이터 로드"""
    base_path = Path.cwd()
    df = pd.read_csv(base_path / 'processed_data/icu/icustays_sampled.csv')
    
    # 날짜 컬럼 변환
    df['intime'] = pd.to_datetime(df['intime'])
    df['outtime'] = pd.to_datetime(df['outtime'])
    
    return df

def categorize_los(los):
    """재원기간을 구간으로 분류"""
    if los <= 3:
        return '단기 (0-3일)'
    elif los <= 7:
        return '중기 (4-7일)'
    else:
        return '장기 (8일+)'

def analyze_icu_statistics(df):
    """ICU별 통계 분석"""
    print("\n" + "=" * 60)
    print("ICU별 재원기간 통계 분석")
    print("=" * 60)
    
    # ICU별 기본 통계
    icu_stats = df.groupby('first_careunit')['los'].agg([
        'count', 'mean', 'median', 'std', 'min', 'max',
        lambda x: x.quantile(0.25),  # Q1
        lambda x: x.quantile(0.75),  # Q3
        lambda x: x.quantile(0.95)   # 95 percentile
    ])
    icu_stats.columns = ['count', 'mean', 'median', 'std', 'min', 'max', 'Q1', 'Q3', 'P95']
    icu_stats = icu_stats.sort_values('mean', ascending=False)
    
    print("\n[ICU별 재원기간 통계]")
    print(icu_stats.round(2))
    
    # 재원기간 구간별 분석
    df['los_category'] = df['los'].apply(categorize_los)
    
    print("\n[재원기간 구간별 분포]")
    los_dist = df['los_category'].value_counts()
    for category, count in los_dist.items():
        print(f"  {category}: {count} ({count/len(df)*100:.1f}%)")
    
    return icu_stats

def analyze_mortality_relationship(df):
    """사망률과 재원기간 관계 분석"""
    print("\n[사망률과 재원기간 관계]")
    
    # 사망 그룹별 재원기간
    mortality_los = df.groupby('mortality_group')['los'].agg(['count', 'mean', 'median'])
    print(mortality_los.round(2))
    
    # ICU별 사망률
    icu_mortality = pd.crosstab(df['first_careunit'], df['mortality_group'], normalize='index') * 100
    
    print("\n[ICU별 사망률 (%)]")
    print(icu_mortality.round(1))
    
    return mortality_los, icu_mortality

def perform_statistical_tests(df):
    """통계적 검정 수행"""
    print("\n" + "=" * 60)
    print("통계적 검정")
    print("=" * 60)
    
    # 주요 ICU만 선택 (n >= 30)
    major_icus = df['first_careunit'].value_counts()
    major_icus = major_icus[major_icus >= 30].index.tolist()
    df_major = df[df['first_careunit'].isin(major_icus)]
    
    # ANOVA 검정
    icu_groups = [group['los'].values for name, group in df_major.groupby('first_careunit')]
    f_stat, p_value = stats.f_oneway(*icu_groups)
    
    print(f"\n[ANOVA 검정 - ICU 간 재원기간 차이]")
    print(f"  F-statistic: {f_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  결과: {'유의미한 차이 있음' if p_value < 0.05 else '유의미한 차이 없음'} (α=0.05)")
    
    # 사망 여부에 따른 재원기간 차이 (t-test)
    alive_los = df[df['hospital_expire_flag'] == 0]['los']
    dead_los = df[df['hospital_expire_flag'] == 1]['los']
    t_stat, p_value_t = stats.ttest_ind(alive_los, dead_los)
    
    print(f"\n[T-test - 생존/사망 간 재원기간 차이]")
    print(f"  생존 평균: {alive_los.mean():.2f}일")
    print(f"  사망 평균: {dead_los.mean():.2f}일")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value_t:.4f}")
    print(f"  결과: {'유의미한 차이 있음' if p_value_t < 0.05 else '유의미한 차이 없음'} (α=0.05)")
    
    return {'anova': {'f_stat': f_stat, 'p_value': p_value},
            't_test': {'t_stat': t_stat, 'p_value': p_value_t}}

def create_visualizations(df, icu_stats):
    """시각화 생성"""
    print("\n" + "=" * 60)
    print("시각화 생성")
    print("=" * 60)
    
    base_path = Path.cwd()
    fig_path = base_path / 'analysis_icu_los/figures'
    
    # 색상 팔레트 설정
    colors = sns.color_palette("husl", n_colors=df['first_careunit'].nunique())
    
    # 1. ICU별 재원기간 박스플롯
    plt.figure(figsize=(14, 8))
    
    # ICU를 평균 재원기간 순으로 정렬
    icu_order = icu_stats.sort_values('mean', ascending=False).index.tolist()
    
    # 이상치 제거를 위해 95 백분위수까지만 표시
    df_plot = df.copy()
    df_plot = df_plot[df_plot['los'] <= df_plot['los'].quantile(0.95)]
    
    sns.boxplot(data=df_plot, y='first_careunit', x='los', 
                order=icu_order, palette=colors)
    plt.xlabel('재원기간 (일)', fontsize=12)
    plt.ylabel('ICU 유닛', fontsize=12)
    plt.title('ICU별 재원기간 분포 (박스플롯)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(fig_path / 'icu_los_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ ICU별 재원기간 박스플롯 저장")
    
    # 2. 평균 재원기간 막대그래프
    plt.figure(figsize=(12, 8))
    
    icu_means = icu_stats.sort_values('mean', ascending=True)
    bars = plt.barh(range(len(icu_means)), icu_means['mean'], color=colors)
    
    # 각 막대에 값 표시
    for i, (idx, row) in enumerate(icu_means.iterrows()):
        plt.text(row['mean'] + 0.1, i, f"{row['mean']:.2f}일", 
                va='center', fontsize=10)
    
    plt.yticks(range(len(icu_means)), icu_means.index)
    plt.xlabel('평균 재원기간 (일)', fontsize=12)
    plt.ylabel('ICU 유닛', fontsize=12)
    plt.title('ICU별 평균 재원기간', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='x')
    
    # 전체 평균선 추가
    overall_mean = df['los'].mean()
    plt.axvline(x=overall_mean, color='red', linestyle='--', alpha=0.7, 
                label=f'전체 평균: {overall_mean:.2f}일')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(fig_path / 'icu_los_barplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ ICU별 평균 재원기간 막대그래프 저장")
    
    # 3. 재원기간 전체 분포 히스토그램
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # 전체 분포
    axes[0].hist(df['los'], bins=50, color='skyblue', edgecolor='black', alpha=0.7)
    axes[0].axvline(df['los'].mean(), color='red', linestyle='--', 
                    label=f'평균: {df["los"].mean():.2f}일')
    axes[0].axvline(df['los'].median(), color='green', linestyle='--', 
                    label=f'중앙값: {df["los"].median():.2f}일')
    axes[0].set_xlabel('재원기간 (일)', fontsize=12)
    axes[0].set_ylabel('빈도', fontsize=12)
    axes[0].set_title('전체 ICU 재원기간 분포', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 로그 스케일 분포
    axes[1].hist(df['los'], bins=50, color='lightcoral', edgecolor='black', alpha=0.7)
    axes[1].set_yscale('log')
    axes[1].set_xlabel('재원기간 (일)', fontsize=12)
    axes[1].set_ylabel('빈도 (로그 스케일)', fontsize=12)
    axes[1].set_title('전체 ICU 재원기간 분포 (로그 스케일)', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(fig_path / 'icu_los_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 재원기간 분포 히스토그램 저장")
    
    # 4. ICU별 사망률 차트
    mortality_by_icu = pd.crosstab(df['first_careunit'], 
                                   df['hospital_expire_flag'], 
                                   normalize='index') * 100
    mortality_by_icu.columns = ['생존', '사망']
    mortality_by_icu = mortality_by_icu.sort_values('사망', ascending=False)
    
    plt.figure(figsize=(12, 8))
    mortality_by_icu.plot(kind='barh', stacked=True, color=['lightgreen', 'lightcoral'])
    plt.xlabel('비율 (%)', fontsize=12)
    plt.ylabel('ICU 유닛', fontsize=12)
    plt.title('ICU별 사망률', fontsize=14, fontweight='bold')
    plt.legend(title='결과', loc='best')
    plt.grid(True, alpha=0.3, axis='x')
    
    # 각 막대에 사망률 표시
    for i, (idx, row) in enumerate(mortality_by_icu.iterrows()):
        plt.text(row['사망']/2, i, f"{row['사망']:.1f}%", 
                va='center', ha='center', fontsize=9, color='white', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(fig_path / 'icu_mortality_rate.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ ICU별 사망률 차트 저장")
    
    # 5. 재원기간 구간별 분포
    df['los_category'] = df['los'].apply(categorize_los)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 전체 구간 분포
    los_dist = df['los_category'].value_counts()
    colors_pie = ['lightblue', 'lightgreen', 'lightcoral']
    axes[0].pie(los_dist.values, labels=los_dist.index, autopct='%1.1f%%', 
                colors=colors_pie, startangle=90)
    axes[0].set_title('전체 재원기간 구간 분포', fontsize=14, fontweight='bold')
    
    # ICU별 구간 분포
    icu_category = pd.crosstab(df['first_careunit'], df['los_category'], normalize='index') * 100
    icu_category = icu_category[['단기 (0-3일)', '중기 (4-7일)', '장기 (8일+)']]
    
    # 주요 ICU만 선택 (상위 6개)
    top_icus = df['first_careunit'].value_counts().head(6).index
    icu_category_top = icu_category.loc[top_icus]
    
    icu_category_top.plot(kind='bar', stacked=True, ax=axes[1], 
                          color=['lightblue', 'lightgreen', 'lightcoral'])
    axes[1].set_xlabel('ICU 유닛', fontsize=12)
    axes[1].set_ylabel('비율 (%)', fontsize=12)
    axes[1].set_title('주요 ICU별 재원기간 구간 분포', fontsize=14, fontweight='bold')
    axes[1].legend(title='재원기간', loc='best')
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45, ha='right')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(fig_path / 'icu_los_categories.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 재원기간 구간별 분포 차트 저장")

def save_results(df, icu_stats, test_results):
    """분석 결과 저장"""
    base_path = Path.cwd()
    data_path = base_path / 'analysis_icu_los/data'
    
    results = {
        'summary': {
            'total_icu_stays': len(df),
            'unique_patients': df['subject_id'].nunique(),
            'unique_admissions': df['hadm_id'].nunique(),
            'icu_units': df['first_careunit'].nunique()
        },
        'overall_los': {
            'mean': float(df['los'].mean()),
            'median': float(df['los'].median()),
            'std': float(df['los'].std()),
            'min': float(df['los'].min()),
            'max': float(df['los'].max()),
            'q1': float(df['los'].quantile(0.25)),
            'q3': float(df['los'].quantile(0.75))
        },
        'icu_statistics': icu_stats.to_dict('index'),
        'los_categories': df['los_category'].value_counts().to_dict(),
        'statistical_tests': test_results,
        'mortality_analysis': {
            'hospital_death_los_mean': float(df[df['hospital_expire_flag']==1]['los'].mean()),
            'survival_los_mean': float(df[df['hospital_expire_flag']==0]['los'].mean()),
            'mortality_rate': float(df['hospital_expire_flag'].mean() * 100)
        }
    }
    
    # JSON으로 저장
    with open(data_path / 'results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✓ 분석 결과가 results.json에 저장되었습니다.")

def main():
    """메인 분석 실행"""
    print("\n" + "=" * 60)
    print("ICU별 재원기간 종합 분석 시작")
    print("=" * 60)
    
    # 데이터 로드
    df = load_data()
    print(f"\n✓ 데이터 로드 완료: {len(df)}건의 ICU 입실 기록")
    
    # 통계 분석
    icu_stats = analyze_icu_statistics(df)
    mortality_los, icu_mortality = analyze_mortality_relationship(df)
    test_results = perform_statistical_tests(df)
    
    # 시각화 생성
    create_visualizations(df, icu_stats)
    
    # 결과 저장
    save_results(df, icu_stats, test_results)
    
    print("\n" + "=" * 60)
    print("분석 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()