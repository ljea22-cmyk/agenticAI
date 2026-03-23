# Week 12. Human-in-the-loop 워크플로우와 점진적 배포

> 원본: docs/ch11.md

## 학습 목표

- Human-in-the-loop(HITL)이 필요한 상황을 식별하고,
  - LangGraph의 `interrupt`와 `Command`로 승인 워크플로우를 구현한다
- Shadow Mode에서 전체 배포까지 5단계 점진적 배포 전략을 설계한다
- 암호화 서명과 변조 방지를 포함한 감사 로그 시스템을 설계한다
- 고위험 작업을 분리하고 적절한 승인 레벨을 적용한다

---

## 도입 배경

- 10장에서는 검증 파이프라인으로 LLM 출력의 신뢰성을 높이는 방법을 학습함
  - 검증 실패 + 재시도 초과 시 → 최종 결정을 사람에게 위임함
- 이 장에서는 그 사람 개입(Human-in-the-Loop, HITL)을 본격적으로 다룸
- AI 에이전트가 아무리 정교해도, 아래 상황에서는 사람의 최종 승인이 필수
  - 되돌릴 수 없는 작업 (예: 데이터 삭제)
  - 윤리적 판단이 필요한 상황 (예: 개인정보 처리)
  - 결제 실행, 외부 시스템 변경 등 고위험 작업
    - AI가 제안하더라도 사람이 확인해야 함

---

## 11.1 Human-in-the-loop의 필요성

- HITL(Human-in-the-loop)의 정의
  - AI 시스템의 특정 지점에서 사람이 개입하여 결정을 내리거나 승인하는 패턴
  - 목표: 완전 자동화가 아니라, AI의 효율성 + 사람의 판단력을 조합하는 것

### HITL이 필요한 상황

- 첫째, **고위험 작업**
  - 결제 처리, 데이터 삭제, 계약 체결 등
  - 되돌리기 어렵거나 비용이 큰 작업
  - 반드시 사람의 승인을 거쳐야 함
- 둘째, **불확실성이 높은 상황**
  - 검증 점수가 낮거나 모델이 확신하지 못하는 경우
  - 사람에게 판단을 위임하는 것이 적절함 (10장 내용 참조)
- 셋째, **윤리적 판단이 필요한 상황**
  - 법적 책임이 따르는 결정, 개인정보 처리, 콘텐츠 검열
  - AI가 판단하더라도 사람이 최종 책임을 져야 함
- 넷째, **외부 시스템에 영향을 미치는 작업**
  - 이메일 발송, API 호출, 서드파티 서비스 연동 등
  - 외부에 변경을 가하는 작업은 신중하게 검토해야 함

### AI 자율성과 사람 통제의 균형

- 모든 작업에 사람 승인을 요구하면 HITL의 의미가 퇴색함
- 바람직한 방향
  - 반복적이고 저위험인 작업 → 자동화
  - 중요한 결정에만 사람 개입
- 구현 방법
  - 작업을 위험도에 따라 분류
  - 차등 승인 정책을 적용

---

## 11.2 HITL 패턴 분류

- HITL은 개입 방식에 따라 여러 패턴으로 분류됨

### 주요 패턴

**표 11.1** HITL 패턴별 적용 시나리오

| 패턴 | 설명 | 적용 예시 |
|:---|:---|:---|
| Approval | 실행 전 명시적 승인 | 결제, 이메일 발송, 데이터 삭제 |
| Review | 결과 확인 후 진행 | 문서 요약, 보고서 생성 |
| Edit | 상태나 결과를 직접 수정 | 프롬프트 수정, 데이터 보정 |
| Escalation | 상위 권한자에게 위임 | 고액 결제, 민감 정보 접근 |
| Override | AI 결정을 사람이 덮어씀 | 자동 분류 결과 수정 |

- **Approval 패턴**
  - 가장 흔한 형태
  - AI가 작업을 제안 → 사람이 승인하거나 거부
- **Review 패턴**
  - AI가 작업을 완료한 후 사람이 결과를 확인
  - 필요시 수정
- **Edit 패턴**
  - 사람이 AI의 중간 상태나 입력을 직접 수정
- **Escalation 패턴**
  - 일반 승인자가 결정할 수 없는 경우
  - 상위 권한자에게 위임
- **Override 패턴**
  - AI가 이미 내린 결정을 사람이 번복
  - → 예시: 자동 분류 시스템에서 오분류를 수정할 때 사용

---

## 11.3 LangGraph의 interrupt와 Command

