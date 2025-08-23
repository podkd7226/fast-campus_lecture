#!/usr/bin/env python3
"""
분석 방법 비교 스크립트
서로 다른 분석 방법의 결과를 비교하여 차이점을 시각화합니다.
특히 21개 검사 vs 98개 검사 분석의 차이를 보여줍니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
import platform

# 한글 폰트 설정
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:  # Linux
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
BASE_PATH = Path('/Users/hyungjun/Desktop/fast campus_lecture')
INITIAL_LAB_PATH = BASE_PATH / 'analysis_initial_lab'
ERROR_EVAL_PATH = BASE_PATH / 'analysis_error_evaluation'

class AnalysisMethodComparator:
    """분석 방법 비교 클래스"""
    
    def __init__(self):
        self.data_21labs = {}
        self.data_98labs = {}
        self.comparison_results = {}
    
    def load_data(self):
        """두 분석 방법의 데이터 로드"""
        print("데이터 로딩 중...")
        
        # 21개 검사 분석 (잘못된 방법)
        self.data_21labs['wide'] = pd.read_csv(
            INITIAL_LAB_PATH / 'data' / 'admission_day_labs_wide.csv'
        )
        self.data_21labs['long'] = pd.read_csv(
            INITIAL_LAB_PATH / 'data' / 'admission_day_labs.csv'
        )
        
        # 98개 검사 분석 (올바른 방법)
        self.data_98labs['wide'] = pd.read_csv(
            INITIAL_LAB_PATH / 'data' / 'initial_labs_wide.csv'
        )
        self.data_98labs['long'] = pd.read_csv(
            INITIAL_LAB_PATH / 'data' / 'initial_labs_long.csv'
        )
        
        print(f"✅ 21개 검사 분석: {len(self.data_21labs['wide'])}건")
        print(f"✅ 98개 검사 분석: {len(self.data_98labs['wide'])}건")
    
    def compare_coverage(self):
        """커버리지 비교"""
        print("\n1. 커버리지 비교")
        print("-" * 50)
        
        # 21개 검사
        n_21 = len(self.data_21labs['wide'])
        pct_21 = n_21 / 1200 * 100
        
        # 98개 검사 (검사가 있는 입원만)
        lab_cols_98 = [col for col in self.data_98labs['wide'].columns 
                      if col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]
        has_any_lab_98 = ~self.data_98labs['wide'][lab_cols_98].isna().all(axis=1)
        n_98 = has_any_lab_98.sum()
        pct_98 = n_98 / 1200 * 100
        
        self.comparison_results['coverage'] = {
            '21_labs': {'count': n_21, 'pct': pct_21},
            '98_labs': {'count': n_98, 'pct': pct_98},
            'difference': n_98 - n_21,
            'missing_in_21': 1200 - n_21
        }
        
        print(f"21개 검사: {n_21}건 ({pct_21:.1f}%)")
        print(f"98개 검사: {n_98}건 ({pct_98:.1f}%)")
        print(f"차이: {n_98 - n_21}건 ({pct_98 - pct_21:.1f}%p)")
        print(f"\n21개 검사에서 놓친 입원: {1200 - n_21}건")
    
    def compare_mortality(self):
        """사망률 비교"""
        print("\n2. 사망률 비교")
        print("-" * 50)
        
        # 21개 검사 그룹
        mortality_21 = self.data_21labs['wide']['hospital_expire_flag'].mean() * 100
        died_21 = self.data_21labs['wide']['hospital_expire_flag'].sum()
        
        # 98개 검사 그룹 (전체)
        mortality_98 = self.data_98labs['wide']['hospital_expire_flag'].mean() * 100
        died_98 = self.data_98labs['wide']['hospital_expire_flag'].sum()
        
        self.comparison_results['mortality'] = {
            '21_labs': {'rate': mortality_21, 'died': died_21},
            '98_labs': {'rate': mortality_98, 'died': died_98},
            'difference': mortality_21 - mortality_98
        }
        
        print(f"21개 검사 그룹: {mortality_21:.1f}% ({died_21}/{len(self.data_21labs['wide'])})")
        print(f"98개 검사 그룹: {mortality_98:.1f}% ({died_98}/{len(self.data_98labs['wide'])})")
        print(f"차이: {mortality_21 - mortality_98:+.1f}%p")
        
        # 누락된 환자의 사망률
        hadm_21 = set(self.data_21labs['wide']['hadm_id'])
        hadm_98 = set(self.data_98labs['wide']['hadm_id'])
        missing_hadm = hadm_98 - hadm_21
        
        missing_df = self.data_98labs['wide'][
            self.data_98labs['wide']['hadm_id'].isin(missing_hadm)
        ]
        missing_mortality = missing_df['hospital_expire_flag'].mean() * 100
        
        print(f"\n누락된 {len(missing_hadm)}명의 사망률: {missing_mortality:.1f}%")
        self.comparison_results['missing_mortality'] = missing_mortality
    
    def compare_lab_availability(self):
        """검사별 가용성 비교"""
        print("\n3. 검사별 가용성 비교")
        print("-" * 50)
        
        # 21개 검사의 공통 검사들
        common_labs = ['Hematocrit', 'Hemoglobin', 'White_Blood_Cells', 
                      'Creatinine', 'Glucose', 'Sodium', 'Potassium']
        
        availability_comparison = {}
        
        for lab in common_labs:
            if lab in self.data_21labs['wide'].columns:
                avail_21 = self.data_21labs['wide'][lab].notna().sum()
                pct_21 = avail_21 / len(self.data_21labs['wide']) * 100
            else:
                avail_21 = 0
                pct_21 = 0
            
            # 98개 검사에서 해당 검사 찾기 (언더스코어 처리)
            lab_98 = lab.replace('_', ' ')
            if lab_98 in self.data_98labs['wide'].columns:
                avail_98 = self.data_98labs['wide'][lab_98].notna().sum()
                pct_98 = avail_98 / len(self.data_98labs['wide']) * 100
            else:
                # 다시 시도
                lab_98 = lab
                if lab_98 in self.data_98labs['wide'].columns:
                    avail_98 = self.data_98labs['wide'][lab_98].notna().sum()
                    pct_98 = avail_98 / len(self.data_98labs['wide']) * 100
                else:
                    avail_98 = 0
                    pct_98 = 0
            
            availability_comparison[lab] = {
                '21_labs': {'count': avail_21, 'pct': pct_21},
                '98_labs': {'count': avail_98, 'pct': pct_98}
            }
            
            print(f"{lab}:")
            print(f"  21개 분석: {avail_21}/{len(self.data_21labs['wide'])} ({pct_21:.1f}%)")
            print(f"  98개 분석: {avail_98}/1200 ({pct_98:.1f}%)")
        
        self.comparison_results['lab_availability'] = availability_comparison
    
    def visualize_comparison(self):
        """비교 결과 시각화"""
        print("\n4. 시각화 생성 중...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 커버리지 비교
        ax1 = axes[0, 0]
        categories = ['21개 검사\n(잘못된 방법)', '98개 검사\n(올바른 방법)']
        counts = [self.comparison_results['coverage']['21_labs']['count'],
                 self.comparison_results['coverage']['98_labs']['count']]
        missing = [1200 - counts[0], 1200 - counts[1]]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, counts, width, label='분석 포함', color='#2E86AB')
        bars2 = ax1.bar(x + width/2, missing, width, label='누락', color='#A23B72')
        
        ax1.set_ylabel('입원 수')
        ax1.set_title('분석 커버리지 비교')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.set_ylim(0, 1300)
        
        # 막대 위에 수치 표시
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}건\n({height/12:.1f}%)',
                    ha='center', va='bottom')
        
        # 2. 사망률 비교
        ax2 = axes[0, 1]
        mortality_data = [
            self.comparison_results['mortality']['21_labs']['rate'],
            self.comparison_results['mortality']['98_labs']['rate'],
            self.comparison_results['missing_mortality']
        ]
        labels = ['21개 검사\n(n=427)', '98개 검사\n(n=1200)', '누락된 환자\n(n=773)']
        colors = ['#E63946', '#2A9D8F', '#F77F00']
        
        bars = ax2.bar(labels, mortality_data, color=colors, alpha=0.7)
        ax2.set_ylabel('사망률 (%)')
        ax2.set_title('그룹별 사망률 비교')
        ax2.set_ylim(0, 40)
        
        # 수치 표시
        for bar, val in zip(bars, mortality_data):
            ax2.text(bar.get_x() + bar.get_width()/2., val + 1,
                    f'{val:.1f}%', ha='center', va='bottom')
        
        # 기준선
        ax2.axhline(y=25, color='gray', linestyle='--', alpha=0.5, label='전체 평균')
        ax2.legend()
        
        # 3. hadm_id 매칭 문제
        ax3 = axes[1, 0]
        
        # 원 그래프로 표현
        sizes = [427, 616, 157]  # 매칭됨, hadm_id null로 누락, 기타
        labels_pie = ['hadm_id 매칭\n(427건)', 
                     'hadm_id NULL\n누락 (616건)', 
                     '검사 없음\n(157건)']
        colors_pie = ['#2E86AB', '#A23B72', '#F18F01']
        explode = (0.1, 0.1, 0)
        
        ax3.pie(sizes, explode=explode, labels=labels_pie, colors=colors_pie,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax3.set_title('21개 검사 분석의 데이터 손실 원인')
        
        # 4. 검사 가용성 비교
        ax4 = axes[1, 1]
        
        if self.comparison_results['lab_availability']:
            labs = list(self.comparison_results['lab_availability'].keys())
            pct_21 = [v['21_labs']['pct'] for v in self.comparison_results['lab_availability'].values()]
            pct_98 = [v['98_labs']['pct'] for v in self.comparison_results['lab_availability'].values()]
            
            x = np.arange(len(labs))
            width = 0.35
            
            bars1 = ax4.bar(x - width/2, pct_21, width, label='21개 검사 (n=427)', color='#E63946')
            bars2 = ax4.bar(x + width/2, pct_98, width, label='98개 검사 (n=1200)', color='#2A9D8F')
            
            ax4.set_xlabel('검사 항목')
            ax4.set_ylabel('가용성 (%)')
            ax4.set_title('주요 검사 가용성 비교')
            ax4.set_xticks(x)
            ax4.set_xticklabels(labs, rotation=45, ha='right')
            ax4.legend()
            ax4.set_ylim(0, 100)
        
        plt.suptitle('21개 검사 vs 98개 검사 분석 방법 비교', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # 저장
        output_path = ERROR_EVAL_PATH / 'figures' / 'analysis_method_comparison.png'
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 시각화 저장: {output_path}")
        plt.show()
    
    def save_comparison_report(self):
        """비교 결과 저장"""
        output_path = ERROR_EVAL_PATH / 'data' / 'comparison_results.json'
        output_path.parent.mkdir(exist_ok=True)
        
        # int64를 int로 변환하는 함수
        def convert_int64(obj):
            if isinstance(obj, dict):
                return {k: convert_int64(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_int64(item) for item in obj]
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            else:
                return obj
        
        # 결과를 변환
        json_safe_results = convert_int64(self.comparison_results)
        
        with open(output_path, 'w') as f:
            json.dump(json_safe_results, f, indent=2)
        
        print(f"\n📄 비교 보고서 저장: {output_path}")
    
    def run(self):
        """전체 비교 실행"""
        print("="*60)
        print("🔍 분석 방법 비교 시작")
        print("="*60)
        
        self.load_data()
        self.compare_coverage()
        self.compare_mortality()
        self.compare_lab_availability()
        self.visualize_comparison()
        self.save_comparison_report()
        
        print("\n" + "="*60)
        print("✅ 분석 완료!")
        print("="*60)


def main():
    """메인 함수"""
    comparator = AnalysisMethodComparator()
    comparator.run()


if __name__ == "__main__":
    main()