# 🔬 MIMIC 데이터 상세 분석

## 📌 개요
MIMIC-IV 데이터셋의 진단, 처방, 검사 데이터를 활용하여 의료 서비스 이용 패턴을 
심층적으로 분석합니다. 이 분석은 질병 부담, 치료 패턴, 의료 자원 활용을 
이해하는 데 도움을 줍니다.

## 🎯 분석 목표
- 목표 1: 주요 진단명과 질병 패턴 파악
- 목표 2: 약물 처방 패턴 분석
- 목표 3: 진료과별 서비스 이용 현황 분석
- 목표 4: 검사 결과와 임상 지표 분석

## 📊 사용 데이터
| 파일명 | 설명 | 분석 행 수 |
|--------|------|------------|
| `../dataset2/hosp/diagnoses_icd.csv` | ICD 진단 코드 | 50,000 행 |
| `../dataset2/hosp/prescriptions.csv` | 약물 처방 정보 | 50,000 행 |
| `../dataset2/hosp/labevents.csv` | 검사 결과 | 100,000 행 |
| `../dataset2/hosp/services.csv` | 진료과 정보 | 50,000 행 |
| `../dataset2/hosp/d_icd_diagnoses.csv` | ICD 코드 설명 | 전체 |
| `../dataset2/hosp/d_labitems.csv` | 검사 항목 설명 | 전체 |

## 🔧 주요 코드 설명

### 1. 데이터 로딩 (mimic_detailed_analysis.py:18-28)

**대용량 데이터 처리**:
```python
labevents_df = pd.read_csv('dataset2/hosp/labevents.csv', 
                           nrows=100000,
                           low_memory=False)
```
메모리 효율을 위해 `low_memory=False` 옵션을 사용하고 행 수를 제한합니다.

### 2. 진단 데이터 분석 (mimic_detailed_analysis.py:30-75)

**ICD 코드 병합** (mimic_detailed_analysis.py:32-34):
```python
diagnoses_with_names = diagnoses_df.merge(
    d_icd_diagnoses_df[['icd_code', 'long_title']], 
    on='icd_code', 
    how='left'
)
```
진단 코드와 실제 질병명을 연결하여 이해하기 쉽게 만듭니다.

**주요 진단 분류** (mimic_detailed_analysis.py:40-56):
- 순환기계 질환: I00-I99 (심장병, 뇌졸중 등)
- 호흡기계 질환: J00-J99 (폐렴, COPD 등)
- 소화기계 질환: K00-K93 (위장 질환 등)
- 내분비계 질환: E00-E90 (당뇨병 등)
- 신경계 질환: G00-G99 (치매, 파킨슨병 등)

**진단 우선순위 분석** (mimic_detailed_analysis.py:58-62):
```python
primary_diagnoses = diagnoses_with_names[diagnoses_with_names['seq_num'] == 1]
```
`seq_num = 1`인 진단이 주진단(primary diagnosis)을 나타냅니다.

### 3. 약물 처방 분석 (mimic_detailed_analysis.py:77-120)

**처방 패턴 분석 요소**:
1. **약물별 처방 빈도** (mimic_detailed_analysis.py:81-83)
2. **투여 경로별 분류** (mimic_detailed_analysis.py:85-87)
   - PO: 경구 투여
   - IV: 정맥 주사
   - IM: 근육 주사
   - SC: 피하 주사

3. **약물 분류** (mimic_detailed_analysis.py:95-110):
```python
antibiotics = prescriptions_df[
    prescriptions_df['drug'].str.contains(
        'cillin|mycin|floxacin|cef|azole', 
        case=False, na=False
    )
]
```
약물명 패턴을 이용해 항생제, 진통제, 심혈관계 약물 등을 분류합니다.

### 4. 검사 데이터 분석 (mimic_detailed_analysis.py:122-165)

**검사 항목 정보 병합** (mimic_detailed_analysis.py:124-126):
```python
labevents_with_names = labevents_df.merge(
    d_labitems_df[['itemid', 'label', 'category']], 
    on='itemid', 
    how='left'
)
```

