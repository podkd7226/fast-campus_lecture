# MIMIC-IV 나이 계산 완전 가이드

## 📌 개요

MIMIC-IV 데이터셋에서 환자의 정확한 나이를 계산하는 것은 예측 모델 개발에 매우 중요합니다. 이 문서는 MIMIC-IV의 날짜 비식별화 시스템과 올바른 나이 계산 방법을 상세히 설명합니다.

---

## 🔍 핵심 개념 이해

### 1. MIMIC-IV의 날짜 비식별화 시스템

MIMIC-IV는 HIPAA(Health Insurance Portability and Accountability Act) 규정을 준수하기 위해 모든 날짜를 미래로 이동시켰습니다[^1][^2].

#### 비식별화 원칙
- **환자별 독립적 이동**: 각 `subject_id`마다 고유한 날짜 이동값 적용
- **일관성 유지**: 한 환자 내에서 모든 날짜는 동일한 간격으로 이동
- **시간 관계 보존**: 날짜 간 간격은 원본과 동일하게 유지

```
실제 시간축:     1950 -------- 2010 -------- 2015
                  (출생)        (입원)        (퇴원)
                        60년          5년
                        
MIMIC-IV 시간축: 2100 -------- 2160 -------- 2165
                  (출생)        (입원)        (퇴원)
                        60년          5년
                      (간격 보존)
```

### 2. Anchor 변수의 의미

#### anchor_year
- **정의**: 환자의 비식별화된 시간축에서 기준이 되는 연도 (2100-2200 사이)[^3]
- **역할**: 각 환자의 시간 정보를 "고정"하는 기준점

#### anchor_age  
- **정의**: `anchor_year` 시점에서의 환자 나이[^3]
- **특이사항**: 89세 이상은 모두 91세로 그룹화 (HIPAA 규정)[^4]

#### anchor_year_group
- **정의**: 실제 데이터 수집 기간을 나타내는 3년 범위 (2008-2019)[^3]
- **용도**: 대략적인 실제 시기 파악

---

## 📐 올바른 나이 계산 방법

### 공식적인 계산 공식[^5][^6]

```python
# 1단계: 비식별화된 출생연도 계산
birth_year = anchor_year - anchor_age

# 2단계: 입원 시 나이 계산
age_at_admission = year(admittime) - birth_year
```

### 실제 구현 예제

```python
import pandas as pd

def calculate_age_at_admission(df):
    """
    MIMIC-IV 데이터에서 입원 시 정확한 나이 계산
    
    Parameters:
    -----------
    df : DataFrame
        anchor_year, anchor_age, admittime 컬럼을 포함한 데이터프레임
    
    Returns:
    --------
    DataFrame with age_at_admission column added
    
    References:
    -----------
    [1] Johnson et al., 2023. MIMIC-IV documentation
    [2] MIT-LCP GitHub Issue #963
    """
    # 비식별화된 출생연도 계산
    df['birth_year'] = df['anchor_year'] - df['anchor_age']
    
    # 입원 연도 추출
    df['admit_year'] = pd.to_datetime(df['admittime']).dt.year
    
    # 입원 시 나이 계산
    df['age_at_admission'] = df['admit_year'] - df['birth_year']
    
    # 89세 이상 그룹 표시
    df.loc[df['anchor_age'] >= 89, 'age_group_note'] = '>89 (grouped)'
    
    return df
```

### 계산 예시

| subject_id | anchor_year | anchor_age | admittime | 계산 과정 | age_at_admission |
|------------|-------------|------------|-----------|-----------|------------------|
| 10001 | 2150 | 60 | 2153-03-15 | 2153 - (2150-60) = 63 | 63세 |
| 10002 | 2180 | 45 | 2185-07-20 | 2185 - (2180-45) = 50 | 50세 |
| 10003 | 2120 | 91 | 2125-01-10 | 2125 - (2120-91) = 96 | 96세* |

*89세 이상 그룹화된 환자

---

## ⚠️ 주의사항

