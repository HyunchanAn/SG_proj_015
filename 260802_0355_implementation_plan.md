# 실데이터 기반 피드백 루프 구축 계획 (Priority 1)

현재 파이프라인의 가장 치명적인 약점인 "데이터가 쌓여도 똑똑해지지 않는 단방향(Open-loop) 구조"를 해결하기 위해, 현장의 성공/실패 데이터를 수집하고 이를 모델과 최적화기에 재공급하는 완전한 폐쇄 루프(Closed-loop)를 설계합니다.

## User Review Required

> [!IMPORTANT]
> **피드백 데이터 수집 주체 결정**
> 1. `SG_proj_014` (오케스트레이터)가 엔드포인트를 노출하여 피드백을 수집하고 DB에 적재하는 방안
> 2. `SG_sys` (API Gateway) 또는 별도의 신규 `016` (피드백/메트릭) 모듈을 만들어 전담시키는 방안
> 본 계획서에서는 **1번 방안(014 모듈 확장)** 으로 작성했습니다. 동의하시나요?

## Open Questions

> [!WARNING]
> 피드백 데이터의 신뢰도(Confidence) 등급이 필요할까요?
> 예를 들어, "실험실 테스트 완료(Lab-tested)"와 "작업자 육안 평가(Visual-check)"는 신뢰도가 다릅니다. 가중치 옵티마이저가 이를 차등 반영(Weighted loss)하도록 스키마에 `confidence_level` 컬럼을 둘지 결정이 필요합니다.

## Proposed Changes

### SG_DB (데이터베이스 리포지토리)

#### [NEW] `init_scripts/02_feedback_tables.sql`
- **`matching_feedback` 테이블 신설**:
  - `feedback_id` (PK)
  - `request_payload` (JSONB) - 당시 요청된 타겟 스펙(SFE, 조도 등)
  - `recommended_product_code` (VARCHAR) - 추천된 제품 코드
  - `is_successful` (BOOLEAN) - 최종 매칭 성공 여부
  - `actual_score` (FLOAT) - 현장 평가 점수 (0~100)
  - `feedback_notes` (TEXT) - 실패 사유 또는 정성적 평가
  - `created_at` (TIMESTAMP)

### SG_proj_014 (오케스트레이터 모듈)

#### [MODIFY] `src/main.py` & `src/api/routes.py`
- `POST /feedback/match` 엔드포인트 신설.
- 프론트엔드 또는 작업자가 매칭 결과를 전송하면, 이를 검증하여 `SG_DB`의 `matching_feedback` 테이블에 INSERT 하는 로직 구현.

### SG_proj_012 (매칭 모듈)

#### [MODIFY] `scripts/optimize_weights.py`
- 기존의 하드코딩된 모의 데이터(`fetch_ground_truth_matches()`)를 제거합니다.
- `SG_DB`의 `matching_feedback` 테이블에서 `is_successful = true` 인 데이터를 쿼리해 Ground Truth로 삼도록 로직을 전면 수정합니다.
- (선택) `cron`이나 스케줄러를 통해 이 스크립트를 주기적으로 자동 실행하고 `config.json`을 업데이트하는 CI/CD 워크플로 구성.

## Verification Plan

### Automated Tests
- `SG_proj_014`: 피드백 접수 API에 대한 유닛/통합 테스트 (Mock DB 활용).
- `SG_proj_012`: DB에서 피드백 리스트를 정상적으로 읽어와 가중치 최적화를 수행하는지 테스트 (sqlite in-memory 테스트).

### Manual Verification
- 로컬 DB에 가상의 피드백 데이터 10건을 INSERT.
- `012`의 `optimize_weights.py`를 실행하여 가중치가 해당 10건의 정답에 맞게 변동되는지 확인.
- `014`의 `/feedback/match` API를 cURL로 호출하여 DB에 레코드가 정상 적재되는지 E2E 확인.