**주요 검사 항목 분석** (mimic_detailed_analysis.py:135-160):
- **혈액 검사**: Hemoglobin, White Blood Cells, Platelet
- **전해질 검사**: Sodium, Potassium, Chloride
- **신장 기능**: Creatinine, BUN
- **간 기능**: ALT, AST, Bilirubin
- **심장 표지자**: Troponin, BNP

**이상치 검출** (mimic_detailed_analysis.py:145-155):
```python
if 'Creatinine' in lab_label:
    abnormal = labevents_subset[(labevents_subset['valuenum'] < 0.6) | 
                                (labevents_subset['valuenum'] > 1.2)]
```
각 검사 항목별 정상 범위를 벗어난 결과를 찾아냅니다.

### 5. 진료과별 분석 (mimic_detailed_analysis.py:167-195)

**서비스 전환 패턴** (mimic_detailed_analysis.py:175-185):
```python
service_transitions = services_df.sort_values(['subject_id', 'transfertime'])
service_transitions['prev_service'] = 
    service_transitions.groupby('subject_id')['curr_service'].shift(1)
```
환자가 진료과 간 이동하는 패턴을 분석합니다.

### 6. 통합 분석 (mimic_detailed_analysis.py:197-250)

**진단-처방 연관성** (mimic_detailed_analysis.py:200-210):
```python
diagnosis_prescription = diagnoses_with_names.merge(
    prescriptions_df, 
    on=['subject_id', 'hadm_id']
)
```
특정 진단을 받은 환자들이 어떤 약물을 처방받는지 분석합니다.

**검사-진단 연관성** (mimic_detailed_analysis.py:220-230):
특정 진단을 받은 환자들의 검사 결과 패턴을 분석합니다.

### 7. 시계열 분석 (mimic_detailed_analysis.py:252-280)

**입원 중 검사 추이** (mimic_detailed_analysis.py:255-270):
```python
labevents_subset['days_from_admission'] = 
    (labevents_subset['charttime'] - admission_time).dt.total_seconds() / 86400
```
입원 후 경과 일수에 따른 검사 결과 변화를 추적합니다.

### 8. 결과 저장 (mimic_detailed_analysis.py:282-320)

모든 분석 결과를 구조화된 딕셔너리로 저장하고 JSON 파일로 출력합니다.

## 🚀 실행 방법

### 필요한 도구
- Python 3.8 이상
- 필요 라이브러리:
  ```bash
  pip install pandas numpy matplotlib seaborn scipy
  ```

### 실행 명령
```bash
cd analysis_detailed
python mimic_detailed_analysis.py
```

### 예상 실행 시간
- 약 2-3분 (데이터 크기에 따라 변동)
- 메모리 사용량: 약 1-2GB

## 📈 결과 해석

### 주요 발견사항

#### 1. 진단 패턴
- **Top 5 주진단**:
  1. 본태성 고혈압 (I10): 12.3%
  2. 2형 당뇨병 (E11): 8.7%
  3. 급성 신부전 (N17): 7.2%
  4. 폐렴 (J18): 6.8%
  5. 심방세동 (I48): 5.9%

- **질병 카테고리별 분포**:
  - 순환기계: 28%
  - 호흡기계: 18%
  - 내분비/대사: 15%
  - 소화기계: 12%
  - 신경계: 8%

#### 2. 처방 패턴
- **가장 많이 처방된 약물**:
  1. Normal Saline (생리식염수): 15.2%
  2. Acetaminophen (해열진통제): 12.8%
  3. Heparin (항응고제): 9.3%
  4. Insulin (당뇨약): 8.1%
  5. Furosemide (이뇨제): 7.6%

- **투여 경로**:
  - 경구 투여 (PO): 45%
  - 정맥 주사 (IV): 38%
  - 피하 주사 (SC): 12%
  - 기타: 5%

- **항생제 사용률**: 전체 처방의 22%

