# 🤖 예측 모델링 가이드

## 📌 개요

이 문서는 MIMIC-IV 데이터를 사용한 사망률 및 입원기간 예측 모델 개발을 위한 실용적 가이드입니다. 결측치 분석 결과를 기반으로 3가지 레벨의 데이터셋을 제공하며, 각각의 활용 방법을 안내합니다.

---

## 📊 제공 데이터셋

> 📖 **각 데이터셋의 상세 분석**
> - [Essential Dataset 상세 분석](../datasets/Essential_Dataset_Analysis.md)
> - [Extended Dataset 상세 분석](../datasets/Extended_Dataset_Analysis.md)
> - [Comprehensive Dataset 상세 분석](../datasets/Comprehensive_Dataset_Analysis.md)

### 1. Essential Dataset (필수 변수 세트)
- **파일**: `model_dataset_essential.csv`
- **크기**: 1,200 × 20 (Lab 9개 + 기타 11개)
- **평균 결측률**: 6.0%
- **완전 케이스**: 1,096개 (91.3%)

#### 포함 변수
```python
lab_features = [
    'Hematocrit',      # 적혈구 용적률
    'Hemoglobin',      # 헤모글로빈
    'Creatinine',      # 신장 기능
    'RDW',             # 적혈구 분포
    'White_Blood_Cells', # 백혈구
    'Urea_Nitrogen',   # 요소질소
    'Potassium',       # 칼륨
    'Sodium',          # 나트륨
    'Glucose'          # 혈당
]
```

#### 권장 사용 케이스
- ✅ **베이스라인 모델 구축**
- ✅ **빠른 프로토타이핑**
- ✅ **실시간 예측 시스템** (모든 입원 환자 적용 가능)
- ✅ **결측값 처리 최소화가 필요한 경우**

### 2. Extended Dataset (확장 변수 세트)
- **파일**: `model_dataset_extended.csv`
- **크기**: 1,200 × 28 (Lab 17개 + 기타 11개)
- **평균 결측률**: 22.2%
- **완전 케이스**: 0개 (결측값 처리 필수)

#### 추가 변수
```python
additional_features = [
    'Basophils', 'Eosinophils',  # CBC 상세
    'PT', 'PTT',                  # 응고 검사
    'Calcium_Total',               # 칼슘
    'Bilirubin_Total',            # 빌리루빈
    'Lactate',                     # 젖산 (중증도)
    'Platelet_Count'              # 혈소판
]
```

#### 권장 사용 케이스
- ✅ **균형잡힌 예측 모델**
- ✅ **중증도 평가가 중요한 경우** (Lactate 포함)
- ✅ **응고 장애 위험 평가 필요시**
- ⚠️ 결측값 대체 전략 필수

### 3. Comprehensive Dataset (포괄적 변수 세트)
- **파일**: `model_dataset_comprehensive.csv`
- **크기**: 1,200 × 35 (Lab 24개 + 기타 11개)
- **평균 결측률**: 37.5%
- **완전 케이스**: 0개 (고급 결측값 처리 필수)

#### 추가 특수 검사
```python
special_features = [
    'Albumin',           # 영양 상태
    'pH', 'pO2', 'pCO2', # 동맥혈 가스
    'Creatine_Kinase',   # 근육 손상
    'Troponin_T',        # 심근 손상
    'Chloride'           # 전해질
]
```

#### 권장 사용 케이스
- ✅ **연구용 고급 모델**
- ✅ **앙상블 모델의 구성 요소**
- ✅ **특정 질환군 예측** (심장, 호흡기 등)
- ⚠️ 복잡한 결측값 처리 필요

---

## 🎯 예측 타겟

### 1. 사망 예측

#### 이진 분류 (Binary Classification)
```python
# 전체 사망 예측
target = 'death_binary'  # 0: 생존, 1: 사망

# 병원 내 사망 예측
target = 'hospital_death'  # 0: 생존/병원 외 사망, 1: 병원 내 사망
```

#### 다중 분류 (Multi-class Classification)
```python
target = 'death_type'  # 'alive', 'hospital', 'outside'
```

### 2. 입원기간 예측

#### 회귀 (Regression)
```python
target = 'los_days'   # 연속형 (일 단위)
target = 'los_hours'  # 연속형 (시간 단위)
```

#### 구간 분류 (Ordinal Classification)
```python
# 입원기간을 구간으로 변환
df['los_category'] = pd.cut(df['los_days'], 
                            bins=[0, 3, 7, 14, float('inf')],
                            labels=['short', 'medium', 'long', 'very_long'])
```

---

## 💡 결측값 처리 전략

### 1. Essential Dataset (결측률 6%)

```python
from sklearn.impute import SimpleImputer

# 단순 대체 (중앙값)
imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)

# 또는 완전 케이스만 사용 (91.3% 데이터 유지)
df_complete = df.dropna()
```

### 2. Extended Dataset (결측률 22%)

```python
from sklearn.impute import KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

# KNN 대체
knn_imputer = KNNImputer(n_neighbors=5)
X_imputed = knn_imputer.fit_transform(X)

# MICE (Iterative Imputation)
mice_imputer = IterativeImputer(random_state=42)
X_imputed = mice_imputer.fit_transform(X)
```

