# Comprehensive Dataset 상세 분석

## 📌 개요

Comprehensive Dataset은 Extended Dataset의 모든 변수에 추가로 동맥혈가스분석(ABG), 심장 표지자, 영양 상태 지표 등 특수 검사를 포함한 포괄적 데이터셋입니다. 연구용 고급 모델과 특정 질환군 예측에 적합하며, 복잡한 결측값 처리가 필요합니다.

---

## 📊 데이터셋 특성

| 항목 | 값 |
|------|-----|
| **파일명** | `model_dataset_comprehensive.csv` |
| **전체 크기** | 1,200 행 × 35 열 |
| **Lab 변수 수** | 24개 |
| **평균 결측률** | 37.5% |
| **완전한 케이스** | 0개 (0%) |
| **용도** | 연구용 고급 모델, 특정 질환 예측 |

---

## 🔍 전체 컬럼 구성 (35개)

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

## 🔬 Lab 변수 상세 분석 (24개)

### A. Essential 변수 (9개) - 결측률 < 10%

1. **Hematocrit_51221_merged**: 4.3% 결측
2. **Hemoglobin_51222**: 4.8% 결측  
3. **RDW_51277**: 4.9% 결측
4. **White_Blood_Cells_51301_merged**: 4.8% 결측
5. **Creatinine_50912_merged**: 6.2% 결측
6. **Urea_Nitrogen_51006_merged**: 6.5% 결측
7. **Potassium_50971_merged**: 7.2% 결측
8. **Sodium_50983_merged**: 7.3% 결측
9. **Glucose_50931**: 8.4% 결측

### B. Extended 추가 변수 (8개) - 결측률 20-55%

10. **Basophils_51146**: 23.4% 결측
11. **Eosinophils_51200**: 23.4% 결측
12. **PT_51274_merged**: 27.2% 결측
13. **PTT_51275_merged**: 28.8% 결측
14. **Calcium__Total_50893**: 21.7% 결측
15. **Bilirubin__Total_50885**: 44.1% 결측
16. **Lactate_50813_merged**: 54.3% 결측
17. **Platelet_Count_51704**: 100.0% 결측 ⚠️

### C. Comprehensive 특화 변수 (7개) - 높은 결측률

#### 영양 상태 지표

#### 18. **Albumin_50862**
- **임상적 의미**: 영양 상태, 간 합성 기능, 예후 지표
- **결측률**: 54.5%
- **정상 범위**: 3.5-5.0 g/dL
- **중요도**: ⭐⭐⭐⭐⭐
- **특이사항**: 
  - < 2.5: 심각한 영양실조
  - 장기 예후의 강력한 예측인자
  - 중환자에서 흔히 감소

#### 동맥혈가스분석 (ABG) - 호흡/대사 평가

#### 19. **pH_50820**
- **임상적 의미**: 산염기 평형, 중증도 평가
- **결측률**: 73.0%
- **정상 범위**: 7.35-7.45
- **중요도**: ⭐⭐⭐⭐⭐
- **위험 수준**:
  - < 7.2: 심각한 산증 (생명 위협)
  - > 7.6: 심각한 알칼리증
- **특이사항**: 기계환기 환자에서 필수

#### 20. **pO2_50821_merged** (Partial Pressure of Oxygen)
- **임상적 의미**: 산소화 상태, 폐 기능
- **결측률**: 74.8%
- **정상 범위**: 75-100 mmHg (room air)
- **중요도**: ⭐⭐⭐⭐⭐
- **위험 수준**:
  - < 60: 저산소혈증
  - < 40: 심각한 저산소증
- **특이사항**: P/F ratio (pO2/FiO2) 계산에 필수

#### 21. **pCO2_50818_merged** (Partial Pressure of CO2)
- **임상적 의미**: 환기 상태, 호흡성 산염기 평가
- **결측률**: 74.8%
- **정상 범위**: 35-45 mmHg
- **중요도**: ⭐⭐⭐⭐⭐
- **의미**:
  - < 35: 과호흡, 호흡성 알칼리증
  - > 45: 저호흡, 호흡성 산증