- LangGraph에서 `interrupt` 함수는 HITL 워크플로우 구현의 권장 방식
- 이 함수를 사용하면
  - 그래프 실행을 특정 노드에서 일시 중지
  - 사람의 입력을 받은 후 재개 가능

### interrupt 함수의 동작 원리

- `interrupt`를 호출하면 발생하는 일
  - 그래프 실행이 일시 중지됨
  - 현재 스레드가 "interrupted" 상태로 표시됨
  - interrupt에 전달한 데이터는 persistence layer(지속성 저장소)에 저장됨
  - 이후 `Command(resume=...)`를 통해 사람의 응답을 전달하면 그래프가 재개됨

```python
from langgraph.types import interrupt, Command

def approval_node(state):
    decision = interrupt({"action": state["action"], "risk": "high"})
    if decision == "approved":
        return Command(goto="execute")
    return Command(goto="reject")
```

### Command 객체

- 그래프의 흐름을 제어하는 도구
- 기능
  - 상태를 업데이트하면서 다음 노드를 지정 가능
  - 동적 라우팅(런타임 시점에 흐름을 결정)을 가능하게 함
  - 사전에 정의된 엣지 없이도 런타임에 흐름을 결정할 수 있음

### 요구사항

- interrupt를 사용하려면 **Checkpointer**가 필요함
  - Checkpointer: 각 단계 후 그래프 상태를 저장하는 컴포넌트
  - 중단된 지점에서 정확히 재개할 수 있게 해 줌
- Checkpointer 구현 종류
  - 메모리 기반
  - 파일 기반
  - 데이터베이스 기반

---

## 11.4 승인 요청 UX 설계

- 사람에게 승인을 요청할 때는 충분한 정보를 제공해야 함
  - ⚠ 정보가 부족하면 올바른 판단을 내릴 수 없음
  - ⚠ 정보가 과다하면 핵심을 놓칠 수 있음

### 승인 요청 메시지 구성

- 효과적인 승인 요청 메시지에 포함되어야 할 요소
  - **작업 내용**: 무엇을 할 것인가
  - **대상**: 어디에 영향을 미치는가
  - **위험도**: 왜 승인이 필요한가
  - **컨텍스트**: 어떤 상황에서 요청되었는가
  - **선택지**: 승인, 거부, 수정 등

### 타임아웃과 기본 동작

- 승인 요청이 무한정 대기할 수는 없음
- 타임아웃을 설정하고, 타임아웃 시 기본 동작을 정의해야 함
  - 고위험 작업: 기본적으로 **거부**
  - 저위험 작업: **자동 승인**

### 비동기 승인

- 모든 승인이 실시간일 필요는 없음
- 저우선순위 작업은 비동기 채널로 라우팅 가능
  - → 예시: Slack, 이메일, 대시보드
- 이 경우 워크플로우는 승인이 완료될 때까지 대기 상태로 유지됨

---

## 11.5 감사 로그와 승인 이력

- 규정 준수와 책임 추적을 위해 모든 승인 이력을 기록해야 함
- 감사 로그(Audit Log)의 핵심
  - "누가, 언제, 무엇을, 왜" 했는지를 추적

### 필수 로깅 항목

- 효과적인 감사 로그에 포함되어야 할 정보
  - **Actor Identity**: 누가 행위를 수행했는가 (사람, 시스템, AI 에이전트)
  - **Timestamp**: 언제 발생했는가
  - **Action**: 무엇을 했는가 (작업 유형, 대상)
  - **Decision**: 결과는 무엇인가 (승인, 거부, 실행, 차단)
  - **Reason**: 왜 그런 결정을 내렸는가
- AI 시스템에서 추가 권장 기록 항목
  - 프롬프트
  - 검색된 컨텍스트
  - 도구 호출 파라미터
  - 안전성 점수

### 불변 로그

- 감사 로그는 변경 불가능(immutable)해야 함
  - 이유: 한 번 기록된 이벤트가 수정·삭제될 수 없어야 책임 추적이 가능함
- 구현 방법
  - 암호화된 저장소 활용
  - 해시 체인(Hash Chain) 활용 → 무결성 보장

### 보존 기간

- 규정에 따라 3~7년 보존이 요구되기도 함
  - → 예시: SOC 2, PCI DSS, HIPAA 등의 규정
- 조직의 규정 준수 요구사항에 맞춰 보존 정책을 설정해야 함

---

## 11.6 고위험 작업 분리

- 모든 작업에 동일한 승인 수준을 적용하는 것은 비효율적
- 위험도에 따라 작업을 분류하고 차등 승인 정책을 적용해야 함

