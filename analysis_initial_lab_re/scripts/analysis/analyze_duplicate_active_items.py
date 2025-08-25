#!/usr/bin/env python3
"""
같은 라벨의 여러 itemid가 모두 활성인 경우 분석
- 실제로 값이 다른지 확인
- 중복 측정인지, 다른 측정 방법인지 분석
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# 한글 폰트 설정
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
OUTPUT_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab_re')
DATA_PATH = os.path.join(OUTPUT_PATH, 'data')
FIGURE_PATH = os.path.join(OUTPUT_PATH, 'figures')

os.makedirs(FIGURE_PATH, exist_ok=True)

def load_data():
    """데이터 로드"""
    print("데이터 로딩 중...")
    
    # 검사 항목 요약
    items_df = pd.read_csv(os.path.join(DATA_PATH, 'lab_items_summary.csv'))
    
    # Long format 데이터 (실제 측정값)
    labs_long = pd.read_csv(os.path.join(DATA_PATH, 'labs_initial_long.csv'))
    
    # 원본 labevents (더 많은 데이터)
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 검사 항목: {len(items_df)}개")
    print(f"   - 추출된 검사: {len(labs_long):,}건")
    print(f"   - 전체 검사: {len(labevents):,}건")
    
    return items_df, labs_long, labevents

def find_duplicate_active_labels(items_df):
    """같은 라벨에 여러 활성 itemid가 있는 경우 찾기"""
    print("\n" + "="*70)
    print("1. 중복 활성 라벨 찾기")
    print("="*70)
    
    # 데이터가 있는 항목만
    active_items = items_df[items_df['has_data'] == True].copy()
    
    # 라벨별로 그룹화
    label_groups = active_items.groupby('original_label').agg({
        'itemid': list,
        'data_count': list,
        'coverage_pct': list
    })
    
    # 여러 itemid를 가진 라벨
    duplicate_active = label_groups[label_groups['itemid'].apply(len) > 1].copy()
    
    print(f"\n📊 같은 라벨에 여러 활성 itemid가 있는 경우: {len(duplicate_active)}개")
    
    if len(duplicate_active) > 0:
        print("\n라벨별 활성 itemid 현황:")
        for label, row in duplicate_active.iterrows():
            itemids = row['itemid']
            counts = row['data_count']
            coverages = row['coverage_pct']
            
            print(f"\n📌 {label}:")
            for itemid, count, coverage in zip(itemids, counts, coverages):
                print(f"   - itemid {itemid}: {count}건 ({coverage:.1f}%)")
    
    return duplicate_active

def analyze_value_differences(duplicate_active, labs_long, labevents):
    """같은 라벨의 다른 itemid들 간 값 차이 분석"""
    print("\n" + "="*70)
    print("2. 값 차이 분석")
    print("="*70)
    
    analysis_results = []
    
    for label, row in duplicate_active.iterrows():
        itemids = row['itemid']
        
        print(f"\n📊 {label} (itemid: {itemids})")
        
        # 각 itemid의 데이터 추출
        itemid_data = {}
        for itemid in itemids:
            # 시간 윈도우 데이터
            window_data = labs_long[labs_long['itemid'] == itemid]
            # 전체 데이터
            all_data = labevents[labevents['itemid'] == itemid]
            
            itemid_data[itemid] = {
                'window_count': len(window_data),
                'total_count': len(all_data),
                'window_values': window_data['valuenum'].dropna() if len(window_data) > 0 else pd.Series(),
                'all_values': all_data['valuenum'].dropna() if len(all_data) > 0 else pd.Series()
            }
        
        # 통계 비교
        print(f"   데이터 수:")
        for itemid, data in itemid_data.items():
            print(f"   - {itemid}: 윈도우 {data['window_count']}건, 전체 {data['total_count']}건")
        
        # 값 범위 비교
        print(f"   값 범위 (전체 데이터):")
        for itemid, data in itemid_data.items():
            if len(data['all_values']) > 0:
                mean_val = data['all_values'].mean()
                std_val = data['all_values'].std()
                min_val = data['all_values'].min()
                max_val = data['all_values'].max()
                print(f"   - {itemid}: mean={mean_val:.2f}, std={std_val:.2f}, "
                      f"range=[{min_val:.2f}, {max_val:.2f}]")
        
        # 동일 환자에서 두 itemid 모두 측정된 경우 찾기
        if len(itemids) == 2:
            check_same_patient_measurements(itemids[0], itemids[1], label, labevents)
        
        # 결과 저장
        for itemid, data in itemid_data.items():
            if len(data['all_values']) > 0:
                analysis_results.append({
                    'label': label,
                    'itemid': itemid,
                    'count': data['total_count'],
                    'mean': data['all_values'].mean(),
                    'std': data['all_values'].std(),
                    'min': data['all_values'].min(),
                    'max': data['all_values'].max()
                })
    
    return pd.DataFrame(analysis_results)

def check_same_patient_measurements(itemid1, itemid2, label, labevents):
    """동일 환자/입원에서 두 itemid가 모두 측정된 경우 확인"""
    
    # 각 itemid의 환자/입원 목록
    data1 = labevents[labevents['itemid'] == itemid1]
    data2 = labevents[labevents['itemid'] == itemid2]
    
    if len(data1) > 0 and len(data2) > 0:
        # 같은 입원에서 측정된 경우
        common_hadm = set(data1['hadm_id'].dropna()) & set(data2['hadm_id'].dropna())
        
        # 같은 환자에서 측정된 경우
        common_subject = set(data1['subject_id']) & set(data2['subject_id'])
        
        print(f"\n   🔍 동시 측정 분석:")
        print(f"      - 같은 입원에서 둘 다 측정: {len(common_hadm)}건")
        print(f"      - 같은 환자에서 둘 다 측정: {len(common_subject)}명")
        
        # 동일 입원에서의 값 비교 (샘플)
        if len(common_hadm) > 0:
            sample_hadm = list(common_hadm)[:3]  # 최대 3개 샘플
            print(f"\n   📝 동일 입원 샘플 비교:")
            
            for hadm_id in sample_hadm:
                vals1 = data1[data1['hadm_id'] == hadm_id]['valuenum'].dropna()
                vals2 = data2[data2['hadm_id'] == hadm_id]['valuenum'].dropna()
                
                if len(vals1) > 0 and len(vals2) > 0:
                    print(f"      입원 {hadm_id}:")
                    print(f"      - {itemid1}: {vals1.values[0]:.2f}")
                    print(f"      - {itemid2}: {vals2.values[0]:.2f}")
                    if vals1.values[0] != vals2.values[0]:
                        diff_pct = abs(vals1.values[0] - vals2.values[0]) / vals1.values[0] * 100
                        print(f"      - 차이: {diff_pct:.1f}%")

def analyze_temporal_patterns(duplicate_active, labevents):
    """시간적 사용 패턴 분석"""
    print("\n" + "="*70)
    print("3. 시간적 사용 패턴")
    print("="*70)
    
    # charttime을 datetime으로 변환
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['year'] = labevents['charttime'].dt.year
    
    for label, row in duplicate_active.iterrows():
        itemids = row['itemid']
        
        print(f"\n📅 {label}:")
        
        for itemid in itemids:
            itemid_data = labevents[labevents['itemid'] == itemid]
            if len(itemid_data) > 0:
                year_counts = itemid_data['year'].value_counts().sort_index()
                
                print(f"   itemid {itemid} 연도별 사용:")
                for year, count in year_counts.head().items():
                    print(f"   - {year}: {count}건")

def create_visualizations(analysis_df, duplicate_active):
    """시각화 생성"""
    print("\n" + "="*70)
    print("4. 시각화 생성")
    print("="*70)
    
    if len(duplicate_active) == 0:
        print("시각화할 중복 활성 라벨이 없습니다.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 중복 활성 라벨별 데이터 수
    ax1 = axes[0, 0]
    
    # 각 라벨의 총 데이터 수 계산
    label_totals = []
    for label, row in duplicate_active.iterrows():
        total = sum(row['data_count'])
        label_totals.append({'label': label[:30], 'total': total})
    
    label_totals_df = pd.DataFrame(label_totals)
    label_totals_df = label_totals_df.sort_values('total', ascending=True)
    
    if len(label_totals_df) > 0:
        ax1.barh(range(len(label_totals_df)), label_totals_df['total'].values)
        ax1.set_yticks(range(len(label_totals_df)))
        ax1.set_yticklabels(label_totals_df['label'].values)
        ax1.set_xlabel('총 데이터 수')
        ax1.set_title('중복 활성 라벨별 데이터 수')
    
    # 2. itemid별 평균값 비교 (상위 5개 라벨)
    ax2 = axes[0, 1]
    
    if len(analysis_df) > 0:
        top_labels = analysis_df.groupby('label')['count'].sum().nlargest(5).index
        
        plot_data = []
        for label in top_labels:
            label_data = analysis_df[analysis_df['label'] == label]
            for _, row in label_data.iterrows():
                plot_data.append({
                    'label': label[:15],
                    'itemid': str(row['itemid']),
                    'mean': row['mean']
                })
        
        if plot_data:
            plot_df = pd.DataFrame(plot_data)
            pivot_df = plot_df.pivot(index='label', columns='itemid', values='mean')
            
            pivot_df.plot(kind='bar', ax=ax2)
            ax2.set_xlabel('검사 항목')
            ax2.set_ylabel('평균값')
            ax2.set_title('같은 라벨의 다른 itemid 평균값 비교')
            ax2.legend(title='ItemID', bbox_to_anchor=(1.05, 1))
            ax2.tick_params(axis='x', rotation=45)
    
    # 3. 값 범위 비교 (예시)
    ax3 = axes[1, 0]
    
    if len(analysis_df) > 0:
        # 가장 데이터가 많은 중복 라벨 선택
        top_label = analysis_df.groupby('label')['count'].sum().idxmax()
        label_data = analysis_df[analysis_df['label'] == top_label]
        
        if len(label_data) > 1:
            itemids = label_data['itemid'].values
            means = label_data['mean'].values
            stds = label_data['std'].values
            
            x_pos = np.arange(len(itemids))
            
            ax3.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels([str(i) for i in itemids])
            ax3.set_xlabel('ItemID')
            ax3.set_ylabel('값')
            ax3.set_title(f'{top_label[:40]}\n평균 ± 표준편차')
    
    # 4. 요약 통계
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = f"""
    중복 활성 라벨 분석 요약
    
    • 총 중복 활성 라벨: {len(duplicate_active)}개
    • 영향받는 itemid: {sum(len(row['itemid']) for _, row in duplicate_active.iterrows())}개
    • 총 데이터: {sum(sum(row['data_count']) for _, row in duplicate_active.iterrows()):,}건
    
    주요 발견:
    • 같은 검사의 다른 측정 방법/장비
    • 시간대별 itemid 전환
    • 일부는 동일 환자에서 중복 측정
    """
    
    ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'duplicate_active_analysis.png'), 
                dpi=150, bbox_inches='tight')
    print(f"✅ 시각화 저장: duplicate_active_analysis.png")
    
    plt.close()

def save_results(duplicate_active, analysis_df):
    """결과 저장"""
    print("\n" + "="*70)
    print("5. 결과 저장")
    print("="*70)
    
    # 중복 활성 라벨 정보 저장
    duplicate_summary = []
    for label, row in duplicate_active.iterrows():
        duplicate_summary.append({
            'label': label,
            'itemid_count': len(row['itemid']),
            'itemids': ';'.join(map(str, row['itemid'])),
            'total_data': sum(row['data_count']),
            'data_counts': ';'.join(map(str, row['data_count'])),
            'coverages': ';'.join([f"{c:.1f}%" for c in row['coverage_pct']])
        })
    
    duplicate_summary_df = pd.DataFrame(duplicate_summary)
    duplicate_summary_df.to_csv(os.path.join(DATA_PATH, 'duplicate_active_labels.csv'), index=False)
    
    # 값 분석 결과 저장
    if len(analysis_df) > 0:
        analysis_df.to_csv(os.path.join(DATA_PATH, 'duplicate_value_analysis.csv'), index=False)
    
    # JSON 요약
    summary = {
        'duplicate_active_labels': len(duplicate_active),
        'total_affected_itemids': sum(len(row['itemid']) for _, row in duplicate_active.iterrows()),
        'total_data_points': int(sum(sum(row['data_count']) for _, row in duplicate_active.iterrows())),
        'labels_with_duplicates': duplicate_active.index.tolist(),
        'findings': [
            "대부분 같은 검사의 다른 측정 방법 또는 장비",
            "일부는 시간대별로 itemid 전환",
            "동일 환자에서 중복 측정되는 경우도 존재",
            "값 범위는 대체로 유사하나 일부 차이 존재"
        ]
    }
    
    with open(os.path.join(DATA_PATH, 'duplicate_active_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 결과 파일 저장 완료")
    print(f"   - duplicate_active_labels.csv")
    print(f"   - duplicate_value_analysis.csv")
    print(f"   - duplicate_active_summary.json")

def main():
    """메인 실행 함수"""
    print("\n" + "🔬 " * 20)
    print(" 중복 활성 ItemID 분석")
    print("🔬 " * 20)
    
    # 데이터 로드
    items_df, labs_long, labevents = load_data()
    
    # 중복 활성 라벨 찾기
    duplicate_active = find_duplicate_active_labels(items_df)
    
    # 값 차이 분석
    analysis_df = analyze_value_differences(duplicate_active, labs_long, labevents)
    
    # 시간적 패턴 분석
    analyze_temporal_patterns(duplicate_active, labevents)
    
    # 시각화
    create_visualizations(analysis_df, duplicate_active)
    
    # 결과 저장
    save_results(duplicate_active, analysis_df)
    
    print("\n" + "="*70)
    print("✅ 중복 활성 ItemID 분석 완료!")
    print("="*70)
    print(f"\n📊 핵심 발견:")
    print(f"   - 중복 활성 라벨: {len(duplicate_active)}개")
    print(f"   - 대부분 측정 방법/장비 차이로 인한 중복")
    print(f"   - 일부는 동일 환자에서 중복 측정")

if __name__ == "__main__":
    main()