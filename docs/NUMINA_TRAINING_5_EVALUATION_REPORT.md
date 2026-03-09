# Numina Training 5 Problems – Evaluation Report

**데이터셋:** `data/numina_training_5k.jsonl` (상위 5문항)  
**실행 스크립트:** `examples/eval_numina_training_5.py`  
**결과 파일:** `results/numina_training_5_eval.json`

---

## 1. 선정된 5문제 요약

| # | 유형 | 참조 답 | 출처 |
|---|------|--------|------|
| 1 | Number Theory | proof | olympiads |
| 2 | Algebra | proof | olympiads |
| 3 | Geometry | proof | olympiads |
| 4 | Combinatorics | **302** | olympiads |
| 5 | Geometry | proof | olympiads |

- **문제 1:** 소수 $p$에 대해 $x^p+y^p+z^p-x-y-z$가 서로 다른 세 소수의 곱이 되게 하는 $p$ 전부 구하기  
- **문제 2:** $a^4-2019a = b^4-2019b = c$일 때 $-\sqrt{c} < ab < 0$ 증명  
- **문제 3:** 삼각형에서 수심·외심·중점을 쓰여 “선분 HM과 AN의 교점이 외접원 위에 있음” 증명  
- **문제 4:** $5\times 100$ 격자에서 조건(인접 검은 칸 ≤2)을 만족하는 검은 칸 수 $n$의 최댓값 → **302**  
- **문제 5:** 외접 사다리꼴에서 내접원과 접점·내심이 한 직선 위에 있음 증명  

---

## 2. 메트릭 (Metrics)

**참조 전용 실행** (`--reference-only`, 솔버 미사용) 기준:

| 항목 | 값 |
|------|-----|
| **Total** | 5 |
| **Correct** | 0 |
| **Incorrect** | 5 |
| **Accuracy** | 0.00% |
| **Avg solve time** | 0.00s |
| **Difficulty** | hard (olympiads) |
| **Source** | olympiads (5/5) |

- 실제 솔버로 평가하려면 모델 로드 후 아래처럼 실행하면 됩니다.  
  `python examples/eval_numina_training_5.py`  
- 참조 답·증명만 보려면:  
  `python examples/eval_numina_training_5.py --reference-only`

---

## 3. 참조 풀이 (Proof)

### Problem 1 [Number Theory] — 참조 답: proof

**Proof (excerpt):**  
Let $A=x^p+y^p+z^p-x-y-z$. For $p=2$, take $x=y=4$, $z=3$ → $A=30=2\cdot 3\cdot 5$. For $p=3$: $x=3,y=2,z=1$ → $A=30$. For $p=5$: $x=2,y=1,z=1$ → $A=30$. For $p\geq 7$, modulo 2 and 3 shows $A$ divisible by 2 and 3; by Fermat, $A\equiv 0\pmod p$, so $A=6p$. If $x\geq 2$ then $6p\geq 2^p-2$; induction gives $2^n-2>6n$ for $n\geq 6$, contradiction. So only $p=2,3,5$.

---

### Problem 2 [Algebra] — 참조 답: proof

**Proof (excerpt):**  
$2019(a-b)=a^4-b^4=(a-b)(a+b)(a^2+b^2)$; since $a\neq b$, $(a+b)(a^2+b^2)=2019$. Then $2c = a^4+b^4-2019(a+b) = a^4+b^4-(a+b)^2(a^2+b^2) = -2ab(a^2+ab+b^2)$, so $ab(a^2+ab+b^2)=-c$. From $a^2+ab+b^2 > (ab)^2$ (with $a+b\neq 0$) one gets $(ab)^2<c$, hence $-\sqrt{c}<ab<\sqrt{c}$ and sign argument gives $-\sqrt{c}<ab<0$.

---

### Problem 3 [Geometry] — 참조 답: proof

**Proof (excerpt):**  
$\angle APQ = \angle HCB$ and $\angle AQP = \angle CBH$, so $\triangle APQ \sim \triangle HCB$. Midpoints $M,N$ of $BC,PQ$ give $\triangle AQN \sim \triangle HBM$, so $\angle ANQ = \angle HMB$. For $L = AN \cap HM$, angle chase gives $\angle MLN = 90°$. Let $D$ be the point on the circumcircle of $ABC$ diametrically opposite $A$; $D$ is the reflection of $H$ in $M$, so $D\in MH$ and $\angle DLA=90°$, hence $L$ lies on the circumcircle of $ABC$.

---

### Problem 4 [Combinatorics] — 참조 답: **302**

**Proof (excerpt):**  
Colouring all edge cells and the full middle row except the second and second-to-last cells gives 302 black cells and satisfies “at most 2 adjacent black”. Covering the board with one initial fragment, 24 middle fragments, and one final fragment shows that in each fragment type, at most 2 cells per letter can be black, yielding upper bound $(5+24\cdot 6+1)\cdot 2+2=302$. So the maximum is **302**.

---

### Problem 5 [Geometry] — 참조 답: proof

**Proof (excerpt):**  
Let $I$ be the incenter of $\triangle ABC$ and $R = BI \cap MN$. Then $m(\widehat{ANM})=90°-\frac12 m(\widehat{MAN})$ and $m(\widehat{BIC})=90°+\frac12 m(\widehat{MAN})$, so $IRNC$ is cyclic, hence $m(\widehat{BRC})=90°$. Then $m(\widehat{BCR}) = \frac12 m(\widehat{BCD})$, so $CR$ is the angle bisector of $\angle DCB$ and $R$ is the incenter of the trapezoid; thus the incenter lies on line $MN$.

---

## 4. 실행 방법

```bash
# 참조 답 + 증명만 (솔버 없음, 빠름)
python examples/eval_numina_training_5.py --reference-only

# 전체 파이프라인으로 5문항 풀기 (모델 로드 필요)
python examples/eval_numina_training_5.py
```

완료 후 메트릭과 상세 결과는 `results/numina_training_5_eval.json`에 저장됩니다.
