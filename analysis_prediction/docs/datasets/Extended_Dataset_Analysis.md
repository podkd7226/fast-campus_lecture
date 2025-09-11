# Extended Dataset 상세 분석

## 📌 개요

Extended Dataset은 Essential Dataset의 모든 변수에 추가로 응고 검사, CBC 상세 항목, 그리고 중증도 지표인 Lactate를 포함한 확장 데이터셋입니다. 균형잡힌 예측 성능과 임상적 유용성을 제공하며, 특히 중증 환자 평가에 유용합니다.

---

## 📊 데이터셋 특성

| 항목 | 값 |
|------|-----|
| **파일명** | `model_dataset_extended.csv` |
| **전체 크기** | 1,200 행 × 28 열 |
| **Lab 변수 수** | 17개 |
| **평균 결측률** | 22.2% |
| **완전한 케이스** | 0개 (0%) |
| **용도** | 균형잡힌 예측 모델, 중증도 평가 |

---

## 🔍 전체 컬럼 구성 (28개)

### 1. 식별자 (2개)
| 변수명 | 설명 |
|--------|------|
| `hadm_id` | 입원 고유 ID |
| `subject_id` | 환자 고유 ID |

### 2. 인구통계 변수 (3개)
| 변수명 | 타입 | 설명 | 결측률 |
|--------|------|------|--------|
| `age` | 연속형 | 입원 시 나이 (정확히 계산됨) | 0% |
| `gender` | 범주형 | 성별 (M/F) | 0% |
| `admission_type` | 범주형 | 입원 유형 | 0% |

### 3. 타겟 변수 (5개)
| 변수명 | 타입 | 설명 | 용도 |
|--------|------|------|------|
| `death_type` | 범주형 | 사망 유형 (alive/hospital/outside) | 다중 분류 |
| `death_binary` | 이진 | 전체 사망 여부 (0/1) | 이진 분류 |
| `hospital_death` | 이진 | 병원 내 사망 여부 (0/1) | 이진 분류 |
| `los_hours` | 연속형 | 입원 시간 | 회귀 |
| `los_days` | 연속형 | 입원 일수 | 회귀 |

### 4. 기타 (1개)
| 변수명 | 설명 | 주의사항 |
|--------|------|----------|
| `hospital_expire_flag` | 병원 내 사망 플래그 | hospital_death와 중복 (제거 권장) |

---

## 🔬 Lab 변수 상세 분석 (17개)

### A. Essential 변수 (9개) - 결측률 < 10%

#### 혈액학 검사
1. **Hematocrit_51221_merged**: 4.3% 결측
2. **Hemoglobin_51222**: 4.8% 결측
3. **RDW_51277**: 4.9% 결측
4. **White_Blood_Cells_51301_merged**: 4.8% 결측

#### 신장 기능
5. **Creatinine_50912_merged**: 6.2% 결측
6. **Urea_Nitrogen_51006_merged**: 6.5% 결측

#### 전해질
7. **Potassium_50971_merged**: 7.2% 결측
8. **Sodium_50983_merged**: 7.3% 결측

#### 대사
9. **Glucose_50931**: 8.4% 결측

### B. 추가 변수 (8개) - Extended 특화

#### CBC 상세 (Differential Count)

#### 10. **Basophils_51146**
- **임상적 의미**: 알레르기 반응, 특정 혈액 질환
- **결측률**: 23.4%
- **정상 범위**: 0-2%
- **중요도**: ⭐⭐⭐
- **특이사항**: 패혈증에서 감소, 알레르기에서 증가

#### 11. **Eosinophils_51200**
- **임상적 의미**: 알레르기, 기생충 감염, 특정 암
- **결측률**: 23.4%
- **정상 범위**: 1-4%
- **중요도**: ⭐⭐⭐
- **특이사항**: 천식, 약물 반응에서 증가

#### 응고 검사 (Coagulation)

#### 12. **PT_51274_merged** (Prothrombin Time)
- **임상적 의미**: 외인성 응고 경로 평가
- **결측률**: 27.2%
- **정상 범위**: 11-13초
- **중요도**: ⭐⭐⭐⭐⭐
- **용도**: 와파린 모니터링, 간기능 평가, 출혈 위험 평가

#### 13. **PTT_51275_merged** (Partial Thromboplastin Time)
- **임상적 의미**: 내인성 응고 경로 평가
- **결측률**: 28.8%
- **정상 범위**: 25-35초
- **중요도**: ⭐⭐⭐⭐⭐
- **용도**: 헤파린 모니터링, 혈우병 진단

#### 대사 지표

#### 14. **Calcium__Total_50893**
- **임상적 의미**: 근육 기능, 신경 전달, 응고
- **결측률**: 21.7%
- **정상 범위**: 8.5-10.5 mg/dL
- **중요도**: ⭐⭐⭐⭐
- **위험 수준**: < 7.0 (테타니), > 14.0 (고칼슘혈증 위기)

#### 15. **Bilirubin__Total_50885**
- **임상적 의미**: 간기능, 황달 평가
- **결측률**: 44.1%
- **정상 범위**: 0.3-1.2 mg/dL
- **중요도**: ⭐⭐⭐⭐
- **특이사항**: > 2.5 시 황달 가시화

#### 중증도 지표