### 위험도 분류 기준

- 위험도 평가의 주요 기준
  - **가역성**: 되돌릴 수 있는가
  - **영향도**: 비용이 얼마나 드는가
  - **범위**: 외부에 영향을 미치는가

**표 11.2** 위험도별 승인 레벨

| 위험도 | 특성 | 승인 레벨 | 예시 |
|:---:|:---|:---|:---|
| 낮음 | 되돌릴 수 있음, 내부 영향 | 자동 승인 | 로그 조회, 검색, 조회 |
| 중간 | 일부 되돌릴 수 있음 | 단일 승인 | 설정 수정, 파일 변경 |
| 높음 | 되돌릴 수 없음, 외부 영향 | 필수 승인 | 삭제, 결제, 외부 전송 |

### 승인 레벨 정의

- **자동 승인**: 저위험 작업에 적용, 사람 개입 없이 진행
- **단일 승인**: 한 명의 승인자가 확인하면 진행
- **필수 승인 (다중 승인)**: 반드시 지정된 권한자의 승인이 있어야 함
  - ⚠ 승인 없이는 절대 실행되지 않음

### 긴급 우회 절차

- 예외적인 상황에서 일시적으로 승인을 우회해야 할 수 있음
- ⚠ 주의사항
  - 모든 우회는 철저히 기록되어야 하며, 사후 감사 대상이 됨
  - 우회 권한은 최소한의 인원에게만 부여해야 함

---

## 11.7 점진적 배포 전략

- 에이전트 시스템의 특성
  - 전통적인 소프트웨어와 달리 비결정적(non-deterministic)
  - 동일한 입력에 대해 다른 도구를 호출하거나 다른 순서로 실행할 수 있음
  - ⚠ 코드 배포처럼 한 번에 전환하는 방식은 위험
- **점진적 배포(Gradual Rollout)**: 에이전트의 행동을 단계별로 검증하며 실제 환경에 투입하는 전략

### 5단계 배포 파이프라인

**표 11.3** 에이전트 점진적 배포 5단계

| 단계 | 이름 | 에이전트 행동 | 검증 기준 | 롤백 조건 |
|:---:|:---|:---|:---|:---|
| 1 | Shadow Mode | 분석만 수행, 실행 안 함 | 기존 시스템과 결과 비교 | 일치율 < 90% |
| 2 | 샌드박스 | 격리 환경에서 실행 | 오류율, 비용, 응답 시간 | 오류율 > 5% |
| 3 | 스테이징 | 실제 데이터, 제한된 영향 | 전체 메트릭 기준 충족 | 이상 징후 탐지 |
| 4 | 소규모 프로덕션 | 트래픽 5-10% 라우팅 | A/B 비교, 사용자 피드백 | 성능 저하 감지 |
| 5 | 전체 배포 | 100% 트래픽 처리 | 지속적 모니터링 | 자동 롤백 임계값 |

### Shadow Mode의 핵심 원리

- Shadow Mode(1단계): 가장 안전한 검증 방법
- 동작 방식
  - 에이전트가 실제 요청을 받아 분석하고 응답을 생성함
  - 그러나 그 결과를 사용자에게 전달하지 않음
  - 대신 기존 시스템의 응답과 비교하여 측정
    - 일치율
    - 품질 점수
    - 비용

```python
def shadow_mode_node(state):
    agent_response = agent.invoke(state["query"])
    legacy_response = legacy_system.process(state["query"])
    comparison = compare_responses(agent_response, legacy_response)
    log_shadow_result(comparison)  # 기록만, 실행 안 함
    return {"shadow_result": comparison}
```

- Shadow Mode에서 충분한 데이터가 축적되면 (일반적으로 1~2주)
  - 일치율과 품질 점수를 기준으로 다음 단계 진입 여부를 판단

### 카나리 배포와 자동 롤백

- 4단계(소규모 프로덕션)에서 **카나리 배포 패턴** 적용
  - 전체 트래픽의 5~10%만 새 에이전트로 라우팅
  - 나머지는 기존 시스템이 처리
- 자동 롤백 조건
  - 핵심 메트릭(오류율, 응답 시간, 비용)이 임계값을 초과하면
  - 자동으로 트래픽을 기존 시스템으로 복원
- 자동 롤백이 에이전트 배포에서 특히 중요한 이유
  - LLM의 비결정적 특성으로 인해
  - 테스트에서 발견하지 못한 엣지 케이스가 프로덕션에서 발생할 수 있기 때문

---

## 11.8 감사 로그 설계: 무결성과 추적 가능성