- **특이사항**: COPD 환자에서 만성적으로 상승

#### 근육 손상 지표

#### 22. **Creatine_Kinase_CK_50910**
- **임상적 의미**: 근육 손상, 심근경색, 횡문근융해증
- **결측률**: 73.5%
- **정상 범위**: 
  - 남성: 39-308 U/L
  - 여성: 26-192 U/L
- **중요도**: ⭐⭐⭐⭐
- **특이사항**:
  - > 1000: 횡문근융해증 의심
  - CK-MB 분획이 심장 특이적

#### 심장 표지자

#### 23. **Troponin_T_51003**
- **임상적 의미**: 심근 손상의 gold standard
- **결측률**: 84.3%
- **정상 범위**: < 0.01 ng/mL
- **중요도**: ⭐⭐⭐⭐⭐
- **특이사항**:
  - 급성 심근경색 진단의 핵심
  - 상승 시 나쁜 예후
  - 패혈증에서도 상승 가능

#### 전해질 추가

#### 24. **Chloride__Whole_Blood_50806_merged**
- **임상적 의미**: 산염기 평형, 체액 균형
- **결측률**: 87.8%
- **정상 범위**: 96-106 mEq/L
- **중요도**: ⭐⭐⭐
- **특이사항**: Strong Ion Difference 계산에 필요

---

## 📈 결측값 패턴 분석

### 결측률 분포
```
0-10%:    9개 변수 (37.5%)
10-30%:   5개 변수 (20.8%)
30-60%:   3개 변수 (12.5%)
60-80%:   5개 변수 (20.8%)
80-90%:   1개 변수 (4.2%)
100%:     1개 변수 (4.2%)
```

### 결측 패턴의 임상적 의미

#### 1. **계층적 검사 시행**
```
기본 검사 (CBC, BMP): 5-10% 결측
↓
추가 검사 (응고, 간기능): 20-45% 결측
↓
중증도 평가 (Lactate, Albumin): 50-55% 결측
↓
특수 검사 (ABG): 73-75% 결측
↓
심장 평가 (Troponin): 84% 결측
```

#### 2. **검사 시행 이유**
- **ABG (73-75% 결측)**: 호흡부전, 기계환기, 중증 대사이상
- **Troponin (84% 결측)**: 흉통, EKG 이상, 심장 위험인자
- **Albumin (55% 결측)**: 영양평가, 중환자, 장기입원

---

## 💡 고급 모델링 전략

### 1. 다단계 결측값 처리
```python
# Step 1: 결측 패턴 분석
missing_pattern = df.isnull().value_counts()

# Step 2: 계층별 대체
from sklearn.impute import SimpleImputer, KNNImputer

# 낮은 결측률 (< 10%): 중앙값
low_missing = ['Hematocrit', 'Hemoglobin', ...]
imputer_simple = SimpleImputer(strategy='median')
df[low_missing] = imputer_simple.fit_transform(df[low_missing])

# 중간 결측률 (10-50%): KNN
mid_missing = ['Basophils', 'PT', 'Lactate', ...]
imputer_knn = KNNImputer(n_neighbors=5)
df[mid_missing] = imputer_knn.fit_transform(df[mid_missing])

# 높은 결측률 (> 50%): Missing Indicator
high_missing = ['pH', 'pO2', 'Troponin', ...]
for col in high_missing:
    df[f'{col}_missing'] = df[col].isna().astype(int)
    df[col].fillna(df[col].median(), inplace=True)
```

