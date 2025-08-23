# 🔗 데이터 매칭 오류: hadm_id NULL 처리 실패 사례

## 📌 요약

**1,043건이 427건이 된 미스터리**
- 예상: 21개 검사 중 하나라도 있는 입원 1,043건 (86.9%)
- 실제: 427건만 추출 (35.6%)
- 원인: hadm_id NULL 처리 실패로 616건 손실

---

## 1. 문제 상황

### 1.1 코드 위치
- 파일: [`../analysis_initial_lab/scripts/analysis/extract_admission_day_labs.py`](../analysis_initial_lab/scripts/analysis/extract_admission_day_labs.py)
- 작성일: 2025-08-19
- 목적: 입원 당일 21개 주요 혈액검사 추출

### 1.2 예상 vs 실제

| 구분 | 예상 | 실제 | 차이 |
|------|------|------|------|
| 전체 입원 | 1,200건 | 1,200건 | - |
| 21개 검사 중 하나라도 | 1,043건 (86.9%) | 427건 (35.6%) | -616건 |
| 검사당 평균 가용성 | ~85% | ~85% | - |

**이상한 점**: 개별 검사 가용성은 정상인데 전체 건수가 1/3로 축소

---

## 2. 원인 분석

### 2.1 MIMIC-IV의 hadm_id 구조

```sql
-- labevents 테이블 구조
CREATE TABLE labevents (
    labevent_id INT,
    subject_id INT,        -- 환자 ID (항상 존재)
    hadm_id INT,          -- 입원 ID (NULL 가능!) ⚠️
    itemid INT,
    charttime TIMESTAMP,
    value VARCHAR,
    valuenum FLOAT
);
```

**핵심 문제**: 
- 외래/응급실 검사는 hadm_id가 NULL
- 전체 검사의 30.3%가 hadm_id NULL

### 2.2 잘못된 코드 분석

```python
# extract_admission_day_labs.py 84-93줄
# hadm_id가 있는 검사와 없는 검사 분리
labs_with_hadm = labevents_filtered[labevents_filtered['hadm_id'].notna()]
labs_without_hadm = labevents_filtered[labevents_filtered['hadm_id'].isna()]

# 1. hadm_id로 직접 매칭 (✅ 작동)
merged_with_hadm = labs_with_hadm.merge(
    admissions[['hadm_id', 'subject_id', 'admit_date', ...]],
    on='hadm_id',
    how='inner'  # ⚠️ INNER JOIN
)

# 2. subject_id와 날짜로 매칭 (❌ 실패)
if len(labs_without_hadm) > 0:
    merged_without_hadm = labs_without_hadm.merge(
        admissions[...],
        left_on=['subject_id', 'chart_date'],
        right_on=['subject_id', 'admit_date'],
        how='inner'  # ⚠️ 또 INNER JOIN
    )
```

### 2.3 실제 데이터 흐름

```
전체 21개 검사 데이터
├── hadm_id 있음 (69.7%)
│   └── INNER JOIN → 427건 매칭 ✅
└── hadm_id 없음 (30.3%)
    └── subject_id + 날짜 매칭 시도
        └── 실패 → 0건 ❌
        
최종 결과: 427건만 남음
```

---

## 3. 검증 실험

### 3.1 검증 코드

```python
import pandas as pd

# 21개 검사 항목
COMMON_LAB_ITEMS = [50983, 50971, 50902, ...]  # 21개

# 데이터 로드
admissions = pd.read_csv('admissions_sampled.csv')
labevents = pd.read_csv('labevents_sampled.csv')

# 방법 1: hadm_id로만 매칭
hadm_only = []
for adm in admissions.itertuples():
    labs = labevents[
        (labevents['hadm_id'] == adm.hadm_id) &
        (labevents['chart_date'] == adm.admit_date)
    ]
    if len(labs) > 0:
        hadm_only.append(adm.hadm_id)

print(f"hadm_id로만: {len(set(hadm_only))}건")  # 427건

# 방법 2: hadm_id + subject_id 복합 매칭
combined = []
for adm in admissions.itertuples():
    labs = labevents[
        ((labevents['hadm_id'] == adm.hadm_id) |  # OR 조건
         ((labevents['subject_id'] == adm.subject_id) & 
          (labevents['hadm_id'].isna()))) &
        (labevents['chart_date'] == adm.admit_date)
    ]
    if len(labs) > 0:
        combined.append(adm.hadm_id)

print(f"복합 매칭: {len(set(combined))}건")  # 1,043건
```

### 3.2 검증 결과

| 매칭 방법 | 결과 | 비율 |
|-----------|------|------|
| hadm_id만 | 427건 | 35.6% |
| hadm_id + subject_id | 1,043건 | 86.9% |
| 차이 (누락된 데이터) | 616건 | 51.3% |

