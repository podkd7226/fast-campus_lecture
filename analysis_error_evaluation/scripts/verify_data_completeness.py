#!/usr/bin/env python3
"""
데이터 완전성 검증 스크립트
데이터 처리 전후의 레코드 수, 키 값, 분포 등을 비교하여
데이터 손실이나 왜곡이 없는지 자동으로 검증합니다.
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
import json
from datetime import datetime

class DataCompletenessVerifier:
    """데이터 완전성 검증 클래스"""
    
    def __init__(self, input_file, output_file, key_column='hadm_id'):
        """
        Args:
            input_file: 원본 데이터 파일 경로
            output_file: 처리된 데이터 파일 경로
            key_column: 고유 식별자 컬럼명
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.key_column = key_column
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'input_file': str(input_file),
            'output_file': str(output_file),
            'checks': {},
            'warnings': [],
            'errors': []
        }
    
    def load_data(self):
        """데이터 로드"""
        try:
            self.input_df = pd.read_csv(self.input_file)
            self.output_df = pd.read_csv(self.output_file)
            print(f"✅ 데이터 로드 완료")
            print(f"   입력: {self.input_file.name} ({len(self.input_df):,} rows)")
            print(f"   출력: {self.output_file.name} ({len(self.output_df):,} rows)")
            return True
        except Exception as e:
            self.report['errors'].append(f"데이터 로드 실패: {str(e)}")
            print(f"❌ 데이터 로드 실패: {str(e)}")
            return False
    
    def check_row_count(self):
        """행 수 검증"""
        print("\n1. 행 수 검증")
        input_rows = len(self.input_df)
        output_rows = len(self.output_df)
        
        self.report['checks']['row_count'] = {
            'input': input_rows,
            'output': output_rows,
            'difference': output_rows - input_rows,
            'ratio': output_rows / input_rows if input_rows > 0 else 0
        }
        
        if output_rows == input_rows:
            print(f"   ✅ 행 수 일치: {input_rows:,}")
        elif output_rows > input_rows:
            print(f"   ⚠️ 행 증가: {input_rows:,} → {output_rows:,} (+{output_rows-input_rows:,})")
            self.report['warnings'].append(f"행 수 증가: {output_rows-input_rows:,}건")
        else:
            loss_pct = (input_rows - output_rows) / input_rows * 100
            print(f"   ❌ 행 손실: {input_rows:,} → {output_rows:,} (-{input_rows-output_rows:,}, {loss_pct:.1f}%)")
            
            if loss_pct > 50:
                self.report['errors'].append(f"심각한 데이터 손실: {loss_pct:.1f}%")
            else:
                self.report['warnings'].append(f"데이터 손실: {loss_pct:.1f}%")
    
    def check_key_completeness(self):
        """키 값 완전성 검증"""
        print(f"\n2. 키 값({self.key_column}) 완전성 검증")
        
        if self.key_column not in self.input_df.columns:
            print(f"   ⚠️ 입력 데이터에 {self.key_column} 컬럼 없음")
            self.report['warnings'].append(f"키 컬럼 없음: {self.key_column}")
            return
        
        input_keys = set(self.input_df[self.key_column].dropna().unique())
        output_keys = set(self.output_df[self.key_column].dropna().unique()) if self.key_column in self.output_df.columns else set()
        
        missing_keys = input_keys - output_keys
        new_keys = output_keys - input_keys
        
        self.report['checks']['key_completeness'] = {
            'input_unique': len(input_keys),
            'output_unique': len(output_keys),
            'missing': len(missing_keys),
            'new': len(new_keys)
        }
        
        if len(missing_keys) == 0 and len(new_keys) == 0:
            print(f"   ✅ 모든 키 값 보존: {len(input_keys):,}개")
        else:
            if len(missing_keys) > 0:
                print(f"   ❌ 누락된 키: {len(missing_keys):,}개")
                if len(missing_keys) <= 10:
                    print(f"      {list(missing_keys)[:10]}")
                self.report['errors'].append(f"키 누락: {len(missing_keys)}개")
            
            if len(new_keys) > 0:
                print(f"   ⚠️ 새로운 키: {len(new_keys):,}개")
                self.report['warnings'].append(f"새로운 키: {len(new_keys)}개")
    
    def check_null_patterns(self):
        """NULL 패턴 검증"""
        print("\n3. NULL 패턴 검증")
        
        # 공통 컬럼 찾기
        common_cols = set(self.input_df.columns) & set(self.output_df.columns)
        
        null_changes = {}
        for col in common_cols:
            input_null_pct = self.input_df[col].isna().mean() * 100
            output_null_pct = self.output_df[col].isna().mean() * 100
            change = output_null_pct - input_null_pct
            
            if abs(change) > 5:  # 5% 이상 변화
                null_changes[col] = {
                    'input': input_null_pct,
                    'output': output_null_pct,
                    'change': change
                }
        
        self.report['checks']['null_patterns'] = null_changes
        
        if len(null_changes) == 0:
            print("   ✅ NULL 패턴 일관성 유지")
        else:
            print(f"   ⚠️ NULL 비율 변화 감지: {len(null_changes)}개 컬럼")
            for col, info in list(null_changes.items())[:5]:
                print(f"      {col}: {info['input']:.1f}% → {info['output']:.1f}% ({info['change']:+.1f}%p)")
    
    def check_value_distributions(self):
        """주요 값 분포 검증"""
        print("\n4. 값 분포 검증")
        
        # 숫자형 컬럼만 선택
        numeric_cols = set(self.input_df.select_dtypes(include=[np.number]).columns) & \
                      set(self.output_df.select_dtypes(include=[np.number]).columns)
        
        distribution_changes = {}
        for col in numeric_cols:
            if col == self.key_column:
                continue
                
            input_stats = {
                'mean': self.input_df[col].mean(),
                'std': self.input_df[col].std(),
                'min': self.input_df[col].min(),
                'max': self.input_df[col].max()
            }
            
            output_stats = {
                'mean': self.output_df[col].mean(),
                'std': self.output_df[col].std(),
                'min': self.output_df[col].min(),
                'max': self.output_df[col].max()
            }
            
            # 평균이 10% 이상 변화했는지 확인
            if not pd.isna(input_stats['mean']) and not pd.isna(output_stats['mean']):
                if input_stats['mean'] != 0:
                    mean_change = abs((output_stats['mean'] - input_stats['mean']) / input_stats['mean'])
                    if mean_change > 0.1:
                        distribution_changes[col] = {
                            'input_mean': input_stats['mean'],
                            'output_mean': output_stats['mean'],
                            'change_pct': mean_change * 100
                        }
        
        self.report['checks']['distributions'] = distribution_changes
        
        if len(distribution_changes) == 0:
            print("   ✅ 값 분포 일관성 유지")
        else:
            print(f"   ⚠️ 분포 변화 감지: {len(distribution_changes)}개 컬럼")
            for col, info in list(distribution_changes.items())[:5]:
                print(f"      {col}: 평균 {info['input_mean']:.2f} → {info['output_mean']:.2f} ({info['change_pct']:.1f}% 변화)")
    
    def check_join_quality(self):
        """JOIN 품질 검증 (hadm_id NULL 체크)"""
        print("\n5. JOIN 품질 검증")
        
        if 'hadm_id' in self.input_df.columns:
            input_null_hadm = self.input_df['hadm_id'].isna().sum()
            input_null_pct = input_null_hadm / len(self.input_df) * 100
            
            if 'hadm_id' in self.output_df.columns:
                output_null_hadm = self.output_df['hadm_id'].isna().sum()
                output_null_pct = output_null_hadm / len(self.output_df) * 100
                
                self.report['checks']['hadm_id_null'] = {
                    'input': {'count': int(input_null_hadm), 'pct': input_null_pct},
                    'output': {'count': int(output_null_hadm), 'pct': output_null_pct}
                }
                
                print(f"   hadm_id NULL:")
                print(f"      입력: {input_null_hadm:,}건 ({input_null_pct:.1f}%)")
                print(f"      출력: {output_null_hadm:,}건 ({output_null_pct:.1f}%)")
                
                if input_null_pct > 20 and output_null_pct == 0:
                    print("   ❌ 경고: hadm_id NULL이 모두 제거됨 (JOIN 문제 가능성)")
                    self.report['errors'].append("hadm_id NULL 모두 제거 - JOIN 오류 의심")
    
    def generate_report(self):
        """최종 보고서 생성"""
        print("\n" + "="*60)
        print("📋 검증 보고서")
        print("="*60)
        
        # 전체 상태 결정
        if len(self.report['errors']) > 0:
            status = "❌ FAIL"
            print(f"\n상태: {status}")
            print(f"오류: {len(self.report['errors'])}개")
            for error in self.report['errors']:
                print(f"  - {error}")
        elif len(self.report['warnings']) > 0:
            status = "⚠️ WARNING"
            print(f"\n상태: {status}")
            print(f"경고: {len(self.report['warnings'])}개")
            for warning in self.report['warnings']:
                print(f"  - {warning}")
        else:
            status = "✅ PASS"
            print(f"\n상태: {status}")
            print("모든 검증 통과")
        
        self.report['status'] = status
        
        # JSON 보고서 저장
        report_file = Path('data_completeness_report.json')
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"\n📄 상세 보고서: {report_file}")
        
        return status == "✅ PASS"
    
    def run(self):
        """전체 검증 실행"""
        print("="*60)
        print("🔍 데이터 완전성 검증 시작")
        print("="*60)
        
        if not self.load_data():
            return False
        
        self.check_row_count()
        self.check_key_completeness()
        self.check_null_patterns()
        self.check_value_distributions()
        self.check_join_quality()
        
        return self.generate_report()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='데이터 완전성 검증')
    parser.add_argument('--input', required=True, help='입력 데이터 파일')
    parser.add_argument('--output', required=True, help='출력 데이터 파일')
    parser.add_argument('--key', default='hadm_id', help='키 컬럼명 (기본: hadm_id)')
    
    args = parser.parse_args()
    
    verifier = DataCompletenessVerifier(args.input, args.output, args.key)
    success = verifier.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()