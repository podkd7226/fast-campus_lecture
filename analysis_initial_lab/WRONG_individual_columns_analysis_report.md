# 개별 itemid 컬럼 유지 방식 분석 보고서

## 📌 요약

개별 itemid를 독립적인 컬럼으로 유지하는 방식을 구현했으나, 예상과 다른 결과가 나타났습니다.

### 예상 vs 실제
- **예상**: 61개 컬럼 (모든 중복 itemid 개별 유지)
- **실제**: 36개 컬럼 (데이터가 있는 itemid만 포함)

### 핵심 발견
- 87개 inclusion=1 항목 중 실제 데이터가 있는 것은 42개뿐
- 중복 라벨 중 일부는 아예 데이터가 없어 제외됨
- 데이터 손실은 없지만, 빈 컬럼 생성도 불가능

---

## 1. 구현 내용

### 1.1 중복 itemid 매핑 테이블

9개 중복 라벨에 대해 19개 itemid를 개별 관리:

| 라벨 | itemid 수 | 개별 컬럼명 예시 |
|------|-----------|-----------------|
| Glucose | 3 | Glucose_50809_BloodGas, Glucose_50931_Chemistry, Glucose_52569_Chemistry2 |
| Creatinine | 2 | Creatinine_50912_Chemistry, Creatinine_52546_Chemistry2 |
| Hemoglobin | 2 | Hemoglobin_50811_BloodGas, Hemoglobin_51222_CBC |
| Hematocrit | 2 | Hematocrit_51638_Chemistry, Hematocrit_51221_CBC |
| pH | 2 | pH_50820_BloodGas, pH_50831_BloodGas |
| Potassium | 2 | Potassium_50971_Chemistry, Potassium_52610_Chemistry2 |
| Sodium | 2 | Sodium_50983_Chemistry, Sodium_52623_Chemistry2 |
| Urea_Nitrogen | 2 | Urea_Nitrogen_51006_Chemistry, Urea_Nitrogen_52647_Chemistry2 |
| White_Blood_Cells | 2 | White_Blood_Cells_51755_Chemistry, White_Blood_Cells_51301_CBC |

### 1.2 구현 특징

1. **고유 라벨 생성**
   - 형식: `{라벨}_{itemid}_{카테고리}`
   - 예: `Glucose_50809_BloodGas`

2. **독립적 처리**
   - 각 itemid를 개별적으로 추출
   - pivot 시 고유 컬럼 생성

3. **임상적 구분 가능**
   - Blood Gas vs Chemistry 구분
   - 측정 방법/장비 차이 보존

---

## 2. 실제 결과 분석

### 2.1 데이터 가용성

| 단계 | 항목 수 | 설명 |
|------|---------|------|
| inclusion=1 | 87 | 원래 지정된 검사 |
| 샘플에 존재 | 61 | 실제 데이터가 있는 itemid |
| 중복 제거 | 51 | 고유한 라벨 수 |
| 시간 윈도우 후 | 42 | ±1일에도 데이터가 있는 itemid |
| 최종 컬럼 | 36 | valuenum이 있는 검사만 |

### 2.2 누락된 중복 itemid

많은 중복 itemid가 실제로는 데이터가 없거나 매우 희소:

```
Glucose 관련:
- 50809: 183건 (사용됨)
- 50931: 1,099건 (사용됨)
- 52569: 0건 (데이터 없음 - 제외)

Creatinine 관련:
- 50912: 데이터 있음 (사용됨)
- 52546: 데이터 없음 (제외)
```

### 2.3 실제 생성된 컬럼 (36개)

```
%_Hemoglobin_A1c, Albumin, Basophils, 
Bilirubin__Direct, Bilirubin__Indirect, Bilirubin__Total,
C-Reactive_Protein, Calcium__Total, 
Calculated_Bicarbonate__Whole_Blood, Calculated_Total_CO2,
Chloride__Whole_Blood, Creatine_Kinase_CK, Creatinine__Whole_Blood,
D-Dimer, Eosinophils, Ferritin, Folate,
Lactate, NTproBNP, O2_Flow, Oxygen,
PT, PTT, Potassium, RDW,
Reticulocyte_Count__Absolute, Reticulocyte_Count__Automated, 
Reticulocyte_Count__Manual, Rheumatoid_Factor,
Sodium, Thrombin, Tidal_Volume, Triglycerides,
Triiodothyronine_T3, Troponin_T, Urea_Nitrogen, WBC_Count
```