---

## 4. 올바른 해결 방법

### 4.1 개선된 코드

```python
# extract_initial_labs_complete.py 93-108줄
for idx, admission in admissions.iterrows():
    hadm_id = admission['hadm_id']
    subject_id = admission['subject_id']
    admit_date = admission['admit_date']
    
    # hadm_id로 먼저 시도
    admission_labs = labevents[
        (labevents['hadm_id'] == hadm_id) & 
        (labevents['chart_date'] == admit_date)
    ]
    
    # hadm_id 매칭 실패시 subject_id + 날짜로 재시도
    if len(admission_labs) == 0:
        admission_labs = labevents[
            (labevents['subject_id'] == subject_id) & 
            (labevents['chart_date'] == admit_date)
        ]
        # hadm_id 보정
        if len(admission_labs) > 0:
            admission_labs = admission_labs.copy()
            admission_labs['hadm_id'] = hadm_id  # ✅ 보정
```

### 4.2 더 나은 방법: LEFT JOIN 활용

```python
# 모든 입원 유지
base_df = admissions[['hadm_id', 'subject_id', 'admit_date']].copy()

# LEFT JOIN으로 검사 데이터 병합
result = base_df.merge(
    lab_data,
    left_on=['hadm_id', 'admit_date'],
    right_on=['hadm_id', 'chart_date'],
    how='left'  # ✅ LEFT JOIN: 매칭 안 되어도 유지
)

# NULL 처리는 별도로
result['has_lab'] = result['itemid'].notna()
```

---

## 5. 영향 분석

### 5.1 누락된 616건의 특성

| 특성 | 값 | 의미 |
|------|-----|------|
| 비율 | 51.3% | 전체의 절반 이상 |
| 검사 위치 | 외래/응급실 | 입원 전 검사 |
| 환자 유형 | 계획 입원 | 사전 검사 완료 |
| 임상적 중요도 | 높음 | 입원 결정 검사 |

### 5.2 분석 결과 왜곡

| 지표 | 427건 분석 | 1,043건 분석 | 왜곡 |
|------|------------|-------------|------|
| 사망률 | 36.5% | ~25% | +11.5%p |
| 검사 완성도 | 85% | 65% | +20%p |
| 평균 검사 수 | 17.1개 | 13.7개 | +3.4개 |

**해석**: 427건은 병원 내 검사를 많이 한 중증 환자 위주

---

## 6. 교훈 및 체크리스트

### ✅ 데이터 매칭 체크리스트

- [ ] **JOIN 키 완전성 확인**
  - [ ] NULL 비율 확인
  - [ ] 대체 키 존재 여부
  
- [ ] **JOIN 방식 선택**
  - [ ] INNER JOIN: 완전 매칭만 필요할 때
  - [ ] LEFT JOIN: 전체 데이터 유지 필요할 때
  - [ ] OUTER JOIN: 양쪽 모두 보존
  
- [ ] **매칭 결과 검증**
  - [ ] 입력 건수 = 출력 건수?
  - [ ] 예상 비율과 실제 비율 비교
  - [ ] 누락 데이터 특성 분석
  
- [ ] **복합 키 처리**
  - [ ] OR 조건 고려
  - [ ] 우선순위 설정
  - [ ] 보정 로직 추가

### 🚨 위험 신호

1. **출력이 입력의 50% 미만**: 뭔가 크게 잘못됨
2. **특정 그룹만 남음**: 선택 편향 발생
3. **NULL이 모두 사라짐**: 정보 손실

### 💡 Best Practice

```python
# 항상 이렇게 시작
print(f"입력: {len(input_df)}건")
print(f"NULL 비율: {input_df['key'].isna().mean():.1%}")

# 매칭 수행
result = matching_function(input_df)

# 항상 이렇게 검증
print(f"출력: {len(result)}건")
print(f"매칭률: {len(result)/len(input_df):.1%}")
assert len(result) >= len(input_df) * 0.8, "너무 많은 데이터 손실!"
```

---

## 7. 참고 자료

### 관련 파일
- 잘못된 분석: [`extract_admission_day_labs.py`](../analysis_initial_lab/scripts/analysis/extract_admission_day_labs.py)
- 개선된 분석: [`extract_initial_labs_complete.py`](../analysis_initial_lab/scripts/analysis/extract_initial_labs_complete.py)
- 결과 비교: [`compare_analysis_methods.py`](./scripts/compare_analysis_methods.py)

### MIMIC-IV 문서
- [hadm_id NULL 처리 가이드](https://mimic.mit.edu/docs/iv/modules/hosp/labevents/)
- [테이블 관계도](https://mimic.mit.edu/docs/iv/modules/hosp/)

---

*작성일: 2025-08-20*  
*핵심 교훈: "NULL은 버그가 아니라 정보다"*