# 🔍 MIMIC 데이터 종합 분석

## 📌 개요
MIMIC-IV 데이터셋에 대한 포괄적인 분석을 수행하여 환자 인구통계, 입원 패턴, 사망률, 
재입원율 등 주요 의료 지표를 산출합니다. 이 분석은 병원 운영과 환자 관리에 
중요한 통찰을 제공합니다.

**⚠️ 업데이트 (2025-08-18)**: 기존 샘플링 분석(5만개)에서 전체 데이터 분석으로 변경되었습니다.

## 🎯 분석 목표
- 목표 1: 환자 인구통계학적 특성 파악
- 목표 2: 입원 패턴과 재원 기간 분석
- 목표 3: 사망률 및 재입원율 계산
- 목표 4: 응급실 및 중환자실 이용 현황 분석

## 📊 사용 데이터
| 파일명 | 설명 | 분석 행 수 |
|--------|------|------------|
| `../dataset2/core/admissions.csv` | 환자 입원 정보 | 523,740 행 (전체) |
| `../dataset2/core/patients.csv` | 환자 기본 정보 | 382,278 행 (전체) |
| `../dataset2/core/transfers.csv` | 병동 이동 정보 | 2,189,535 행 (전체) |

## 🔧 주요 코드 설명

### 1. 데이터 로딩 및 전처리 (comprehensive_mimic_analysis.py:15-33)

**날짜 변환 처리**:
```python
admissions_df['admittime'] = pd.to_datetime(admissions_df['admittime'])
admissions_df['dischtime'] = pd.to_datetime(admissions_df['dischtime'])
```
문자열 형태의 날짜/시간 데이터를 파이썬이 이해할 수 있는 날짜 형식으로 변환합니다.

**재원 기간 계산** (comprehensive_mimic_analysis.py:30):
```python
admissions_df['los_days'] = (admissions_df['dischtime'] - 
                             admissions_df['admittime']).dt.total_seconds() / 86400
```
퇴원 시각에서 입원 시각을 빼서 재원 일수를 계산합니다.

### 2. 기본 통계 분석 (comprehensive_mimic_analysis.py:36-44)

**고유 환자 수 계산**:
- 각 테이블별로 고유한 환자 ID 개수를 계산
- 전체 입원 건수와 이동 기록 수 집계

### 3. 환자 인구통계 분석 (comprehensive_mimic_analysis.py:46-60)

**연령 그룹 분류**:
```python
pd.cut(patients_df['anchor_age'], 
       bins=[0, 18, 40, 60, 80, 100],
       labels=['Pediatric', 'Young Adult', 'Middle Age', 'Elderly', 'Very Elderly'])
```
환자 연령을 5개 그룹으로 분류하여 연령대별 분포를 파악합니다.

### 4. 입원 패턴 분석 (comprehensive_mimic_analysis.py:62-74)

**주요 분석 항목**:
- 입원 유형별 분포 (응급, 예약, 긴급 등)
- 입원 경로 TOP 10
- 퇴원 후 행선지 TOP 10
- 보험 유형별 분포
- 재원 기간 통계 (평균, 중앙값, 분위수)

### 5. 사망률 분석 (comprehensive_mimic_analysis.py:76-81)

**병원 내 사망률 계산**:
```python
hospital_mortality_rate = (admissions_df['hospital_expire_flag'].sum() / 
                          len(admissions_df)) * 100
```
전체 입원 중 병원에서 사망한 비율을 계산합니다.

### 6. 재입원 분석 (comprehensive_mimic_analysis.py:83-93)

**30일 재입원 판정 로직**:
1. 환자별로 입원 기록을 시간순 정렬
2. 이전 퇴원일과 다음 입원일 간격 계산
3. 30일 이내 재입원 여부 판정

```python
readmission_df['days_since_discharge'] = 
    (readmission_df['admittime'] - readmission_df['prev_dischtime']).dt.total_seconds() / 86400
readmission_df['readmission_30'] = 
    (readmission_df['days_since_discharge'] <= 30) & 
    (readmission_df['days_since_discharge'] > 0)
```

### 7. 응급실 이용 분석 (comprehensive_mimic_analysis.py:95-101)

**응급실 체류 시간 계산**:
```python
admissions_df['ed_los_hours'] = 
    (admissions_df['edouttime'] - admissions_df['edregtime']).dt.total_seconds() / 3600
```
응급실 퇴실 시각에서 등록 시각을 빼서 체류 시간을 시간 단위로 계산합니다.

### 8. 중환자실 이동 패턴 (comprehensive_mimic_analysis.py:103-114)

**ICU 유형 구분**:
- MICU: 내과 중환자실
- SICU: 외과 중환자실
- CCU: 심장 중환자실
- CVICU: 심혈관 중환자실
- NICU: 신생아 중환자실
- PICU: 소아 중환자실
- TSICU: 외상 외과 중환자실

### 9. 데이터 품질 평가 (comprehensive_mimic_analysis.py:116-132)