#### 16. **Lactate_50813_merged** ⚠️ 핵심 지표
- **임상적 의미**: 조직 관류, 쇼크, 패혈증 중증도
- **결측률**: 54.3%
- **정상 범위**: 0.5-2.0 mmol/L
- **중요도**: ⭐⭐⭐⭐⭐
- **위험 수준**: 
  - 2-4: 경미한 상승
  - > 4: 심각한 조직 저산소증
- **특이사항**: 사망 예측의 강력한 지표

#### 17. **Platelet_Count_51704**
- **임상적 의미**: 출혈 위험, 응고 장애
- **결측률**: 100.0% ⚠️
- **정상 범위**: 150,000-400,000/μL
- **중요도**: ⭐⭐⭐⭐⭐
- **주의**: 이 변수는 데이터에 없음 (제거 필요)

---

## 📈 결측값 패턴 분석

### 결측률 분포
```
0-10%:   9개 변수 (52.9%)
10-30%:  5개 변수 (29.4%)
30-50%:  1개 변수 (5.9%)
50-60%:  1개 변수 (5.9%)
100%:    1개 변수 (5.9%) - Platelet_Count
```

### 결측 패턴 특징
- **계층적 결측**: 기본 검사 < CBC 상세 < 응고 검사 < 특수 검사
- **정보적 결측**: Lactate는 중증 환자에서 주로 시행 (54.3% 결측)
- **완전 케이스 없음**: 모든 행에 최소 1개 이상 결측값 존재

### 사망군별 Lactate 시행률
```python
# 사망군에서 Lactate 검사 시행률이 높음
생존군: 45.7% 시행
사망군: 75.3% 시행 (특히 병원 내 사망)
```

---

## 💡 모델링 권장사항

### 1. 필수 결측값 처리 (완전 케이스 0%)
```python
# Option 1: KNN Imputation (패턴 기반)
from sklearn.impute import KNNImputer
imputer = KNNImputer(n_neighbors=5)
X_imputed = imputer.fit_transform(X)

# Option 2: MICE (다변량 대체)
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
mice = IterativeImputer(random_state=42)
X_imputed = mice.fit_transform(X)

# Option 3: 결측 지시자 추가
df['lactate_missing'] = df['Lactate'].isna().astype(int)
# Lactate 결측 자체가 "덜 중증"을 의미할 수 있음
```

### 2. 특징 엔지니어링
```python
# 응고 지표
df['coag_abnormal'] = ((df['PT'] > 15) | (df['PTT'] > 40)).astype(int)

# 간기능 지표
df['liver_dysfunction'] = ((df['Bilirubin_Total'] > 2) & (df['PT'] > 15)).astype(int)

# 중증도 점수
df['severity_score'] = (
    (df['Lactate'] > 2).fillna(0) +
    (df['WBC'] < 4).fillna(0) + (df['WBC'] > 12).fillna(0) +
    (df['Creatinine'] > 2).fillna(0)
)
```

### 3. 단계적 모델링 전략
```python
# Step 1: Essential 변수만으로 기본 모델
model_basic = train_model(X[essential_features])

# Step 2: CBC 상세 추가
model_cbc = train_model(X[essential_features + cbc_features])

# Step 3: 응고 검사 추가
model_coag = train_model(X[essential_features + cbc_features + coag_features])

# Step 4: 전체 (Lactate 포함)
model_full = train_model(X[all_features])
```

---

## ⚠️ 주의사항

### 1. Platelet_Count 변수
- 100% 결측으로 실제 사용 불가
- 데이터셋에서 제거 필요

### 2. Lactate의 특수성
- 54.3% 결측이지만 매우 중요한 예후 지표
- 결측 자체가 정보를 담고 있음 (중증도가 낮음을 시사)
- Missing indicator 방법 권장

### 3. 응고 검사 해석
- PT/PTT는 보통 함께 시행
- 항응고제 사용 환자에서 필수
- 수술 전 평가에 중요

---

## 🎯 활용 시나리오

### 1. 중증도 평가 모델
- Lactate를 포함하여 패혈증, 쇼크 환자 예측
- 중환자실 입실 필요성 평가

### 2. 출혈 위험 평가
- PT/PTT를 활용한 수술 전 위험도 평가
- 항응고 치료 모니터링

### 3. 다단계 스크리닝
- Essential 변수로 1차 스크리닝
- 고위험군에서 추가 검사 결과 활용

---

## 📊 데이터 품질 요약

| 평가 항목 | 점수 | 설명 |
|-----------|------|------|
| **완전성** | ⭐⭐⭐ | 평균 결측률 22.2%, 완전 케이스 0% |
| **신뢰성** | ⭐⭐⭐⭐ | 표준 검사 + 중요 추가 검사 |
| **적용성** | ⭐⭐⭐ | 결측값 처리 필수 |
| **임상적 가치** | ⭐⭐⭐⭐⭐ | 중증도 평가 가능 (Lactate) |

---

## 🔗 관련 문서
- [Essential Dataset 분석](./Essential_Dataset_Analysis.md) - 기본 변수만 포함
- [Comprehensive Dataset 분석](./Comprehensive_Dataset_Analysis.md) - 특수 검사 추가 포함
- [모델링 가이드](../guides/Modeling_Guide.md) - 실제 모델 구현 방법

---

*작성일: 2025-01-06*  
*데이터: MIMIC-IV 샘플 1,200건*