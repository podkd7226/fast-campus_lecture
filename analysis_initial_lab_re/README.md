# 🏥 MIMIC-IV 초기 혈액검사 데이터 분석 (Refined Version)

## 📌 개요

MIMIC-IV 데이터셋에서 입원 초기 혈액검사 데이터를 체계적으로 추출하고 분석합니다.
1,200개 입원 사례에서 87개 주요 검사 항목을 itemid 기반으로 개별 처리하여 데이터 무결성을 보장합니다.

## 🎯 분석 목표

- **목표 1**: 입원 초기(±1일) 혈액검사 데이터 추출
- **목표 2**: itemid별 개별 처리로 중복 라벨 문제 해결
- **목표 3**: 데이터 가용성 평가 및 활용 방안 제시

## 📋 분석 방법론

### "초기 혈액검사"의 정의

본 분석에서 초기 혈액검사는 다음과 같이 정의됩니다:

1. **시간적 기준**: 입원일 기준 -1일, 0일(당일), +1일
2. **데이터 범위**: d_labitems_inclusion.csv의 87개 inclusion=1 항목
3. **판단 기준**: 우선순위 Day 0 > Day -1 > Day +1
4. **제외 기준**: inclusion=0 항목, 시간 윈도우 외 데이터

#### 구체적 예시
- **포함**: 입원 당일 측정한 Hemoglobin → 해당 값 사용
- **포함**: 입원 당일 없고 전일에만 있는 Creatinine → 전일 값 사용
- **제외**: 입원 3일 후 측정한 Glucose → 윈도우 밖이므로 제외

## 📊 사용 데이터

| 파일명 | 설명 | 크기 |
|--------|------|------|
| `../processed_data/core/admissions_sampled.csv` | 입원 정보 | 1,200 행 |
| `../processed_data/core/patients_sampled.csv` | 환자 정보 | 1,171 행 |
| `../processed_data/hosp/labevents_sampled.csv` | 검사 결과 | 2,825,084 행 |
| `../processed_data/hosp/d_labitems_inclusion.csv` | 검사 항목 정의 | 87개 inclusion=1 |

## 🔧 주요 코드 설명

### 데이터 로딩 (scripts/analysis/extract_initial_labs_clean.py:83-105)
```python
# 샘플 데이터 로드
admissions = pd.read_csv('admissions_sampled.csv')
labevents = pd.read_csv('labevents_sampled.csv')
```
입원 정보와 검사 결과를 읽어 메모리에 로드합니다.

### itemid 기반 처리 (scripts/analysis/extract_initial_labs_clean.py:39-56)
```python
# 각 itemid별 고유 라벨 생성
unique_label = f"{clean_label}_{itemid}"
```
같은 라벨이라도 itemid가 다르면 별도 컬럼으로 처리하여 데이터 손실을 방지합니다.

### 시간 윈도우 적용 (scripts/analysis/extract_initial_labs_clean.py:165-177)
```python
# 우선순위: Day 0 > Day -1 > Day +1
for day in [0, -1, 1]:
    if data_exists:
        break
```
입원 당일을 우선으로 하되, 없으면 전일/익일 데이터를 사용합니다.

## 🚀 실행 방법

### 필요한 도구
- Python 3.8 이상
- pandas, numpy 라이브러리
- 약 4GB 메모리

### 실행 명령
```bash
# 프로젝트 루트에서
cd analysis_initial_lab_re

# 가상환경 활성화
source ../.venv/bin/activate

# 스크립트 실행
python scripts/analysis/extract_initial_labs_clean.py
```

### 예상 실행 시간
- 약 2-3분 (데이터 크기에 따라 변동)

## 📈 결과 해석

### 주요 발견사항

1. **높은 커버리지**: 96.2% 입원에서 최소 1개 이상 검사 데이터 존재
2. **핵심 검사 5종**: Hematocrit, Hemoglobin, WBC, RDW, Creatinine이 95% 이상 커버
3. **시간 분포**: 82.5%가 입원 당일, 나머지는 전일/익일 데이터 활용

### 생성된 파일

#### 메인 데이터
- `data/labs_initial_wide.csv`: 1,200 × 93 (검사 값만, offset 제외)
- `data/labs_initial_long.csv`: 20,118개 검사 레코드
- `data/labs_offset_info.csv`: 각 검사의 day_offset 정보

#### 메타데이터
- `data/lab_items_summary.csv`: 87개 검사 항목 요약
- `data/labs_metadata.json`: 추출 과정 상세 정보

### 데이터 구조 예시

**labs_initial_wide.csv** (처음 5개 컬럼):
```
hadm_id | subject_id | Hematocrit_51221 | Hemoglobin_51222 | WBC_51301
--------|------------|------------------|------------------|----------
21234   | 10001      | 38.5            | 12.3             | 8.7
21235   | 10002      | NaN             | 14.1             | 10.2
```

**labs_offset_info.csv**:
```
hadm_id | itemid | lab_name         | day_offset | source
--------|--------|------------------|------------|--------
21234   | 51221  | Hematocrit_51221 | 0          | Day0
21234   | 51222  | Hemoglobin_51222 | -1         | Day-1
```

## ⚠️ 분석의 제한점

### 1. 데이터 제한
- 전체 MIMIC-IV가 아닌 1,200개 샘플만 분석
- 87개 검사 항목으로 제한 (전체 검사의 일부)

### 2. 방법론적 제한
- 동일 날짜 여러 검사 중 첫 번째 값만 사용
- 수치 데이터(valuenum)만 추출, 텍스트 결과 제외

### 3. 해석상 주의점
- 39개 항목은 샘플에 데이터가 전혀 없음 (실제로는 존재할 수 있음)
- 중복 itemid는 서로 다른 측정 방법/장비를 의미할 수 있음

## ❓ 자주 묻는 질문

**Q: 왜 itemid별로 개별 컬럼을 만드나요?**
A: 같은 검사(예: Glucose)도 측정 방법이나 장비에 따라 여러 itemid를 가질 수 있습니다. 이를 하나로 합치면 중요한 정보가 손실될 수 있어 개별 보존합니다.

**Q: offset 정보는 왜 분리했나요?**
A: 메인 데이터(검사 값)와 메타데이터(측정 시점)를 분리하여 더 깔끔한 데이터 구조를 만들었습니다. 필요시 hadm_id와 itemid로 조인 가능합니다.

**Q: 데이터가 없는 컬럼은 왜 유지하나요?**
A: 전체 데이터셋과의 일관성을 유지하고, 향후 데이터 추가 시 구조 변경 없이 사용 가능하도록 했습니다.

## 🔗 관련 분석

- [종합 분석](../analysis_comprehensive/README.md)
- [샘플링 방법론](../analysis_samplingmethod/README.md)
- [결측값 분석](../analysis_missing_values/README.md)

## 📚 참고 자료

- MIMIC-IV 공식 문서: https://mimic.mit.edu/
- 분석 보고서: [initial_lab_analysis_report.md](./initial_lab_analysis_report.md)
- 추출 스크립트: [extract_initial_labs_clean.py](./scripts/analysis/extract_initial_labs_clean.py)

---

*최종 업데이트: 2025년 8월*  
*작성자: MIMIC 분석팀*  
*버전: 2.0 (Refined)*