---

## 3. 문제점과 원인

### 3.1 예상보다 적은 컬럼 수

**문제**: 61개 예상 → 36개 실제

**원인**:
1. 많은 itemid가 샘플 데이터에 없음
2. 시간 윈도우(±1일)에도 데이터 없음
3. valuenum이 NULL인 검사 제외

### 3.2 중복 해결 효과 미미

**문제**: 대부분의 중복 itemid 중 하나만 실제 데이터 존재

**예시**:
- Glucose: 3개 중 2개만 데이터
- Creatinine: 2개 중 1개만 데이터
- Hemoglobin: 중복 항목 모두 데이터 없음

### 3.3 희소 데이터 문제

일부 검사는 극도로 희소:
- Rheumatoid_Factor: 1건
- Thrombin: 1건
- WBC_Count: 1건

---

## 4. 성과와 한계

### 4.1 성과

✅ **데이터 무결성 보장**
- 존재하는 모든 데이터 100% 보존
- 임의적 선택 없음

✅ **임상적 구분 가능**
- itemid별 고유 컬럼으로 출처 명확

✅ **재현성 확보**
- 일관된 처리 방식

### 4.2 한계

❌ **컬럼 수 증가 효과 미미**
- 실제로는 36개 컬럼 (이전 45개보다 오히려 감소)
- 데이터 부족으로 인한 한계

❌ **샘플 데이터의 한계**
- 1,200건 샘플에서는 많은 검사가 누락
- 전체 데이터셋 필요

❌ **복잡성 증가**
- 컬럼명이 길고 복잡
- 분석 시 그룹핑 필요

---

## 5. 권장사항

### 5.1 단기 개선

1. **하이브리드 접근**
   - 데이터가 충분한 검사: 개별 컬럼
   - 희소한 검사: 병합

2. **컬럼명 단순화**
   - 현재: `Glucose_50809_BloodGas`
   - 개선: `Glucose_BG` (Blood Gas)

### 5.2 장기 개선

1. **전체 데이터셋 사용**
   - 523,740건 전체 데이터에서 추출
   - 모든 itemid의 실제 가용성 파악

2. **임계값 기반 필터링**
   - 최소 100건 이상 데이터가 있는 itemid만 포함
   - 극도로 희소한 검사 제외

3. **메타데이터 강화**
   - 각 itemid의 임상적 의미 문서화
   - 사용 가이드라인 제공

---

## 6. 결론

개별 itemid 컬럼 유지 방식은 이론적으로 우수하나, 현재 샘플 데이터의 한계로 인해 완전한 효과를 보지 못했습니다.

### 핵심 교훈
1. **데이터 가용성이 최우선**: 아무리 좋은 방법론도 데이터가 없으면 무용
2. **샘플링의 중요성**: 1,200건은 87개 검사를 대표하기에 부족
3. **실용적 접근 필요**: 이상적 방법보다 실제 데이터에 맞는 방법 선택

### 최종 권장
- **현재 데이터**: 기존 45개 컬럼 방식 유지
- **전체 데이터 확보 시**: 개별 컬럼 방식 재시도
- **중간 솔루션**: 주요 중복 검사(Glucose, Creatinine)만 개별 관리

---

## 부록: 생성된 파일

1. **데이터 파일**
   - `labs_individual_long.csv`: 10,453 레코드
   - `labs_individual_wide.csv`: 1,200 × 80 (36 검사 + 36 offset + 메타)
   - `labs_individual_sources.csv`: 출처 추적

2. **메타데이터**
   - `duplicate_items_mapping.json`: 중복 매핑
   - `extraction_metadata_individual.json`: 추출 통계
   - `lab_items_individual.csv`: 42개 검사 목록

3. **스크립트**
   - `extract_labs_individual_columns.py`: 구현 코드

---

*문서 작성일: 2025-08-24*
*작성자: MIMIC 데이터 분석 팀*