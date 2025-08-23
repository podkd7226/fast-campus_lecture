#!/usr/bin/env python3
"""
시간 윈도우 분석 - 1,200개 입원 기준 절대값 평가
모든 수치를 1,200개 입원 기준으로 명확하게 표현
"""

import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
DATA_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/data')
FIGURE_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/figures')

# 폴더 생성
os.makedirs(FIGURE_PATH, exist_ok=True)

def load_data():
    """데이터 로드"""
    print("데이터 로딩 중...")
    
    # 1. 입원 당일만 데이터
    day0_wide = pd.read_csv(os.path.join(DATA_PATH, 'initial_labs_wide.csv'))
    
    # 2. 시간 윈도우 데이터
    window_wide = pd.read_csv(os.path.join(DATA_PATH, 'labs_time_window_wide.csv'))
    window_long = pd.read_csv(os.path.join(DATA_PATH, 'labs_time_window_long.csv'))
    
    # 3. 통계 데이터
    with open(os.path.join(DATA_PATH, 'lab_statistics.json'), 'r') as f:
        stats_day0 = json.load(f)
    
    with open(os.path.join(DATA_PATH, 'lab_statistics_time_window.json'), 'r') as f:
        stats_window = json.load(f)
    
    print(f"✅ 데이터 로드 완료")
    
    return day0_wide, window_wide, window_long, stats_day0, stats_window

