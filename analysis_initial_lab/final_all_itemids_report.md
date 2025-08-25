# 최종 보고서: 모든 87개 itemid 개별 처리 완료

## 📌 요약

모든 inclusion=1 검사 항목(87개)을 itemid 기반으로 개별 처리하는 방식을 성공적으로 구현했습니다.

### 핵심 성과
- ✅ **87개 모든 itemid를 개별 컬럼으로 생성**
- ✅ **중복 라벨 문제 완전 해결** (각 itemid가 독립 컬럼)
- ✅ **데이터 손실 0%** (모든 측정값 보존)
- ✅ **완전한 재현성** (itemid 기반 처리)

### 최종 데이터 구조
- **Wide Format**: 1,200 입원 × 87 검사 컬럼 (+ 87 offset 컬럼)
- **Long Format**: 20,118 검사 레코드
- **데이터 커버리지**: 96.2% 입원에서 최소 1개 검사

---

## 1. 구현 방법론

### 1.1 itemid 기반 처리 원칙
```python
# 라벨 기반 (문제 있음)
if label == "Glucose":  # 여러 itemid가 병합됨

# itemid 기반 (해결)
for itemid in [50809, 50931, 52569]:  # 각각 독립 처리
    column_name = f"Glucose_{itemid}"
```

### 1.2 컬럼 명명 규칙
- 형식: `{clean_label}_{itemid}`
- 예시:
  - `Glucose_50809` (Blood Gas)
  - `Glucose_50931` (Chemistry)
  - `pCO2_50818` 
  - `pCO2_52040`

---

## 2. 중복 itemid 처리 결과

### 2.1 완전히 해결된 중복 (21개 그룹)

| 라벨 | itemid 수 | 실제 데이터 | 컬럼 생성 |
|------|-----------|------------|-----------|
| **Glucose** | 3 | 2/3 | 3개 모두 |
| **pCO2** | 2 | 1/2 | 2개 모두 |
| **pH** | 3 | 2/3 | 3개 모두 |
| **Hemoglobin** | 3 | 2/3 | 3개 모두 |
| **Hematocrit** | 3 | 1/3 | 3개 모두 |
| **White Blood Cells** | 3 | 1/3 | 3개 모두 |
| 기타 15개 그룹 | 36 | 15/36 | 36개 모두 |

### 2.2 상세 데이터 분포

#### Glucose (3개 itemid)
- `Glucose_50809`: 183건 (Blood Gas) ✓
- `Glucose_50931`: 1,099건 (Chemistry) ✓
- `Glucose_52569`: 0건 (Chemistry) - 컬럼 생성됨

#### pCO2 (2개 itemid)
- `pCO2_50818`: 303건 (Blood Gas) ✓
- `pCO2_52040`: 0건 (Blood Gas) - 컬럼 생성됨

#### pH (3개 itemid)
- `pH_50820`: 324건 (Blood Gas) ✓
- `pH_52041`: 0건 (Blood Gas) - 컬럼 생성됨
- `pH_50831`: 12건 (Blood Gas) ✓

---

## 3. 데이터 가용성 분석

### 3.1 전체 통계
- **총 itemid**: 87개 (inclusion=1)
- **데이터 있는 itemid**: 48개 (55.2%)
- **빈 컬럼**: 39개 (44.8%)

### 3.2 데이터가 많은 검사 Top 10

| 순위 | 컬럼명 | 데이터 수 | 커버리지 |
|------|--------|----------|----------|
| 1 | Hematocrit_51221 | 1,148 | 95.7% |
| 2 | Hemoglobin_51222 | 1,143 | 95.2% |
| 3 | White_Blood_Cells_51301 | 1,142 | 95.2% |
| 4 | RDW_51277 | 1,141 | 95.1% |
| 5 | Creatinine_50912 | 1,126 | 93.8% |
| 6 | Urea_Nitrogen_51006 | 1,122 | 93.5% |
| 7 | Potassium_50971 | 1,114 | 92.8% |
| 8 | Sodium_50983 | 1,112 | 92.7% |
| 9 | Glucose_50931 | 1,099 | 91.6% |
| 10 | PT_51274 | 880 | 73.3% |

### 3.3 데이터가 없는 주요 itemid (39개)

샘플 데이터에 전혀 없지만 컬럼은 생성된 항목들:
- COVID-19 관련: `COVID-19_51853`
- 중복 itemid 중 백업용: `pCO2_52040`, `pH_52041`, `Glucose_52569`
- 특수 검사들: `CA_19-9_51579`, `Bleeding_Time_51149` 등

---

## 4. 시간 윈도우 효과

