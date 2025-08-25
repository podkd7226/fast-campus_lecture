#!/usr/bin/env python3
"""
선택적 ItemID 통합 스크립트
- 안전한 경우만 itemid 통합 (한쪽이 비어있는 경우)
- 둘 다 활성인 경우는 통합하지 않음
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 경로 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
OUTPUT_PATH = os.path.join(BASE_PATH, 'analysis_initial_lab_re')
DATA_PATH = os.path.join(OUTPUT_PATH, 'data')

def load_merge_rules():
    """통합 규칙 로드 및 생성"""
    print("=" * 70)
    print("1. 통합 규칙 생성")
    print("=" * 70)
    
    # 개선 가능 항목 (한쪽이 비어있는 경우)
    improvable = pd.read_csv(os.path.join(DATA_PATH, 'improvable_items.csv'))
    
    # 중복 활성 라벨 (둘 다 데이터 있는 경우)
    duplicate_active = pd.read_csv(os.path.join(DATA_PATH, 'duplicate_active_labels.csv'))
    
    # 통합 불가 라벨 (둘 다 활성)
    no_merge_labels = set(duplicate_active['label'].tolist())
    
    print(f"\n📊 분석 결과:")
    print(f"   - 개선 가능 항목: {len(improvable)}개")
    print(f"   - 중복 활성 라벨: {len(duplicate_active)}개 (통합 불가)")
    
    # 안전한 통합 규칙 생성
    safe_merge_rules = {}
    unsafe_merges = []
    
    for _, row in improvable.iterrows():
        label = row['label']
        
        # 중복 활성 라벨은 제외
        if label in no_merge_labels:
            unsafe_merges.append({
                'label': label,
                'reason': '둘 다 활성 (값 차이 존재)'
            })
            continue
        
        # 빈 itemid들
        empty_itemids = str(row['empty_itemids']).split(';')
        # 활성 itemid들
        active_itemids = str(row['active_itemids']).split(';')
        
        # 첫 번째 활성 itemid로 통합
        target_itemid = int(active_itemids[0])
        
        for empty_id in empty_itemids:
            try:
                empty_id = int(empty_id)
                safe_merge_rules[empty_id] = target_itemid
            except:
                continue
    
    print(f"\n✅ 통합 규칙 생성 완료:")
    print(f"   - 안전한 통합: {len(safe_merge_rules)}개 itemid")
    print(f"   - 통합 불가: {len(unsafe_merges)}개 라벨")
    
    if unsafe_merges:
        print(f"\n⚠️ 통합 불가 항목:")
        for item in unsafe_merges:
            print(f"   - {item['label']}: {item['reason']}")
    
    return safe_merge_rules, unsafe_merges

def load_data():
    """데이터 로드"""
    print("\n" + "=" * 70)
    print("2. 데이터 로딩")
    print("=" * 70)
    
    # 입원 데이터
    admissions = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv'))
    admissions['admittime'] = pd.to_datetime(admissions['admittime'])
    admissions['admit_date'] = admissions['admittime'].dt.date
    
    # 검사 데이터
    labevents = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/labevents_sampled.csv'))
    labevents['charttime'] = pd.to_datetime(labevents['charttime'])
    labevents['chart_date'] = labevents['charttime'].dt.date
    
    # inclusion 정보
    inclusion_df = pd.read_csv(os.path.join(BASE_PATH, 'processed_data/hosp/d_labitems_inclusion.csv'))
    included_labs = inclusion_df[inclusion_df['inclusion'] == 1].copy()
    
    print(f"✅ 데이터 로드 완료")
    print(f"   - 입원: {len(admissions):,}건")
    print(f"   - 전체 검사: {len(labevents):,}건")
    print(f"   - Inclusion=1 항목: {len(included_labs)}개")
    
    return admissions, labevents, included_labs

def apply_merge_rules(labevents, merge_rules):
    """통합 규칙 적용"""
    print("\n" + "=" * 70)
    print("3. ItemID 통합 적용")
    print("=" * 70)
    
    # 원본 백업
    original_counts = labevents['itemid'].value_counts()
    
    # 통합 적용
    merged_count = 0
    for old_id, new_id in merge_rules.items():
        mask = labevents['itemid'] == old_id
        count = mask.sum()
        if count > 0:
            labevents.loc[mask, 'itemid'] = new_id
            merged_count += count
            print(f"   - {old_id} → {new_id}: {count}건 통합")
    
    # 통합 후 통계
    new_counts = labevents['itemid'].value_counts()
    
    print(f"\n✅ 통합 완료:")
    print(f"   - 통합된 레코드: {merged_count:,}건")
    print(f"   - 고유 itemid: {len(original_counts)} → {len(new_counts)}")
    
    return labevents

def create_merged_lab_items(included_labs, merge_rules):
    """통합된 검사 항목 딕셔너리 생성"""
    print("\n" + "=" * 70)
    print("4. 통합된 검사 항목 생성")
    print("=" * 70)
    
    # 통합 대상 itemid들
    merged_itemids = set(merge_rules.keys())
    
    LAB_ITEMS = {}
    LAB_METADATA = {}
    
    for _, row in included_labs.iterrows():
        itemid = row['itemid']
        
        # 통합되는 itemid는 건너뛰기
        if itemid in merged_itemids:
            continue
        
        original_label = row['label']
        
        # 라벨 정리
        clean_label = (original_label
                      .replace(' ', '_')
                      .replace(',', '_')
                      .replace('(', '')
                      .replace(')', '')
                      .replace('/', '_')
                      .replace('-', '_'))
        
        # 통합 대상인 경우 표시
        if itemid in merge_rules.values():
            # 통합된 itemid 찾기
            merged_from = [k for k, v in merge_rules.items() if v == itemid]
            unique_label = f"{clean_label}_{itemid}_merged"
        else:
            unique_label = f"{clean_label}_{itemid}"
        
        LAB_ITEMS[itemid] = unique_label
        LAB_METADATA[itemid] = {
            'original_label': original_label,
            'clean_label': clean_label,
            'unique_label': unique_label,
            'category': row.get('category', ''),
            'fluid': row.get('fluid', ''),
            'merged_from': merged_from if itemid in merge_rules.values() else []
        }
    
    print(f"✅ 통합된 검사 항목: {len(LAB_ITEMS)}개")
    
    # 통합 통계
    merged_targets = [v for v in merge_rules.values()]
    unique_targets = set(merged_targets)
    print(f"   - 통합 대상 itemid: {len(unique_targets)}개")
    print(f"   - 제거된 itemid: {len(merged_itemids)}개")
    
    return LAB_ITEMS, LAB_METADATA

def extract_labs_with_window(admissions, labevents, LAB_ITEMS):
    """시간 윈도우 적용하여 검사 추출"""
    print("\n" + "=" * 70)
    print("5. 시간 윈도우 검사 추출")
    print("=" * 70)
    
    # inclusion=1 itemid만 필터링
    lab_itemids = list(LAB_ITEMS.keys())
    labevents_filtered = labevents[labevents['itemid'].isin(lab_itemids)].copy()
    
    print(f"✅ 필터링: {len(labevents_filtered):,}건")
    
    results = []
    offset_info = []
    
    for idx, admission in admissions.iterrows():
        if idx % 200 == 0 and idx > 0:
            print(f"   처리 진행: {idx}/{len(admissions)}")
            
        hadm_id = admission['hadm_id']
        subject_id = admission['subject_id']
        admit_date = pd.to_datetime(admission['admit_date']).date()
        
        # 3일 윈도우
        date_minus1 = admit_date - timedelta(days=1)
        date_plus1 = admit_date + timedelta(days=1)
        
        # 각 날짜별 검사
        labs_by_day = {
            0: labevents_filtered[
                ((labevents_filtered['hadm_id'] == hadm_id) | 
                 (labevents_filtered['subject_id'] == subject_id)) & 
                (labevents_filtered['chart_date'] == admit_date)
            ],
            -1: labevents_filtered[
                (labevents_filtered['subject_id'] == subject_id) & 
                (labevents_filtered['chart_date'] == date_minus1)
            ],
            1: labevents_filtered[
                ((labevents_filtered['hadm_id'] == hadm_id) | 
                 (labevents_filtered['subject_id'] == subject_id)) & 
                (labevents_filtered['chart_date'] == date_plus1)
            ]
        }
        
        # 각 itemid별 처리
        for itemid, lab_name in LAB_ITEMS.items():
            selected_data = None
            selected_day = None
            
            # 우선순위: Day 0 > Day -1 > Day +1
            for day in [0, -1, 1]:
                day_labs = labs_by_day[day]
                item_labs = day_labs[day_labs['itemid'] == itemid]
                if len(item_labs) > 0:
                    selected_data = item_labs.iloc[0]
                    selected_day = day
                    break
            
            if selected_data is not None:
                results.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'admit_date': admit_date,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'charttime': selected_data['charttime'],
                    'chart_date': selected_data['chart_date'],
                    'valuenum': selected_data['valuenum'],
                    'value': selected_data.get('value', ''),
                    'valueuom': selected_data.get('valueuom', ''),
                    'flag': selected_data.get('flag', ''),
                    'ref_range_lower': selected_data.get('ref_range_lower', np.nan),
                    'ref_range_upper': selected_data.get('ref_range_upper', np.nan)
                })
                
                offset_info.append({
                    'hadm_id': hadm_id,
                    'itemid': itemid,
                    'lab_name': lab_name,
                    'day_offset': selected_day,
                    'source': f"Day{selected_day:+d}" if selected_day != 0 else "Day0"
                })
    
    long_df = pd.DataFrame(results) if results else pd.DataFrame()
    offset_df = pd.DataFrame(offset_info) if offset_info else pd.DataFrame()
    
    print(f"\n✅ 추출 완료:")
    print(f"   - 검사 레코드: {len(long_df):,}건")
    print(f"   - 고유 itemid: {long_df['itemid'].nunique() if len(long_df) > 0 else 0}개")
    
    return long_df, offset_df

def create_wide_format(admissions, long_df, LAB_ITEMS):
    """Wide format 생성"""
    print("\n" + "=" * 70)
    print("6. Wide Format 변환")
    print("=" * 70)
    
    # 기본 입원 정보
    wide_df = admissions[['hadm_id', 'subject_id', 'admittime', 
                          'hospital_expire_flag', 'deathtime']].copy()
    wide_df['admit_date'] = pd.to_datetime(wide_df['admittime']).dt.date
    
    # 모든 검사 컬럼 초기화
    for itemid, lab_name in LAB_ITEMS.items():
        wide_df[lab_name] = np.nan
    
    # 실제 데이터 채우기
    if not long_df.empty:
        pivot_df = long_df.pivot_table(
            index='hadm_id',
            columns='lab_name',
            values='valuenum',
            aggfunc='first'
        )
        
        for hadm_id in pivot_df.index:
            if hadm_id in wide_df['hadm_id'].values:
                idx = wide_df[wide_df['hadm_id'] == hadm_id].index[0]
                for col in pivot_df.columns:
                    if col in wide_df.columns:
                        wide_df.loc[idx, col] = pivot_df.loc[hadm_id, col]
    
    # 통계
    lab_columns = [col for col in wide_df.columns 
                   if col not in ['hadm_id', 'subject_id', 'admittime', 
                                 'hospital_expire_flag', 'deathtime', 'admit_date']]
    
    print(f"✅ Wide format 생성 완료")
    print(f"   - 차원: {wide_df.shape[0]} × {len(lab_columns)} 검사")
    
    # 커버리지 계산
    non_null_counts = {}
    for col in lab_columns:
        non_null = wide_df[col].notna().sum()
        if non_null > 0:
            non_null_counts[col] = non_null
    
    has_any_lab = ~wide_df[lab_columns].isna().all(axis=1)
    
    print(f"\n📊 커버리지:")
    print(f"   - 데이터 있는 컬럼: {len(non_null_counts)}/{len(lab_columns)}")
    print(f"   - 검사 있는 입원: {has_any_lab.sum()}/{len(wide_df)} "
          f"({has_any_lab.sum()/len(wide_df)*100:.1f}%)")
    
    return wide_df, lab_columns

def save_results(wide_df, long_df, offset_df, merge_rules, unsafe_merges, 
                 LAB_ITEMS, LAB_METADATA, lab_columns):
    """결과 저장"""
    print("\n" + "=" * 70)
    print("7. 결과 저장")
    print("=" * 70)
    
    # CSV 파일 저장
    wide_df.to_csv(os.path.join(DATA_PATH, 'labs_initial_merged_wide.csv'), index=False)
    long_df.to_csv(os.path.join(DATA_PATH, 'labs_initial_merged_long.csv'), index=False)
    offset_df.to_csv(os.path.join(DATA_PATH, 'labs_merged_offset_info.csv'), index=False)
    
    # 통합 매핑 테이블 저장
    merge_mapping = []
    for old_id, new_id in merge_rules.items():
        if new_id in LAB_METADATA:
            merge_mapping.append({
                'old_itemid': old_id,
                'new_itemid': new_id,
                'label': LAB_METADATA[new_id]['original_label']
            })
    
    if merge_mapping:
        merge_mapping_df = pd.DataFrame(merge_mapping)
        merge_mapping_df.to_csv(os.path.join(DATA_PATH, 'merge_mapping.csv'), index=False)
    
    # 메타데이터
    metadata = {
        'extraction_info': {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'selective_itemid_merging',
            'description': '안전한 경우만 itemid 통합 (한쪽이 비어있는 경우)'
        },
        'merge_statistics': {
            'total_merge_rules': len(merge_rules),
            'merged_itemids': list(merge_rules.keys()),
            'target_itemids': list(set(merge_rules.values())),
            'unsafe_merges': len(unsafe_merges),
            'unsafe_labels': [item['label'] for item in unsafe_merges]
        },
        'data_summary': {
            'original_itemids': 87,
            'final_itemids': len(LAB_ITEMS),
            'total_admissions': len(wide_df),
            'total_lab_records': len(long_df),
            'columns_with_data': len([c for c in lab_columns 
                                     if wide_df[c].notna().sum() > 0])
        },
        'coverage': {
            'admissions_with_labs': int((~wide_df[lab_columns].isna().all(axis=1)).sum()),
            'coverage_rate': float((~wide_df[lab_columns].isna().all(axis=1)).sum() / 
                                 len(wide_df) * 100)
        }
    }
    
    with open(os.path.join(DATA_PATH, 'merge_summary.json'), 'w') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 파일 저장 완료")
    print(f"   - labs_initial_merged_wide.csv: {wide_df.shape}")
    print(f"   - labs_initial_merged_long.csv: {len(long_df):,} records")
    print(f"   - merge_mapping.csv: {len(merge_mapping)} mappings")
    print(f"   - merge_summary.json")
    
    return metadata

def main():
    """메인 실행 함수"""
    print("\n" + "🔄 " * 20)
    print(" 선택적 ItemID 통합 처리")
    print("🔄 " * 20)
    
    # 1. 통합 규칙 생성
    merge_rules, unsafe_merges = load_merge_rules()
    
    # 2. 데이터 로드
    admissions, labevents, included_labs = load_data()
    
    # 3. 통합 규칙 적용
    labevents = apply_merge_rules(labevents, merge_rules)
    
    # 4. 통합된 검사 항목 생성
    LAB_ITEMS, LAB_METADATA = create_merged_lab_items(included_labs, merge_rules)
    
    # 5. 시간 윈도우 검사 추출
    long_df, offset_df = extract_labs_with_window(admissions, labevents, LAB_ITEMS)
    
    # 6. Wide format 변환
    wide_df, lab_columns = create_wide_format(admissions, long_df, LAB_ITEMS)
    
    # 7. 결과 저장
    metadata = save_results(wide_df, long_df, offset_df, merge_rules, unsafe_merges,
                          LAB_ITEMS, LAB_METADATA, lab_columns)
    
    print("\n" + "=" * 70)
    print("🎉 선택적 ItemID 통합 완료!")
    print("=" * 70)
    print(f"\n📊 최종 결과:")
    print(f"   - ItemID: 87개 → {metadata['data_summary']['final_itemids']}개")
    print(f"   - 안전하게 통합: {len(merge_rules)}개")
    print(f"   - 통합 불가: {len(unsafe_merges)}개 (값 차이 존재)")
    print(f"   - 커버리지: {metadata['coverage']['coverage_rate']:.1f}%")

if __name__ == "__main__":
    main()