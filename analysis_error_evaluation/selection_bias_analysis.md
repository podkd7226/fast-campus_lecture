# 🎯 선택 편향 분석: 21개 vs 98개 검사 선택의 영향

## 📌 요약

**"가장 흔한" 21개 검사만 선택한 결과**
- 사망률 왜곡: 36.5% (잘못) vs 25.0% (실제)
- 환자군 편향: 중증 환자 과대 대표
- 모델 일반화 불가능

---

## 1. 선택 편향이란?

### 1.1 정의
**Selection Bias**: 분석 대상을 잘못 선택하여 전체 모집단을 대표하지 못하는 오류

### 1.2 이번 사례
```
전체 1,200명 환자
    ↓
"흔한" 21개 검사만 선택
    ↓
427명만 분석 (35.6%)
    ↓
나머지 773명 (64.4%) 무시
```

**문제**: 427명이 전체 1,200명을 대표한다고 가정

---

## 2. 21개 검사 선택의 문제

### 2.1 선택 기준의 오류

```python
# extract_admission_day_labs.py 18-45줄
COMMON_LAB_ITEMS = {
    # Basic Metabolic Panel (8개)
    50983: 'Sodium',
    50971: 'Potassium',
    # ... 
    
    # Complete Blood Count (9개)
    51222: 'Hemoglobin',
    51221: 'Hematocrit',
    # ...
    
    # Other Common Tests (3개)
    50893: 'Calcium_Total',
    50960: 'Magnesium',
    50970: 'Phosphate'
}
```

**선택 논리**: "가장 흔한 검사" = "가장 중요한 검사"? ❌

### 2.2 제외된 중요 검사들

| 검사 카테고리 | 제외된 검사 | 임상적 중요도 | 영향 |
|--------------|------------|--------------|------|
| 응고 검사 | PT, PTT, D-Dimer | 수술/출혈 평가 필수 | 수술 환자 누락 |
| 간기능 | Albumin, Bilirubin, AST, ALT | 간부전 평가 | 간질환 환자 누락 |
| 심장 표지자 | Troponin, NTproBNP | 심근경색/심부전 진단 | 심장 환자 누락 |
| 감염 지표 | Lactate, CRP, Procalcitonin | 패혈증 평가 | 중증 감염 누락 |
| 신장 기능 | eGFR, Cystatin C | 신부전 정도 | 신장 환자 누락 |

---

## 3. 선택 편향의 실제 영향

### 3.1 환자군 특성 비교

| 특성 | 21개 검사 (427명) | 98개 검사 (1,200명) | 차이 |
|------|------------------|-------------------|------|
| **포함 비율** | 35.6% | 100% | -64.4% |
| **사망률** | 36.5% (156/427) | 25.0% (300/1200) | +11.5%p |
| **평균 검사 수** | 17.1개 | 13.7개 | +3.4개 |
| **ICU 입원율** | 추정 60% | 추정 40% | +20%p |

### 3.2 사망률 왜곡 분석

```python
# 실제 데이터 기반 계산
전체 1,200명 중 사망: 300명 (25.0%)

# 21개 검사 그룹 (427명)
- 사망: 156명 (36.5%)
- 생존: 271명

# 제외된 그룹 (773명)
- 사망: 144명 (18.6%)  # 300 - 156
- 생존: 629명

# 결론: 제외된 그룹의 사망률이 훨씬 낮음
```

**해석**: 
- 21개 검사를 많이 한 환자 = 더 아픈 환자
- 검사를 적게 한 환자 = 상대적으로 건강한 환자
- **Berkson's Bias** 발생

---

## 4. 98개 검사 (inclusion=1) 접근법

### 4.1 올바른 선택 기준

```python
# extract_initial_labs_complete.py 30-31줄
inclusion_df = pd.read_csv('d_labitems_inclusion.csv')
included_labs = inclusion_df[inclusion_df['inclusion'] == 1]
# 전문가가 선별한 87-98개 검사 사용
```

**장점**:
- 도메인 전문가의 판단 반영
- 체계적 선택 (inclusion 플래그)
- 재현 가능성

### 4.2 커버리지 비교

| 검사 유형 | 21개 검사 | 98개 검사 | 개선 |
|-----------|-----------|-----------|------|
| 기본 대사 | ✅ 8/8 | ✅ 8/8 | - |
| 혈액학 | ✅ 9/9 | ✅ 9/9 | - |
| 응고 | ❌ 0/3 | ✅ 3/3 | +3 |
| 간기능 | ❌ 0/5 | ✅ 5/5 | +5 |
| 심장 | ❌ 0/3 | ✅ 3/3 | +3 |
| 감염 | ❌ 0/4 | ✅ 4/4 | +4 |
| **전체** | **21개** | **98개** | **+77개** |

---

## 5. 머신러닝 모델에 미치는 영향

### 5.1 훈련 데이터 편향

```python
# 잘못된 모델 (21개 검사, 427명)
model_biased = train_model(X_427, y_427)
# 특징: 중증 환자에 과적합
# 문제: 경증 환자 예측 실패

# 올바른 모델 (98개 검사, 1,200명)  
model_correct = train_model(X_1200, y_1200)
# 특징: 전체 스펙트럼 학습
# 장점: 일반화 가능
```