- 11.5절에서 감사 로그의 기본 개념과 필수 항목을 다룸
- 이 절에서는 프로덕션 환경에서 요구되는 사항을 설계
  - 암호화 서명
  - 변조 방지
  - 에이전트 행동의 완전한 추적 가능성

### 암호화 서명 기반 로그 무결성

- 각 로그 엔트리에 디지털 서명을 적용하면 사후 변조를 탐지할 수 있음
- 사용 기술: **HMAC** (Hash-based Message Authentication Code, 해시 기반 메시지 인증 코드)
  - 로그 내용과 타임스탬프를 함께 서명

```python
import hmac, hashlib, json

def sign_log_entry(entry: dict, secret_key: bytes) -> str:
    payload = json.dumps(entry, sort_keys=True).encode()
    return hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
```

- 서명 검증 방법
  - 동일한 키로 서명을 재계산
  - 저장된 서명과 비교하여 변조 여부를 판단

### 해시 체인: 블록체인 원리의 적용

- **해시 체인(Hash Chain)**: 각 로그 엔트리가 이전 엔트리의 해시를 포함하는 구조
  - 블록체인의 핵심 원리와 동일한 방식
  - ⚠ 중간 로그가 삭제되거나 변경되면 체인이 깨져 즉시 탐지됨
- 구조
  - 첫 번째 엔트리: 초기 해시(genesis hash)를 가짐
  - 이후 각 엔트리: `hash(이전_해시 + 현재_내용 + 타임스탬프)`로 연결됨
- 검증 방법
  - 첫 엔트리부터 순차적으로 해시를 재계산
  - 체인의 무결성을 확인

### 에이전트 행동의 완전한 추적

- 에이전트 시스템에서는 단순 입출력 기록을 넘어, 중간 추론 과정까지 추적해야 함
- 완전한 추적 가능성(Full Traceability)을 위해 기록해야 할 정보

**표 11.4** 에이전트 감사 로그 확장 스키마

| 계층 | 기록 항목 | 목적 |
|:---|:---|:---|
| 요청 | 원본 입력, 세션 ID, 사용자 ID | 요청 식별 |
| 추론 | 프롬프트, 모델 응답, 토큰 수, 지연 시간 | 의사결정 추적 |
| 도구 | 호출된 도구, 파라미터, 반환값, 실행 시간 | 행동 감사 |
| 승인 | 승인 요청, 승인자, 결정, 사유 | 책임 추적 |
| 결과 | 최종 출력, 품질 점수, 후속 조치 | 결과 검증 |

- 이 스키마를 적용하면 다음 질문에 완전하게 답할 수 있음
  - "에이전트가 왜 이 도구를 호출했는가"
  - "누가 이 작업을 승인했는가"
- 활용 목적
  - 규제 대응
  - 사고 조사
  - 시스템 개선의 근거

---

## 11.9 실습: 승인 워크플로우 구현

- 실습 내용
  - 위험도에 따른 차등 승인 로직과 감사 로그가 포함된 HITL 워크플로우 구현
  - 저위험 작업: 자동 진행
  - 중위험 작업: 단일 승인
  - 고위험 작업: 반드시 승인 후 실행

_전체 코드는 practice/chapter11/code/11-7-hitl-workflow.py 참고_

### 실습 환경 설정

```bash
cd practice/chapter11
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r code/requirements.txt
```

### 핵심 구현

- 위험도 분류와 승인 라우팅은 LangGraph 조건부 엣지로 구현

```python
graph.add_conditional_edges(
    "classify",
    route_after_classification,
    {"approve": "approve", "execute": "execute"}
)
```

- 라우팅 흐름
  - 저위험 작업: `classify` 노드 → 바로 `execute` 노드로 진행
  - 중위험/고위험 작업: `classify` 노드 → `approve` 노드를 거침
    - 승인 시: `execute` 노드로 분기
    - 미승인 시: `block` 노드로 분기

### 감사 로그 구현

- 모든 이벤트는 `AuditLog` 클래스를 통해 기록됨

```python
audit_log.log("approval_request", {
    "request_id": state["request_id"],
    "action_type": state["action_type"],
    "decision": approval_status
})
```

### 실행 결과

- 4개의 테스트 요청에 대해 워크플로우를 실행한 결과

**표 11.5** HITL 워크플로우 실행 결과

| 작업 유형 | 대상 | 위험도 | 승인 필요 | 결과 |
|:---|:---|:---:|:---:|:---:|
| read (조회) | users_table | 낮음 | 아니오 | 실행됨 |
| modify (수정) | config_settings | 중간 | 예 | 승인 → 실행됨 |
| delete (삭제) | user_data | 높음 | 예 | 거부 → 차단됨 |
| send (전송) | external_api | 높음 | 예 | 승인 → 실행됨 |

