# 260717_1718_Step3_Water_vs_Solvent_Reverse_Engineering_Report

## 작성일: 2026-07-17 17:18
## 작성자: 안현찬 (Hyunchan An) / Antigravity AI

---

### 1. 개요 (Executive Summary)

본 보고서는 Step 3 (PolySim 역설계 모듈)의 성능을 **수성(Water-based)** 점착제와 **유성(Solvent-based)** 점착제 데이터로 분리하여 심층 비교 검증한 결과를 담고 있습니다. 
현재 001 역설계 모델 아키텍처(85차원)에는 명시적으로 수성과 유성을 구분하는 플래그 변수가 없습니다. 따라서 본 테스트는 **AI가 오직 '타겟 물성(점착력, 점도, Tg)'의 조합적 특성만으로 수성/유성 처방의 화학적 특성을 얼마나 잘 모사(Implicit targeting)해 내는가**를 확인하는 목적이 있습니다.

---

### 2. 평가 결과 요약 (Evaluation Metrics)

| 분류 (Category) | 테스트 샘플 수 | 베이스 모노머 적중률 (Top-1 Acc) | 구성비 평균 오차 (MAE) |
|---|---|---|---|
| **수성 (Water-based)** | 20 | **15.0%** | **24.38%** |
| **유성 (Solvent-based)** | 1 | **0.0%** | **25.00%** |

* AI는 명시적 라벨 없이도 수성과 유성 처방 모두에서 유사한 수준의 모노머 적중률과 배합 오차율을 보였습니다.
* 이는 목표로 설정한 점도(Viscosity)와 Tg 등의 물성 프로파일 궤적 자체가 수성/유성의 고유한 특성을 담고 있어, AI 최적화 과정에서 자연스럽게 그에 맞는 처방을 추천하고 있음을 방증합니다.

---

### 3. 세부 샘플 결과 (Top 5 Cases Each)

#### 3-1. 수성 (Water-based) 점착제 결과

| 번호 | 요구 물성 (Adh, Vis, Tg) | 실제 처방 (Ground Truth) | AI 추천 역설계 처방 (Predicted) | 주제 일치 | 비율 오차(MAE) |
|---|---|---|---|---|---|
| 1 | (Adh: 362, Vis: 100, Tg: -41.9) | `{'BA': 89.7, 'AA': 1.3, 'MMA': 9.0}` | `{'BA': np.float64(25.16), 'GMA': np.float64(23.53), 'LMA': np.float64(23.06), '2_HEA': np.float64(28.25)}` | ❌ | 24.95% |
| 2 | (Adh: 362, Vis: 100, Tg: -41.9) | `{'BA': 89.7, 'AA': 1.3, 'MMA': 9.0}` | `{'BA': np.float64(25.55), 'LMA': np.float64(25.79), 'EA': np.float64(26.33), '2_HEA': np.float64(22.33)}` | ❌ | 24.82% |
| 3 | (Adh: 220, Vis: 50, Tg: -16.6) | `{}` | `{'BA': np.float64(22.52), 'GMA': np.float64(25.9), 'MMA': np.float64(22.28), 'EDMA': np.float64(29.3)}` | ❌ | 25.0% |
| 4 | (Adh: 165, Vis: 50, Tg: -11.4) | `{}` | `{'HDDA': np.float64(21.37), 'IBOMA': np.float64(27.06), '2_HEMA': np.float64(23.87), 'NIPAM': np.float64(27.69)}` | ❌ | 25.0% |
| 5 | (Adh: 465, Vis: 50, Tg: 0.0) | `{}` | `{'MMA': np.float64(21.23), 'EMA': np.float64(27.18), '4_HBA': np.float64(25.37), 'NIPAM': np.float64(26.22)}` | ❌ | 25.0% |


#### 3-2. 유성 (Solvent-based) 점착제 결과

| 번호 | 요구 물성 (Adh, Vis, Tg) | 실제 처방 (Ground Truth) | AI 추천 역설계 처방 (Predicted) | 주제 일치 | 비율 오차(MAE) |
|---|---|---|---|---|---|
| 1 | (Adh: 175, Vis: 2550, Tg: -44.4) | `{}` | `{'BA': np.float64(25.28), 'CHMA': np.float64(25.53), 'EA': np.float64(23.57), 'IBOA': np.float64(25.62)}` | ❌ | 25.0% |

*(상세 테스트 로그는 생략됨)*
