# MIMIC-IV 샘플링 방법론 상세 보고서

## 목차
1. [서론](#1-서론)
2. [이론적 배경](#2-이론적-배경)
3. [샘플링 설계](#3-샘플링-설계)
4. [구현 방법](#4-구현-방법)
5. [결과 분석](#5-결과-분석)
6. [검증 및 품질 보증](#6-검증-및-품질-보증)
7. [제한사항](#7-제한사항)
8. [결론](#8-결론)

---

## 1. 서론

### 1.1 연구 배경
MIMIC-IV는 382,278명의 환자와 523,740건의 입원 기록을 포함하는 대규모 데이터셋입니다.
이러한 대규모 데이터는 풍부한 정보를 제공하지만, 동시에 다음과 같은 도전과제를 제시합니다:

- **계산 자원 제한**: 전체 데이터 처리에 많은 시간과 메모리 필요
- **클래스 불균형**: 사망률 약 2.5%로 심각한 불균형
- **다양한 사망 유형**: 병원 내 사망과 병원 후 사망의 임상적 의미 차이

### 1.2 연구 목적
본 샘플링 방법론은 다음을 목표로 합니다:
1. 사망률 예측 모델 개발을 위한 균형잡힌 데이터셋 구축
2. 단기(병원 내) 및 장기(병원 후) 예후를 모두 고려
3. 재현 가능하고 과학적인 샘플링 프로세스 확립

---

## 2. 이론적 배경

### 2.1 MIMIC-IV의 사망 데이터 구조

#### 2.1.1 병원 내 사망 (In-hospital mortality)
- **정의**: `hospital_expire_flag = 1`
- **의미**: 해당 입원 기간 중 병원에서 사망
- **데이터 출처**: 병원 전자의무기록 시스템
- **임상적 의의**: 급성 중증도 및 치료 반응성 반영

#### 2.1.2 병원 후 사망 (Post-hospital mortality)
- **정의**: `hospital_expire_flag = 0 AND dod IS NOT NULL`
- **의미**: 퇴원 후 1년 이내 사망
- **데이터 출처**: CDC 주 사망 기록 (MIMIC-IV v2.0부터)
- **임상적 의의**: 장기 예후 및 퇴원 후 관리 질 반영

#### 2.1.3 생존 (Survived)
- **정의**: `dod IS NULL`
- **의미**: 마지막 퇴원 후 최소 1년 생존
- **검열(Censoring)**: 1년 이상 생존 시 추가 추적 없음

### 2.2 샘플링 이론

#### 2.2.1 층화 샘플링 (Stratified Sampling)
본 연구는 outcome 기반 층화 샘플링을 적용합니다:
- **층(Strata)**: 사망 유형별 3개 층
- **장점**: 각 outcome의 충분한 대표성 확보
- **단점**: 원본 분포와 다른 인위적 균형

#### 2.2.2 균형 데이터셋의 필요성
- **기계학습 관점**: 클래스 불균형으로 인한 편향 방지
- **통계적 검정력**: 각 그룹의 충분한 샘플 확보
- **임상적 타당성**: 다양한 예후 패턴 학습

---

## 3. 샘플링 설계

### 3.1 샘플 크기 결정

#### 3.1.1 전체 샘플 크기: 1,200건
**근거**:
```
최소 샘플 크기 = n × c × (1 + r)
- n: 그룹당 최소 샘플 (100)
- c: 그룹 수 (3)
- r: 안전 계수 (3.0)
= 100 × 3 × 4 = 1,200
```

#### 3.1.2 그룹별 할당
| 그룹 | 샘플 수 | 비율 | 근거 |
|------|---------|------|------|
| 병원 내 사망 | 300 | 25% | 급성 중증도 대표 |
| 병원 후 사망 | 300 | 25% | 장기 예후 대표 |
| 생존 | 600 | 50% | 대조군 역할 |

### 3.2 제외 기준

#### 3.2.1 0세 환자 제외
- **이유**: 신생아/영아의 특수한 생리학적 특성
- **영향**: 전체 462,112건 중 약 61,628건 제외 (13.3%)

### 3.3 무작위화 전략
- **방법**: 단순 무작위 샘플링 (Simple Random Sampling)
- **시드값**: `random_state = 42`
- **이유**: 재현성 확보 및 선택 편향 최소화

---

## 4. 구현 방법

### 4.1 데이터 준비 단계

```python
# 1. 데이터 로드
admissions = pd.read_csv('admissions.csv')
patients = pd.read_csv('patients.csv')

# 2. 병합
df = admissions.merge(patients[['subject_id', 'anchor_age', 'dod']], 
                     on='subject_id')

# 3. 0세 제외
df_filtered = df[df['anchor_age'] > 0]
```

### 4.2 분류 알고리즘

```python
# 명확한 분류 로직
def classify_mortality(row):
    if row['hospital_expire_flag'] == 1:
        return 'in_hospital_death'
    elif row['hospital_expire_flag'] == 0 and pd.notna(row['dod']):
        return 'post_hospital_death'
    elif pd.isna(row['dod']):
        return 'survived'
    else:
        return 'undefined'  # 예외 처리
```

### 4.3 샘플링 실행

```python
# 각 그룹에서 샘플링
samples = {}
for group_name, target_size in [
    ('in_hospital_death', 300),
    ('post_hospital_death', 300),
    ('survived', 600)
]:
    group_data = df_filtered[df_filtered['mortality_group'] == group_name]
    actual_size = min(target_size, len(group_data))
    samples[group_name] = group_data.sample(
        n=actual_size, 
        random_state=42
    )
```

### 4.4 관련 데이터 추출

#### 4.4.1 추출 전략
샘플된 1,200개 admission의 hadm_id를 기준으로 관련 데이터 추출:

**필터링 로직 개선**:
```python
# 효율적: hadm_id만 사용
filtered = df[df['hadm_id'].isin(sampled_hadm_ids)]

# 비효율적 (기존): subject_id OR hadm_id
# filtered = df[(df['subject_id'].isin(subject_ids)) | 
#               (df['hadm_id'].isin(hadm_ids))]
```

#### 4.4.2 Core 테이블 추출
- **patients**: 1,171명 (subject_id 기준)
- **transfers**: 4,682건 (hadm_id 기준)
- **admissions**: 1,200건 (이미 샘플링됨)

#### 4.4.3 Hosp 테이블 추출

**환자 데이터 테이블** (hadm_id로 필터링):
| 테이블 | 원본 크기 | 추출된 크기 | 추출률 |
|--------|-----------|-------------|--------|
| diagnoses_icd | 5,280,351 | 17,471 | 0.33% |
| labevents | 122,103,667 | 334,442 | 0.27% |
| prescriptions | 17,008,053 | 73,200 | 0.43% |
| microbiologyevents | 3,228,713 | 8,777 | 0.27% |
| procedures_icd | 779,625 | 2,831 | 0.36% |
| drgcodes | 769,622 | 1,897 | 0.25% |
| services | 562,892 | 1,376 | 0.24% |

**사전 테이블** (전체 복사):
- d_hcpcs: HCPCS 코드 정의
- d_icd_diagnoses: ICD 진단 코드 정의
- d_icd_procedures: ICD 시술 코드 정의
- d_labitems: 검사 항목 정의

#### 4.4.4 메모리 최적화
대용량 테이블(labevents) 처리:
```python
# 청크 단위 처리
for chunk in pd.read_csv(source_path, chunksize=100000):
    filtered = chunk[chunk['hadm_id'].isin(hadm_ids)]
    if not filtered.empty:
        chunks.append(filtered)
```

---

## 5. 결과 분석

### 5.1 샘플링 결과 요약

#### 5.1.1 전체 통계
```
원본 데이터 (0세 제외):
• 전체: 462,112건
• 병원 내 사망: 9,137건 (1.98%)
• 병원 후 사망: 25,095건 (5.43%)
• 생존: 427,880건 (92.59%)

샘플 데이터:
• 전체: 1,200건
• 병원 내 사망: 300건 (25.0%)
• 병원 후 사망: 300건 (25.0%)
• 생존: 600건 (50.0%)
```

#### 5.1.2 추출 효율성
| 그룹 | 가용 데이터 | 요청 샘플 | 실제 샘플 | 샘플링률 |
|------|------------|-----------|-----------|----------|
| 병원 내 사망 | 9,137 | 300 | 300 | 3.28% |
| 병원 후 사망 | 25,095 | 300 | 300 | 1.20% |
| 생존 | 427,880 | 600 | 600 | 0.14% |

### 5.2 샘플 특성

#### 5.2.1 환자 분포
- **고유 환자 수**: 1,171명 (1,200건 중)
- **재입원률**: 2.5% (29명이 2회 이상 입원)

#### 5.2.2 관련 데이터 규모
- **Transfers**: 4,682건 (평균 3.9건/admission)
- **ICU stays**: 예상 약 400-500건

---

## 6. 검증 및 품질 보증

### 6.1 데이터 무결성 검증

#### 6.1.1 분류 검증
```python
# 검증 코드
assert len(in_hospital) + len(post_hospital) + len(survived) == len(df_filtered)
assert df_filtered[df_filtered['hospital_expire_flag'] == 1]['dod'].notna().all()
```

#### 6.1.2 ID 일관성
- 모든 sampled hadm_id가 원본에 존재
- 모든 sampled subject_id가 patients 테이블에 존재

### 6.2 통계적 검증

#### 6.2.1 무작위성 검정
- Chi-square test for independence
- Kolmogorov-Smirnov test for distribution

#### 6.2.2 대표성 평가
- 연령 분포 비교 (원본 vs 샘플)
- 성별 분포 비교
- 입원 기간 분포 비교

### 6.3 재현성 보장
- **고정 시드**: random_state = 42
- **환경 독립성**: pandas 버전에 관계없이 동일 결과
- **문서화**: 모든 단계 상세 기록

---

## 7. 제한사항

### 7.1 샘플링 편향
1. **Outcome 균형화**: 실제 사망률과 다른 인위적 분포
2. **시간적 편향**: 최근 환자일수록 병원 후 사망 정보 부족 가능
3. **지역적 편향**: Massachusetts 외 지역 환자의 사망 정보 불완전

### 7.2 데이터 제한
1. **검열**: 1년 이상 추적 불가
2. **결측**: 일부 환자의 dod 정보 부재
3. **불일치**: hospital_expire_flag와 deathtime 간 불일치 (소수)

### 7.3 일반화 제한
1. **단일 기관**: Beth Israel Deaconess Medical Center
2. **ICU 중심**: 일반 병동 환자 과소대표
3. **미국 의료**: 타 국가 적용 시 주의 필요

---

## 8. 결론

### 8.1 성과
1. **균형 데이터셋**: 사망률 예측 모델에 적합한 1,200건 샘플
2. **포괄적 outcome**: 단기/장기 사망 모두 포함
3. **재현 가능**: 명확한 방법론과 코드 제공

### 8.2 활용 방안
1. **예측 모델 개발**: 기계학습 모델 훈련용 데이터
2. **통계 분석**: 사망 위험 요인 분석
3. **방법론 검증**: 샘플링 전략의 효과성 평가

### 8.3 향후 개선 방향
1. **동적 샘플링**: 시간 경과에 따른 업데이트
2. **층화 변수 추가**: 연령, 진단명 등 고려
3. **외부 검증**: 타 기관 데이터로 검증

---

## 부록

### A. 실행 환경
- Python 3.8+
- pandas 2.0+
- numpy 1.24+

### B. 파일 구조
```
analysis_samplingmethod/
├── scripts/analysis/
│   ├── perform_sampling.py (전체 기능)
│   └── perform_sampling_test.py (최적화 버전)
├── data/
│   ├── sampled_ids.csv
│   └── sampling_results.json
└── figures/
    └── sampling_distribution.png

processed_data/
├── core/
│   ├── admissions_sampled.csv
│   ├── patients_sampled.csv
│   └── transfers_sampled.csv
└── [추가 테이블]
```

### C. 참고 문헌
1. MIT-LCP. (2022). MIMIC-IV v2.0 Release Notes.
2. Johnson, A., et al. (2023). MIMIC-IV, a freely accessible electronic health record dataset. Scientific Data.
3. GitHub Issues: #190, #1199, #1406, #1411 - MIT-LCP/mimic-code

---

*작성일: 2025년 8월*  
*버전: 1.0*  
*작성자: MIMIC 분석팀*