### 5.2 예측 성능 차이 (추정)

| 모델 | 훈련 AUC | 테스트 AUC | 일반화 |
|------|----------|------------|--------|
| 21개 검사 모델 | 0.85 | 0.65 | 실패 |
| 98개 검사 모델 | 0.80 | 0.78 | 성공 |

**이유**: 과적합 vs 적절한 학습

---

## 6. 생존자 편향 추가 분석

### 6.1 검사를 안 한 이유

773명이 21개 기본 검사를 안 한 이유:

| 이유 | 추정 비율 | 예시 |
|------|-----------|------|
| **너무 건강** | 30% | 단순 골절, 경미한 수술 |
| **너무 위급** | 20% | 즉시 수술, CPR 상황 |
| **특수 검사만** | 25% | 심장 환자 (Troponin만) |
| **외부 검사** | 15% | 전원 환자 |
| **기타** | 10% | DNR, 호스피스 |

### 6.2 Missing Not At Random (MNAR)

```
검사 미시행 ≠ 랜덤
검사 미시행 = 임상적 결정

따라서:
- Missing Completely At Random (MCAR) ❌
- Missing At Random (MAR) ❌  
- Missing Not At Random (MNAR) ✅
```

**함의**: 단순 제외 시 심각한 편향 발생

---

## 7. 올바른 접근법

### 7.1 전체 포함 원칙

```python
# ❌ 잘못된 접근
df_with_labs = df[df['has_any_lab'] == True]
# 773명 제외 → 편향

# ✅ 올바른 접근
df_all = df.copy()  # 1,200명 모두 유지
df_all['has_any_lab'] = check_labs(df_all)
df_all['n_labs'] = count_labs(df_all)
# 검사 여부도 특징으로 활용
```

### 7.2 결측값 처리 전략

```python
# 1. 지시자 변수 추가
df['lab_missing'] = df['lab_value'].isna()

# 2. 조건부 대체
df.loc[df['lab_missing'], 'lab_value'] = population_median

# 3. 다중 대체 (Multiple Imputation)
from sklearn.impute import IterativeImputer
imputer = IterativeImputer()
df_imputed = imputer.fit_transform(df)
```

---

## 8. 체크리스트 및 권장사항

### ✅ 선택 편향 예방 체크리스트

- [ ] **포함 기준 명확화**
  - [ ] 도메인 전문가 검토
  - [ ] 문헌 기반 근거
  - [ ] 재현 가능한 정의
  
- [ ] **제외 영향 평가**
  - [ ] 제외된 샘플 수와 비율
  - [ ] 제외된 샘플의 특성
  - [ ] 제외 이유 문서화
  
- [ ] **대표성 검증**
  - [ ] 포함 샘플 vs 전체 모집단 비교
  - [ ] 주요 변수 분포 비교
  - [ ] 결과 변수 비교
  
- [ ] **민감도 분석**
  - [ ] 다양한 포함 기준으로 재분석
  - [ ] 결과의 robust성 확인

### 💡 Best Practice

1. **시작은 전체 데이터로**
   ```python
   df_all = load_all_data()  # 1,200명
   df_filtered = apply_criteria(df_all)
   print(f"제외: {len(df_all) - len(df_filtered)}명")
   ```

2. **제외 이유 추적**
   ```python
   df_all['excluded'] = False
   df_all['exclusion_reason'] = None
   df_all.loc[condition, 'excluded'] = True
   df_all.loc[condition, 'exclusion_reason'] = 'No labs'
   ```

3. **영향 분석**
   ```python
   compare_groups(
       included=df_filtered,
       excluded=df_all[df_all['excluded']]
   )
   ```

---

## 9. 결론

### 핵심 교훈

> **"데이터가 없는 것도 데이터다"**
> 
> 검사를 안 한 773명을 무시하면,  
> 검사를 많이 한 427명만의 이야기가 된다.

### 실무 권장사항

1. **하드코딩 금지**: 21개 검사 같은 자의적 선택 피하기
2. **도메인 지식 활용**: inclusion 플래그 같은 전문가 판단 활용
3. **전체 유지**: 가능한 모든 샘플 포함
4. **투명성**: 제외 기준과 영향 명시

---

## 10. 참고 자료

### 관련 파일
- [21개 검사 분석](../analysis_initial_lab/scripts/analysis/extract_admission_day_labs.py)
- [98개 검사 분석](../analysis_initial_lab/scripts/analysis/extract_initial_labs_complete.py)
- [비교 스크립트](./scripts/compare_analysis_methods.py)

### 문헌
- Berkson, J. (1946). "Limitations of the application of fourfold table analysis to hospital data"
- Hernán, M. A., et al. (2004). "A structural approach to selection bias"

---

*작성일: 2025-08-20*  
*핵심 메시지: "적은 것이 때로는 더 많다, 하지만 편향된 적음은 항상 틀렸다"*