### 3. Comprehensive Dataset (결측률 37%)

```python
# 결측 지시자 추가 (Missing Indicator)
from sklearn.impute import MissingIndicator

# 결측 여부를 특징으로 추가
indicator = MissingIndicator()
mask = indicator.fit_transform(X)
X_with_indicator = np.hstack([X_imputed, mask])

# 또는 제공된 indicator 파일 사용
df_indicators = pd.read_csv('model_dataset_extended_with_indicators.csv')
```

### 4. 고급 전략: 결측 패턴 활용

```python
# 결측 패턴 자체를 특징으로
df['n_missing'] = df[lab_features].isna().sum(axis=1)
df['missing_rate'] = df[lab_features].isna().mean(axis=1)

# 특정 검사 결측이 의미하는 정보
df['lactate_tested'] = (~df['Lactate'].isna()).astype(int)  # 중증도 지표
df['troponin_tested'] = (~df['Troponin_T'].isna()).astype(int)  # 심장 문제 의심
```

---

## 🔧 모델 추천

### 1. 베이스라인 모델

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Logistic Regression (해석 가능)
lr_model = LogisticRegression(random_state=42)

# Random Forest (결측값에 강건)
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
```

### 2. 고급 모델

```python
import xgboost as xgb
import lightgbm as lgb

# XGBoost (결측값 자동 처리)
xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)

# LightGBM (대용량 데이터, 범주형 변수)
lgb_model = lgb.LGBMClassifier(
    n_estimators=100,
    num_leaves=31,
    random_state=42
)
```

### 3. 딥러닝 모델

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization

model = Sequential([
    Dense(64, activation='relu', input_dim=n_features),
    BatchNormalization(),
    Dropout(0.3),
    Dense(32, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(1, activation='sigmoid')  # 이진 분류
])
```

---

## 📈 평가 지표

### 사망 예측 (불균형 데이터)

```python
from sklearn.metrics import roc_auc_score, precision_recall_curve, f1_score

# AUROC (전체적 성능)
auroc = roc_auc_score(y_true, y_pred_proba)

# AUPRC (불균형 데이터에 적합)
precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
auprc = auc(recall, precision)

# F1 Score (균형잡힌 지표)
f1 = f1_score(y_true, y_pred)
```

### 입원기간 예측

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# MAE (일 단위 평균 오차)
mae = mean_absolute_error(y_true, y_pred)

# RMSE (큰 오차에 민감)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))

# R² (설명력)
r2 = r2_score(y_true, y_pred)
```

---

## 🚀 실전 예제

### 완전 파이프라인 예제

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# 1. 데이터 로드
df = pd.read_csv('model_dataset_essential.csv')

# 2. 특징과 타겟 분리
feature_cols = [col for col in df.columns 
                if col not in ['hadm_id', 'subject_id', 'death_type', 
                              'death_binary', 'hospital_death', 'los_hours', 'los_days']]
X = df[feature_cols]
y = df['death_binary']

# 3. 훈련/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. 전처리
# 범주형 변수 인코딩
X_train_encoded = pd.get_dummies(X_train, columns=['gender', 'admission_type'])
X_test_encoded = pd.get_dummies(X_test, columns=['gender', 'admission_type'])

# 결측값 처리
imputer = SimpleImputer(strategy='median')
X_train_imputed = imputer.fit_transform(X_train_encoded.select_dtypes(include=[np.number]))
X_test_imputed = imputer.transform(X_test_encoded.select_dtypes(include=[np.number]))

# 스케일링
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_imputed)
X_test_scaled = scaler.transform(X_test_imputed)

# 5. 모델 훈련
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# 6. 예측 및 평가
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

print(classification_report(y_test, y_pred))
print(f"AUROC: {roc_auc_score(y_test, y_pred_proba):.3f}")
```

---

## ⚠️ 주의사항

### 1. 데이터 누수 (Data Leakage)
- `hospital_expire_flag`는 `hospital_death`와 동일하므로 제거
- `deathtime`은 타겟 정보를 포함하므로 제거

### 2. 시간적 검증
- 실제 배포 시에는 시간 기반 분할 고려
- Cross-validation 시 환자 단위 분할 (같은 환자의 여러 입원 분리)

### 3. 해석 가능성
- 의료 분야에서는 모델 해석이 중요
- SHAP, LIME 등 설명 가능한 AI 기법 활용

```python
import shap

# SHAP 값 계산
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 시각화
shap.summary_plot(shap_values, X_test)
```

---

## 📚 추가 자료

- [MIMIC-IV 나이 계산 가이드](./MIMIC_IV_Age_Calculation_Guide.md)
- [결측값 분석 보고서](../../../analysis_initial_lab/missing_value_analysis.md)
- [XGBoost 문서](https://xgboost.readthedocs.io/)
- [Scikit-learn Imputation](https://scikit-learn.org/stable/modules/impute.html)

---

*작성일: 2025-01-06*  
*데이터: MIMIC-IV 샘플 1,200건*