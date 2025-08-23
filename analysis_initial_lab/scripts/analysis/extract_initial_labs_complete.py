#!/usr/bin/env python3
"""
입원 당일 73개 주요 혈액검사 데이터 추출 스크립트
d_labitems_inclusion.csv에서 inclusion=1인 모든 검사 항목 추출
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
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
    
    # 주요 검사 출력
    print("\n주요 검사 항목:")
    for i, (itemid, label) in enumerate(list(LAB_ITEMS.items())[:10]):
        print(f"  - {itemid}: {label}")
    print(f"  ... 외 {len(LAB_ITEMS)-10}개")
    
    return LAB_ITEMS

def load_data(LAB_ITEMS):
    """데이터 로드"""
    print("\n2. 데이터 로딩 중...")
    
    # 입원 데이터 (1,200건)
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['admit_date'] = admissions['admittime'].dt.date
    
    # 환자 데이터
    patients = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/patients_sampled.csv'))
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['chart_date'] = labevents['charttime'].dt.date
    
    # inclusion=1인 검사만 필터링
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건 (전체 유지)")
    print(f"   - 환자: {len(patients):,}명")
    print(f"   - 전체 검사: {len(labevents):,}건")
    print(f"   - 필터링된 검사 (73개 항목): {len(labevents_filtered):,}건")
    
    return admissions, patients, labevents_filtered

def extract_admission_day_labs(admissions, labevents, LAB_ITEMS):
    """입원 당일 검사 추출"""
    print("\n3. 입원 당일 검사 추출 중...")
    
    # 입원별로 처리를 위한 준비
    results = []
    
    # 각 입원에 대해 처리
    for idx, admission in admissions.iterrows():
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_date = admission['admit_date']
        
        # 해당 입원의 당일 검사 찾기
        # hadm_id로 매칭 시도
        admission_labs = labevents[
            (labevents['hadm_id'] == hadm_id) & 
            (labevents['chart_date'] == admit_date)
        ]
        
        # hadm_id가 없으면 subject_id와 날짜로 매칭
        if len(admission_labs) == 0:
            admission_labs = labevents[
                (labevents['subject_id'] == subject_id) & 
                (labevents['chart_date'] == admit_date)
            ]
            # hadm_id 보정
            if len(admission_labs) > 0:
                admission_labs = admission_labs.copy()
                admission_labs['hadm_id'] = hadm_id
        
        # 각 검사별로 첫 번째 값만 가져오기
        for itemid in LAB_ITEMS.keys():
            lab_data = admission_labs[admission_labs['itemid'] == itemid]
            if len(lab_data) > 0:
                # 첫 번째 검사값 사용
                first_lab = lab_data.iloc[0]
                results.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'admit_date': admit_date,
                    'itemid': itemid,
                    'lab_name': LAB_ITEMS[itemid],
                    'charttime': first_lab['charttime'],
                    'valuenum': first_lab['valuenum'],
                    'value': first_lab.get('value', ''),
                    'valueuom': first_lab.get('valueuom', ''),
                    'flag': first_lab.get('flag', ''),
                    'ref_range_lower': first_lab.get('ref_range_lower', np.nan),
                    'ref_range_upper': first_lab.get('ref_range_upper', np.nan)
                })
    
    # Long format DataFrame 생성
    if results:
        long_df = pd.DataFrame(results)
    else:
        long_df = pd.DataFrame()
    
    print(f"✅ 입원 당일 검사 추출 완료")
    print(f"   - 추출된 검사 레코드: {len(long_df):,}건")
    
    # 입원별 검사 수 통계
    if not long_df.empty:
        labs_per_admission = long_df.groupby('hadm_id')['itemid'].count()
        admissions_with_labs = len(labs_per_admission)
        print(f"   - 검사가 있는 입원: {admissions_with_labs:,}건 / {len(admissions)}건 ({admissions_with_labs/len(admissions)*100:.1f}%)")
        print(f"   - 입원당 평균 검사 수: {labs_per_admission.mean():.1f}개")
    else:
        print("   ⚠️ 입원 당일 검사 데이터 없음")
    
    return long_df

def create_wide_format(admissions, long_df, LAB_ITEMS):
    """Wide format 변환 - 모든 입원 유지"""
    print("\n4. Wide format 변환 중...")
    
    # 모든 입원으로 시작
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 검사 데이터가 있는 경우 pivot
    if not long_df.empty:
        pivot_df = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'
        )
        
        # 입원 데이터와 병합
        wide_df = wide_df.merge(pivot_df, left_on='hadm_id', right_index=True, how='left')
    else:
        # 검사 데이터가 없으면 모든 검사 컬럼을 NaN으로 추가
        for lab_name in LAB_ITEMS.values():
            wide_df[lab_name] = np.nan
    
    print(f"✅ Wide format 변환 완료")
    print(f"   - 차원: {wide_df.shape[0]} 입원 × {wide_df.shape[1]-5} 검사 항목")
    print(f"   - 모든 입원 유지: {len(wide_df) == len(admissions)}")
    
    # 결측값 통계
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
    missing_stats = wide_df[lab_columns].isna().sum().sort_values()
    
    print(f"\n검사별 결측률 (상위 10개):")
    for lab in missing_stats.head(10).index:
        missing_count = missing_stats[lab]
        missing_pct = missing_count / len(wide_df) * 100
        print(f"  - {lab}: {len(wide_df) - missing_count}개 ({100-missing_pct:.1f}% 가용)")
    
    return wide_df

def calculate_statistics(wide_df):
    """통계 계산"""
    print("\n5. 통계 계산 중...")
    
    stats = {}
    
    # 전체 통계
    stats['total_admissions'] = len(wide_df)
    
    # 검사 컬럼 식별
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
    
    # 검사가 하나라도 있는 입원 수
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    stats['admissions_with_labs'] = int(has_any_lab.sum())
    stats['admissions_without_labs'] = stats['total_admissions'] - stats['admissions_with_labs']
    
    # 검사별 통계
    stats['lab_statistics'] = {}
    for lab in lab_columns:
        lab_data = wide_df[lab].dropna()
        if len(lab_data) > 0:
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
                'max': float(lab_data.max())
            }
    
    # 사망률 통계
    if 'hospital_expire_flag' in wide_df.columns:
        stats['mortality_rate'] = float(wide_df['hospital_expire_flag'].mean() * 100)
        
        # 생존/사망 그룹별 통계
        survived = wide_df[wide_df['hospital_expire_flag'] == 0]
        died = wide_df[wide_df['hospital_expire_flag'] == 1]
        
        stats['survived_count'] = len(survived)
        stats['died_count'] = len(died)
        
        # 각 그룹의 검사 가용성
        stats['lab_availability'] = {
            'survived': {},
            'died': {}
        }
        
        for lab in lab_columns:
            stats['lab_availability']['survived'][lab] = float((~survived[lab].isna()).mean() * 100)
            stats['lab_availability']['died'][lab] = float((~died[lab].isna()).mean() * 100)
    
    print("✅ 통계 계산 완료")
    
    return stats

def create_visualizations(wide_df, stats):
    """시각화 생성"""
    print("\n6. 시각화 생성 중...")
    
    # 검사 컬럼 식별
    lab_columns = [col for col in wide_df.columns if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
    
    # 1. 검사 가용성 히트맵
    plt.figure(figsize=(16, 10))
    
    # 가용률 계산
    availability = []
    lab_names = []
    for lab in lab_columns:
        if lab in stats['lab_statistics']:
            availability.append(100 - stats['lab_statistics'][lab]['missing_pct'])
            lab_names.append(lab)
    
    # 정렬
    sorted_indices = np.argsort(availability)[::-1]
    availability = [availability[i] for i in sorted_indices]
    lab_names = [lab_names[i] for i in sorted_indices]
    
    # 히트맵 데이터 준비 (10x8 그리드로 표시)
    n_labs = len(lab_names)
    n_cols = 10
    n_rows = (n_labs + n_cols - 1) // n_cols
    
    heatmap_data = np.full((n_rows, n_cols), np.nan)
    for i, val in enumerate(availability):
        row = i // n_cols
        col = i % n_cols
        heatmap_data[row, col] = val
    
    # 히트맵 그리기
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', 
                vmin=0, vmax=100, cbar_kws={'label': 'Availability (%)'})
    
    # 라벨 추가
    for i, lab in enumerate(lab_names[:30]):  # 상위 30개만 표시
        row = i // n_cols
        col = i % n_cols
        plt.text(col + 0.5, row + 0.1, lab[:15], fontsize=6, ha='center')
    
    plt.title('Lab Test Availability Heatmap (% of admissions with test)', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'lab_availability_heatmap.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 결측 패턴 분석
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 2-1. 입원별 검사 수 분포
    labs_per_admission = (~wide_df[lab_columns].isna()).sum(axis=1)
    axes[0, 0].hist(labs_per_admission, bins=30, edgecolor='black')
    axes[0, 0].set_xlabel('Number of Lab Tests')
    axes[0, 0].set_ylabel('Number of Admissions')
    axes[0, 0].set_title('Distribution of Lab Tests per Admission')
    axes[0, 0].axvline(labs_per_admission.mean(), color='red', linestyle='--', 
                       label=f'Mean: {labs_per_admission.mean():.1f}')
    axes[0, 0].legend()
    
    # 2-2. 검사별 가용률 분포
    availability_values = [100 - stat['missing_pct'] for stat in stats['lab_statistics'].values()]
    axes[0, 1].hist(availability_values, bins=20, edgecolor='black')
    axes[0, 1].set_xlabel('Availability (%)')
    axes[0, 1].set_ylabel('Number of Lab Tests')
    axes[0, 1].set_title('Distribution of Lab Test Availability')
    
    # 2-3. 생존/사망별 검사 수
    if 'hospital_expire_flag' in wide_df.columns:
        survived_labs = labs_per_admission[wide_df['hospital_expire_flag'] == 0]
        died_labs = labs_per_admission[wide_df['hospital_expire_flag'] == 1]
        
        axes[1, 0].boxplot([survived_labs, died_labs], labels=['Survived', 'Died'])
        axes[1, 0].set_ylabel('Number of Lab Tests')
        axes[1, 0].set_title('Lab Tests by Survival Status')
        axes[1, 0].grid(True, alpha=0.3)
    
    # 2-4. 상위 20개 검사 가용률
    top_labs = sorted(stats['lab_statistics'].items(), 
                     key=lambda x: x[1]['count'], reverse=True)[:20]
    lab_names_top = [lab[0][:20] for lab in top_labs]
    availability_top = [100 - lab[1]['missing_pct'] for lab in top_labs]
    
    axes[1, 1].barh(range(len(lab_names_top)), availability_top)
    axes[1, 1].set_yticks(range(len(lab_names_top)))
    axes[1, 1].set_yticklabels(lab_names_top, fontsize=8)
    axes[1, 1].set_xlabel('Availability (%)')
    axes[1, 1].set_title('Top 20 Most Available Lab Tests')
    axes[1, 1].invert_yaxis()
    
    plt.suptitle('Missing Pattern Analysis', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_PATH, 'missing_pattern_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 시각화 생성 완료")
    print(f"   - lab_availability_heatmap.png")
    print(f"   - missing_pattern_analysis.png")

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 입원 당일 73개 혈액검사 데이터 추출")
    print("=" * 80)
    
    # 1. inclusion=1인 검사 항목 로드
    LAB_ITEMS = load_inclusion_labs()
    
    # 2. 데이터 로드
    admissions, patients, labevents = load_data(LAB_ITEMS)
    
    # 3. 입원 당일 검사 추출
    long_df = extract_admission_day_labs(admissions, labevents, LAB_ITEMS)
    
    # 4. Wide format 변환
    wide_df = create_wide_format(admissions, long_df, LAB_ITEMS)
    
    # 5. 통계 계산
    stats = calculate_statistics(wide_df)
    
    # 6. 시각화 생성
    create_visualizations(wide_df, stats)
    
    # 7. 결과 저장
    print("\n7. 결과 저장 중...")
    
    # Long format 저장
    if not long_df.empty:
        long_df.to_csv(os.path.join(DATA_PATH, 'initial_labs_long.csv'), index=False)
        print(f"   ✅ Long format: initial_labs_long.csv ({len(long_df):,} 레코드)")
    
    # Wide format 저장
    wide_df.to_csv(os.path.join(DATA_PATH, 'initial_labs_wide.csv'), index=False)
    print(f"   ✅ Wide format: initial_labs_wide.csv ({len(wide_df)} × {len(wide_df.columns)} 차원)")
    
    # 통계 저장
    with open(os.path.join(DATA_PATH, 'lab_statistics.json'), 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✅ 통계: lab_statistics.json")
    
    # 8. 최종 요약
    print("\n" + "=" * 80)
    print("✅ 추출 완료!")
    print("=" * 80)
    
    print(f"\n[데이터 요약]")
    print(f"• 총 입원: {stats['total_admissions']}건 (모두 유지)")
    print(f"• 검사가 있는 입원: {stats['admissions_with_labs']}건 ({stats['admissions_with_labs']/stats['total_admissions']*100:.1f}%)")
    print(f"• 검사가 없는 입원: {stats['admissions_without_labs']}건 ({stats['admissions_without_labs']/stats['total_admissions']*100:.1f}%)")
    
    if 'mortality_rate' in stats:
        print(f"• 전체 사망률: {stats['mortality_rate']:.1f}%")
        print(f"  - 생존: {stats['survived_count']}건")
        print(f"  - 사망: {stats['died_count']}건")
    
    print(f"\n[검사 항목 통계]")
    print(f"• 총 검사 항목: {len(LAB_ITEMS)}개")
    print(f"• 실제 데이터가 있는 검사: {len(stats['lab_statistics'])}개")
    
    # 상위 5개 검사
    if stats['lab_statistics']:
        print(f"\n[가장 많이 시행된 검사 TOP 5]")
        top_labs = sorted(stats['lab_statistics'].items(), 
                         key=lambda x: x[1]['count'], reverse=True)[:5]
        for i, (lab, lab_stat) in enumerate(top_labs, 1):
            print(f"  {i}. {lab}: {lab_stat['count']}건 ({100-lab_stat['missing_pct']:.1f}%)")
    
    print(f"\n💾 저장 위치: analysis_initial_lab/data/")
    print(f"📊 시각화: analysis_initial_lab/figures/")
    
    return wide_df, long_df, stats

if __name__ == "__main__":
    wide_df, long_df, stats = main()