### 1. anchor_age를 직접 사용하면 안 되는 이유

```python
# ❌ 잘못된 방법
df['age'] = df['anchor_age']  # anchor_year 시점의 나이

# ✅ 올바른 방법  
df['age'] = pd.to_datetime(df['admittime']).dt.year - (df['anchor_year'] - df['anchor_age'])
```

**차이 예시**:
- anchor_age: 60세 (anchor_year 시점)
- 실제 입원일: anchor_year + 3년
- 올바른 입원 시 나이: 63세
- **오차: 3년**

### 2. 89세 이상 환자 처리

HIPAA 규정에 따라 89세 이상 환자는 모두 91세로 기록됩니다[^4]. 이로 인해:

- 실제 나이가 89-110세인 모든 환자가 anchor_age = 91
- 계산된 나이도 부정확할 수 있음
- 연구 시 이 그룹은 별도 처리 권장

```python
# 89세 이상 환자 식별
elderly_patients = df[df['anchor_age'] >= 89].copy()
elderly_patients['age_category'] = '89+'
```

### 3. 환자 간 시간 비교 불가

```python
# ❌ 잘못된 비교
patient_a_admit = '2150-01-01'  
patient_b_admit = '2150-01-01'
# 두 환자가 같은 날 입원했다고 가정할 수 없음!

# ✅ 올바른 접근
# 각 환자의 데이터는 독립적으로 분석
# 환자 간 시간 관계는 anchor_year_group으로만 대략 추정
```

---

## 📊 검증 방법

### 나이 계산 정확성 검증

```python
def validate_age_calculation(df):
    """나이 계산 검증"""
    
    # 1. 음수 나이 확인
    negative_age = df['age_at_admission'] < 0
    if negative_age.any():
        print(f"⚠️ 음수 나이 발견: {negative_age.sum()}건")
    
    # 2. 극단적 나이 확인  
    extreme_age = df['age_at_admission'] > 120
    if extreme_age.any():
        print(f"⚠️ 120세 초과: {extreme_age.sum()}건")
    
    # 3. anchor_age와의 차이 분석
    df['age_diff'] = df['age_at_admission'] - df['anchor_age']
    print(f"평균 나이 차이: {df['age_diff'].mean():.1f}년")
    print(f"차이 범위: {df['age_diff'].min():.1f} ~ {df['age_diff'].max():.1f}년")
    
    return df
```

---

## 📖 참고문헌

[^1]: Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R. (2023). MIMIC-IV, a freely accessible electronic health record dataset. *Scientific Data*, 10(1), 1. https://www.nature.com/articles/s41597-022-01899-x

[^2]: Johnson, A., Pollard, T., & Mark, R. (2023). MIMIC-IV v3.1. PhysioNet. https://physionet.org/content/mimiciv/3.1/

[^3]: MIT-LCP. (2023). MIMIC-IV Core Module Documentation - Patients Table. GitHub. https://github.com/MIT-LCP/mimic-iv-website/blob/master/content/core/patients.md

[^4]: Goldberger, A., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215–e220.

[^5]: MIT-LCP. (2021). Calculate the age of patient - Issue #963. GitHub. https://github.com/MIT-LCP/mimic-code/issues/963

[^6]: MIT-LCP. (2021). What are ANCHOR_AGE and ANCHOR_YEAR - Issue #819. GitHub. https://github.com/MIT-LCP/mimic-code/issues/819

---

## 🔗 추가 자료

- [MIMIC-IV 공식 문서](https://mimic.mit.edu/docs/iv/)
- [MIMIC-IV 데이터 처리 파이프라인](https://pmc.ncbi.nlm.nih.gov/articles/PMC9854277/)
- [MIMIC 커뮤니티 포럼](https://github.com/MIT-LCP/mimic-code/discussions)

---

## 📝 버전 이력

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0 | 2025-01-06 | Analysis Team | 초기 문서 작성 |

---

*이 문서는 MIMIC-IV v3.1을 기준으로 작성되었습니다.*