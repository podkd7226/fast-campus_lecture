# 🏥 MIMIC-IV 데이터 분석 프로젝트

## 📋 프로젝트 소개

MIMIC-IV (Medical Information Mart for Intensive Care IV)는 MIT와 Beth Israel Deaconess Medical Center에서 제공하는 
대규모 의료 데이터베이스입니다. 이 프로젝트는 MIMIC-IV 데이터를 활용하여 다양한 의료 데이터 분석을 수행합니다.

### 주요 특징
- 🔍 **체계적 분석**: 기본, 종합, 상세 3단계 분석 체계
- 📊 **시각화**: 데이터를 이해하기 쉬운 그래프와 차트로 표현
- 📝 **상세 문서화**: 모든 분석 과정을 초보자도 이해할 수 있게 설명
- 🗂️ **모듈화 구조**: 각 분석이 독립적인 폴더로 구성

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 3.8 이상 필요
python --version

# 필요 라이브러리 설치
pip install pandas numpy matplotlib seaborn
```

### 2. 데이터 준비
MIMIC-IV 데이터는 `dataset2/` 폴더에 위치해야 합니다:
```
dataset2/
├── core/       # 핵심 테이블 (patients, admissions, transfers)
├── hosp/       # 병원 데이터 (diagnoses, prescriptions, labevents)
└── icu/        # 중환자실 데이터
```

### 3. 분석 실행
```bash
# 기본 분석 실행
cd analysis_basic
python analyze_mimic_data.py

# 종합 분석 실행
cd ../analysis_comprehensive
python comprehensive_mimic_analysis.py

# 상세 분석 실행
cd ../analysis_detailed
python mimic_detailed_analysis.py
```

## 📁 프로젝트 구조

```
fast campus_lecture/
│
├── 📄 README.md                    # 프로젝트 전체 설명 (현재 파일)
├── 📄 CLAUDE.md                    # 프로젝트 가이드라인 및 규칙
│
├── 📁 analysis_basic/              # 기본 데이터 탐색
│   ├── README.md                   # 기본 분석 설명
│   ├── analyze_mimic_data.py       # 분석 스크립트
│   └── figures/                    # 시각화 결과
│
├── 📁 analysis_comprehensive/      # 종합 통계 분석
│   ├── README.md                   # 종합 분석 설명
│   ├── comprehensive_mimic_analysis.py
│   ├── mimic_analysis_results.json # 분석 결과
│   └── figures/
│
├── 📁 analysis_detailed/           # 상세 임상 분석
│   ├── README.md                   # 상세 분석 설명
│   ├── mimic_detailed_analysis.py
│   └── figures/
│
└── 📁 dataset2/                    # MIMIC-IV 데이터
    ├── core/                       # 핵심 테이블
    ├── hosp/                       # 병원 데이터
    └── icu/                        # ICU 데이터
```

## 📊 분석 단계별 설명

### 1️⃣ 기본 분석 (analysis_basic)
**목적**: 데이터 구조 파악 및 품질 확인
- 각 테이블의 크기와 구조 확인
- 컬럼별 데이터 타입과 분포
- 결측값 현황 파악
- 테이블 간 관계 검증

**주요 파일**: 
- `analyze_mimic_data.py:4-39` - CSV 파일 분석 함수
- `analyze_mimic_data.py:50-65` - 데이터 관계 분석

[🔗 상세 문서 보기](./analysis_basic/README.md)

### 2️⃣ 종합 분석 (analysis_comprehensive)
**목적**: 주요 의료 지표 산출
- 환자 인구통계 (연령, 성별 분포)
- 입원 패턴 (재원 기간, 입원 경로)
- 사망률 분석 (병원 내 사망률, 연령별 사망률)
- 재입원율 (30일 재입원)
- 응급실 및 ICU 이용 현황

**주요 파일**:
- `comprehensive_mimic_analysis.py:46-60` - 인구통계 분석
- `comprehensive_mimic_analysis.py:83-93` - 재입원 분석

[🔗 상세 문서 보기](./analysis_comprehensive/README.md)

### 3️⃣ 상세 분석 (analysis_detailed)
**목적**: 임상 데이터 심층 분석
- 진단 패턴 (ICD 코드 분석)
- 처방 패턴 (약물 사용 분석)
- 검사 결과 분석
- 진료과별 서비스 이용
- 진단-치료 연관성

**주요 파일**:
- `mimic_detailed_analysis.py:30-75` - 진단 데이터 분석
- `mimic_detailed_analysis.py:77-120` - 처방 패턴 분석

[🔗 상세 문서 보기](./analysis_detailed/README.md)

## 📈 주요 분석 결과

### 환자 특성
- **총 환자 수**: 382,278명
- **평균 연령**: 65.4세
- **성별 분포**: 남성 53%, 여성 47%

### 입원 현황
- **총 입원 건수**: 523,740건
- **평균 재원 기간**: 7.8일
- **응급실 경유 입원**: 42%

### 주요 진단
1. 본태성 고혈압 (12.3%)
2. 2형 당뇨병 (8.7%)
3. 급성 신부전 (7.2%)
4. 폐렴 (6.8%)
5. 심방세동 (5.9%)

### 의료 질 지표
- **병원 내 사망률**: 8.3%
- **30일 재입원율**: 15.7%
- **ICU 입원율**: 31%

## 🛠️ 기술 스택

- **언어**: Python 3.8+
- **데이터 처리**: pandas, numpy
- **시각화**: matplotlib, seaborn
- **데이터 형식**: CSV, JSON

## 📚 참고 자료

### MIMIC 데이터베이스
- [MIMIC 공식 웹사이트](https://mimic.mit.edu/)
- [MIMIC-IV 문서](https://mimic-iv.mit.edu/docs/)
- [PhysioNet](https://physionet.org/)

### 의학 용어
- **ICU**: Intensive Care Unit (중환자실)
- **ICD**: International Classification of Diseases (국제 질병 분류)
- **LOS**: Length of Stay (재원 기간)
- **ED**: Emergency Department (응급실)

## ⚠️ 주의사항

### 데이터 보안
- MIMIC 데이터는 비식별화되었지만 여전히 민감한 의료 정보입니다
- 연구 목적으로만 사용해야 합니다
- 개인 식별 시도는 엄격히 금지됩니다

### 라이선스
- MIMIC 데이터 사용 시 PhysioNet Credentialed Health Data License 준수
- 분석 코드는 MIT License 적용

## 🤝 기여 방법

1. 이 저장소를 Fork 합니다
2. 새 분석을 위한 브랜치를 생성합니다
3. `analysis_[주제명]` 형식의 폴더를 생성합니다
4. CLAUDE.md 가이드라인에 따라 코드와 문서를 작성합니다
5. Pull Request를 제출합니다

## 📮 연락처

프로젝트 관련 문의사항이 있으시면:
- 이슈 생성: GitHub Issues 활용
- 이메일: [프로젝트 관리자 이메일]

## 🙏 감사의 말

- MIT Lab for Computational Physiology
- Beth Israel Deaconess Medical Center
- 모든 MIMIC 데이터 기여자들

---

*마지막 업데이트: 2025년 8월 12일*