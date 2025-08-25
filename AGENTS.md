# Repository Guidelines

## 프로젝트 구조 및 모듈 구성
- `analysis_*`: 주제별 분석 폴더. 핵심 스크립트는 `analysis_initial_lab/scripts/analysis/*.py`에 위치합니다.
- `analysis_initial_lab/data`, `analysis_initial_lab/figures`: 입력 데이터와 생성된 그래프/표 결과.
- `dataset2/`, `processed_data/`: 로컬 데이터와 파생 산출물(대용량·민감 데이터는 커밋 금지).
- `pyproject.toml`, `uv.lock`: 의존성 및 프로젝트 메타데이터.

## 빌드 · 테스트 · 개발 명령
- 의존성 설치: `uv sync`
- 스크립트 실행(예): `uv run python analysis_initial_lab/scripts/analysis/analyze_initial_labs.py`
- 다른 분석 실행: `uv run python analysis_initial_lab/scripts/analysis/create_missing_rate_comparison.py`
- 린트/포맷(선택): Ruff 사용 시 `uv run ruff check .`, `uv run ruff format .`

## 코딩 스타일 · 네이밍
- PEP 8, 4칸 들여쓰기, 88–100자 줄폭.
- 파일/함수는 `snake_case`, 클래스는 `PascalCase`, 상수는 `UPPER_SNAKE`.
- 분석 스크립트는 동사로 시작: 예) `extract_labs_all_itemids.py`.
- `WRONG_*.py`는 보존용입니다. 수정 대신 새 파일로 개선하세요.

## 테스트 지침
- 현재 공식 테스트 미구성. 소규모 샘플로 실행 후 `figures/` 또는 `processed_data/` 산출물을 확인하세요.
- 순수 함수화 및 간단한 `assert`/도크스트링 예제 추가를 권장합니다.
- 테스트 도입 시: `tests/`에 `test_*.py` 생성, 실행은 `uv run pytest`.

## 커밋 · PR 가이드
- Conventional Commits 권장: 예) `feat: 시간 창 분석 추가`, `fix: 결측치 집계 오류 수정`.
- PR에는 요약, 배경, 재현 명령어, 전/후 비교 결과(그림/표 경로)를 포함하세요.
- 대용량/민감 데이터(특히 PHI)가 포함되지 않았는지 반드시 확인하세요.

## 보안 · 설정 팁
- 환자 식별 정보와 원본 데이터는 절대 커밋하지 않습니다.
- 파일 경로는 하드코딩 대신 상수/환경변수로 파라미터화하세요.