- 결과 분석
  - 4개 요청 중 3개 실행, 1개(삭제) 차단
  - 삭제 작업: 고위험으로 분류 → 추가 검토 필요를 이유로 거부됨
  - 의미: 고위험 작업이 사람 승인 없이는 진행되지 않음을 확인

### 산출물

- 실습 결과 저장 경로
  - `practice/chapter11/data/output/ch11_hitl_result.json`: 워크플로우 실행 결과
  - `practice/chapter11/data/output/ch11_audit_log.json`: 감사 로그 (11개 이벤트)

---

## 11.10 실패 사례와 교훈

- HITL 워크플로우 운영 시 발생할 수 있는 문제와 대응 방법 정리

### 승인 지연으로 인한 병목

- 문제: 승인 요청이 쌓이면 전체 시스템이 느려짐
- 완화 방법
  - 승인자 풀을 확대
  - 비동기 승인 채널을 활용
  - 타임아웃 후 자동 에스컬레이션(상위 권한자에게 자동 위임) 정책 적용

### 승인 피로 (Approval Fatigue)

- 문제: 너무 많은 승인 요청은 승인자의 피로를 유발
  - 결과: 형식적인 승인으로 이어질 수 있음
- 대응 방법
  - 위험도 분류를 정교화하여 정말 중요한 작업에만 승인 요구
  - 저위험 작업의 자동화 비율을 높이는 것이 핵심

### 권한 남용과 우회

- 문제: 긴급 우회 절차가 남용되면 HITL의 의미가 사라짐
- 대응 방법
  - ⚠ 모든 우회는 예외 없이 로깅하고, 정기적으로 감사해야 함
  - 우회 권한은 최소 인원에게만 부여
  - 우회 사용 시마다 사유를 반드시 기록

### 로그 누락과 데이터 무결성

- 문제: 감사 로그가 누락되면 책임 추적이 불가능해짐
- 대응 방법
  - 로깅은 동기적으로 수행
  - ⚠ 로그 저장 실패 시 작업도 실패하도록 구현하는 것이 안전
  - 해시 체인이나 블록체인 기반 로깅을 통해 무결성 강화 가능

---

## 핵심 정리

- HITL은 AI의 효율성과 사람의 판단력을 조합하는 패턴
  - 위험도에 따라 자동·단일·필수 승인으로 차등화
- LangGraph의 `interrupt`와 `Command`로 승인 워크플로우를 구현
  - Checkpointer가 상태를 보존
- 에이전트 배포는 5단계 점진적 배포로 진행
  - Shadow Mode → 샌드박스 → 스테이징 → 소규모 프로덕션 → 전체 배포
- 감사 로그는 HMAC 서명과 해시 체인으로 무결성을 보장
  - 요청·추론·도구·승인·결과 5개 계층을 기록
- 승인 피로를 방지하기 위해 저위험 작업은 자동화
- 카나리 배포와 자동 롤백으로 프로덕션 안정성 확보

---

## 다음 장 예고

- 완성된 에이전트 시스템을 배포하고 운영하는 방법을 다룸
- 학습 예정 내용
  - 관측 가능성 (Observability)
  - 비용 최적화
  - 보안 관리
  - 프로덕션 환경에서 고려해야 할 사항 전반

---

## 참고문헌

LangChain. (2025). Human-in-the-loop. *LangGraph Documentation*. https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/

LangChain. (2025). Making it easier to build human-in-the-loop agents with interrupt. *LangChain Blog*. https://blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/

Permit.io. (2025). Human-in-the-Loop for AI Agents: Best Practices, Frameworks, Use Cases, and Demo. https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo

ISACA. (2025). Safeguarding the Enterprise AI Evolution Best Practices for Agentic AI Workflows. https://www.isaca.org/resources/news-and-trends/industry-news/2025/safeguarding-the-enterprise-ai-evolution-best-practices-for-agentic-ai-workflows

Latitude. (2025). Audit Logs in AI Systems: What to Track and Why. https://latitude-blog.ghost.io/blog/audit-logs-in-ai-systems-what-to-track-and-why/

Anthropic. (2025). Building effective agents. https://www.anthropic.com/research/building-effective-agents

Microsoft. (2025). Safe deployment practices for AI agents. *Azure AI Documentation*. https://learn.microsoft.com/en-us/azure/ai-services/agents/concepts/safe-deployment