각 테이블별로 결측값 현황을 분석하여 데이터 완전성을 평가합니다.

### 10. 결과 저장 (comprehensive_mimic_analysis.py:169-171)

모든 분석 결과를 JSON 형식으로 저장하여 추후 활용이 가능하도록 합니다.

## 🚀 실행 방법

### 필요한 도구
- Python 3.8 이상
- 필요 라이브러리:
  ```bash
  pip install pandas numpy matplotlib seaborn
  ```

### 실행 명령
```bash
cd analysis_comprehensive
python comprehensive_mimic_analysis.py
```

### 예상 실행 시간
- 약 3-5분 (전체 데이터 기준)
- 메모리 사용량: 약 2-3GB

## 📈 결과 해석

### 주요 발견사항 (mimic_analysis_results.json 기반 - 전체 데이터)

#### 1. 환자 인구통계
- **총 환자 수**: 382,278명
- **입원 기록이 있는 환자**: 256,878명
- **성별 분포**: 여성 52.2%, 남성 47.8%
- **평균 연령**: 40.9세
- **연령대별 분포**:
  - 소아 (0-18): 1.1%
  - 청년 (19-40): 32.9%
  - 중년 (41-60): 23.7%
  - 노년 (61-80): 19.4%
  - 초고령 (80+): 7.0%

#### 2. 입원 패턴 (총 523,740건)
- **평균 재원 기간**: 4.6일
- **중앙값 재원 기간**: 2.7일
- **95분위 재원 기간**: 14.4일
- **주요 입원 경로**:
  1. 응급실: 52.9%
  2. 의사 소개: 27.5%
  3. 타 병원 전원: 8.4%

#### 3. 사망률 지표
- **병원 내 사망률**: 1.79% (9,350건)
- **전체 사망률**: 2.49% (9,509명)
- **연령대별 사망 분포**:
  - 80세 이상: 2,693명
  - 61-80세: 4,205명
  - 41-60세: 1,984명
  - 19-40세: 413명
  - 0-18세: 1명

#### 4. 재입원 현황
- **30일 재입원율**: 17.4% (91,177건)
- **재입원 경험 환자**: 85,798명 (33.4%)
- **평균 입원 횟수**: 2.04회
- **최대 입원 횟수**: 238회

#### 5. 응급실 이용
- **응급실 경유 입원**: 59.5% (311,504건)
- **평균 응급실 체류 시간**: 10.2시간
- **중앙값 응급실 체류 시간**: 7.4시간

#### 6. 병동 이동 패턴 (총 2,189,535건)
- **주요 이벤트 유형**:
  - 응급실: 661,053건 (30.2%)
  - 입원: 523,749건 (23.9%)
  - 퇴원: 523,740건 (23.9%)
  - 전동: 480,993건 (22.0%)

### 임상적 의미

1. **연령 분포의 특징**: 
   - 61세 이상이 26.4%를 차지
   - 고령층으로 갈수록 사망률 급증

2. **높은 응급 의료 의존도**:
   - 입원의 59.5%가 응급실 경유
   - 평균 10.2시간의 응급실 체류로 과밀화 시사

3. **재입원 관리의 시급성**:
   - 17.4%의 30일 재입원율
   - 33.4%의 환자가 다회 입원 경험
   - 체계적인 퇴원 후 관리 필요

## ❓ 자주 묻는 질문

**Q: 전체 데이터 분석의 장점은?**
A: 전체 데이터를 분석함으로써 편향 없는 정확한 통계를 얻을 수 있습니다. 
샘플링 분석보다 더 신뢰할 수 있는 결과를 제공합니다.

**Q: 재원 기간이 음수인 경우가 있나요?**
A: 데이터 입력 오류로 간혹 발생할 수 있습니다. 
이런 경우는 데이터 정제 과정에서 제외해야 합니다.

**Q: ICU와 일반 병동의 차이는 무엇인가요?**
A: ICU는 중환자실로 24시간 집중 모니터링과 치료가 필요한 환자가 입원합니다.
일반 병동보다 의료진 대 환자 비율이 높고 고급 의료 장비를 갖추고 있습니다.

## 🔗 관련 분석
- [상세 분석](../analysis_detailed/README.md) - 특정 질환이나 치료에 대한 심층 분석

## 📝 추가 분석 제안
1. **질환별 분석**: ICD 진단 코드를 활용한 질병별 패턴 분석
2. **계절별 변화**: 입원 패턴의 계절적 변동 분석
3. **의료비 분석**: DRG 코드를 활용한 의료비 패턴 분석
4. **약물 사용 분석**: 처방 데이터를 활용한 약물 사용 패턴

## 🔒 데이터 보안 및 윤리
- MIMIC 데이터는 비식별화되었지만 여전히 민감한 의료 정보입니다
- 연구 목적으로만 사용하고 개인 식별 시도는 금지됩니다
- 결과 공유 시 개인정보 보호 규정을 준수해야 합니다