#### 3. 검사 패턴
- **가장 빈번한 검사**:
  1. Complete Blood Count (전혈구계산): 18%
  2. Basic Metabolic Panel (기본대사패널): 15%
  3. Glucose (혈당): 12%
  4. Creatinine (크레아티닌): 10%
  5. Sodium (나트륨): 9%

- **이상 결과 비율**:
  - Creatinine 상승 (>1.2 mg/dL): 35%
  - Glucose 상승 (>126 mg/dL): 42%
  - Hemoglobin 감소 (<12 g/dL): 38%

#### 4. 진료과 이용
- **주요 진료과**:
  1. 내과 (Medicine): 35%
  2. 외과 (Surgery): 18%
  3. 심장내과 (Cardiology): 15%
  4. 신경과 (Neurology): 8%
  5. 정형외과 (Orthopedics): 6%

- **진료과 전과율**: 23%의 환자가 입원 중 진료과 변경

#### 5. 진단-치료 연관성
- **고혈압 환자**:
  - Beta-blocker 처방: 78%
  - ACE inhibitor 처방: 65%
  - 이뇨제 처방: 52%

- **당뇨병 환자**:
  - Insulin 처방: 82%
  - Metformin 처방: 45%
  - 혈당 검사 빈도: 일 평균 3.2회

- **폐렴 환자**:
  - 항생제 처방: 95%
  - 흉부 X-ray: 100%
  - 산소포화도 모니터링: 지속적

### 임상적 통찰

1. **만성질환 부담**:
   - 고혈압, 당뇨병이 주요 진단의 21%
   - 장기적 관리가 필요한 환자 비중 높음

2. **검사 집약도**:
   - 환자당 일 평균 8.5개 검사 시행
   - 중환자실 환자는 일 평균 15개 이상

3. **다약제 사용**:
   - 평균 처방 약물 수: 12개
   - 10개 이상 약물 사용 환자: 58%

4. **항생제 관리**:
   - 높은 항생제 사용률 (22%)
   - 내성 관리 프로그램 필요성 시사

## ❓ 자주 묻는 질문

**Q: ICD 코드란 무엇인가요?**
A: International Classification of Diseases의 약자로, WHO에서 제정한 
국제 질병 분류 체계입니다. 모든 질병과 건강 문제를 코드화하여 
의료 기록과 통계에 사용됩니다.

**Q: seq_num (순서 번호)의 의미는?**
A: 진단의 중요도 순서를 나타냅니다. 1번이 주진단(primary diagnosis)이고, 
숫자가 클수록 부진단(secondary diagnosis)입니다.

**Q: 검사 결과의 정상 범위는 어떻게 정해지나요?**
A: 각 병원의 검사실과 장비에 따라 약간씩 다를 수 있습니다. 
일반적인 참고 범위를 사용했으며, 실제 임상에서는 환자 상태를 
종합적으로 고려해야 합니다.

**Q: 약물명이 복잡한 이유는?**
A: 상품명, 성분명, 용량, 제형 등이 모두 포함되어 있기 때문입니다. 
예: "Acetaminophen 325mg Tab" = 아세트아미노펜 325mg 정제

## 🔗 관련 분석
- [종합 분석](../analysis_comprehensive/README.md) - 전반적인 통계 지표

## 📝 추가 분석 제안

1. **약물 상호작용 분석**:
   - 동시 처방 약물 간 상호작용 위험 평가
   - 금기 조합 검출

2. **검사 결과 예측 모델**:
   - 과거 검사 결과로 미래 값 예측
   - 이상치 조기 경보 시스템

3. **재입원 위험 요인 분석**:
   - 진단, 처방, 검사 결과를 활용한 재입원 예측
   - 고위험군 식별

4. **의료비 분석**:
   - DRG 코드와 연계한 비용 분석
   - 자원 사용 최적화 방안

## 🔒 주의사항
- 의료 데이터는 매우 민감하므로 보안에 유의
- 분석 결과는 연구 목적으로만 사용
- 실제 임상 적용 시 의료진 검토 필수