### 2. 도메인 지식 기반 특징 생성
```python
# ABG 해석
def classify_abg(row):
    if pd.isna(row['pH']):
        return 'not_done'
    elif row['pH'] < 7.35:
        if row['pCO2'] > 45:
            return 'respiratory_acidosis'
        else:
            return 'metabolic_acidosis'
    elif row['pH'] > 7.45:
        if row['pCO2'] < 35:
            return 'respiratory_alkalosis'
        else:
            return 'metabolic_alkalosis'
    else:
        return 'normal'

df['abg_interpretation'] = df.apply(classify_abg, axis=1)

# P/F Ratio (ARDS 평가)
df['pf_ratio'] = df['pO2'] / df['FiO2']  # FiO2 필요
df['ards_severity'] = pd.cut(df['pf_ratio'], 
                             bins=[0, 100, 200, 300, float('inf')],
                             labels=['severe', 'moderate', 'mild', 'none'])

# 심장 위험 점수
df['cardiac_risk'] = (
    (df['Troponin_T'] > 0.01).fillna(0) * 3 +
    (df['Creatine_Kinase'] > 308).fillna(0) * 1 +
    (df['age'] > 65) * 1
)
```

### 3. 앙상블 전략
```python
# Model 1: Essential features only (완전성 높음)
model1 = RandomForestClassifier()
model1.fit(X_essential, y)

# Model 2: Extended features (중증도 포함)
model2 = XGBClassifier()  # XGBoost는 결측값 자동 처리
model2.fit(X_extended, y)

# Model 3: Comprehensive with indicators
model3 = LGBMClassifier()  # LightGBM도 결측값 처리
model3.fit(X_comprehensive_with_indicators, y)

# Ensemble
from sklearn.ensemble import VotingClassifier
ensemble = VotingClassifier([
    ('essential', model1),
    ('extended', model2),
    ('comprehensive', model3)
], weights=[0.3, 0.4, 0.3])
```

---

## ⚠️ 중요 주의사항

### 1. 극심한 결측률 변수
- **Platelet_Count**: 100% 결측 (제거 필수)
- **Chloride**: 87.8% 결측 (신중한 사용)
- **Troponin**: 84.3% 결측 (심장 환자 서브그룹에만 유용)

### 2. ABG 해석의 복잡성
- pH, pO2, pCO2는 함께 해석해야 의미 있음
- FiO2 (산소 농도) 정보 없이 pO2만으로는 제한적
- 고도, 체온 등 보정 필요

### 3. 시간 의존성
- Troponin은 심근경색 후 시간에 따라 변화
- CK는 손상 후 6-12시간 후 최고치
- 입원 "당일"의 정의가 중요

---

## 🎯 특화 활용 시나리오

### 1. 호흡부전 예측 모델
```python
# ABG 변수 중심
respiratory_features = ['pH', 'pO2', 'pCO2', 'Lactate']
respiratory_model = train_model(df[respiratory_features + basic_features])
```

### 2. 심장 위험도 평가
```python
# Troponin, CK 중심
cardiac_features = ['Troponin_T', 'Creatine_Kinase', 'age', 'gender']
cardiac_model = train_model(df[cardiac_features + basic_features])
```

### 3. 영양/예후 평가
```python
# Albumin 중심
prognosis_features = ['Albumin', 'age', 'Creatinine', 'Bilirubin']
prognosis_model = train_model(df[prognosis_features])
```

---

## 📊 데이터 품질 요약

| 평가 항목 | 점수 | 설명 |
|-----------|------|------|
| **완전성** | ⭐⭐ | 평균 결측률 37.5%, 일부 변수 > 80% |
| **신뢰성** | ⭐⭐⭐⭐ | 표준 검사 + 특수 검사 포함 |
| **적용성** | ⭐⭐ | 고급 결측값 처리 필수 |
| **임상적 가치** | ⭐⭐⭐⭐⭐ | 포괄적 평가 가능 |
| **연구 가치** | ⭐⭐⭐⭐⭐ | 다양한 질환 예측 가능 |

---

## 🔗 관련 문서
- [Essential Dataset 분석](./Essential_Dataset_Analysis.md) - 기본 변수만 포함
- [Extended Dataset 분석](./Extended_Dataset_Analysis.md) - 중간 수준 변수
- [모델링 가이드](./Modeling_Guide.md) - 실제 모델 구현 방법
- [MIMIC-IV 나이 계산](./MIMIC_IV_Age_Calculation_Guide.md) - 정확한 나이 계산법

---

*작성일: 2025-01-06*  
*데이터: MIMIC-IV 샘플 1,200건*