# 📊 MIMIC-IV hosp 데이터 추출 결과 보고서

## 📌 개요
2025년 8월 19일, MIMIC-IV 데이터셋의 hosp 폴더에서 샘플링된 1,200건의 입원 데이터에 대응하는 병원 데이터를 성공적으로 추출했습니다.

**사용 스크립트**: `scripts/analysis/extract_hosp_essential.py`

## 🎯 추출 목표
- 샘플링된 환자(1,171명)의 병원 관련 데이터 추출
- 전체 데이터셋 분석에 필요한 사전 테이블 보존
- 머신러닝 모델 학습용 균형잡힌 데이터셋 구축

## 📊 추출 결과

### 1. 환자별 데이터 (샘플링 적용)
| 테이블 | 원본 크기 | 추출 크기 | 추출 비율 | 파일 크기 |
|--------|-----------|-----------|-----------|-----------|
| diagnoses_icd | 5,280,351행 | 129,924행 | 2.5% | 3.5 MB |
| drgcodes | 769,622행 | 13,147행 | 1.7% | 913 KB |
| labevents | 122,103,667행 | 2,825,084행 | 2.3% | 316 MB |
| microbiologyevents | 3,397,914행 | 80,931행 | 2.4% | 18 MB |
| services | 562,892행 | 10,160행 | 1.8% | 435 KB |

**총 추출 데이터**: 3,059,246행

### 2. 사전 테이블 (전체 복사)
| 테이블 | 설명 | 파일 크기 |
|--------|------|-----------|
| d_hcpcs.csv | HCPCS 코드 사전 | 3.2 MB |
| d_icd_diagnoses.csv | ICD 진단 코드 사전 | 8.4 MB |
| d_icd_procedures.csv | ICD 시술 코드 사전 | 7.0 MB |
| d_labitems.csv | 검사 항목 사전 | 0.1 MB |

## 🔧 기술적 세부사항

### 처리 방법
- **대용량 파일 처리**: labevents (1.2억 행)는 100,000행 단위 청크로 처리
- **필터링 기준**: subject_id 또는 hadm_id가 샘플에 포함된 경우
- **처리 시간**: 총 158.8초 (약 2분 39초)

### 데이터 감소율
- 평균 97.6%의 데이터 감소
- 원본 대비 약 2.3%의 데이터만 추출
- 저장 공간: 약 339 MB (원본 수 GB에서 대폭 감소)

## 📁 파일 위치
```
processed_data/hosp/
├── 환자 데이터 (샘플링)
│   ├── diagnoses_icd_sampled.csv      # 진단 코드
│   ├── drgcodes_sampled.csv           # DRG 코드
│   ├── labevents_sampled.csv          # 검사 결과
│   ├── microbiologyevents_sampled.csv # 미생물 검사
│   └── services_sampled.csv           # 진료 서비스
├── 사전 테이블 (전체)
│   ├── d_hcpcs.csv                    # HCPCS 코드 사전
│   ├── d_icd_diagnoses.csv            # ICD 진단 사전
│   ├── d_icd_procedures.csv           # ICD 시술 사전
│   └── d_labitems.csv                 # 검사 항목 사전
└── extraction_stats.json              # 추출 통계
```

## 🔧 실행 방법

### 스크립트 실행
```bash
# 프로젝트 루트에서 실행
cd "/Users/hyungjun/Desktop/fast campus_lecture"
source .venv/bin/activate
python analysis_samplingmethod/scripts/analysis/extract_hosp_essential.py
```

**실행 파일**: `extract_hosp_essential.py`
- 이 스크립트는 필수 5개 테이블(diagnoses_icd, drgcodes, labevents, microbiologyevents, services)과 4개 사전 테이블을 추출합니다
- 다른 extract_hosp_*.py 파일들은 테스트용이었으며 삭제되었습니다

## 🚀 활용 방법

### Python에서 데이터 로드
```python
import pandas as pd

# 진단 코드 로드
diagnoses = pd.read_csv('processed_data/hosp/diagnoses_icd_sampled.csv')

# ICD 코드 사전과 조인
icd_dict = pd.read_csv('processed_data/hosp/d_icd_diagnoses.csv')
diagnoses_with_names = diagnoses.merge(
    icd_dict, 
    on=['icd_code', 'icd_version'], 
    how='left'
)
```

### 데이터 통합 예시
```python
# 입원 데이터와 진단 데이터 결합
admissions = pd.read_csv('processed_data/core/admissions_sampled.csv')
diagnoses = pd.read_csv('processed_data/hosp/diagnoses_icd_sampled.csv')

# 입원별 진단 개수 계산
diagnosis_counts = diagnoses.groupby('hadm_id').size().reset_index(name='diagnosis_count')
admissions_with_diag = admissions.merge(diagnosis_counts, on='hadm_id', how='left')
```

## 📈 주요 통계

### 샘플 환자 특성
- **총 환자 수**: 1,171명
- **총 입원 건수**: 1,200건
- **평균 진단 수**: 108개/입원
- **평균 검사 수**: 2,354개/입원
- **평균 서비스 수**: 8.5개/입원

### 데이터 품질
- ✅ 모든 샘플 환자에 대한 데이터 추출 완료
- ✅ 데이터 무결성 검증 통과
- ✅ 사전 테이블과의 매핑 가능

## 💡 참고사항

### 사용 시 주의점
1. 이 데이터는 머신러닝 모델 학습용으로 균형잡힌 샘플입니다
2. 실제 사망률 통계 분석에는 전체 데이터를 사용해야 합니다
3. labevents는 가장 큰 테이블로, 분석 시 메모리 관리가 필요할 수 있습니다

### 다음 단계
1. ICU 데이터 추출 (icu 폴더)
2. 통합 데이터셋 구축
3. 탐색적 데이터 분석 (EDA)
4. 머신러닝 모델 개발

## 🔗 관련 문서
- [샘플링 방법론](../sampling_methodology_report.md)
- [종합 분석](../../analysis_comprehensive/README.md)
- [CLAUDE.md 가이드라인](../../CLAUDE.md)

---

*작성일: 2025-08-19*
*작성자: MIMIC-IV 분석팀*