#!/usr/bin/env python3
"""
라벨 기반 커버리지 분석
- itemid별이 아닌 라벨별로 데이터 통합하여 분석
- 실제로 비어있는 항목 vs itemid 문제로 비어보이는 항목 구분
- 데이터는 수정하지 않고 분석만 수행
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
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture/analysis_initial_lab_re'
DATA_PATH = os.path.join(BASE_PATH, 'data')
FIGURE_PATH = os.path.join(BASE_PATH, 'figures')

os.makedirs(FIGURE_PATH, exist_ok=True)

def load_data():
    """데이터 로드"""
    print("데이터 로딩 중...")
    
    # 검사 항목 요약
    items_df = pd.read_csv(os.path.join(DATA_PATH, 'lab_items_summary.csv'))
    
    # offset 정보 (실제 측정 데이터)
    offset_df = pd.read_csv(os.path.join(DATA_PATH, 'labs_offset_info.csv'))
    
    # 빈 컬럼 상세
    empty_df = pd.read_csv(os.path.join(DATA_PATH, 'empty_columns_details.csv'))
    
    # 대체 itemid
    alt_df = pd.read_csv(os.path.join(DATA_PATH, 'alternative_itemids.csv'))
    
    print(f"✅ 데이터 로드 완료")
    
    return items_df, offset_df, empty_df, alt_df

def analyze_itemid_vs_label(items_df):
    """itemid별 분석 vs 라벨별 분석 비교"""
    print("\n" + "="*70)
    print("1. ItemID별 vs 라벨별 현황 비교")
    print("="*70)
    
    # 현재 상태 (itemid별)
    total_itemids = len(items_df)
    active_itemids = len(items_df[items_df['has_data'] == True])
    empty_itemids = len(items_df[items_df['has_data'] == False])
    
    print(f"\n📊 현재 상태 (ItemID 기준):")
    print(f"   - 전체 itemid: {total_itemids}개")
    print(f"   - 데이터 있는 itemid: {active_itemids}개 ({active_itemids/total_itemids*100:.1f}%)")
    print(f"   - 빈 itemid: {empty_itemids}개 ({empty_itemids/total_itemids*100:.1f}%)")
    
    # 라벨별 그룹화
    label_groups = items_df.groupby('original_label').agg({
        'itemid': 'count',
        'data_count': 'sum',
        'has_data': 'any'
    }).rename(columns={'itemid': 'itemid_count', 'has_data': 'label_has_data'})
    
    total_labels = len(label_groups)
    active_labels = len(label_groups[label_groups['label_has_data'] == True])
    empty_labels = len(label_groups[label_groups['label_has_data'] == False])
    
    print(f"\n📊 라벨 기준 분석:")
    print(f"   - 고유 라벨: {total_labels}개")
    print(f"   - 데이터 있는 라벨: {active_labels}개 ({active_labels/total_labels*100:.1f}%)")
    print(f"   - 빈 라벨: {empty_labels}개 ({empty_labels/total_labels*100:.1f}%)")
    
    # 개선 가능성
    improvement_potential = active_labels - active_itemids
    print(f"\n💡 개선 가능성:")
    print(f"   - itemid 통합 시 추가 활성화 가능: {empty_itemids - empty_labels}개")
    print(f"   - 실제로 완전히 비어있는 항목: {empty_labels}개 (라벨 기준)")
    
    return label_groups

def analyze_duplicate_labels(items_df, label_groups):
    """중복 라벨 상세 분석"""
    print("\n" + "="*70)
    print("2. 중복 라벨 상세 분석")
    print("="*70)
    
    # 여러 itemid를 가진 라벨
    duplicate_labels = label_groups[label_groups['itemid_count'] > 1].copy()
    duplicate_labels = duplicate_labels.sort_values('itemid_count', ascending=False)
    
    print(f"\n📊 중복 라벨 현황: {len(duplicate_labels)}개 라벨이 여러 itemid 보유")
    
    # 카테고리 분류
    categories = {
        'all_empty': [],      # 모든 itemid가 비어있음
        'partial_data': [],   # 일부 itemid에만 데이터 있음
        'all_active': []      # 모든 itemid에 데이터 있음 (드물 것)
    }
    
    for label, group_data in duplicate_labels.iterrows():
        # 해당 라벨의 모든 itemid 정보
        label_items = items_df[items_df['original_label'] == label]
        
        has_data_count = label_items['has_data'].sum()
        total_count = len(label_items)
        total_data = label_items['data_count'].sum()
        
        if has_data_count == 0:
            categories['all_empty'].append({
                'label': label,
                'itemid_count': total_count,
                'itemids': label_items['itemid'].tolist()
            })
        elif has_data_count == total_count:
            categories['all_active'].append({
                'label': label,
                'itemid_count': total_count,
                'total_data': total_data,
                'itemids': label_items['itemid'].tolist()
            })
        else:
            categories['partial_data'].append({
                'label': label,
                'empty_itemids': label_items[label_items['has_data'] == False]['itemid'].tolist(),
                'active_itemids': label_items[label_items['has_data'] == True]['itemid'].tolist(),
                'total_data': total_data,
                'potential_loss': f"{has_data_count}/{total_count} active"
            })
    
    print(f"\n📊 중복 라벨 분류:")
    print(f"   - 일부만 데이터 있음: {len(categories['partial_data'])}개")
    print(f"   - 모두 비어있음: {len(categories['all_empty'])}개")
    print(f"   - 모두 활성: {len(categories['all_active'])}개")
    
    # 상세 출력
    if categories['partial_data']:
        print(f"\n⚠️ ItemID 문제로 데이터 손실 중인 라벨 (Top 10):")
        for item in categories['partial_data'][:10]:
            print(f"   - {item['label']}: "
                  f"빈 itemid {item['empty_itemids']} → "
                  f"활성 itemid {item['active_itemids']}")
            print(f"     (총 {item['total_data']}건 데이터 존재)")
    
    return categories

def analyze_itemid_patterns(items_df, offset_df):
    """ItemID 번호 패턴 분석"""
    print("\n" + "="*70)
    print("3. ItemID 번호 패턴 분석")
    print("="*70)
    
    # itemid 번호대별 분류
    def classify_itemid(itemid):
        if itemid < 51000:
            return '50000대 (구형)'
        elif itemid < 52000:
            return '51000대 (현재)'
        else:
            return '52000대 (신형)'
    
    items_df['itemid_range'] = items_df['itemid'].apply(classify_itemid)
    
    # 번호대별 통계
    range_stats = items_df.groupby('itemid_range').agg({
        'itemid': 'count',
        'has_data': 'sum',
        'data_count': 'sum'
    }).rename(columns={'itemid': 'total_items', 'has_data': 'active_items'})
    
    print("\n📊 ItemID 번호대별 분포:")
    for range_name, stats in range_stats.iterrows():
        active_pct = stats['active_items'] / stats['total_items'] * 100
        print(f"   - {range_name}: {stats['total_items']}개 "
              f"(활성 {stats['active_items']}개, {active_pct:.1f}%)")
        if stats['data_count'] > 0:
            print(f"     데이터: {stats['data_count']:.0f}건")
    
    # 실제 사용 패턴 (offset_df 기반)
    offset_itemid_counts = offset_df['itemid'].value_counts()
    
    # 가장 많이 사용되는 itemid Top 10
    print("\n📊 가장 많이 사용되는 ItemID Top 10:")
    for itemid, count in offset_itemid_counts.head(10).items():
        item_info = items_df[items_df['itemid'] == itemid]
        if not item_info.empty:
            label = item_info.iloc[0]['original_label']
            range_class = classify_itemid(itemid)
            print(f"   - {itemid} ({range_class}): {label} - {count}건")
    
    return range_stats

def find_real_empty_labels(label_groups, items_df):
    """실제로 완전히 비어있는 라벨 찾기"""
    print("\n" + "="*70)
    print("4. 실제로 완전히 비어있는 검사 항목")
    print("="*70)
    
    # 데이터가 전혀 없는 라벨
    empty_labels = label_groups[label_groups['label_has_data'] == False]
    
    print(f"\n📊 완전히 비어있는 라벨: {len(empty_labels)}개")
    
    # 원인별 분류
    real_empty = {
        'special_tests': [],
        'blood_gas': [],
        'other_fluid': [],
        'unknown': []
    }
    
    for label, _ in empty_labels.iterrows():
        # 해당 라벨의 모든 itemid
        label_items = items_df[items_df['original_label'] == label]
        
        # 카테고리 확인
        categories = label_items['category'].unique()
        fluids = label_items['fluid'].unique()
        
        # 분류
        if 'COVID' in label or 'CA 19-9' in label or 'INR' in label:
            real_empty['special_tests'].append(label)
        elif 'Blood Gas' in str(categories[0]):
            real_empty['blood_gas'].append(label)
        elif 'Other Body Fluid' in str(fluids[0]) or 'Fluid' in str(fluids[0]):
            real_empty['other_fluid'].append(label)
        else:
            real_empty['unknown'].append(label)
    
    print("\n📊 실제 빈 라벨 원인:")
    print(f"   - 특수 검사: {len(real_empty['special_tests'])}개")
    if real_empty['special_tests']:
        for test in real_empty['special_tests'][:5]:
            print(f"     • {test}")
    
    print(f"\n   - Blood Gas 관련: {len(real_empty['blood_gas'])}개")
    if real_empty['blood_gas']:
        for test in real_empty['blood_gas'][:5]:
            print(f"     • {test}")
    
    print(f"\n   - 기타 체액: {len(real_empty['other_fluid'])}개")
    if real_empty['other_fluid']:
        for test in real_empty['other_fluid'][:5]:
            print(f"     • {test}")
    
    print(f"\n   - 원인 불명: {len(real_empty['unknown'])}개")
    
    return real_empty

def create_analysis_visualizations(items_df, label_groups, range_stats, categories):
    """분석 시각화"""
    print("\n" + "="*70)
    print("5. 시각화 생성")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. ItemID vs 라벨 기준 비교
    ax1 = axes[0, 0]
    comparison_data = {
        'ItemID 기준': [48, 39],  # 활성, 비활성
        '라벨 기준': [
            len(label_groups[label_groups['label_has_data'] == True]),
            len(label_groups[label_groups['label_has_data'] == False])
        ]
    }
    
    x = np.arange(len(['활성', '비활성']))
    width = 0.35
    
    for i, (key, values) in enumerate(comparison_data.items()):
        ax1.bar(x + i*width, values, width, label=key)
    
    ax1.set_xlabel('상태')
    ax1.set_ylabel('개수')
    ax1.set_title('ItemID별 vs 라벨별 커버리지 비교')
    ax1.set_xticks(x + width/2)
    ax1.set_xticklabels(['활성', '비활성'])
    ax1.legend()
    
    # 값 표시
    for i, (key, values) in enumerate(comparison_data.items()):
        for j, v in enumerate(values):
            ax1.text(j + i*width, v, str(v), ha='center', va='bottom')
    
    # 2. ItemID 번호대별 활성률
    ax2 = axes[0, 1]
    range_names = range_stats.index
    active_pcts = (range_stats['active_items'] / range_stats['total_items'] * 100).values
    
    bars = ax2.bar(range(len(range_names)), active_pcts, 
                   color=['#ff9999', '#66b3ff', '#99ff99'])
    ax2.set_xticks(range(len(range_names)))
    ax2.set_xticklabels(range_names, rotation=45, ha='right')
    ax2.set_ylabel('활성 비율 (%)')
    ax2.set_title('ItemID 번호대별 데이터 활성률')
    ax2.set_ylim(0, 100)
    
    # 값 표시
    for bar, pct in zip(bars, active_pcts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{pct:.1f}%', ha='center', va='bottom')
    
    # 3. 중복 라벨 분류
    ax3 = axes[1, 0]
    dup_categories = {
        '일부 활성': len(categories['partial_data']),
        '모두 비활성': len(categories['all_empty']),
        '모두 활성': len(categories['all_active'])
    }
    
    colors = ['#ffd700', '#ff6b6b', '#4ecdc4']
    wedges, texts, autotexts = ax3.pie(dup_categories.values(), 
                                        labels=dup_categories.keys(),
                                        colors=colors,
                                        autopct=lambda pct: f'{int(pct*sum(dup_categories.values())/100)}개\n({pct:.1f}%)',
                                        startangle=90)
    ax3.set_title('중복 라벨 데이터 상태 분포')
    
    # 4. 개선 가능성
    ax4 = axes[1, 1]
    
    # 현재 vs 개선 후
    current_active = len(items_df[items_df['has_data'] == True])
    label_based_active = len(label_groups[label_groups['label_has_data'] == True])
    
    improvement_data = {
        '현재\n(ItemID별)': [current_active, 87-current_active],
        '라벨 통합 시': [label_based_active, len(label_groups)-label_based_active]
    }
    
    x_pos = np.arange(len(improvement_data))
    bottoms = [0, 0]
    colors_stack = ['#2ca02c', '#ff7f0e']
    labels = ['활성', '비활성']
    
    for i, label in enumerate(labels):
        values = [improvement_data[k][i] for k in improvement_data.keys()]
        bars = ax4.bar(x_pos, values, bottom=bottoms, 
                      label=label, color=colors_stack[i])
        
        # 값 표시
        for j, (v, b) in enumerate(zip(values, bottoms)):
            if v > 0:
                ax4.text(j, b + v/2, f'{v}', ha='center', va='center', fontweight='bold')
        
        bottoms = [b + v for b, v in zip(bottoms, values)]
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(improvement_data.keys())
    ax4.set_ylabel('검사 항목 수')
    ax4.set_title('라벨 통합 시 개선 효과')
    ax4.legend()
    ax4.set_ylim(0, 90)
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'label_based_analysis.png'), 
                dpi=150, bbox_inches='tight')
    print(f"✅ 시각화 저장: label_based_analysis.png")
    
    plt.close()

def save_analysis_results(label_groups, categories, real_empty):
    """분석 결과 저장"""
    print("\n" + "="*70)
    print("6. 분석 결과 저장")
    print("="*70)
    
    # 라벨별 통계 저장
    label_stats = label_groups.reset_index()
    label_stats.to_csv(os.path.join(DATA_PATH, 'label_based_statistics.csv'), index=False)
    
    # 개선 가능 항목 저장
    improvable_items = []
    for item in categories['partial_data']:
        improvable_items.append({
            'label': item['label'],
            'empty_itemids': ';'.join(map(str, item['empty_itemids'])),
            'active_itemids': ';'.join(map(str, item['active_itemids'])),
            'total_data': item['total_data']
        })
    
    if improvable_items:
        improvable_df = pd.DataFrame(improvable_items)
        improvable_df.to_csv(os.path.join(DATA_PATH, 'improvable_items.csv'), index=False)
    
    # 분석 요약 JSON
    summary = {
        'analysis_type': 'label_based_coverage',
        'itemid_analysis': {
            'total': 87,
            'active': 48,
            'empty': 39,
            'coverage_pct': 55.2
        },
        'label_analysis': {
            'total': len(label_groups),
            'active': len(label_groups[label_groups['label_has_data'] == True]),
            'empty': len(label_groups[label_groups['label_has_data'] == False]),
            'coverage_pct': len(label_groups[label_groups['label_has_data'] == True]) / len(label_groups) * 100
        },
        'duplicate_labels': {
            'total': len(label_groups[label_groups['itemid_count'] > 1]),
            'partial_data': len(categories['partial_data']),
            'all_empty': len(categories['all_empty']),
            'all_active': len(categories['all_active'])
        },
        'real_empty': {
            'total': len(label_groups[label_groups['label_has_data'] == False]),
            'special_tests': len(real_empty['special_tests']),
            'blood_gas': len(real_empty['blood_gas']),
            'other_fluid': len(real_empty['other_fluid']),
            'unknown': len(real_empty['unknown'])
        },
        'improvement_potential': {
            'false_empty_itemids': 39 - len(label_groups[label_groups['label_has_data'] == False]),
            'description': 'ItemID 통합 시 활성화 가능한 항목 수'
        }
    }
    
    with open(os.path.join(DATA_PATH, 'label_analysis_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 결과 파일 저장 완료")
    print(f"   - label_based_statistics.csv")
    print(f"   - improvable_items.csv")
    print(f"   - label_analysis_summary.json")
    
    return summary

def main():
    """메인 실행 함수"""
    print("\n" + "🔬 " * 20)
    print(" 라벨 기반 커버리지 분석 (오류 분석)")
    print("🔬 " * 20)
    
    # 데이터 로드
    items_df, offset_df, empty_df, alt_df = load_data()
    
    # ItemID vs 라벨 분석
    label_groups = analyze_itemid_vs_label(items_df)
    
    # 중복 라벨 분석
    categories = analyze_duplicate_labels(items_df, label_groups)
    
    # ItemID 패턴 분석
    range_stats = analyze_itemid_patterns(items_df, offset_df)
    
    # 실제 빈 라벨 찾기
    real_empty = find_real_empty_labels(label_groups, items_df)
    
    # 시각화
    create_analysis_visualizations(items_df, label_groups, range_stats, categories)
    
    # 결과 저장
    summary = save_analysis_results(label_groups, categories, real_empty)
    
    print("\n" + "="*70)
    print("✅ 라벨 기반 분석 완료!")
    print("="*70)
    print(f"\n📊 핵심 발견:")
    print(f"   - ItemID 기준: 87개 중 48개 활성 (55.2%)")
    print(f"   - 라벨 기준: {summary['label_analysis']['total']}개 중 "
          f"{summary['label_analysis']['active']}개 활성 ({summary['label_analysis']['coverage_pct']:.1f}%)")
    print(f"   - 거짓 빈 항목: {summary['improvement_potential']['false_empty_itemids']}개 "
          f"(itemid 문제)")
    print(f"   - 진짜 빈 항목: {summary['real_empty']['total']}개 (라벨 기준)")

if __name__ == "__main__":
    main()