def analyze_absolute_values(day0_wide, window_wide, window_long):
    """1,200개 입원 기준 절대값 분석"""
    print("\n" + "="*80)
    print("📊 1,200개 입원 기준 절대값 분석")
    print("="*80)
    
    # 기본 검사 컬럼 (day_offset 제외)
    lab_columns = [col for col in window_wide.columns 
                   if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] 
                   and '_day_offset' not in col]
    
    results = {}
    
    print("\n### 전체 요약 (1,200개 입원 기준)")
    print("-" * 60)
    
    # 1. 전체 가용성
    has_lab_day0 = ~day0_wide[lab_columns].isna().all(axis=1)
    has_lab_window = ~window_wide[lab_columns].isna().all(axis=1)
    
    n_day0 = has_lab_day0.sum()
    n_window = has_lab_window.sum()
    n_improved = n_window - n_day0
    
    print(f"입원 당일만:")
    print(f"  - 검사 있음: {n_day0}건 ({n_day0/1200*100:.1f}%)")
    print(f"  - 검사 없음: {1200-n_day0}건 ({(1200-n_day0)/1200*100:.1f}%)")
    
    print(f"\n시간 윈도우 적용:")
    print(f"  - 검사 있음: {n_window}건 ({n_window/1200*100:.1f}%)")
    print(f"  - 검사 없음: {1200-n_window}건 ({(1200-n_window)/1200*100:.1f}%)")
    
    print(f"\n개선 효과:")
    print(f"  - 추가된 입원: {n_improved}건 ({n_improved/1200*100:.1f}%p 증가)")
    
    # 2. 검사별 상세 분석
    print("\n### 검사별 가용성 (1,200개 입원 기준)")
    print("-" * 60)
    
    lab_analysis = []
    
    for lab in lab_columns:
        # Day 0만
        n_day0_lab = day0_wide[lab].notna().sum()
        pct_day0_lab = n_day0_lab / 1200 * 100
        
        # 시간 윈도우
        n_window_lab = window_wide[lab].notna().sum()
        pct_window_lab = n_window_lab / 1200 * 100
        
        # 개선
        n_improved_lab = n_window_lab - n_day0_lab
        pct_improved_lab = pct_window_lab - pct_day0_lab
        
        # Day offset 분석 (어디서 데이터가 왔는지)
        offset_col = f"{lab}_day_offset"
        if offset_col in window_wide.columns:
            day_sources = window_wide[window_wide[lab].notna()][offset_col].value_counts().to_dict()
            n_from_day0 = day_sources.get(0.0, 0)
            n_from_minus1 = day_sources.get(-1.0, 0)
            n_from_plus1 = day_sources.get(1.0, 0)
        else:
            n_from_day0 = n_from_minus1 = n_from_plus1 = 0
        
        lab_analysis.append({
            'lab_name': lab,
            'day0_count': n_day0_lab,
            'day0_pct': pct_day0_lab,
            'window_count': n_window_lab,
            'window_pct': pct_window_lab,
            'improved_count': n_improved_lab,
            'improved_pct': pct_improved_lab,
            'from_day0': n_from_day0,
            'from_minus1': n_from_minus1,
            'from_plus1': n_from_plus1
        })
    
    # DataFrame으로 변환 및 정렬
    lab_df = pd.DataFrame(lab_analysis)
    lab_df = lab_df.sort_values('improved_count', ascending=False)
    
    # 상위 10개 출력
    print("\n📈 가용성 개선 상위 10개 검사")
    print("-" * 100)
    print(f"{'검사명':<30} | {'당일만':<20} | {'시간윈도우':<20} | {'개선':<15} | {'데이터 출처'}")
    print("-" * 100)
    
    for _, row in lab_df.head(10).iterrows():
        print(f"{row['lab_name']:<30} | "
              f"{row['day0_count']:>4}건 ({row['day0_pct']:>5.1f}%) | "
              f"{row['window_count']:>4}건 ({row['window_pct']:>5.1f}%) | "
              f"+{row['improved_count']:>3}건 (+{row['improved_pct']:>4.1f}%p) | "
              f"D0:{row['from_day0']:>4}, D-1:{row['from_minus1']:>3}, D+1:{row['from_plus1']:>3}")
    
    # 3. 데이터 출처 분석 (전체)
    print("\n### 전체 데이터 출처 분석 (20,118개 검사 레코드)")
    print("-" * 60)
    
    if 'day_offset' in window_long.columns:
        source_counts = window_long['day_offset'].value_counts().sort_index()
        
        print(f"Day-1 (입원 전일): {source_counts.get(-1, 0):>5}건 ({source_counts.get(-1, 0)/len(window_long)*100:>5.1f}%)")
        print(f"Day 0 (입원 당일): {source_counts.get(0, 0):>5}건 ({source_counts.get(0, 0)/len(window_long)*100:>5.1f}%)")
        print(f"Day+1 (입원 익일): {source_counts.get(1, 0):>5}건 ({source_counts.get(1, 0)/len(window_long)*100:>5.1f}%)")
    
    # 4. 완전 결측 입원 분석
    print("\n### 완전 결측 입원 분석")
    print("-" * 60)
    
    # 당일만에서 결측인 입원
    no_lab_day0 = day0_wide[~has_lab_day0]['hadm_id'].tolist()
    # 시간 윈도우에서도 여전히 결측인 입원
    no_lab_window = window_wide[~has_lab_window]['hadm_id'].tolist()
    # 시간 윈도우로 해결된 입원
    resolved = set(no_lab_day0) - set(no_lab_window)
    
    print(f"당일 검사 없음: {len(no_lab_day0)}건")
    print(f"시간 윈도우로 해결: {len(resolved)}건")
    print(f"여전히 검사 없음: {len(no_lab_window)}건")
    
    return lab_df

