#!/usr/bin/env python3
"""
Missing Pattern 시각화
- 통합된 데이터 기반
- 100명 샘플, 70개 검사를 3개 히트맵으로 분할
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import os

# 한글 폰트 설정
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture/analysis_initial_lab_re'
DATA_PATH = os.path.join(BASE_PATH, 'data')
FIGURE_PATH = os.path.join(BASE_PATH, 'figures')

os.makedirs(FIGURE_PATH, exist_ok=True)

def load_data():
    """통합된 데이터 로드"""
    print("데이터 로딩 중...")
    
    # 통합된 Wide format 데이터
    merged_wide = pd.read_csv(os.path.join(DATA_PATH, 'labs_initial_merged_wide.csv'))
    
    # 메타 컬럼 제외
    meta_cols = ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 
                 'deathtime', 'admit_date']
    lab_cols = [col for col in merged_wide.columns if col not in meta_cols]
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 전체 입원: {len(merged_wide):,}개")
    print(f"   - 검사 항목: {len(lab_cols)}개")
    
    return merged_wide, lab_cols

def sample_data(merged_wide, n_samples=100):
    """100명 랜덤 샘플링"""
    print(f"\n📊 {n_samples}명 랜덤 샘플링...")
    
    # 랜덤 샘플 (재현 가능하도록 seed 고정)
    np.random.seed(42)
    sample_indices = np.random.choice(len(merged_wide), n_samples, replace=False)
    sample_df = merged_wide.iloc[sample_indices].copy()
    
    # 샘플 정보
    mortality_rate = sample_df['hospital_expire_flag'].mean()
    print(f"   - 샘플 사망률: {mortality_rate:.1%}")
    
    return sample_df

def calculate_missing_rates(merged_wide, lab_cols):
    """검사별 결측률 계산"""
    print("\n📊 검사별 결측률 계산...")
    
    missing_rates = {}
    for col in lab_cols:
        missing_rate = merged_wide[col].isna().sum() / len(merged_wide) * 100
        missing_rates[col] = missing_rate
    
    # 결측률 기준 정렬
    sorted_labs = sorted(missing_rates.items(), key=lambda x: x[1])
    
    print(f"   - 평균 결측률: {np.mean(list(missing_rates.values())):.1f}%")
    print(f"   - 최소 결측률: {min(missing_rates.values()):.1f}%")
    print(f"   - 최대 결측률: {max(missing_rates.values()):.1f}%")
    
    return sorted_labs

def create_missing_heatmaps(sample_df, sorted_labs):
    """3개의 Missing Pattern 히트맵 생성"""
    print("\n📊 Missing Pattern 히트맵 생성...")
    
    # 검사를 3개 그룹으로 분할
    n_labs = len(sorted_labs)
    group_size = n_labs // 3
    
    groups = [
        sorted_labs[:group_size+1],  # 첫 번째 그룹 (결측률 낮음)
        sorted_labs[group_size+1:2*group_size+1],  # 두 번째 그룹
        sorted_labs[2*group_size+1:]  # 세 번째 그룹 (결측률 높음)
    ]
    
    # 입원을 총 검사 수로 정렬
    lab_cols_in_sample = [lab for lab, _ in sorted_labs]
    test_counts = (~sample_df[lab_cols_in_sample].isna()).sum(axis=1)
    sample_df_sorted = sample_df.iloc[test_counts.argsort()[::-1]]
    
    # 각 그룹별 히트맵 생성
    for i, group in enumerate(groups, 1):
        if not group:
            continue
            
        print(f"\n   히트맵 {i} 생성 중...")
        
        # 해당 그룹의 검사 컬럼만 선택
        group_labs = [lab for lab, _ in group]
        
        # Missing 매트릭스 생성 (0: missing, 1: present)
        missing_matrix = (~sample_df_sorted[group_labs].isna()).astype(int)
        
        # 시각화
        fig, ax = plt.subplots(figsize=(20, 8))
        
        # 히트맵
        sns.heatmap(missing_matrix.T, 
                   cmap=['white', 'steelblue'],
                   cbar_kws={'label': '데이터 유무 (0: 없음, 1: 있음)'},
                   xticklabels=False,  # 입원 ID는 너무 많아서 생략
                   yticklabels=[lab[:30] for lab in group_labs],  # 검사명 (30자 제한)
                   ax=ax)
        
        # 제목 및 라벨
        missing_rates_text = f"평균 결측률: {np.mean([rate for _, rate in group]):.1f}%"
        ax.set_title(f'Missing Pattern 히트맵 {i} (검사 {len(group)}개)\n{missing_rates_text}', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('입원 (100명 샘플)', fontsize=12)
        ax.set_ylabel('검사 항목', fontsize=12)
        
        # Y축 라벨 크기 조정
        ax.tick_params(axis='y', labelsize=8)
        
        # 그리드 추가
        ax.set_xticks(np.arange(0, len(sample_df_sorted), 10))
        ax.set_xticklabels(np.arange(0, len(sample_df_sorted), 10))
        
        plt.tight_layout()
        
        # 저장
        filename = f'missing_pattern_heatmap_{i}.png'
        plt.savefig(os.path.join(FIGURE_PATH, filename), dpi=150, bbox_inches='tight')
        print(f"   ✅ {filename} 저장 완료")
        
        plt.close()
    
    return groups

def create_summary_statistics(merged_wide, sample_df, sorted_labs):
    """종합 통계 시각화"""
    print("\n📊 종합 통계 시각화 생성...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 입원별 검사 수 분포 (샘플 100명)
    ax1 = axes[0, 0]
    lab_cols = [lab for lab, _ in sorted_labs]
    test_counts = (~sample_df[lab_cols].isna()).sum(axis=1)
    
    ax1.hist(test_counts, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(test_counts.mean(), color='red', linestyle='--', 
               label=f'평균: {test_counts.mean():.1f}개')
    ax1.set_xlabel('검사 수')
    ax1.set_ylabel('입원 수')
    ax1.set_title(f'입원별 검사 수 분포 (n={len(sample_df)})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 검사별 결측률 (전체 70개)
    ax2 = axes[0, 1]
    labs = [lab[:20] for lab, _ in sorted_labs]
    rates = [rate for _, rate in sorted_labs]
    
    # 결측률 구간별 색상
    colors = ['green' if r < 30 else 'yellow' if r < 70 else 'red' for r in rates]
    
    # 막대 그래프 (너무 많아서 상위/하위 15개씩만)
    top_15 = sorted_labs[:15]
    bottom_15 = sorted_labs[-15:]
    selected = top_15 + bottom_15
    
    selected_labs = [lab[:15] for lab, _ in selected]
    selected_rates = [rate for _, rate in selected]
    selected_colors = ['green' if r < 30 else 'yellow' if r < 70 else 'red' for r in selected_rates]
    
    bars = ax2.barh(range(len(selected)), selected_rates, color=selected_colors)
    ax2.set_yticks(range(len(selected)))
    ax2.set_yticklabels(selected_labs, fontsize=8)
    ax2.set_xlabel('결측률 (%)')
    ax2.set_title('검사별 결측률 (상위 15개 + 하위 15개)')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 중간 구분선
    ax2.axhline(y=14.5, color='black', linestyle='--', alpha=0.5)
    ax2.text(50, 14.5, '···', ha='center', va='center', fontsize=16)
    
    # 3. 결측률 분포
    ax3 = axes[1, 0]
    ax3.hist(rates, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(np.mean(rates), color='red', linestyle='--', 
               label=f'평균: {np.mean(rates):.1f}%')
    ax3.set_xlabel('결측률 (%)')
    ax3.set_ylabel('검사 항목 수')
    ax3.set_title('검사별 결측률 분포')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 요약 통계
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # 전체 통계
    total_missing_rate = np.mean(rates)
    n_complete = len([r for r in rates if r == 0])
    n_rare = len([r for r in rates if r > 90])
    n_common = len([r for r in rates if r < 10])
    
    summary_text = f"""
    📊 Missing Value 요약 통계
    
    【전체 현황】
    • 총 검사 항목: {len(sorted_labs)}개
    • 평균 결측률: {total_missing_rate:.1f}%
    • 완전 데이터: {n_complete}개 항목
    
    【결측률 구간별】
    • 0-10% (흔한 검사): {n_common}개
    • 10-50% (보통): {len([r for r in rates if 10 <= r < 50])}개
    • 50-90% (드문 검사): {len([r for r in rates if 50 <= r < 90])}개
    • 90-100% (매우 드문): {n_rare}개
    
    【샘플 통계 (n=100)】
    • 평균 검사 수: {test_counts.mean():.1f}개
    • 중앙값: {test_counts.median():.0f}개
    • 범위: {test_counts.min()}-{test_counts.max()}개
    """
    
    ax4.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center',
            fontfamily='monospace')
    
    plt.suptitle('Missing Value 종합 분석', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # 저장
    plt.savefig(os.path.join(FIGURE_PATH, 'missing_summary_stats.png'), 
                dpi=150, bbox_inches='tight')
    print("   ✅ missing_summary_stats.png 저장 완료")
    
    plt.close()

def save_missing_info(sorted_labs, groups):
    """Missing 정보 저장"""
    print("\n📊 Missing 정보 저장...")
    
    # 검사별 결측률 CSV
    missing_df = pd.DataFrame(sorted_labs, columns=['test_name', 'missing_rate'])
    missing_df['group'] = 0
    
    # 그룹 정보 추가
    for i, group in enumerate(groups, 1):
        for lab, _ in group:
            missing_df.loc[missing_df['test_name'] == lab, 'group'] = i
    
    missing_df.to_csv(os.path.join(DATA_PATH, 'missing_rates_by_test.csv'), index=False)
    print("   ✅ missing_rates_by_test.csv 저장 완료")

def main():
    """메인 실행 함수"""
    print("\n" + "🔍 " * 20)
    print(" Missing Pattern 시각화")
    print("🔍 " * 20)
    
    # 데이터 로드
    merged_wide, lab_cols = load_data()
    
    # 100명 샘플링
    sample_df = sample_data(merged_wide, n_samples=100)
    
    # 검사별 결측률 계산
    sorted_labs = calculate_missing_rates(merged_wide, lab_cols)
    
    # Missing Pattern 히트맵 생성 (3개)
    groups = create_missing_heatmaps(sample_df, sorted_labs)
    
    # 종합 통계 시각화
    create_summary_statistics(merged_wide, sample_df, sorted_labs)
    
    # 정보 저장
    save_missing_info(sorted_labs, groups)
    
    print("\n" + "="*70)
    print("✅ Missing Pattern 시각화 완료!")
    print("="*70)
    print(f"\n생성된 파일:")
    print(f"   - missing_pattern_heatmap_1.png (결측률 낮은 검사)")
    print(f"   - missing_pattern_heatmap_2.png (중간 검사)")
    print(f"   - missing_pattern_heatmap_3.png (결측률 높은 검사)")
    print(f"   - missing_summary_stats.png (종합 통계)")
    print(f"   - missing_rates_by_test.csv (검사별 결측률)")

if __name__ == "__main__":
    main()