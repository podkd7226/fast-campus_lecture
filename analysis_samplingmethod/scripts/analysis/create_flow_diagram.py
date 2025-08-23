#!/usr/bin/env python3
"""
MIMIC-IV 샘플링 Flow Diagram 생성 스크립트
전체 데이터셋에서 샘플링까지의 흐름을 시각화
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def create_flow_diagram():
    # 한글 폰트 설정
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    
    # Figure 설정
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 색상 정의
    color_total = '#E8F4F8'
    color_filtered = '#D1E9F0'
    color_death_hospital = '#FFE4E4'
    color_death_post = '#FFD9CC'
    color_survived = '#E4F7E4'
    color_sample = '#FFE5B4'
    
    # 1. 전체 데이터셋 (제목을 박스 내부로 이동)
    total_box = FancyBboxPatch((1, 8.2), 8, 1.3,
                               boxstyle="round,pad=0.05",
                               facecolor=color_total,
                               edgecolor='black',
                               linewidth=2)
    ax.add_patch(total_box)
    ax.text(5, 9.0, 'MIMIC-IV Total Dataset', ha='center', va='center', fontsize=14, fontweight='bold')
    ax.text(5, 8.5, '523,740 admissions', ha='center', va='center', fontsize=11)
    
    # 화살표 1
    arrow1 = FancyArrowPatch((5, 8.0), (5, 7.3),
                            arrowstyle='->,head_width=0.3,head_length=0.2',
                            linewidth=2, color='gray')
    ax.add_patch(arrow1)
    ax.text(6.2, 7.6, 'Exclude age=0\n(61,628 admissions)', ha='left', va='center', fontsize=9, style='italic')
    
    # 2. 0세 제외 후
    filtered_box = FancyBboxPatch((1, 6.3), 8, 1,
                                  boxstyle="round,pad=0.05",
                                  facecolor=color_filtered,
                                  edgecolor='black',
                                  linewidth=2)
    ax.add_patch(filtered_box)
    ax.text(5, 7.0, 'Filtered Dataset (age > 0)', ha='center', va='center', fontsize=13, fontweight='bold')
    ax.text(5, 6.6, '462,112 admissions', ha='center', va='center', fontsize=11)
    
    # 화살표 2 (3방향 분기)
    # 병원 내 사망
    arrow2a = FancyArrowPatch((2.5, 6.1), (1.5, 5.1),
                             arrowstyle='->,head_width=0.2,head_length=0.15',
                             linewidth=1.5, color='gray')
    ax.add_patch(arrow2a)
    
    # 병원 후 사망
    arrow2b = FancyArrowPatch((5, 6.1), (5, 5.1),
                             arrowstyle='->,head_width=0.2,head_length=0.15',
                             linewidth=1.5, color='gray')
    ax.add_patch(arrow2b)
    
    # 생존
    arrow2c = FancyArrowPatch((7.5, 6.1), (8.5, 5.1),
                             arrowstyle='->,head_width=0.2,head_length=0.15',
                             linewidth=1.5, color='gray')
    ax.add_patch(arrow2c)
    
    # 3. 분류된 그룹들
    # 병원 내 사망
    hospital_box = FancyBboxPatch((0.2, 4.0), 2.5, 1,
                                  boxstyle="round,pad=0.03",
                                  facecolor=color_death_hospital,
                                  edgecolor='darkred',
                                  linewidth=1.5)
    ax.add_patch(hospital_box)
    ax.text(1.45, 4.7, 'In-Hospital Death', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(1.45, 4.4, '9,137 (2.0%)', ha='center', va='center', fontsize=9)
    ax.text(1.45, 4.15, 'of total', ha='center', va='center', fontsize=8, style='italic')
    
    # 병원 후 사망
    post_box = FancyBboxPatch((3.8, 4.0), 2.5, 1,
                              boxstyle="round,pad=0.03",
                              facecolor=color_death_post,
                              edgecolor='darkorange',
                              linewidth=1.5)
    ax.add_patch(post_box)
    ax.text(5.05, 4.7, 'Post-Hospital Death', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.05, 4.4, '25,095 (5.4%)', ha='center', va='center', fontsize=9)
    ax.text(5.05, 4.15, 'of total', ha='center', va='center', fontsize=8, style='italic')
    
    # 생존
    survived_box = FancyBboxPatch((7.3, 4.0), 2.5, 1,
                                  boxstyle="round,pad=0.03",
                                  facecolor=color_survived,
                                  edgecolor='darkgreen',
                                  linewidth=1.5)
    ax.add_patch(survived_box)
    ax.text(8.55, 4.7, 'Survived', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(8.55, 4.4, '427,880 (92.6%)', ha='center', va='center', fontsize=9)
    ax.text(8.55, 4.15, 'of total', ha='center', va='center', fontsize=8, style='italic')
    
    # 샘플링 화살표
    # 병원 내 사망
    arrow3a = FancyArrowPatch((1.45, 3.8), (1.45, 3.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='darkred')
    ax.add_patch(arrow3a)
    ax.text(0.5, 3.4, 'Random\nSample', ha='center', va='center', fontsize=8)
    
    # 병원 후 사망
    arrow3b = FancyArrowPatch((5.05, 3.8), (5.05, 3.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='darkorange')
    ax.add_patch(arrow3b)
    ax.text(4.1, 3.4, 'Random\nSample', ha='center', va='center', fontsize=8)
    
    # 생존
    arrow3c = FancyArrowPatch((8.55, 3.8), (8.55, 3.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='darkgreen')
    ax.add_patch(arrow3c)
    ax.text(7.6, 3.4, 'Random\nSample', ha='center', va='center', fontsize=8)
    
    # 4. 샘플된 데이터
    # 병원 내 사망 샘플
    sample_hospital = FancyBboxPatch((0.2, 2.0), 2.5, 0.9,
                                     boxstyle="round,pad=0.03",
                                     facecolor=color_sample,
                                     edgecolor='darkred',
                                     linewidth=1.5)
    ax.add_patch(sample_hospital)
    ax.text(1.45, 2.6, '300 samples', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(1.45, 2.3, '(3.3% of 9,137)', ha='center', va='center', fontsize=8)
    
    # 병원 후 사망 샘플
    sample_post = FancyBboxPatch((3.8, 2.0), 2.5, 0.9,
                                boxstyle="round,pad=0.03",
                                facecolor=color_sample,
                                edgecolor='darkorange',
                                linewidth=1.5)
    ax.add_patch(sample_post)
    ax.text(5.05, 2.6, '300 samples', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.05, 2.3, '(1.2% of 25,095)', ha='center', va='center', fontsize=8)
    
    # 생존 샘플
    sample_survived = FancyBboxPatch((7.3, 2.0), 2.5, 0.9,
                                     boxstyle="round,pad=0.03",
                                     facecolor=color_sample,
                                     edgecolor='darkgreen',
                                     linewidth=1.5)
    ax.add_patch(sample_survived)
    ax.text(8.55, 2.6, '600 samples', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(8.55, 2.3, '(0.14% of 427,880)', ha='center', va='center', fontsize=8)
    
    # 최종 화살표
    arrow4a = FancyArrowPatch((1.45, 1.8), (3.5, 1.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='gray')
    ax.add_patch(arrow4a)
    
    arrow4b = FancyArrowPatch((5.05, 1.8), (5.05, 1.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='gray')
    ax.add_patch(arrow4b)
    
    arrow4c = FancyArrowPatch((8.55, 1.8), (6.5, 1.0),
                             arrowstyle='->,head_width=0.15,head_length=0.1',
                             linewidth=1.2, color='gray')
    ax.add_patch(arrow4c)
    
    # 5. 최종 균형 데이터셋
    final_box = FancyBboxPatch((2, 0.1), 6, 1,
                               boxstyle="round,pad=0.05",
                               facecolor='#FFD700',
                               edgecolor='black',
                               linewidth=2.5)
    ax.add_patch(final_box)
    ax.text(5, 0.8, 'Final Balanced Dataset', ha='center', va='center', fontsize=13, fontweight='bold')
    ax.text(5, 0.5, '1,200 admissions', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(5, 0.25, '25% : 25% : 50%', ha='center', va='center', fontsize=10)
    
    # 제목 (별도로 표시하지 않고 첫 번째 박스에 포함됨)
    
    # 범례
    legend_elements = [
        mpatches.Rectangle((0, 0), 1, 1, fc=color_death_hospital, ec='darkred', label='In-Hospital Death'),
        mpatches.Rectangle((0, 0), 1, 1, fc=color_death_post, ec='darkorange', label='Post-Hospital Death'),
        mpatches.Rectangle((0, 0), 1, 1, fc=color_survived, ec='darkgreen', label='Survived'),
        mpatches.Rectangle((0, 0), 1, 1, fc=color_sample, ec='black', label='Sampled Data')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    # Random State 표시
    ax.text(9.5, 0.2, 'Random State: 42', ha='right', va='bottom', fontsize=8, style='italic')
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    import os
    
    # 그래프 생성
    fig = create_flow_diagram()
    
    # 저장 경로
    output_dir = '/Users/hyungjun/Desktop/fast campus_lecture/analysis_samplingmethod/figures'
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'sampling_flow_diagram.png')
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Flow diagram saved to: {output_path}")
    
    plt.show()