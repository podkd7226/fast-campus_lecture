# 🏥 MIMIC-IV 의료 데이터 분석 실습
## Fast Campus 의료 데이터 분석 강의 자료

---

## 📋 이 강의는 무엇인가요?

**의료진을 위한 데이터 분석 입문 과정**입니다.
프로그래밍 경험이 없어도 괜찮습니다! 실제 병원 데이터(MIMIC-IV)를 활용하여 단계별로 배워나갑니다.

### 🎯 무엇을 배우나요?
- ✅ 병원 데이터를 컴퓨터로 분석하는 방법
- ✅ 환자 통계를 그래프로 만드는 방법
- ✅ AI를 활용한 사망률 예측 모델 만들기
- ✅ 연구 논문에 사용할 수 있는 데이터 처리 방법

### 📊 MIMIC-IV란?
미국 보스턴 병원의 실제 환자 데이터입니다.
- **환자 수**: 약 38만 명
- **입원 기록**: 약 52만 건
- **기간**: 2008년~2019년
- **특징**: 개인정보는 모두 제거된 안전한 데이터

---

## 🚀 프로그램 설치하기 (처음 한 번만!)

### 🖥️ 컴퓨터 준비하기

#### 1단계: 터미널(명령창) 열기
- **Windows**: 시작 메뉴 → "cmd" 검색 → 명령 프롬프트 실행
- **Mac**: Spotlight(🔍) → "터미널" 검색 → Terminal 실행

#### 2단계: 프로그램 설치하기

##### 🍎 Mac 사용자
터미널에 아래 명령어를 **한 줄씩** 복사해서 붙여넣고 Enter를 누르세요:

```bash
# 1. uv 설치 (Python 패키지 관리 도구)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 강의 자료 다운로드 (Git이 설치되어 있어야 함)
git clone https://github.com/podkd7226/fast-campus_lecture.git

# 3. 프로젝트 폴더로 이동
cd fast-campus_lecture

# 4. 필요한 프로그램들 자동 설치 (pyproject.toml 기반)
uv lock
uv sync

# 5. 가상환경 활성화 (매번 실행 전 필요)
source .venv/bin/activate

# 6. 설치 확인
python --version  # Python 3.13 이상이면 OK!
```

##### 🪟 Windows 사용자
명령 프롬프트에 아래 명령어를 **한 줄씩** 복사해서 붙여넣고 Enter를 누르세요:

```powershell
# 1. uv 설치 (Python 패키지 관리 도구)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 강의 자료 다운로드 (Git이 설치되어 있어야 함)
git clone https://github.com/podkd7226/fast-campus_lecture.git

# 3. 프로젝트 폴더로 이동
cd fast-campus_lecture

# 4. 필요한 프로그램들 자동 설치 (pyproject.toml 기반)
uv lock
uv sync

# 5. 가상환경 활성화 (매번 실행 전 필요)
.venv\Scripts\activate

# 6. 설치 확인
python --version  # Python 3.13 이상이면 OK!
```

📌 **중요**: `uv lock`과 `uv sync`는 반드시 `pyproject.toml` 파일이 있는 프로젝트 폴더에서 실행해야 합니다!

✅ **설치 완료 확인**: 마지막 명령어 실행 시 "Python 3.13" 이상이 나타나면 성공!

### 📂 실습 데이터 소개

강의에서 사용할 데이터는 이미 준비되어 있습니다:

| 데이터 종류 | 내용 | 환자 수 |
|------------|------|---------|
| 입원 정보 | 입원일, 퇴원일, 진료과 | 1,200건 |
| 환자 정보 | 나이, 성별, 인종 | 1,171명 |
| 검사 결과 | 혈액검사, 소변검사 등 | 다양 |
| 진단 정보 | ICD 질병 코드 | 다양 |
| 처방 정보 | 약물 처방 내역 | 다양 |

💡 **특별한 점**: 사망/생존 환자가 균등하게 포함되어 AI 학습에 최적화

---

## 📚 실습 폴더별 분석 내용

### 📊 `analysis_comprehensive/` - 종합 통계 분석
전체 MIMIC 데이터셋(52만 건)의 기본 통계를 분석합니다.
- 환자 인구통계: 연령, 성별, 인종 분포
- 입원 패턴: 재원기간, 입원경로, 퇴원형태
- 주요 의료지표: 병원 내 사망률, 30일 재입원율

### 👥 `analysis_demographic/` - 환자군 특성 분석
환자를 다양한 기준으로 분류하여 특성을 파악합니다.
- 연령대별 질병 패턴
- 성별에 따른 입원 특성
- 인종별 의료 이용 현황

### 🎲 `analysis_samplingmethod/` - 데이터 샘플링 방법론
대규모 데이터에서 연구용 샘플을 추출하는 방법을 다룹니다.
- 균형잡힌 1,200건 샘플 추출
- 사망/생존 비율 조정 (50:50)
- 재현 가능한 샘플링 전략

### 🔬 `analysis_initial_lab/` - 입원 당일 검사 분석
입원 첫날 시행된 혈액검사 데이터를 분석합니다.
- 70개 주요 검사항목 분석
- 검사 시행률 및 결측값 패턴
- 검사 결과와 예후의 상관관계

### ⏱️ `analysis_icu_los/` - ICU 재원기간 분석
중환자실 입실 환자의 재원기간을 분석합니다.
- ICU 재원일수 분포
- 장기 재원 위험요인
- 진료과별 ICU 이용 패턴

### ☠️ `analysis_death/` - 사망률 상세 분석
병원 내외 사망을 구분하여 분석합니다.
- 병원 내 사망: 2.5%
- 병원 후 사망: 5.4%
- 연령별, 질환별 사망률

