#!/usr/bin/env python3
"""
MIMIC-IV hosp 필수 테이블 추출 스크립트
요청된 5개 환자 테이블과 4개 사전 테이블 추출
"""

import pandas as pd
import numpy as np
import os
import shutil
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 설정
BASE_PATH = '/Users/hyungjun/Desktop/fast campus_lecture'
CHUNK_SIZE = 100000  # 대용량 파일 청크 크기

def load_sampled_ids():
    """샘플된 ID 로드"""
    print("1. 샘플 ID 로딩 중...")
    
    # 샘플링된 admissions에서 ID 추출
    admissions_path = os.path.join(BASE_PATH, 'processed_data/core/admissions_sampled.csv')
    admissions = pd.read_csv(admissions_path)
    
    subject_ids = set(admissions['subject_id'].unique())
    hadm_ids = set(admissions['hadm_id'].unique())
    
    print(f"✅ 샘플 ID 로드 완료")
    print(f"   - Subject IDs: {len(subject_ids):,}개")
    print(f"   - Admission IDs: {len(hadm_ids):,}개")
    
    return subject_ids, hadm_ids

def copy_dictionary_tables():
    """사전 테이블 복사 (전체 데이터셋에 필요)"""
    print("\n2. 사전 테이블 복사 중...")
    
    dictionary_tables = [
        'd_hcpcs.csv',
        'd_icd_diagnoses.csv', 
        'd_icd_procedures.csv',
        'd_labitems.csv'
    ]
    
    source_dir = os.path.join(BASE_PATH, 'dataset2/hosp')
    target_dir = os.path.join(BASE_PATH, 'processed_data/hosp')
    
    copied_count = 0
    for table in dictionary_tables:
        source_path = os.path.join(source_dir, table)
        target_path = os.path.join(target_dir, table)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            file_size = os.path.getsize(target_path) / (1024 * 1024)  # MB
            print(f"   ✅ {table} 복사 완료 ({file_size:.1f} MB)")
            copied_count += 1
        else:
            print(f"   ⚠️ {table} 파일 없음")
    
    return copied_count