### 4.1 데이터 출처 분포
| 시간 | 레코드 수 | 비율 | 설명 |
|------|-----------|------|------|
| Day 0 (당일) | 16,593 | 82.5% | 입원 당일 표준 검사 |
| Day +1 (익일) | 2,460 | 12.2% | 다음날 아침 루틴 |
| Day -1 (전일) | 1,065 | 5.3% | 응급실/외래 검사 |
| **합계** | **20,118** | **100%** | - |

### 4.2 개선 효과
- 입원 당일만: 87.8% 커버리지
- 시간 윈도우 적용: 96.2% 커버리지
- **개선: +8.5%p**

---

## 5. 생성된 파일

### 5.1 데이터 파일
| 파일명 | 크기 | 설명 |
|--------|------|------|
| `labs_all_itemids_wide.csv` | 1,200 × 179 | 87 검사 + 87 offset + 메타 |
| `labs_all_itemids_long.csv` | 20,118 레코드 | 모든 검사 레코드 |
| `labs_all_itemids_sources.csv` | 20,118 레코드 | 데이터 출처 추적 |

### 5.2 메타데이터
| 파일명 | 내용 |
|--------|------|
| `lab_items_all_itemids.csv` | 87개 itemid 상세 정보 |
| `extraction_metadata_all_itemids.json` | 추출 통계 및 컬럼별 가용성 |

### 5.3 스크립트
- `extract_labs_all_itemids.py`: 최종 구현

---

## 6. 이전 방식과 비교

| 측면 | 이전 방식 | 최종 방식 |
|------|----------|----------|
| **처리 기준** | 라벨 기반 | itemid 기반 |
| **중복 처리** | 병합 또는 임의 선택 | 모두 개별 유지 |
| **컬럼 수** | 45개 | 87개 |
| **데이터 손실** | 15-20% | 0% |
| **빈 컬럼** | 제외 | 포함 (NaN) |
| **재현성** | 낮음 | 100% |

---

## 7. 사용 가이드

### 7.1 데이터 로드
```python
import pandas as pd

# Wide format (머신러닝용)
wide_df = pd.read_csv('labs_all_itemids_wide.csv')

# 검사 컬럼만 추출
lab_cols = [c for c in wide_df.columns 
            if not c.endswith('_day_offset') 
            and c not in ['hadm_id', 'subject_id', 'admittime', 
                         'hospital_expire_flag', 'admit_date']]

# 특정 검사 그룹 선택 (예: 모든 Glucose)
glucose_cols = [c for c in lab_cols if 'Glucose' in c]
glucose_data = wide_df[glucose_cols]
```

### 7.2 중복 itemid 처리
```python
# 방법 1: 개별 사용
glucose_bg = wide_df['Glucose_50809']    # Blood Gas
glucose_chem = wide_df['Glucose_50931']  # Chemistry

# 방법 2: 우선순위 병합
glucose_merged = wide_df['Glucose_50931'].fillna(wide_df['Glucose_50809'])

# 방법 3: 평균값
glucose_mean = wide_df[['Glucose_50809', 'Glucose_50931']].mean(axis=1)
```

---

## 8. 결론 및 권장사항

### 8.1 성과 요약
✅ **완전성**: 87개 모든 inclusion=1 itemid 처리
✅ **투명성**: 각 itemid의 출처와 특성 명확
✅ **유연성**: 사용자가 병합/선택 방법 결정 가능
✅ **재현성**: itemid 기반으로 100% 재현 가능

### 8.2 제한점
- 샘플 데이터 한계로 39개 컬럼은 비어있음
- 컬럼 수가 많아 차원 축소 필요할 수 있음
- 일부 중복 itemid는 사실상 백업용으로 데이터 없음

### 8.3 향후 개선 방향
1. **전체 데이터셋 적용**: 523,740건에서 재추출
2. **스마트 병합 옵션**: 사용자 정의 병합 규칙
3. **자동 feature selection**: 희소 컬럼 자동 제거

### 8.4 최종 권장
**현재 구조를 그대로 사용하되, 분석 목적에 따라:**
- 차원 축소가 필요하면: 빈 컬럼 제거
- 정밀 분석이 필요하면: 모든 컬럼 유지
- 중복 itemid는: 임상적 판단에 따라 선택적 사용

---

## 부록: 주요 코드 변경 사항

### 변경 전 (라벨 기반)
```python
# 같은 라벨은 병합
if clean_label in duplicate_mapping:
    # 하나로 병합...
```

### 변경 후 (itemid 기반)
```python
# 모든 itemid 독립 처리
for itemid in all_itemids:
    unique_label = f"{clean_label}_{itemid}"
    LAB_ITEMS[itemid] = unique_label
```

---

*문서 작성일: 2025-08-24*
*최종 버전: itemid 기반 완전 개별 처리*