### 🤖 `analysis_prediction/` - AI 예측 모델 개발
머신러닝을 이용한 사망률 예측 모델을 구축합니다.
- 3단계 데이터셋: Essential, Extended, Comprehensive
- 다양한 ML 알고리즘 비교 (Logistic Regression, Random Forest, XGBoost)
- 모델 성능: 정확도 75-83%

### 🗺️ `analysis_tsne/` - 고차원 데이터 시각화
t-SNE 기법으로 복잡한 의료 데이터를 2차원으로 표현합니다.
- 70차원 검사 데이터를 2D로 축소
- 환자군 클러스터링
- 사망/생존 패턴 시각화

### 🖼️ `xray/` - 특별 실습 자료
Jupyter Notebook 형태의 실습 자료입니다.
- `xray_first.ipynb`: X-ray 이미지 전처리
- `xray_second.ipynb`: 이미지 특징 추출
- `xray_third.ipynb`: 딥러닝 적용
- `regex_sample.ipynb`: 의료 텍스트 정규표현식

---

## 📊 실습으로 얻을 수 있는 결과들

### 🏥 환자 통계 (실습 데이터)
- **총 환자**: 1,171명
- **평균 나이**: 65.8세
- **남녀 비율**: 남자 55%, 여자 45%
- **평균 입원기간**: 약 9일

### 💡 AI 모델 성능
우리가 만든 사망률 예측 AI의 정확도:
- **기본 모델**: 75.8% 정확도
- **고급 모델**: 80.8% 정확도
- **최신 XGBoost**: 78.3% 정확도

🎯 **의미**: 10명 중 8명의 예후를 정확히 예측 가능!

---

## 🛠️ 사용하는 도구들 (자동 설치됨!)

### 📝 기본 도구
- **Python**: 데이터 분석용 프로그래밍 언어
- **Jupyter Notebook**: 코드를 한 줄씩 실행하며 배우기
- **uv**: 필요한 프로그램 자동 설치 도구

### 📊 분석 도구
- **pandas**: 엑셀처럼 데이터를 표로 다루기
- **matplotlib**: 그래프 그리기
- **scikit-learn**: AI 모델 만들기

💡 **걱정 마세요!** 이 모든 도구는 자동으로 설치됩니다.

---

## 📁 프로젝트 구조

각 분석은 독립적인 폴더로 구성되어 있습니다:

```
fast_campus_lecture/
├── 📄 README.md (현재 파일)
├── 📄 CLAUDE.md (프로젝트 가이드)
│
├── 📁 analysis_comprehensive/    # 기초 통계
├── 📁 analysis_demographic/      # 환자 분류
├── 📁 analysis_samplingmethod/   # 데이터 샘플링
├── 📁 analysis_initial_lab/      # 검사 분석
├── 📁 analysis_icu_los/         # ICU 분석
├── 📁 analysis_death/           # 사망률 분석
├── 📁 analysis_prediction/      # AI 예측 모델
├── 📁 analysis_tsne/           # 데이터 시각화
├── 📁 xray/                    # 특별 실습
│
├── 📁 dataset2/                # 원본 데이터
└── 📁 processed_data/          # 처리된 데이터
```

---

## 💡 자주 묻는 질문

### ❓ 프로그래밍을 전혀 못해도 되나요?
**네!** 이 강의는 의료진을 위해 만들어졌습니다. 코드를 직접 작성하기보다는 준비된 코드를 실행하고 결과를 해석하는 데 중점을 둡니다.

### ❓ 이 데이터로 논문을 쓸 수 있나요?
샘플 데이터는 학습용입니다. 실제 연구를 위해서는 MIMIC 공식 사이트에서 전체 데이터를 받으셔야 합니다.

### ❓ 매번 가상환경을 활성화해야 하나요?
네, 터미널을 새로 열 때마다 필요합니다. 이 명령어는 Python 실습 환경을 활성화합니다.
- **Mac**: `source .venv/bin/activate`
- **Windows**: `.venv\Scripts\activate`

## 📚 더 자세한 내용은?

각 분석 폴더의 `README.md` 파일을 확인하세요:
- 📊 [기초 통계 분석 자세히 보기](./analysis_comprehensive/README.md)
- 👥 [환자 분류 자세히 보기](./analysis_demographic/README.md)
- 🎲 [데이터 샘플링 자세히 보기](./analysis_samplingmethod/README.md)
- 🔬 [검사 데이터 분석 자세히 보기](./analysis_initial_lab/README.md)
- ⏱️ [ICU 분석 자세히 보기](./analysis_icu_los/README.md)
- ☠️ [사망률 분석 자세히 보기](./analysis_death/README.md)
- 🎨 [AI 예측 모델 자세히 보기](./analysis_prediction/README.md)
- 🗺️ [데이터 시각화 자세히 보기](./analysis_tsne/README.md)

---

## 📮 도움이 필요하신가요?

- **강의 Q&A**: Fast Campus 플랫폼에서 질문하기
- **MIMIC 데이터**: [공식 사이트](https://mimic-iv.mit.edu/docs/)
- **Python 기초**: 강의 자료의 '파이썬 기초' 섹션 참고

---

## 🎯 학습 목표 달성하기

이 강의를 완료하면:
1. ✅ 병원 데이터를 직접 분석할 수 있습니다
2. ✅ 통계와 그래프를 만들 수 있습니다
3. ✅ AI 예측 모델을 이해하고 활용할 수 있습니다
4. ✅ 연구에 필요한 데이터 처리 능력을 갖추게 됩니다

---

**함께 의료 데이터 분석의 세계로 떠나볼까요? 🚀**
*최종 업데이트: 2025년 9월*