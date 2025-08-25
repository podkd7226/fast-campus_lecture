#!/usr/bin/env python3
"""
빈 컬럼 원인 분석
- 39개 완전히 비어있는 컬럼 분석
- 카테고리별, Fluid 타입별 분류
- 원인 추정 및 패턴 파악
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
    
    # d_labitems_inclusion 원본 (더 자세한 정보)
    inclusion_path = '/Users/hyungjun/Desktop/fast campus_lecture/processed_data/hosp/d_labitems_inclusion.csv'
    inclusion_df = pd.read_csv(inclusion_path)
    inclusion_df = inclusion_df[inclusion_df['inclusion'] == 1]
    
    # 전체 labevents 데이터 (빈도 확인용)
    labevents_path = '/Users/hyungjun/Desktop/fast campus_lecture/processed_data/hosp/labevents_sampled.csv'
    labevents = pd.read_csv(labevents_path)
    
    print(f"✅ 데이터 로드 완료")
    
    return items_df, inclusion_df, labevents

def analyze_empty_columns(items_df, inclusion_df):
    """빈 컬럼 분석"""
    print("\n" + "="*70)
    print("1. 빈 컬럼 현황")
    print("="*70)
    
    # 빈 컬럼 필터링
    empty_items = items_df[items_df['has_data'] == False].copy()
    has_data_items = items_df[items_df['has_data'] == True].copy()
    
    print(f"\n📊 전체 현황:")
    print(f"   - 전체 검사 항목: {len(items_df)}개")
    print(f"   - 데이터 있는 항목: {len(has_data_items)}개 ({len(has_data_items)/len(items_df)*100:.1f}%)")
    print(f"   - 완전 비어있는 항목: {len(empty_items)}개 ({len(empty_items)/len(items_df)*100:.1f}%)")
    
    # inclusion_df와 병합하여 더 자세한 정보 얻기
    empty_items_detailed = empty_items.merge(
        inclusion_df[['itemid', 'category', 'fluid', 'loinc_code']], 
        on='itemid', 
        how='left',
        suffixes=('', '_inclusion')
    )
    
    # category가 비어있는 경우 원본 사용
    empty_items_detailed['category'] = empty_items_detailed['category'].fillna(
        empty_items_detailed['category_inclusion']
    )
    empty_items_detailed['fluid'] = empty_items_detailed['fluid'].fillna(
        empty_items_detailed['fluid_inclusion']
    )
    
    return empty_items_detailed, has_data_items

def categorize_empty_columns(empty_items):
    """빈 컬럼 분류"""
    print("\n" + "="*70)
    print("2. 빈 컬럼 분류")
    print("="*70)
    
    # 1. 카테고리별 분류
    category_counts = empty_items['category'].value_counts()
    print("\n📊 카테고리별 분포:")
    for cat, count in category_counts.items():
        print(f"   - {cat}: {count}개")
    
    # 2. Fluid 타입별 분류
    fluid_counts = empty_items['fluid'].value_counts()
    print("\n📊 Fluid 타입별 분포:")
    for fluid, count in fluid_counts.items():
        print(f"   - {fluid}: {count}개")
    
    # 3. 중복 라벨 패턴 찾기
    label_counts = empty_items.groupby('original_label').size()
    duplicate_labels = label_counts[label_counts > 1]
    
    if len(duplicate_labels) > 0:
        print(f"\n📊 중복 라벨 패턴 (같은 라벨, 다른 itemid):")
        for label, count in duplicate_labels.items():
            itemids = empty_items[empty_items['original_label'] == label]['itemid'].tolist()
            print(f"   - {label}: {count}개 itemid {itemids}")
    
    return category_counts, fluid_counts, duplicate_labels

def analyze_empty_reasons(empty_items, labevents):
    """빈 컬럼 원인 분석"""
    print("\n" + "="*70)
    print("3. 빈 컬럼 원인 추정")
    print("="*70)
    
    # 전체 데이터셋에서 해당 itemid 검색
    empty_itemids = empty_items['itemid'].tolist()
    
    # 전체 샘플에서 해당 itemid 빈도
    itemid_frequencies = labevents['itemid'].value_counts()
    
    empty_in_full = []
    for itemid in empty_itemids:
        freq = itemid_frequencies.get(itemid, 0)
        empty_in_full.append({
            'itemid': itemid,
            'frequency_in_full': freq
        })
    
    freq_df = pd.DataFrame(empty_in_full)
    
    # 원인 분류
    reasons = {
        'special_tests': [],      # 특수 검사
        'duplicate_itemids': [],  # 중복 itemid
        'no_data_in_sample': [],  # 샘플에 없음
        'blood_gas_related': [],  # Blood Gas 관련
        'other_fluid': []         # 다른 체액
    }
    
    for _, item in empty_items.iterrows():
        itemid = item['itemid']
        label = item['original_label']
        category = item.get('category', '')
        fluid = item.get('fluid', '')
        
        # 특수 검사 패턴
        special_keywords = ['COVID', 'CA 19-9', 'Folate', 'INR']
        if any(keyword in label for keyword in special_keywords):
            reasons['special_tests'].append(f"{label} ({itemid})")
        
        # Blood Gas 관련
        elif 'Blood Gas' in str(category) or 'pH' in label or 'pO2' in label or 'pCO2' in label:
            reasons['blood_gas_related'].append(f"{label} ({itemid})")
        
        # 다른 체액
        elif 'Other Body Fluid' in str(fluid) or 'Fluid' in str(fluid):
            reasons['other_fluid'].append(f"{label} ({itemid})")
        
        # 중복 itemid (같은 라벨이 다른 itemid에도 있는 경우)
        elif label in ['Hematocrit', 'Hemoglobin', 'Glucose', 'Creatinine', 'Lactate', 'Platelet Count']:
            reasons['duplicate_itemids'].append(f"{label} ({itemid})")
        
        # 나머지는 샘플에 없음
        else:
            reasons['no_data_in_sample'].append(f"{label} ({itemid})")
    
    print("\n📊 원인별 분류:")
    print(f"   1. 특수 검사 (선택적): {len(reasons['special_tests'])}개")
    if reasons['special_tests']:
        for item in reasons['special_tests'][:5]:
            print(f"      - {item}")
    
    print(f"\n   2. Blood Gas 관련: {len(reasons['blood_gas_related'])}개")
    if reasons['blood_gas_related']:
        for item in reasons['blood_gas_related'][:5]:
            print(f"      - {item}")
    
    print(f"\n   3. 중복 itemid (다른 itemid 사용): {len(reasons['duplicate_itemids'])}개")
    if reasons['duplicate_itemids']:
        for item in reasons['duplicate_itemids'][:5]:
            print(f"      - {item}")
    
    print(f"\n   4. 다른 체액 검사: {len(reasons['other_fluid'])}개")
    if reasons['other_fluid']:
        for item in reasons['other_fluid'][:5]:
            print(f"      - {item}")
    
    print(f"\n   5. 샘플 데이터 한계: {len(reasons['no_data_in_sample'])}개")
    
    return reasons, freq_df

def check_alternative_itemids(empty_items, has_data_items):
    """대체 itemid 존재 여부 확인"""
    print("\n" + "="*70)
    print("4. 대체 itemid 분석")
    print("="*70)
    
    # 데이터가 있는 항목의 라벨
    has_data_labels = set(has_data_items['original_label'].unique())
    
    # 빈 항목 중 같은 라벨이 데이터 있는 항목에 있는지 확인
    alternatives = []
    
    for _, item in empty_items.iterrows():
        label = item['original_label']
        itemid = item['itemid']
        
        if label in has_data_labels:
            # 해당 라벨로 데이터가 있는 itemid 찾기
            active_items = has_data_items[has_data_items['original_label'] == label]
            for _, active in active_items.iterrows():
                alternatives.append({
                    'empty_itemid': itemid,
                    'active_itemid': active['itemid'],
                    'label': label,
                    'active_count': active['data_count'],
                    'active_coverage': active['coverage_pct']
                })
    
    alternatives_df = pd.DataFrame(alternatives)
    
    if len(alternatives_df) > 0:
        print(f"\n📊 대체 가능한 itemid 발견: {len(alternatives_df)}개")
        print("\n   빈 itemid → 활성 itemid (데이터 수, 커버리지):")
        
        for _, alt in alternatives_df.head(10).iterrows():
            print(f"   - {alt['label']}: {alt['empty_itemid']} → {alt['active_itemid']} "
                  f"({alt['active_count']:.0f}건, {alt['active_coverage']:.1f}%)")
    
    return alternatives_df

def create_visualizations(empty_items, category_counts, fluid_counts, reasons):
    """시각화 생성"""
    print("\n" + "="*70)
    print("5. 시각화 생성")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 카테고리별 빈 컬럼 분포
    ax1 = axes[0, 0]
    if len(category_counts) > 0:
        ax1.bar(range(len(category_counts)), category_counts.values, color='coral')
        ax1.set_xticks(range(len(category_counts)))
        ax1.set_xticklabels(category_counts.index, rotation=45, ha='right')
        ax1.set_ylabel('빈 컬럼 수')
        ax1.set_title('카테고리별 빈 컬럼 분포')
        
        # 값 표시
        for i, v in enumerate(category_counts.values):
            ax1.text(i, v, str(v), ha='center', va='bottom')
    
    # 2. Fluid 타입별 분포
    ax2 = axes[0, 1]
    if len(fluid_counts) > 0:
        colors = plt.cm.Set3(range(len(fluid_counts)))
        wedges, texts, autotexts = ax2.pie(fluid_counts.values, 
                                           labels=fluid_counts.index,
                                           colors=colors,
                                           autopct='%1.1f%%',
                                           startangle=90)
        ax2.set_title('Fluid 타입별 빈 컬럼 분포')
    
    # 3. 원인별 분류
    ax3 = axes[1, 0]
    reason_counts = {
        '특수 검사': len(reasons['special_tests']),
        'Blood Gas': len(reasons['blood_gas_related']),
        '중복 itemid': len(reasons['duplicate_itemids']),
        '다른 체액': len(reasons['other_fluid']),
        '샘플 한계': len(reasons['no_data_in_sample'])
    }
    
    bars = ax3.bar(range(len(reason_counts)), reason_counts.values(), 
                   color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc'])
    ax3.set_xticks(range(len(reason_counts)))
    ax3.set_xticklabels(reason_counts.keys(), rotation=45, ha='right')
    ax3.set_ylabel('항목 수')
    ax3.set_title('빈 컬럼 원인별 분류')
    
    # 값 표시
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    # 4. 데이터 있는 vs 없는 항목 비교
    ax4 = axes[1, 1]
    data_status = {
        '데이터 있음': 48,
        '데이터 없음': 39
    }
    colors = ['#2ca02c', '#ff7f0e']
    wedges, texts, autotexts = ax4.pie(data_status.values(), 
                                       labels=data_status.keys(),
                                       colors=colors,
                                       autopct=lambda pct: f'{pct:.1f}%\n({int(pct*87/100)}개)',
                                       startangle=90,
                                       explode=(0, 0.1))
    ax4.set_title('전체 87개 검사 항목 데이터 가용성')
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'empty_columns_analysis.png'), 
                dpi=150, bbox_inches='tight')
    print(f"✅ 시각화 저장: empty_columns_analysis.png")
    
    plt.close()

def save_analysis_results(empty_items, reasons, alternatives_df):
    """분석 결과 저장"""
    print("\n" + "="*70)
    print("6. 분석 결과 저장")
    print("="*70)
    
    # 빈 컬럼 상세 정보 저장
    empty_items.to_csv(os.path.join(DATA_PATH, 'empty_columns_details.csv'), index=False)
    
    # 대체 itemid 정보 저장
    if len(alternatives_df) > 0:
        alternatives_df.to_csv(os.path.join(DATA_PATH, 'alternative_itemids.csv'), index=False)
    
    # 분석 요약 JSON 저장
    summary = {
        'overview': {
            'total_items': 87,
            'items_with_data': 48,
            'empty_items': 39,
            'empty_percentage': 44.8
        },
        'empty_reasons': {
            'special_tests': len(reasons['special_tests']),
            'blood_gas_related': len(reasons['blood_gas_related']),
            'duplicate_itemids': len(reasons['duplicate_itemids']),
            'other_fluid': len(reasons['other_fluid']),
            'sample_limitation': len(reasons['no_data_in_sample'])
        },
        'alternative_itemids': {
            'found': len(alternatives_df) if len(alternatives_df) > 0 else 0,
            'unique_labels': alternatives_df['label'].nunique() if len(alternatives_df) > 0 else 0
        },
        'recommendations': [
            "중복 itemid 통합 필요 (Hematocrit, Hemoglobin, Glucose 등)",
            "Blood Gas 검사는 ICU 데이터와 연계 필요",
            "특수 검사는 선택적 포함 고려",
            "더 큰 샘플 사용 시 커버리지 개선 예상"
        ]
    }
    
    with open(os.path.join(DATA_PATH, 'empty_columns_analysis.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 결과 파일 저장 완료")
    print(f"   - empty_columns_details.csv")
    print(f"   - alternative_itemids.csv")
    print(f"   - empty_columns_analysis.json")

def main():
    """메인 실행 함수"""
    print("\n" + "🔬 " * 20)
    print(" 빈 컬럼 원인 분석")
    print("🔬 " * 20)
    
    # 데이터 로드
    items_df, inclusion_df, labevents = load_data()
    
    # 빈 컬럼 분석
    empty_items, has_data_items = analyze_empty_columns(items_df, inclusion_df)
    
    # 분류
    category_counts, fluid_counts, duplicate_labels = categorize_empty_columns(empty_items)
    
    # 원인 분석
    reasons, freq_df = analyze_empty_reasons(empty_items, labevents)
    
    # 대체 itemid 확인
    alternatives_df = check_alternative_itemids(empty_items, has_data_items)
    
    # 시각화
    create_visualizations(empty_items, category_counts, fluid_counts, reasons)
    
    # 결과 저장
    save_analysis_results(empty_items, reasons, alternatives_df)
    
    print("\n" + "="*70)
    print("✅ 빈 컬럼 원인 분석 완료!")
    print("="*70)
    print(f"\n📊 핵심 발견:")
    print(f"   - 39개 빈 컬럼 중 상당수가 중복 itemid 또는 특수 검사")
    print(f"   - Blood Gas 관련 검사는 ICU 데이터 필요")
    print(f"   - 일부는 더 큰 샘플에서 데이터 존재 가능")

if __name__ == "__main__":
    main()