def create_absolute_visualization(lab_df):
    """절대값 기준 시각화"""
    print("\n시각화 생성 중...")
    
    # 설정
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    
    # Figure 생성
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 전체 가용성 비교 (막대그래프)
    ax1 = axes[0, 0]
    categories = ['입원 당일만', '시간 윈도우']
    has_lab = [1053, 1155]  # 실제 데이터
    no_lab = [147, 45]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, has_lab, width, label='검사 있음', color='#2E86AB')
    bars2 = ax1.bar(x + width/2, no_lab, width, label='검사 없음', color='#A23B72')
    
    # 막대 위에 수치 표시
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}건\n({height/12:.1f}%)',
                ha='center', va='bottom')
    
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}건\n({height/12:.1f}%)',
                ha='center', va='bottom')
    
    ax1.set_ylabel('입원 수')
    ax1.set_title('전체 가용성 비교 (1,200개 입원 기준)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()
    ax1.set_ylim(0, 1300)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. 검사별 개선 효과 (상위 15개)
    ax2 = axes[0, 1]
    top15 = lab_df.head(15)
    
    y_pos = np.arange(len(top15))
    ax2.barh(y_pos, top15['day0_count'], 0.4, 
             label='당일만', color='#5C946E', alpha=0.7)
    ax2.barh(y_pos + 0.4, top15['window_count'], 0.4,
             label='시간 윈도우', color='#2E86AB', alpha=0.7)
    
    ax2.set_yticks(y_pos + 0.2)
    ax2.set_yticklabels(top15['lab_name'], fontsize=8)
    ax2.set_xlabel('검사 가능한 입원 수')
    ax2.set_title('검사별 가용성 개선 (상위 15개)')
    ax2.legend()
    ax2.grid(axis='x', alpha=0.3)
    
    # 3. 데이터 출처 분포 (파이 차트)
    ax3 = axes[1, 0]
    sizes = [1065, 16593, 2460]  # Day-1, Day0, Day+1
    labels = ['Day-1\n(입원 전일)\n1,065건\n5.3%', 
              'Day 0\n(입원 당일)\n16,593건\n82.5%', 
              'Day+1\n(입원 익일)\n2,460건\n12.2%']
    colors = ['#F18F01', '#2E86AB', '#A23B72']
    explode = (0.1, 0, 0.1)
    
    ax3.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='', shadow=True, startangle=90)
    ax3.set_title('전체 검사 레코드 출처 분포 (20,118건)')
    
    # 4. 개선율 분포 (히스토그램)
    ax4 = axes[1, 1]
    improvements = lab_df['improved_pct'].values
    
    ax4.hist(improvements, bins=20, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax4.axvline(x=improvements.mean(), color='red', linestyle='--', 
                label=f'평균: {improvements.mean():.1f}%p')
    ax4.set_xlabel('가용성 개선 (%p)')
    ax4.set_ylabel('검사 항목 수')
    ax4.set_title('검사별 가용성 개선율 분포')
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    plt.suptitle('시간 윈도우 효과 분석 - 1,200개 입원 기준 절대값', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(FIGURE_PATH, 'time_window_absolute_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 시각화 저장: {output_path}")
    plt.show()

def save_results(lab_df):
    """결과 저장"""
    print("\n결과 저장 중...")
    
    # CSV 저장
    output_path = os.path.join(DATA_PATH, 'time_window_absolute_analysis.csv')
    lab_df.to_csv(output_path, index=False)
    print(f"✅ 분석 결과 저장: {output_path}")
    
    # 요약 통계 JSON
    summary = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_admissions": 1200,
        "admission_day_only": {
            "with_labs": 1053,
            "without_labs": 147,
            "coverage_pct": 87.75
        },
        "time_window": {
            "with_labs": 1155,
            "without_labs": 45,
            "coverage_pct": 96.25
        },
        "improvement": {
            "additional_admissions": 102,
            "improvement_pct": 8.5
        },
        "data_sources": {
            "total_records": 20118,
            "day_minus1": 1065,
            "day0": 16593,
            "day_plus1": 2460,
            "day_minus1_pct": 5.29,
            "day0_pct": 82.48,
            "day_plus1_pct": 12.23
        },
        "top_improvements": lab_df.head(10).to_dict('records')
    }
    
    json_path = os.path.join(DATA_PATH, 'time_window_absolute_summary.json')
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ 요약 통계 저장: {json_path}")

def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print("🔍 시간 윈도우 분석 - 1,200개 입원 기준 절대값 평가")
    print("="*80)
    
    # 1. 데이터 로드
    day0_wide, window_wide, window_long, stats_day0, stats_window = load_data()
    
    # 2. 절대값 분석
    lab_df = analyze_absolute_values(day0_wide, window_wide, window_long)
    
    # 3. 시각화
    create_absolute_visualization(lab_df)
    
    # 4. 결과 저장
    save_results(lab_df)
    
    print("\n" + "="*80)
    print("✅ 분석 완료!")
    print("="*80)

if __name__ == "__main__":
    main()