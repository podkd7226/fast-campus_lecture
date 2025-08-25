#!/usr/bin/env python3
"""
시간 윈도우를 확장한 혈액검사 데이터 추출 스크립트
입원 전일(-1), 당일(0), 익일(+1) 데이터를 우선순위에 따라 병합
우선순위: 당일 > 전일 > 익일
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
FIGURE_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/figures')
DATA_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab/data')

# 폴더 생성
os.makedirs(FIGURE_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

def load_inclusion_labs():
    """inclusion=1인 검사 항목 로드"""
    print("1. inclusion=1인 검사 항목 로딩 중...")
    
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    # 검사명 정리 (공백을 언더스코어로)
    included_labs['clean_label'] = included_labs['label'].str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
    
    # itemid와 검사명 매핑
    LAB_ITEMS = dict(zip(included_labs['itemid'], included_labs['clean_label']))
    
    print(f"✅ {len(LAB_ITEMS)}개 검사 항목 로드 완료")
    
    return LAB_ITEMS

def load_data(LAB_ITEMS):
    """데이터 로드"""
    print("\n2. 데이터 로딩 중...")
    
    # 입원 데이터 (1,200건)
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['admit_date'] = pd.to_datetime(admissions['admittime']).dt.date
    
    # 환자 데이터
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['chart_date'] = pd.to_datetime(labevents['charttime']).dt.date
    
    # inclusion=1인 검사만 필터링
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건 (전체 유지)")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 전체 검사: {len(labevents):,}건")
    print(f"   - 필터링된 검사 ({len(LAB_ITEMS)}개 항목): {len(labevents_filtered):,}건")
    
    return admissions, patients, labevents_filtered

def extract_labs_with_time_window(admissions, labevents, LAB_ITEMS):
    """시간 윈도우를 적용한 검사 추출"""
    print("\n3. 시간 윈도우를 적용한 검사 추출 중...")
    print("   - 우선순위: 입원 당일 > 입원 전일 > 입원 익일")
    
    results = []
    source_tracking = []  # 데이터 출처 추적
    
    # 진행 상황 추적
    total_admissions = len(admissions)
    
    for idx, admission in admissions.iterrows():
        if idx % 100 == 0:
            print(f"   - 처리 중: {idx}/{total_admissions}")
            
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_date = pd.to_datetime(admission['admit_date']).date()
        
        # 3일 윈도우 날짜 계산
        date_minus1 = admit_date - timedelta(days=1)
        date_plus1 = admit_date + timedelta(days=1)
        
        # 각 날짜별 검사 추출
        # 1. 입원 당일 (우선순위 1)
        labs_day0 = labevents[
            ((labevents['hadm_id'] == hadm_id) | (labevents['subject_id'] == subject_id)) & 
            (labevents['chart_date'] == admit_date)
        ].copy()
        labs_day0['day_offset'] = 0
        
        # 2. 입원 전일 (우선순위 2)
        labs_day_minus1 = labevents[
            (labevents['subject_id'] == subject_id) & 
            (labevents['chart_date'] == date_minus1)
        ].copy()
        labs_day_minus1['day_offset'] = -1
        
        # 3. 입원 익일 (우선순위 3)
        labs_day_plus1 = labevents[
            ((labevents['hadm_id'] == hadm_id) | (labevents['subject_id'] == subject_id)) & 
            (labevents['chart_date'] == date_plus1)
        ].copy()
        labs_day_plus1['day_offset'] = 1
        
        # 각 검사 항목별로 우선순위에 따라 선택
        for itemid, lab_name in LAB_ITEMS.items():
            # 우선순위 1: 입원 당일
            lab_data = labs_day0[labs_day0['itemid'] == itemid]
            selected_day = 0
            
            # 우선순위 2: 입원 전일
            if len(lab_data) == 0:
                lab_data = labs_day_minus1[labs_day_minus1['itemid'] == itemid]
                selected_day = -1
            
            # 우선순위 3: 입원 익일
            if len(lab_data) == 0:
                lab_data = labs_day_plus1[labs_day_plus1['itemid'] == itemid]
                selected_day = 1
            
            # 데이터가 있으면 첫 번째 값 사용
            if len(lab_data) > 0:
                first_lab = lab_data.iloc[0]
                results.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'admit_date': admit_date,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'charttime': first_lab['charttime'],
                    'chart_date': first_lab['chart_date'],
                    'valuenum': first_lab['valuenum'],
                    'value': first_lab.get('value', ''),
                    'valueuom': first_lab.get('valueuom', ''),
                    'flag': first_lab.get('flag', ''),
                    'ref_range_lower': first_lab.get('ref_range_lower', np.nan),
                    'ref_range_upper': first_lab.get('ref_range_upper', np.nan),
                    'day_offset': selected_day
                })
                
                # 데이터 출처 추적
                source_tracking.append({
                    'hadm_id': hadm_id,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'day_offset': selected_day,
                    'source': 'Day-1' if selected_day == -1 else ('Day0' if selected_day == 0 else 'Day+1')
                })
    
    # Long format DataFrame 생성
    if results:
        long_df = pd.DataFrame(results)
    else:
        long_df = pd.DataFrame()
    
    source_df = pd.DataFrame(source_tracking) if source_tracking else pd.DataFrame()
    
    print(f"\n✅ 시간 윈도우 검사 추출 완료")
    print(f"   - 추출된 검사 레코드: {len(long_df):,}건")
    
    # 데이터 출처 통계
    if not source_df.empty:
        source_stats = source_df.groupby('source').size()
        print(f"\n   [데이터 출처 분포]")
        for source, count in source_stats.items():
            pct = count / len(source_df) * 100
            print(f"   - {source}: {count:,}건 ({pct:.1f}%)")
    
    return long_df, source_df

def create_wide_format(admissions, long_df, LAB_ITEMS):
    """Wide format 변환 - 모든 입원 유지"""
    print("\n4. Wide format 변환 중...")
    
    # 모든 입원으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 검사 데이터가 있는 경우 pivot
    if not long_df.empty:
        # 검사 값 pivot
        pivot_df = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'
        )
        
        # day_offset pivot (어느 날짜에서 왔는지)
        offset_pivot = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='day_offset',
            aggfunc='first'
        )
        # 컬럼명에 _day_offset 추가
        offset_pivot.columns = [f"{col}_day_offset" for col in offset_pivot.columns]
        
        # 입원 데이터와 병합
        wide_df = wide_df.merge(pivot_df, left_on='hadm_id', right_index=True, how='left')
        wide_df = wide_df.merge(offset_pivot, left_on='hadm_id', right_index=True, how='left')
    else:
        # 검사 데이터가 없으면 모든 검사 컬럼을 NaN으로 추가
        for lab_name in LAB_ITEMS.values():
            wide_df[lab_name] = np.nan
            wide_df[f"{lab_name}_day_offset"] = np.nan
    
    print(f"✅ Wide format 변환 완료")
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {len([c for c in wide_df.columns if '_day_offset' not in c])-5} 검사 항목")
    print(f"   - 모든 입원 유지: {len(wide_df) == len(admissions)}")
    
    # 결측값 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    # 검사가 있는 입원 수
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    print(f"\n   [가용성 개선]")
    print(f"   - 검사가 있는 입원: {has_any_lab.sum()}건 ({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    print(f"   - 검사가 없는 입원: {(~has_any_lab).sum()}건 ({(~has_any_lab).sum()/len(wide_df)*100:.1f}%)")
    
    return wide_df

def calculate_statistics(wide_df, source_df):
    """통계 계산 (시간 윈도우 효과 포함)"""
    print("\n5. 통계 계산 중...")
    
    stats = {}
    
    # 전체 통계
    stats['total_admissions'] = len(wide_df)
    
    # 검사 컬럼 식별
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    
    # 검사가 하나라도 있는 입원 수
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    stats['admissions_with_labs'] = int(has_any_lab.sum())
    stats['admissions_without_labs'] = stats['total_admissions'] - stats['admissions_with_labs']
    stats['coverage_rate'] = float(stats['admissions_with_labs'] / stats['total_admissions'] * 100)
    
    # 검사별 통계
    stats['lab_statistics'] = {}
    for lab in lab_columns:
        lab_data = wide_df[lab].dropna()
        if len(lab_data) > 0:
            # day_offset 정보 추가
            offset_col = f"{lab}_day_offset"
            if offset_col in wide_df.columns:
                offset_data = wide_df.loc[~wide_df[lab].isna(), offset_col]
                day_counts = offset_data.value_counts().to_dict()
            else:
                day_counts = {}
            
            stats['lab_statistics'][lab] = {
                'count': int(len(lab_data)),
                'missing_count': int(len(wide_df) - len(lab_data)),
                'missing_pct': float((len(wide_df) - len(lab_data)) / len(wide_df) * 100),
                'mean': float(lab_data.mean()),
                'std': float(lab_data.std()),
                'min': float(lab_data.min()),
                'q1': float(lab_data.quantile(0.25)),
                'median': float(lab_data.median()),
                'q3': float(lab_data.quantile(0.75)),
                'max': float(lab_data.max()),
                'day_sources': {
                    'day_minus1': int(day_counts.get(-1, 0)),
                    'day0': int(day_counts.get(0, 0)),
                    'day_plus1': int(day_counts.get(1, 0))
                }
            }
    
    # 시간 윈도우 효과 분석
    if not source_df.empty:
        stats['time_window_effect'] = {
            'total_labs': len(source_df),
            'day_minus1': int(source_df[source_df['day_offset'] == -1].shape[0]),
            'day0': int(source_df[source_df['day_offset'] == 0].shape[0]),
            'day_plus1': int(source_df[source_df['day_offset'] == 1].shape[0]),
            'day_minus1_pct': float(source_df[source_df['day_offset'] == -1].shape[0] / len(source_df) * 100),
            'day0_pct': float(source_df[source_df['day_offset'] == 0].shape[0] / len(source_df) * 100),
            'day_plus1_pct': float(source_df[source_df['day_offset'] == 1].shape[0] / len(source_df) * 100)
        }
    
    # 사망률 통계
    if 'hospital_expire_flag' in wide_df.columns:
        stats['mortality_rate'] = float(wide_df['hospital_expire_flag'].mean() * 100)
        
        survived = wide_df[wide_df['hospital_expire_flag'] == 0]
        died = wide_df[wide_df['hospital_expire_flag'] == 1]
        
        stats['survived_count'] = len(survived)
        stats['died_count'] = len(died)
    
    print("✅ 통계 계산 완료")
    
    return stats

def create_comparison_visualizations(wide_df, stats, source_df):
    """비교 시각화 생성"""
    print("\n6. 시각화 생성 중...")
    
    # 1. 시간 윈도우 효과 시각화
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1-1. 데이터 출처 분포 (파이 차트)
    if 'time_window_effect' in stats:
        window_data = stats['time_window_effect']
        labels = ['Day-1 (전일)', 'Day0 (당일)', 'Day+1 (익일)']
        sizes = [window_data['day_minus1'], window_data['day0'], window_data['day_plus1']]
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        axes[0, 0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('Data Source Distribution')
    
    # 1-2. 입원별 검사 수 분포
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date'] and '_day_offset' not in col]
    labs_per_admission = (~wide_df[lab_columns].isna()).sum(axis=1)
    
    axes[0, 1].hist(labs_per_admission, bins=30, edgecolor='black', alpha=0.7)
    axes[0, 1].axvline(labs_per_admission.mean(), color='red', linestyle='--', 
                       label=f'Mean: {labs_per_admission.mean():.1f}')
    axes[0, 1].set_xlabel('Number of Lab Tests')
    axes[0, 1].set_ylabel('Number of Admissions')
    axes[0, 1].set_title('Lab Tests per Admission (Time Window)')
    axes[0, 1].legend()
    
    # 1-3. 가용성 개선 효과 (상위 20개 검사)
    lab_stats = stats['lab_statistics']
    top_labs = sorted(lab_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
    
    lab_names = [lab[0][:15] for lab in top_labs]
    availability = [100 - lab[1]['missing_pct'] for lab in top_labs]
    
    axes[1, 0].barh(range(len(lab_names)), availability, color='skyblue')
    axes[1, 0].set_yticks(range(len(lab_names)))
    axes[1, 0].set_yticklabels(lab_names, fontsize=8)
    axes[1, 0].set_xlabel('Availability (%)')
    axes[1, 0].set_title('Top 20 Lab Tests Availability (With Time Window)')
    axes[1, 0].invert_yaxis()
    
    # 1-4. 검사별 데이터 출처 분포 (상위 10개)
    top_10_labs = top_labs[:10]
    lab_names_10 = [lab[0][:12] for lab in top_10_labs]
    
    day_minus1_counts = [lab[1]['day_sources']['day_minus1'] for lab in top_10_labs]
    day0_counts = [lab[1]['day_sources']['day0'] for lab in top_10_labs]
    day_plus1_counts = [lab[1]['day_sources']['day_plus1'] for lab in top_10_labs]
    
    x = np.arange(len(lab_names_10))
    width = 0.25
    
    axes[1, 1].bar(x - width, day_minus1_counts, width, label='Day-1', color='#ff9999')
    axes[1, 1].bar(x, day0_counts, width, label='Day0', color='#66b3ff')
    axes[1, 1].bar(x + width, day_plus1_counts, width, label='Day+1', color='#99ff99')
    
    axes[1, 1].set_xlabel('Lab Tests')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].set_title('Data Source by Lab Test (Top 10)')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(lab_names_10, rotation=45, ha='right', fontsize=8)
    axes[1, 1].legend()
    
    plt.suptitle('Time Window Effect Analysis', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'time_window_effect.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 가용성 비교 히트맵
    # 원래 당일 데이터와 비교하기 위해 당일만 데이터 로드
    original_stats_path = os.path.join(DATA_PATH, 'lab_statistics.json')
    if os.path.exists(original_stats_path):
        with open(original_stats_path, 'r') as f:
            original_stats = json.load(f)
        
        # 비교 데이터 준비
        comparison_data = []
        for lab_name in list(lab_stats.keys())[:30]:  # 상위 30개만
            if lab_name in original_stats.get('lab_statistics', {}):
                original_avail = 100 - original_stats['lab_statistics'][lab_name]['missing_pct']
                window_avail = 100 - lab_stats[lab_name]['missing_pct']
                improvement = window_avail - original_avail
                comparison_data.append({
                    'lab': lab_name[:20],
                    'day0_only': original_avail,
                    'with_window': window_avail,
                    'improvement': improvement
                })
        
        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)
            comp_df = comp_df.sort_values('with_window', ascending=False)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 히트맵 데이터
            heatmap_data = comp_df[['day0_only', 'with_window', 'improvement']].T
            heatmap_data.columns = comp_df['lab'].values
            
            sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', 
                       vmin=0, vmax=100, cbar_kws={'label': 'Availability (%)'}, ax=ax)
            
            ax.set_title('Lab Availability: Day0 Only vs Time Window', fontsize=14)
            ax.set_xlabel('')
            ax.set_yticklabels(['Day0 Only', 'With Window', 'Improvement'], rotation=0)
            
            plt.tight_layout()
            plt.savefig(os.path.join(FIGURE_PATH, 'availability_comparison.png'), dpi=300, bbox_inches='tight')
            plt.close()
    
    print("✅ 시각화 생성 완료")
    print(f"   - time_window_effect.png")
    print(f"   - availability_comparison.png")

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 시간 윈도우를 적용한 혈액검사 데이터 추출")
    print("   입원 전일(-1), 당일(0), 익일(+1) 데이터 병합")
    print("=" * 80)
    
    # 1. inclusion=1인 검사 항목 로드
    LAB_ITEMS = load_inclusion_labs()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data(LAB_ITEMS)
    
    # 3. 시간 윈도우를 적용한 검사 추출
    long_df, source_df = extract_labs_with_time_window(admissions, labevents, LAB_ITEMS)
    
    # 4. Wide format 변환
    wide_df = create_wide_format(admissions, long_df, LAB_ITEMS)
    
    # 5. 통계 계산
    stats = calculate_statistics(wide_df, source_df)
    
    # 6. 시각화 생성
    create_comparison_visualizations(wide_df, stats, source_df)
    
    # 7. 결과 저장
    print("\n7. 결과 저장 중...")
    
    # Long format 저장
    if not long_df.empty:
        long_df.to_csv(os.path.join(DATA_PATH, 'labs_time_window_long.csv'), index=False)
        print(f"   ✅ Long format: labs_time_window_long.csv ({len(long_df):,} 레코드)")
    
    # Wide format 저장
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_time_window_wide.csv'), index=False)
    print(f"   ✅ Wide format: labs_time_window_wide.csv ({len(wide_df)} × {len(wide_df.columns)} 차원)")
    
    # 데이터 출처 저장
    if not source_df.empty:
        source_df.to_csv(os.path.join(DATA_PATH, 'lab_source_days.csv'), index=False)
        print(f"   ✅ 데이터 출처: lab_source_days.csv ({len(source_df):,} 레코드)")
    
    # 통계 저장
    with open(os.path.join(DATA_PATH, 'lab_statistics_time_window.json'), 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✅ 통계: lab_statistics_time_window.json")
    
    # 8. 최종 요약
    print("\n" + "=" * 80)
    print("✅ 시간 윈도우 추출 완료!")
    print("=" * 80)
    
    print(f"\n[데이터 요약]")
    print(f"• 총 입원: {stats['total_admissions']}건 (모두 유지)")
    print(f"• 검사가 있는 입원: {stats['admissions_with_labs']}건 ({stats['coverage_rate']:.1f}%)")
    print(f"• 검사가 없는 입원: {stats['admissions_without_labs']}건 ({stats['admissions_without_labs']/stats['total_admissions']*100:.1f}%)")
    
    if 'time_window_effect' in stats:
        window = stats['time_window_effect']
        print(f"\n[데이터 출처 분포]")
        print(f"• 입원 전일 (Day-1): {window['day_minus1']:,}건 ({window['day_minus1_pct']:.1f}%)")
        print(f"• 입원 당일 (Day0): {window['day0']:,}건 ({window['day0_pct']:.1f}%)")
        print(f"• 입원 익일 (Day+1): {window['day_plus1']:,}건 ({window['day_plus1_pct']:.1f}%)")
    
    # 개선 효과 (당일 데이터와 비교)
    print(f"\n[가용성 개선 효과]")
    print(f"• 당일만: 1,053건 (87.8%) → 시간 윈도우: {stats['admissions_with_labs']}건 ({stats['coverage_rate']:.1f}%)")
    improvement = stats['coverage_rate'] - 87.8
    print(f"• 개선: +{improvement:.1f}% 포인트")
    
    if stats['lab_statistics']:
        print(f"\n[가장 많이 시행된 검사 TOP 5]")
        top_labs = sorted(stats['lab_statistics'].items(), 
                         key=lambda x: x[1]['count'], reverse=True)[:5]
        for i, (lab, lab_stat) in enumerate(top_labs, 1):
            sources = lab_stat['day_sources']
            print(f"  {i}. {lab}: {lab_stat['count']}건 ({100-lab_stat['missing_pct']:.1f}%)")
            print(f"     - 출처: 전일 {sources['day_minus1']}건, 당일 {sources['day0']}건, 익일 {sources['day_plus1']}건")
    
    print(f"\n💾 저장 위치: analysis_initial_lab/data/")
    print(f"📊 시각화: analysis_initial_lab/figures/")
    
    return wide_df, long_df, source_df, stats

if __name__ == "__main__":
    wide_df, long_df, source_df, stats = main()