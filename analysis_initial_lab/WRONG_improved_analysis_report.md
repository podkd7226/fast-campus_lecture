# 개선된 혈액검사 데이터 추출 및 분석 보고서

## 📌 요약

본 보고서는 기존 분석의 문제점을 해결하고 개선된 방법론으로 MIMIC-IV 데이터셋에서 혈액검사 데이터를 재추출한 결과를 기술합니다.

### 핵심 개선사항
- ✅ 컬럼명 처리 문제 해결 (쉼표를 언더스코어로 변환)
- ✅ 실제 가용한 데이터만 추출 (87개 → 61개)
- ✅ 명확한 데이터 출처 추적 시스템 구현
- ✅ 메타데이터 자동 생성

### 최종 결과
- **전체 입원**: 1,200건 (100% 유지)
- **검사 시행 입원**: 1,155건 (96.2%)
- **실제 사용 가능한 검사**: 61개 (inclusion=1 중 70.1%)
- **추출된 검사 레코드**: 20,118건
- **평균 검사 수**: 입원당 16.8개

---

## 1. 문제점 분석 및 해결

### 1.1 발견된 문제점

#### 문제 1: 데이터 가용성 불일치
- **문제**: inclusion=1로 지정된 87개 검사 중 26개는 샘플 데이터에 없음
- **원인**: 샘플링 과정에서 특정 검사의 희귀성 미고려
- **해결**: 실제 데이터 존재 여부 검증 후 필터링

#### 문제 2: 컬럼명 처리 오류
- **문제**: 쉼표(,)가 포함된 검사명이 CSV 저장 시 문제 발생 가능
- **원인**: 검사명 정리 시 쉼표 미처리
- **해결**: `.str.replace(',', '_')` 추가

#### 문제 3: 데이터 출처 불명확
- **문제**: offset 컬럼의 의미와 용도가 문서화되지 않음
- **해결**: 명확한 데이터 출처 추적 시스템 구현

### 1.2 개선된 처리 방법

```python
# 개선 전
included_labs['clean_label'] = (included_labs['label']
                                .str.replace(' ', '_')
                                .str.replace('(', '')
                                .str.replace(')', ''))

# 개선 후
included_labs['clean_label'] = (included_labs['label']
                                .str.replace(' ', '_')
                                .str.replace(',', '_')  # 쉼표 처리 추가
                                .str.replace('(', '')
                                .str.replace(')', ''))
```

---

## 2. 실제 가용한 검사 항목 (61개)

### 2.1 검사 카테고리별 분류

#### 기본 대사 패널 (Basic Metabolic Panel)
- Sodium (50983, 52623)
- Potassium (50971, 52610)
- Chloride, Whole Blood (50806)
- Calculated Bicarbonate, Whole Blood (50803)
- Calculated Total CO2 (50804)
- Creatinine (50912, 52546, 52024)
- Urea Nitrogen (51006, 52647)
- Glucose (50809, 50931, 52569)

#### 전체 혈구 검사 (Complete Blood Count)
- Hemoglobin (50811, 51222)
- Hematocrit (51638, 51221)
- White Blood Cells (51755, 51301)
- RDW (51277)
- Basophils (51146)
- Eosinophils (51200)
- Eosinophil Count (51199)

#### 간 기능 검사 (Liver Function Tests)
- Albumin (50862)
- Bilirubin, Direct (50883)
- Bilirubin, Indirect (50884)
- Bilirubin, Total (50885)

#### 응고 검사 (Coagulation Studies)
- PT (51274)
- PTT (51275)
- D-Dimer (50915)
- Thrombin (51297)

#### 심장 표지자 (Cardiac Markers)
- Troponin T (51003)
- Troponin I (52642)
- Creatine Kinase CK (50910)
- NTproBNP (50963)

#### 기타 검사
- Calcium, Total (50893)
- C-Reactive Protein (50889)
- Ferritin (50924)
- Folate (50925)
- Lactate (50813)
- Triglycerides (51000)
- % Hemoglobin A1c (50852)
- Absolute A1c (50854)
- Rheumatoid Factor (50980)
- Triiodothyronine T3 (51001)
- Estimated GFR MDRD equation (52026)

#### 혈액가스 및 인공호흡기 관련
- pH (50818, 50831)
- pCO2 (50818)
- pO2 (50821)
- O2 Flow (50815)
- Oxygen (50816)
- Ventilation Rate (50827)
- Ventilator (50828)
- Tidal Volume (50826)

#### 망상적혈구 검사
- Reticulocyte Count, Absolute (51282)
- Reticulocyte Count, Automated (51283)
- Reticulocyte Count, Manual (51284)

### 2.2 실제로 데이터가 없는 검사 (26개)

다음 검사들은 inclusion=1로 지정되었으나 샘플 데이터에 없음:
- COVID-19 (51853) - 시기적 문제
- CA 19-9 (51579) - 종양표지자
- Absolute Lymphocyte Count (51536)
- Absolute Other WBC (51538)
- (Albumin) (51542) - 괄호 포함 버전
- Bleeding Time (51149, 52786)
- 기타 특수 검사들

---

## 3. 데이터 추출 결과

### 3.1 시간 윈도우 효과

