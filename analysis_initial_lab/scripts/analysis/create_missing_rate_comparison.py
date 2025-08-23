#!/usr/bin/env python3
"""
시간 윈도우 적용 전후 결측률 비교 시각화
검사별로 결측률이 얼마나 감소했는지 보여주는 그래프 생성
"""

import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# 한글 폰트 설정
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:  # Linux
    plt.rcParams['font.family'] = 'NanumGothic'

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
DATA_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/data')
FIGURE_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/figures')

def load_data():
    """데이터 로드"""
    print("데이터 로딩 중...")
    
    # 통계 데이터 로드
    with open(os.path.join(DATA_PATH, 'lab_statistics.json'), 'r') as f:
        stats_day0 = json.load(f)
    
    with open(os.path.join(DATA_PATH, 'lab_statistics_time_window.json'), 'r') as f:
        stats_window = json.load(f)
    
    return stats_day0, stats_window

def prepare_comparison_data(stats_day0, stats_window):
    """비교 데이터 준비"""
    comparison_data = []
    
    # 각 검사별로 비교
    for lab_name in stats_day0['lab_statistics'].keys():
        day0_missing = stats_day0['lab_statistics'][lab_name]['missing_pct']
        window_missing = stats_window['lab_statistics'][lab_name]['missing_pct']
        
        # 가용성으로 변환 (100 - 결측률)
        day0_available = 100 - day0_missing
        window_available = 100 - window_missing
        improvement = window_available - day0_available
        
        comparison_data.append({
            'lab_name': lab_name.replace('_', ' '),
            'day0_missing': day0_missing,
            'window_missing': window_missing,
            'day0_available': day0_available,
            'window_available': window_available,
            'improvement': improvement
        })
    
    # DataFrame으로 변환하고 개선율 기준 정렬
    df = pd.DataFrame(comparison_data)
    df = df.sort_values('improvement', ascending=False)
    
    return df

