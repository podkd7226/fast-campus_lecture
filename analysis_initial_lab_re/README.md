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

#### 초기 추출 데이터 (ItemID별 개별 처리)
- `data/labs_initial_wide.csv`: 1,200 × 87 검사 컬럼 (원본 itemid 유지)
- `data/labs_initial_long.csv`: 20,118개 검사 레코드
- `data/labs_offset_info.csv`: 각 검사의 day_offset 정보

#### 병합 최적화 데이터 (선택적 ItemID 통합)
- `data/labs_initial_merged_wide.csv`: 1,200 × 70 검사 컬럼 (안전한 병합 적용)
- `data/labs_initial_merged_long.csv`: 20,118개 검사 레코드 (병합된 itemid)
- `data/labs_merged_offset_info.csv`: 병합된 검사의 day_offset 정보

#### 병합 관련 분석 파일
- `data/improvable_items.csv`: 개선 가능 항목 (한쪽만 활성인 경우)
- `data/duplicate_active_labels.csv`: 중복 활성 라벨 (병합 불가)
- `data/merge_mapping.csv`: ItemID 병합 매핑 테이블 (17개 매핑)
- `data/merge_summary.json`: 병합 프로세스 결과 요약

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

## 🔄 선택적 ItemID 병합 프로세스

### 병합의 필요성과 원리

MIMIC-IV 데이터베이스에서 동일한 검사가 여러 itemid로 나뉘어 저장되는 경우가 있습니다. 이는 다음과 같은 이유로 발생합니다:

1. **장비 변경**: 병원이 새로운 검사 장비를 도입하면서 새 itemid 생성
2. **시스템 업그레이드**: 의료정보시스템 업데이트로 인한 코드 변경
3. **측정 방법 차이**: 같은 검사라도 측정 방법에 따라 다른 itemid 부여

### 데이터 분석 결과 (scripts/analysis/analyze_duplicate_active_items.py)

초기 분석에서 87개 itemid 중 다음과 같은 패턴을 발견했습니다:

#### 1. 안전하게 병합 가능한 경우 (17개 itemid)
한쪽 itemid에만 데이터가 있고 다른 쪽은 완전히 비어있는 경우:

| 검사명 | 빈 itemid | 활성 itemid | 병합 방향 |
|--------|-----------|-------------|-----------|
| Hematocrit | 51638, 51639 | 51221 | → 51221 |
| White Blood Cells | 51755, 51756 | 51301 | → 51301 |
| Creatinine | 52546 | 50912 | → 50912 |
| Sodium | 52623 | 50983 | → 50983 |
| Potassium | 52610 | 50971 | → 50971 |

#### 2. 병합 불가능한 경우 (3개 라벨)
두 itemid 모두 데이터가 있어 값 손실 위험이 있는 경우:

| 검사명 | itemid들 | 각 커버리지 | 병합 불가 이유 |
|--------|----------|-------------|---------------|
| pH | 50820, 50831 | 27.0%, 1.0% | 둘 다 활성, 측정값 차이 가능 |
| Glucose | 50931, 50809 | 91.6%, 15.1% | 둘 다 활성, 측정 방법 다름 |
| Hemoglobin | 51222, 50811 | 95.2%, 11.6% | 둘 다 활성, 장비 차이 가능 |

### 병합 프로세스 구현 (scripts/analysis/extract_initial_labs_merged.py)

```python
# 1. 안전한 병합 규칙 생성 (라인 41-69)
for _, row in improvable.iterrows():
    if label not in duplicate_active_labels:  # 중복 활성이 아닌 경우만
        target_itemid = active_itemids[0]
        for empty_id in empty_itemids:
            merge_rules[empty_id] = target_itemid

# 2. 병합 적용 (라인 118-126)
for old_id, new_id in merge_rules.items():
    labevents.loc[labevents['itemid'] == old_id, 'itemid'] = new_id
```

### 병합 전후 비교

| 구분 | 병합 전 | 병합 후 | 개선 효과 |
|------|---------|---------|-----------|
| **파일명** | labs_initial_wide.csv | labs_initial_merged_wide.csv | - |
| **검사 컬럼 수** | 87개 | 70개 | -19.5% |
| **데이터 있는 컬럼** | 48개 | 48개 | 동일 |
| **전체 커버리지** | 96.2% | 96.25% | +0.05% |
| **파일 크기** | 더 큼 | 더 작음 | 구조 단순화 |

### 병합의 장점

1. **데이터 구조 단순화**: 87개 → 70개 컬럼으로 감소
2. **분석 효율성 향상**: 의미적으로 동일한 검사가 하나의 컬럼으로 통합
3. **머신러닝 적용 용이**: 차원 축소로 모델 학습 효율성 증대
4. **해석 가능성 향상**: 중복된 검사 항목이 제거되어 결과 해석 명확

### 병합의 안전성 보장

병합 과정에서 데이터 무결성을 보장하기 위한 원칙:

1. **보수적 접근**: 한쪽이 완전히 비어있는 경우만 병합
2. **값 충돌 방지**: 둘 다 데이터가 있으면 병합하지 않음
3. **추적 가능성**: `merge_mapping.csv`에 모든 병합 기록 보존
4. **원본 보존**: 병합 전 데이터(`labs_initial_wide.csv`)도 유지

## ❓ 자주 묻는 질문

**Q: 왜 itemid별로 개별 컬럼을 만드나요?**
A: 같은 검사(예: Glucose)도 측정 방법이나 장비에 따라 여러 itemid를 가질 수 있습니다. 이를 하나로 합치면 중요한 정보가 손실될 수 있어 개별 보존합니다.

**Q: labs_initial_wide.csv와 labs_initial_merged_wide.csv의 차이는?**
A: `labs_initial_wide.csv`는 87개 itemid를 모두 개별 컬럼으로 유지한 원본이고, `labs_initial_merged_wide.csv`는 안전한 경우만 선택적으로 병합하여 70개로 축소한 최적화 버전입니다. 한쪽이 비어있는 itemid들만 병합하여 데이터 손실 없이 구조를 단순화했습니다.

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