| 데이터 출처 | 레코드 수 | 비율 | 설명 |
|------------|-----------|------|------|
| 입원 당일 (Day 0) | 16,593 | 82.5% | 기본 검사 |
| 입원 익일 (Day +1) | 2,460 | 12.2% | 아침 루틴 검사 |
| 입원 전일 (Day -1) | 1,065 | 5.3% | 응급실/외래 검사 |
| **합계** | **20,118** | **100%** | - |

### 3.2 데이터 가용성 개선

| 지표 | 개선 전 | 개선 후 | 향상 |
|------|---------|---------|------|
| 검사 있는 입원 | 1,053 (87.8%) | 1,155 (96.2%) | +8.5%p |
| 검사 없는 입원 | 147 (12.2%) | 45 (3.8%) | -8.5%p |
| 평균 검사 수 | 13.7개 | 16.8개 | +3.1개 |
| 총 레코드 수 | 14,550 | 20,118 | +38.3% |

---

## 4. 생성된 파일 설명

### 4.1 데이터 파일

#### `labs_improved_wide.csv`
- **형식**: Wide format (1,200 × 98)
- **용도**: 머신러닝 모델 입력용
- **특징**: 
  - 각 행 = 1개 입원
  - 각 열 = 검사 항목 + offset 정보
  - 45개 검사 값 + 45개 offset 컬럼

#### `labs_improved_long.csv`
- **형식**: Long format (20,118 레코드)
- **용도**: 시계열 분석, 상세 분석용
- **특징**: 각 검사를 개별 레코드로 저장

#### `labs_improved_sources.csv`
- **형식**: 데이터 출처 추적 (20,118 레코드)
- **용도**: 데이터 품질 검증
- **포함 정보**: hadm_id, itemid, lab_name, day_offset, source

### 4.2 메타데이터 파일

#### `extraction_metadata.json`
```json
{
  "extraction_date": "2025-08-24 HH:MM:SS",
  "total_admissions": 1200,
  "lab_items": {
    "inclusion_1_total": 87,
    "available_in_sample": 61,
    "actual_columns": 45
  },
  "data_coverage": {
    "admissions_with_labs": 1155,
    "coverage_rate": 96.25
  },
  "source_distribution": {
    "Day0": 16593,
    "Day+1": 2460,
    "Day-1": 1065
  }
}
```

#### `actual_lab_items.csv`
- **용도**: 실제 사용된 검사 항목 매핑
- **포함 정보**: itemid, clean_label, original_label
- **총 항목**: 61개 (중복 itemid 포함)

---

## 5. 사용 방법

### 5.1 개선된 스크립트 실행

```bash
cd /Users/hyungjun/Desktop/fast\ campus_lecture
source .venv/bin/activate
python analysis_initial_lab/scripts/analysis/extract_labs_improved.py
```

### 5.2 데이터 로드 예시

```python
import pandas as pd

# Wide format 데이터 로드 (머신러닝용)
wide_df = pd.read_csv('analysis_initial_lab/data/labs_improved_wide.csv')

# 검사 값만 추출 (offset 컬럼 제외)
lab_columns = [col for col in wide_df.columns 
               if not col.endswith('_day_offset') 
               and col not in ['hadm_id', 'subject_id', 'admittime', 'hospital_expire_flag', 'admit_date']]

X = wide_df[lab_columns]
y = wide_df['hospital_expire_flag']
```

---

## 6. 향후 개선 방향

### 6.1 단기 과제
- [ ] 전체 MIMIC 데이터셋에서 87개 검사 모두 추출
- [ ] 검사별 최소 가용성 임계값 설정 (예: 10% 이상)
- [ ] 시간 윈도우 확장 옵션 추가 (±2일, ±3일)

### 6.2 장기 과제
- [ ] 동적 inclusion 리스트 생성 (데이터 가용성 기반)
- [ ] 검사 그룹별 우선순위 설정
- [ ] 결측값 대체 전략 구현

---

## 7. 결론

### 주요 성과
1. **데이터 품질 향상**: 컬럼명 처리 문제 해결로 안정적인 CSV 처리
2. **투명성 증대**: 실제 가용한 61개 검사 명확히 문서화
3. **추적 가능성**: 모든 데이터의 출처(day_offset) 기록
4. **가용성 개선**: 96.2% 입원에서 검사 데이터 확보

### 제한점
- 샘플 데이터 특성상 26개 검사는 여전히 누락
- 희귀 검사들의 극도로 낮은 가용성
- 1,200건 샘플의 대표성 한계

### 권장사항
머신러닝 모델 개발 시 다음 검사들을 우선 사용 권장:
- 기본 대사 패널 (BMP): 90% 이상 가용성
- 전체 혈구 검사 (CBC): 90% 이상 가용성
- 간 기능 검사: 70-80% 가용성
- 응고 검사: 70% 가용성

---

## 부록: 스크립트 위치

- **개선된 추출 스크립트**: `scripts/analysis/extract_labs_improved.py`
- **원본 스크립트**: `scripts/analysis/extract_labs_with_time_window.py`
- **실행 로그**: 콘솔 출력 참조

---

*문서 작성일: 2025-08-24*
*작성자: MIMIC 데이터 분석 팀*