def create_comparison_plots(df):
    """3개 그룹으로 나누어 비교 그래프 생성"""
    
    # 개선율 기준으로 3개 그룹으로 나누기
    n_labs = len(df)
    group_size = n_labs // 3
    
    group1 = df.iloc[:group_size]  # 상위 개선
    group2 = df.iloc[group_size:2*group_size]  # 중간 개선
    group3 = df.iloc[2*group_size:]  # 하위 개선
    
    # Figure 생성
    fig, axes = plt.subplots(3, 1, figsize=(14, 16))
    
    groups = [
        (group1, '가용성 개선 상위 검사', axes[0]),
        (group2, '가용성 개선 중위 검사', axes[1]),
        (group3, '가용성 개선 하위 검사', axes[2])
    ]
    
    for group_df, title, ax in groups:
        # 검사명 준비
        labs = group_df['lab_name'].values
        x = np.arange(len(labs))
        width = 0.35
        
        # 막대 그래프 그리기
        bars1 = ax.barh(x - width/2, group_df['day0_available'].values, width, 
                        label='입원 당일만', color='#5C946E', alpha=0.8)
        bars2 = ax.barh(x + width/2, group_df['window_available'].values, width,
                        label='시간 윈도우', color='#2E86AB', alpha=0.8)
        
        # 개선율 텍스트 추가
        for i, (day0, window, improvement) in enumerate(zip(
            group_df['day0_available'].values,
            group_df['window_available'].values,
            group_df['improvement'].values)):
            
            # 개선율을 막대 끝에 표시
            if improvement > 0:
                ax.text(max(day0, window) + 1, i, 
                       f'+{improvement:.1f}%p',
                       va='center', fontsize=9, color='red', fontweight='bold')
        
        # 축 설정
        ax.set_yticks(x)
        ax.set_yticklabels(labs, fontsize=9)
        ax.set_xlabel('가용성 (%)', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, 105)
        
        # 50% 기준선 추가
        ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
        ax.axvline(x=90, color='green', linestyle='--', alpha=0.5, linewidth=0.5)
    
    plt.suptitle('시간 윈도우 적용에 따른 검사별 가용성 변화\n(1,200개 입원 기준)', 
                 fontsize=14, fontweight='bold', y=1.002)
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(FIGURE_PATH, 'missing_rate_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 그래프 저장: {output_path}")
    plt.show()
    
    return output_path

def create_top20_comparison(df):
    """상위 20개 검사 개선 비교 (더 명확한 시각화)"""
    
    # 상위 20개 선택
    top20 = df.head(20)
    
    # Figure 생성
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 데이터 준비
    labs = top20['lab_name'].values
    x = np.arange(len(labs))
    
    # 막대 그래프 (가로)
    width = 0.35
    bars1 = ax.barh(x - width/2, top20['day0_available'].values, width,
                    label='입원 당일만', color='#E63946', alpha=0.7)
    bars2 = ax.barh(x + width/2, top20['window_available'].values, width,
                    label='시간 윈도우', color='#2A9D8F', alpha=0.7)
    
    # 개선율 화살표와 텍스트
    for i, (day0, window, improvement) in enumerate(zip(
        top20['day0_available'].values,
        top20['window_available'].values,
        top20['improvement'].values)):
        
        # 화살표로 개선 표시
        if improvement > 5:  # 5%p 이상 개선만 화살표
            ax.annotate('', xy=(window-1, i+width/2), xytext=(day0+1, i-width/2),
                       arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1.5, alpha=0.6))
        
        # 개선율 텍스트
        ax.text(max(day0, window) + 2, i, 
               f'+{improvement:.1f}%p',
               va='center', fontsize=9, color='darkgreen', fontweight='bold')
    
    # 축 설정
    ax.set_yticks(x)
    ax.set_yticklabels(labs, fontsize=10)
    ax.set_xlabel('가용성 (%)', fontsize=11)
    ax.set_title('가용성 개선 상위 20개 검사\n입원 당일 vs 시간 윈도우 (Day-1, Day0, Day+1)', 
                fontsize=12, fontweight='bold')
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(0, 105)
    
    # 기준선
    ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5, linewidth=0.5, label='50% 기준')
    ax.axvline(x=90, color='green', linestyle='--', alpha=0.5, linewidth=0.5, label='90% 목표')
    
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(FIGURE_PATH, 'top20_availability_improvement.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 상위 20개 그래프 저장: {output_path}")
    plt.show()
    
    return output_path

def create_improvement_distribution(df):
    """개선율 분포 히스토그램"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 1. 개선율 히스토그램
    ax1.hist(df['improvement'].values, bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax1.axvline(x=df['improvement'].mean(), color='red', linestyle='--', 
                label=f'평균: {df["improvement"].mean():.1f}%p', linewidth=2)
    ax1.axvline(x=df['improvement'].median(), color='green', linestyle='--',
                label=f'중앙값: {df["improvement"].median():.1f}%p', linewidth=2)
    ax1.set_xlabel('가용성 개선율 (%p)', fontsize=11)
    ax1.set_ylabel('검사 항목 수', fontsize=11)
    ax1.set_title('검사별 가용성 개선율 분포', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. 개선 전후 산점도
    ax2.scatter(df['day0_available'].values, df['window_available'].values, 
               c=df['improvement'].values, cmap='RdYlGn', s=50, alpha=0.6)
    
    # 대각선 (변화 없음 선)
    ax2.plot([0, 100], [0, 100], 'k--', alpha=0.3, label='변화 없음')
    
    # 색상 막대
    cbar = plt.colorbar(ax2.collections[0], ax=ax2)
    cbar.set_label('개선율 (%p)', rotation=270, labelpad=15)
    
    ax2.set_xlabel('입원 당일만 가용성 (%)', fontsize=11)
    ax2.set_ylabel('시간 윈도우 가용성 (%)', fontsize=11)
    ax2.set_title('가용성 개선 전후 비교', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.set_xlim(0, 105)
    ax2.set_ylim(0, 105)
    
    plt.suptitle('시간 윈도우 효과 분석', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(FIGURE_PATH, 'improvement_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 분포 그래프 저장: {output_path}")
    plt.show()
    
    return output_path

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("📊 시간 윈도우 결측률 개선 시각화")
    print("="*60)
    
    # 1. 데이터 로드
    stats_day0, stats_window = load_data()
    
    # 2. 비교 데이터 준비
    df = prepare_comparison_data(stats_day0, stats_window)
    
    # 3. 통계 출력
    print(f"\n📈 전체 통계:")
    print(f"- 분석 검사 항목: {len(df)}개")
    print(f"- 평균 개선율: {df['improvement'].mean():.1f}%p")
    print(f"- 최대 개선: {df['improvement'].max():.1f}%p ({df.iloc[0]['lab_name']})")
    print(f"- 최소 개선: {df['improvement'].min():.1f}%p ({df.iloc[-1]['lab_name']})")
    
    # 4. 그래프 생성
    print("\n📊 그래프 생성 중...")
    path1 = create_comparison_plots(df)
    path2 = create_top20_comparison(df)
    path3 = create_improvement_distribution(df)
    
    print("\n" + "="*60)
    print("✅ 모든 그래프 생성 완료!")
    print(f"생성된 파일:")
    print(f"1. {path1}")
    print(f"2. {path2}")
    print(f"3. {path3}")
    print("="*60)

if __name__ == "__main__":
    main()