def extract_patient_table(table_name, subject_ids, hadm_ids, use_chunks=False):
    """환자별 데이터 테이블 추출"""
    source_path = os.path.join(BASE_PATH, f'dataset2/hosp/{table_name}.csv')
    target_path = os.path.join(BASE_PATH, f'processed_data/hosp/{table_name}_sampled.csv')
    
    if not os.path.exists(source_path):
        print(f"   ⚠️ {table_name} 파일 없음")
        return 0
    
    print(f"   처리 중: {table_name}...")
    
    try:
        if use_chunks:
            # 대용량 파일은 청크로 처리
            filtered_chunks = []
            total_rows = 0
            chunk_count = 0
            
            for chunk_num, chunk in enumerate(pd.read_csv(source_path, chunksize=CHUNK_SIZE)):
                # subject_id 또는 hadm_id로 필터링
                if 'subject_id' in chunk.columns and 'hadm_id' in chunk.columns:
                    filtered = chunk[
                        (chunk['subject_id'].isin(subject_ids)) | 
                        (chunk['hadm_id'].isin(hadm_ids))
                    ]
                elif 'subject_id' in chunk.columns:
                    filtered = chunk[chunk['subject_id'].isin(subject_ids)]
                elif 'hadm_id' in chunk.columns:
                    filtered = chunk[chunk['hadm_id'].isin(hadm_ids)]
                else:
                    print(f"      ⚠️ {table_name}: subject_id/hadm_id 컬럼 없음")
                    return 0
                
                if not filtered.empty:
                    filtered_chunks.append(filtered)
                    total_rows += len(filtered)
                
                chunk_count += 1
                if chunk_count % 100 == 0:
                    print(f"      처리 중... {chunk_count * CHUNK_SIZE:,} 행 검사, {total_rows:,} 행 매칭")
            
            if filtered_chunks:
                result_df = pd.concat(filtered_chunks, ignore_index=True)
                result_df.to_csv(target_path, index=False)
                file_size = os.path.getsize(target_path) / (1024 * 1024)  # MB
                print(f"   ✅ {table_name}: {total_rows:,} 행 추출 ({file_size:.1f} MB)")
                return total_rows
            else:
                print(f"   ⚠️ {table_name}: 매칭 데이터 없음")
                return 0
                
        else:
            # 작은 파일은 한 번에 처리
            df = pd.read_csv(source_path)
            original_rows = len(df)
            
            if 'subject_id' in df.columns and 'hadm_id' in df.columns:
                filtered = df[
                    (df['subject_id'].isin(subject_ids)) | 
                    (df['hadm_id'].isin(hadm_ids))
                ]
            elif 'subject_id' in df.columns:
                filtered = df[df['subject_id'].isin(subject_ids)]
            elif 'hadm_id' in df.columns:
                filtered = df[df['hadm_id'].isin(hadm_ids)]
            else:
                print(f"      ⚠️ {table_name}: subject_id/hadm_id 컬럼 없음")
                return 0
            
            if not filtered.empty:
                filtered.to_csv(target_path, index=False)
                file_size = os.path.getsize(target_path) / (1024 * 1024)  # MB
                reduction_pct = (1 - len(filtered) / original_rows) * 100
                print(f"   ✅ {table_name}: {len(filtered):,} 행 추출 ({file_size:.1f} MB, {reduction_pct:.1f}% 감소)")
                return len(filtered)
            else:
                print(f"   ⚠️ {table_name}: 매칭 데이터 없음")
                return 0
                
    except Exception as e:
        print(f"   ❌ {table_name} 처리 중 오류: {e}")
        return 0

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 MIMIC-IV Hosp 필수 테이블 추출")
    print("=" * 80)
    
    start_time = datetime.now()
    
    # 결과 저장용
    extraction_stats = {
        'extraction_date': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'dictionary_tables': {},
        'patient_tables': {},
        'processing_time': None
    }
    
    # 1. 샘플 ID 로드
    subject_ids, hadm_ids = load_sampled_ids()
    extraction_stats['sampled_subjects'] = len(subject_ids)
    extraction_stats['sampled_admissions'] = len(hadm_ids)
    
    # 2. 사전 테이블 복사
    dict_count = copy_dictionary_tables()
    extraction_stats['dictionary_tables']['count'] = dict_count
    extraction_stats['dictionary_tables']['files'] = [
        'd_hcpcs.csv', 'd_icd_diagnoses.csv', 
        'd_icd_procedures.csv', 'd_labitems.csv'
    ]
    
    # 3. 필수 환자 데이터 테이블 추출
    print("\n3. 필수 환자 데이터 테이블 추출 중...")
    
    # 요청된 5개 필수 테이블
    essential_tables = [
        ('diagnoses_icd', False),      # 진단 코드
        ('drgcodes', False),           # DRG 코드
        # ('labevents', True),           # 검사 결과 (대용량) - 별도 처리 필요
        ('microbiologyevents', False), # 미생물 검사
        ('services', False)            # 진료 서비스
    ]
    
    print("\n   ⚠️ 참고: labevents는 매우 큰 파일(1.2억 행)이므로 별도로 처리합니다.")
    
    for table_name, use_chunks in essential_tables:
        row_count = extract_patient_table(table_name, subject_ids, hadm_ids, use_chunks)
        extraction_stats['patient_tables'][table_name] = row_count
    
    # 4. 처리 시간 계산
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    extraction_stats['processing_time'] = f"{processing_time:.1f} seconds"
    
    # 5. 통계 저장
    print("\n4. 추출 통계 저장 중...")
    stats_path = os.path.join(BASE_PATH, 'processed_data/hosp/extraction_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(extraction_stats, f, indent=2)
    print(f"✅ 통계 저장: extraction_stats.json")
    
    # 6. 요약 출력
    print("\n" + "=" * 80)
    print("✅ Hosp 필수 테이블 추출 완료!")
    print("=" * 80)
    
    print("\n[추출 요약]")
    print(f"• 처리 시간: {processing_time:.1f}초")
    print(f"• 샘플 환자: {len(subject_ids):,}명")
    print(f"• 샘플 입원: {len(hadm_ids):,}건")
    print(f"• 사전 테이블: {dict_count}개 (전체 복사)")
    
    total_rows = sum(extraction_stats['patient_tables'].values())
    successful_tables = sum(1 for v in extraction_stats['patient_tables'].values() if v > 0)
    print(f"• 환자 데이터: {successful_tables}/5개 테이블, 총 {total_rows:,} 행")
    
    print("\n[테이블별 통계]")
    for table, count in extraction_stats['patient_tables'].items():
        if count > 0:
            print(f"  ✓ {table}: {count:,} 행")
        else:
            print(f"  ✗ {table}: 데이터 없음")
    
    print(f"\n💾 저장 위치: processed_data/hosp/")
    print(f"📊 통계 파일: processed_data/hosp/extraction_stats.json")
    
    return extraction_stats

if __name__ == "__main__":
    stats = main()