# 🚨 데이터 분석 오류 평가 및 예방 가이드

## 📌 개요

이 문서는 MIMIC-IV 데이터 분석 과정에서 실제로 발생한 오류들을 체계적으로 정리하고, 
향후 유사한 실수를 예방하기 위한 가이드라인을 제공합니다.

**핵심 교훈**: "작동하는 코드 ≠ 올바른 분석"

---

## ⚠️ 주요 오류 유형 및 체크리스트

### 1. 데이터 매칭 오류 ✅
- [ ] JOIN 방식 확인 (INNER vs LEFT)
- [ ] NULL 값 처리 확인
- [ ] 매칭 키의 완전성 검증
- [ ] 전체 데이터 개수 보존 확인

**실제 사례**: [hadm_id 매칭 실패로 616건 누락](./data_matching_errors.md)
- 결과: 1,043건 → 427건으로 축소 (59% 손실)

### 2. 선택 편향 (Selection Bias) ✅
- [ ] 전체 모집단 대표성 확인
- [ ] 필터링 조건의 타당성 검증
- [ ] 제외된 데이터의 특성 분석
- [ ] 결과의 일반화 가능성 평가

**실제 사례**: [21개 검사만 선택한 분석](./selection_bias_analysis.md)
- 영향: 사망률 왜곡 (36.5% vs 실제 25.0%)

### 3. 생존자 편향 (Survivorship Bias) ✅
- [ ] 분석에서 제외된 케이스 확인
- [ ] 데이터가 없는 이유 파악
- [ ] Missing Not At Random (MNAR) 검토
- [ ] 완전 케이스 분석의 한계 인식

**예시**: 검사를 하지 않은 환자 제외
- 문제: 너무 건강하거나 너무 아파서 검사 못함

### 4. 데이터 완전성 오류 ✅
- [ ] 입력 데이터 수 = 출력 데이터 수
- [ ] 예상 범위와 실제 결과 비교
- [ ] 극단값 및 이상치 확인
- [ ] 데이터 타입 일관성

**검증 도구**: [verify_data_completeness.py](./scripts/verify_data_completeness.py)

---

## 🔍 실제 오류 사례 분석

### 사례 1: hadm_id NULL 처리 실패

| 분석 방법 | 결과 | 문제점 |
|----------|------|--------|
| 잘못된 방법 | 427건 (35.6%) | hadm_id NULL 무시 |
| 올바른 방법 | 1,043건 (86.9%) | subject_id + 날짜 매칭 |

**상세 분석**: [데이터 매칭 오류 분석](./data_matching_errors.md)

### 사례 2: 하드코딩된 검사 항목

| 접근법 | 검사 수 | 커버리지 | 사망률 |
|--------|---------|----------|--------|
| 하드코딩 | 21개 | 35.6% | 36.5% |
| inclusion=1 | 98개 | 87.8% | 25.0% |

**상세 분석**: [선택 편향 분석](./selection_bias_analysis.md)

---

## 💡 예방 가이드라인

### 1. 데이터 로딩 단계
```python
# ❌ 잘못된 예
df_filtered = df[df['condition'] == True]  # 조건 맞는 것만

# ✅ 올바른 예
df_all = df.copy()  # 전체 유지
df_all['meets_condition'] = df_all['condition'] == True
```

### 2. JOIN 작업
```python
# ❌ 위험한 INNER JOIN
result = df1.merge(df2, on='key', how='inner')
# 매칭 안 되는 데이터 손실

# ✅ 안전한 LEFT JOIN
result = df1.merge(df2, on='key', how='left')
# 모든 데이터 보존
```

### 3. NULL 처리
```python
# ❌ NULL 무시
df_clean = df.dropna()

# ✅ NULL 분석
print(f"NULL 비율: {df.isna().mean()}")
print(f"NULL 패턴: {df.isna().sum()}")
```

### 4. 검증 루틴
```python
# ✅ 항상 검증
assert len(output_df) == len(input_df), "데이터 손실 발생!"
assert output_df['key'].nunique() == input_df['key'].nunique()
```

---

## 📊 검증 도구

### 1. 데이터 완전성 검증
```bash
python scripts/verify_data_completeness.py \
    --input data/original.csv \
    --output data/processed.csv
```

### 2. 분석 방법 비교
```bash
python scripts/compare_analysis_methods.py \
    --method1 ../analysis_initial_lab/scripts/analysis/extract_admission_day_labs.py \
    --method2 ../analysis_initial_lab/scripts/analysis/extract_initial_labs_complete.py
```

---

## 📚 참고 자료

### 내부 문서
- [데이터 매칭 오류 상세](./data_matching_errors.md)
- [선택 편향 분석](./selection_bias_analysis.md)
- [실제 사례: analysis_initial_lab](../analysis_initial_lab/README.md)

### 외부 자료
- [Statistical Bias Types](https://en.wikipedia.org/wiki/Bias_(statistics))
- [Data Quality Assessment](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3797360/)
- [MIMIC-IV Documentation](https://mimic.mit.edu/)

---

## 🎯 핵심 교훈

> **"데이터 분석의 90%는 데이터 전처리"**
> 
> 하지만 잘못된 전처리는 100% 잘못된 결론으로 이어집니다.

### 기억해야 할 원칙

1. **의심하라**: 예상과 다른 결과가 나오면 코드를 의심
2. **검증하라**: 각 단계마다 데이터 수와 분포 확인
3. **보존하라**: 원본 데이터는 최대한 유지
4. **문서화하라**: 제외된 데이터와 그 이유 명시
5. **재현하라**: 다른 사람이 같은 결과를 얻을 수 있게

---

## 🔄 업데이트 이력

| 날짜 | 내용 | 관련 이슈 |
|------|------|-----------|
| 2025-08-20 | 최초 작성 | hadm_id 매칭 오류 발견 |
| 2025-08-20 | 선택 편향 사례 추가 | 21개 vs 98개 검사 |

---

*작성자: Claude*  
*검토 필요: 데이터 분석팀*  
*다음 업데이트: 새로운 오류 발견 시*