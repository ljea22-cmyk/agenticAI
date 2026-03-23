# Week 6. LangGraph 1.0으로 상태·분기·반복을 제어한다

> 원본: docs/ch6.md

## 학습 목표

- LangGraph의 상태(State) 모델을 정의하고 노드 간 데이터를 전달한다
- LangGraph 1.0의 안정성 보장과 핵심 변경 사항을 설명한다
- 조건부 엣지(conditional edge)를 사용하여 워크플로우 분기를 구현한다
- LangSmith를 활용하여 LangGraph 워크플로우를 추적하고 디버깅한다
- 체크포인터와 Store API를 구분하여 단기·장기 메모리 전략을 설계한다

## 선수 지식

- 5장에서 구현한 LangChain 에이전트 개념
- Python 기본 문법 및 TypedDict
- OpenAI API 사용 경험

---

## 6.1 LangGraph 소개: 그래프 기반 워크플로우의 필요성

- 5장의 ReAct 에이전트는 단순한 도구 호출에는 적합하나 복잡한 비즈니스 로직에 한계가 있음
  - 조건 분기, 반복, 병렬 실행이 필요한 경우
    - LLM의 판단에만 의존하면 예측 불가능한 동작 발생 가능
- LangGraph는 노드(node)와 엣지(edge)로 워크플로우를 **명시적으로** 정의
  - 개발자가 제어 흐름을 직접 설계
    - 결과: 디버깅이 쉽고 동작을 예측 가능

**표 6.1** ReAct 에이전트와 LangGraph 비교

| 특성 | ReAct 에이전트 | LangGraph |
|-----|--------------|-----------|
| 제어 흐름 | LLM이 결정 | 개발자가 명시적 정의 |
| 조건 분기 | 프롬프트에 의존 | 조건부 엣지로 정확히 제어 |
| 상태 관리 | 메시지 히스토리 | 타입 안전한 State 객체 |
| 디버깅 | 로그 분석 필요 | 그래프 시각화 가능 |

- LangGraph는 LangChain 위에 구축
- 순환 그래프(cyclic graph, 노드 간 순환 연결이 허용되는 그래프) 지원
  - 에이전트가 반복적으로 작업을 수행하고, 결과를 검증하고, 필요시 재시도하는 패턴을 자연스럽게 표현 가능

---

## 6.2 상태(State) 모델링

- LangGraph의 핵심은 **State 객체**
  - TypedDict를 사용하여 워크플로우 전체에서 공유되는 상태를 정의
  - 각 노드가 상태를 읽고 업데이트하는 구조

```python
class WorkflowState(TypedDict):
    draft: str
    feedback: Annotated[list[str], add]
    revision_count: int
```

_전체 코드는 practice/chapter6/code/6-6-langgraph-workflow.py 참고_

- 상태 정의의 핵심 개념: **리듀서(reducer)**
  - 기본 동작: 노드가 반환하는 값은 기존 상태를 **덮어씀**
  - `Annotated`와 `operator.add`를 함께 사용하면 리스트에 값을 **누적**할 수 있음
    - → 예시: 피드백 히스토리를 유지하는 데 유용
- 상태는 워크플로우의 "메모리" 역할
  - 노드가 실행될 때마다 상태가 업데이트되고 다음 노드로 전달
  - 타입 힌트를 통해 각 필드가 올바른 타입인지 검증 가능

---

## 6.3 조건 분기: 검증 결과에 따른 경로 선택

- 조건부 엣지(conditional edge)를 사용하면 상태에 따라 다른 노드로 분기 가능
  - 분기 조건을 결정하는 함수를 정의
  - `add_conditional_edges`로 분기 함수를 그래프에 등록

- 분기 함수 정의 방법
  - 현재 상태를 분석하고 다음 노드의 이름을 **문자열**로 반환
  - 반환값과 실제 노드를 매핑하는 딕셔너리를 함께 전달

```python
def should_continue(state: WorkflowState) -> str:
    if state["revision_count"] >= 3:
        return "end"
    return "revise" if state["feedback"] else "end"
```

_전체 코드는 practice/chapter6/code/6-6-langgraph-workflow.py 참고_

```python
builder.add_conditional_edges(
    "validate",
    should_continue,
    {"end": END, "revise": "revise"}
)
```

- 이 패턴의 효과
  - 검증 통과 시 → 종료(END)
  - 검증 실패 시 → 수정 노드(`revise`)로 이동
  - 분기 로직이 코드로 명확하게 표현됨

---

## 6.4 반복 루프: 재시도와 검증 루프

- LangGraph는 순환 그래프를 지원하므로 "생성 → 검증 → 실패 시 수정" 사이클을 반복 가능
- ⚠ 무한 루프 방지를 위해 최대 반복 횟수 설정이 필수

- 실습에서 구현한 워크플로우 흐름
  1. `generate_draft`: 초안 생성
  2. `validate`: 초안 검증, 피드백 생성
  3. 조건 분기
     - 통과 시 → 종료
     - 실패 시 → `revise`로 이동
  4. `revise`: 피드백을 반영하여 수정
  5. 다시 `validate`로 이동 (최대 3회 반복)

- 이 패턴의 핵심 구조
  - `revise` 노드가 `validate` 노드로 다시 연결됨 (순환 구조)
  - 조건 분기에서 종료 조건을 명확히 정의하여 무한 루프 방지

---

## 6.5 실패 복구: 에러 핸들링과 폴백

- 노드 실행 중 발생 가능한 에러 유형
  - API 호출 실패
  - 타임아웃
  - 잘못된 응답

- 에러 처리 구현 방법
  - 노드 내부에서 `try-except`로 처리
  - 에러 발생 시 → 상태에 에러 정보를 기록
  - 조건 분기에서 에러 상태를 확인 → 적절한 경로로 이동

- 폴백(fallback, 대체 수단) 전략 선택지
  - 더 간단한 모델 사용
  - 캐시된 응답 반환
  - 사람에게 에스컬레이션(escalation, 상위 담당자에게 전달)

- LangGraph의 추가 기능: 노드 수준에서 재시도 정책 설정 가능
  - 지수 백오프(exponential backoff, 재시도 간격을 지수적으로 늘리는 방식) 적용
    - 결과: 일시적인 오류에서 자동으로 복구 가능

---

## 6.6 LangGraph 1.0: 첫 안정 릴리스

- LangGraph 1.0은 2025년 10월 22일 일반 공개(GA, General Availability)
  - LangChain 1.0과 동시에 발표
  - Uber, LinkedIn, Klarna 등 기업에서 1년 이상 프로덕션 운영한 결과를 바탕으로 안정화

### 6.6.1 API 안정성 보장

- v1.0의 핵심 가치: 새 기능 추가가 아니라 **안정성 확정**
  - v0.6.6 → v1.0 업그레이드 시 브레이킹 체인지(breaking change, 하위 호환성을 깨는 변경) 전혀 없음
  - **v2.0까지 하위 호환성을 공식 보장**
- 유일한 변경점
  - `langgraph.prebuilt.create_react_agent` → `langchain.agents.create_agent`로 이전
  - 기존 함수의 제거는 v2.0에서 예정 (즉시 삭제되지 않음)

**표 6.2** LangGraph pre-1.0 vs 1.0 주요 변경

| 항목 | pre-1.0 (0.x) | v1.0 |
|------|---------------|------|
| API 안정성 | 실험적, 수시 변경 | v2.0까지 안정 보장 |
| 내구 실행(Durable Execution) | 존재했으나 비공식 | 공식 지원, 프로덕션 검증 |
| 스트리밍 | 기본 지원 | LLM 토큰·도구 호출·상태 전이 전체 스트리밍 |
| Human-in-the-loop | 패턴으로 존재 | 1등급 API(interrupt → resume) |
| Functional API | 미존재 | `@task`, `@entrypoint` 데코레이터 추가 |
| 메모리 | 체크포인터 중심 | 단기(체크포인터) + 장기(Store API) 이원 체계 |

### 6.6.2 Functional API

- v1.0에서 새로 추가된 Functional API
  - `@task`와 `@entrypoint` 데코레이터로 워크플로우를 정의하는 방식
  - 기존 StateGraph 방식과의 차이점
    - Python 함수를 직접 조합
    - 단순한 파이프라인에서 그래프 정의 없이도 내구 실행(durable execution, 중단 후 재시작이 가능한 실행)의 이점을 누릴 수 있음
- StateGraph vs Functional API 비교
  - StateGraph: 명시적 제어 흐름이 필요한 경우에 적합
  - Functional API: 익숙한 함수 호출 패턴으로 빠르게 프로토타이핑할 때 유리

---

## 6.7 LangSmith 통합: 워크플로우 추적과 평가

- LangGraph 워크플로우가 복잡해질수록 "어떤 노드에서 무엇이 일어났는가" 추적이 중요
- LangSmith는 LangGraph와 네이티브 통합
  - 환경 변수 설정만으로 트레이싱(tracing, 실행 흐름 기록) 활성화

```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "ls__..."
os.environ["LANGSMITH_PROJECT"] = "my-langgraph-project"
```

### 6.7.1 중첩 스팬(Nested Span) 트레이싱

- LangSmith의 트레이싱 모델은 **트리 구조**를 따름
  - **트레이스(Trace)**: 에이전트의 단일 실행 단위
    - 그 안에 여러 **런(Run)**이 부모-자식 관계로 중첩
      - 각 런에서 확인 가능한 정보
        - LLM 호출, 도구 호출, 노드 전환 등 각 단계의 입력
        - 출력
        - 소요 시간
  - 10개 이상의 도구 호출이 포함된 멀티스텝 에이전트도 즉시 재생(replay)하여 병목 지점 식별 가능
- 커스텀 함수에 `@traceable` 데코레이터 적용 시
  - 모델 호출 옆에 커스텀 로직도 트레이스에 포함
  - 별도 로깅 코드 없이도 노드별 상태 정보를 자동으로 수집 가능

### 6.7.2 평가 워크플로우

- LangSmith는 오프라인·온라인 양면의 평가 체계를 제공
- 오프라인 평가 진행 순서
  1. 데이터셋 구성
     - 수동 큐레이션
     - 프로덕션 트레이스
     - 합성 데이터(synthetic data, AI가 생성한 테스트 데이터)
  2. 에이전트를 전체 데이터셋에 대해 실행
  3. 평가자(evaluator)로 점수를 매김
     - 평가자 유형 혼합 사용 가능
       - LLM-as-judge (LLM이 직접 답변의 품질을 평가)
       - 코드 기반 휴리스틱(heuristic, 경험적 규칙)
       - 커스텀 로직
- 버전 고정 데이터셋 활용
  - 프롬프트나 모델 변경 시 성능 회귀(regression, 이전보다 성능이 나빠지는 현상)를 감지 가능

---

## 6.8 LangGraph + 장기 메모리

- 6.2절의 상태(State)는 하나의 워크플로우 실행 내에서만 유효
- 실제 에이전트 애플리케이션은 대화 간에도 정보를 유지해야 함
- LangGraph는 이를 위해 두 가지 메모리 계층을 제공
  - **체크포인터(Checkpointer)**: 단기 메모리
  - **스토어(Store)**: 장기 메모리

### 6.8.1 체크포인터 vs 스토어

**표 6.3** 메모리 계층 비교

| 구분 | 체크포인터(Checkpointer) | 스토어(Store) |
|------|--------------------------|---------------|
| 범위 | 단일 스레드(대화) 내 | 스레드 간(cross-thread) |
| 용도 | 멀티턴 대화 컨텍스트, 중단 복구 | 사용자 선호, 학습된 지식, 과거 결정 |
| 데이터 | 그래프 실행 상태의 스냅샷 | JSON 문서(key-value) |
| 수명 | 스레드 종료 시 의미 감소 | 애플리케이션 수명과 동일 |
| 검색 | thread_id + checkpoint_id | namespace + key, 또는 의미 검색 |

- 체크포인터의 역할
  - "이 대화에서 어디까지 진행했는가"를 다룸
- 스토어의 역할
  - "이 사용자에 대해 무엇을 알고 있는가"를 다룸
- ⚠ 체크포인터만으로는 대화를 넘어선 학습이 불가능
  - 장기 메모리가 필요한 에이전트는 두 계층을 **함께** 사용해야 함

### 6.8.2 Store API

- LangGraph의 `BaseStore` 인터페이스는 세 가지 핵심 메서드를 제공

```python
store.put(("users", "user_123"), "pref", {"language": "ko"})
item = store.get(("users", "user_123"), "pref")
results = store.search(("users", "user_123"), query="선호 언어")
```

- 각 메서드의 역할
  - `put`: 네임스페이스에 JSON 문서를 저장
  - `get`: 키 기반으로 조회
  - `search`: 필터 또는 의미 검색(semantic search, 의미적 유사성으로 검색) 수행
- 네임스페이스는 계층적으로 구성 가능
  - → 예시: `("users", "user_123", "preferences")`

### 6.8.3 외부 저장소 통합

- ⚠ 프로덕션 환경에서는 `InMemoryStore` 대신 영속적인 외부 저장소 사용 필요
- 대표적인 선택지

- **MongoDB 통합**
  - `langgraph-store-mongodb` 패키지가 `MongoDBStore` 제공
  - MongoDB의 네이티브 JSON 문서 구조와 LangGraph의 메모리 형식이 직접 매핑
  - Atlas Vector Search로 의미 기반 메모리 검색 지원
  - TTL(Time To Live) 인덱스로 오래된 메모리를 자동 정리 가능

- **Redis 통합**
  - `langgraph-checkpoint-redis` 패키지 제공 항목
    - 체크포인터: `RedisSaver`, `ShallowRedisSaver`
    - 스토어: `RedisStore`
  - Redis 8.0 이상에서는 RedisJSON과 RediSearch가 기본 내장
    - 벡터 검색과 메타데이터 필터링을 별도 설정 없이 사용 가능

---

## 6.9 실습: 초안 생성 → 검증 → 수정 워크플로우

### 실습 목표

- LangGraph로 순환 워크플로우를 구현한다
- OpenAI API를 사용하여 초안을 생성하고, 검증하고, 수정한다
- 최대 3회 수정 후 최종 결과를 파일로 저장한다

### 실습 환경 설정

```bash
cd practice/chapter6
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
cp code/.env.example code/.env  # OPENAI_API_KEY 설정
python3 code/6-6-langgraph-workflow.py
```

### 워크플로우 구성

```
[START] → [generate_draft] → [validate] → {조건 분기}
                                              ↓ (통과)
                                           [END]
                                              ↓ (실패 & 수정 횟수 < 3)
                                           [revise] → [validate] → ...
```

### 실행 결과

실제 실행 시 생성된 초안:

```
인공지능(AI)은 소프트웨어 개발의 패러다임을 변화시키고 있습니다.
최근 연구에 따르면, AI 도구를 활용한 개발 팀은 전통적인 방법에 비해
코드 작성 속도가 최대 40% 향상될 수 있습니다...
```

**표 6.4** 워크플로우 실행 결과

| 항목 | 값 |
|-----|-----|
| 주제 | 인공지능이 소프트웨어 개발에 미치는 영향 |
| 수정 횟수 | 0 |
| 검증 통과 | true |
| 실행 시간 | 약 8초 |

### 실습 산출물

- `practice/chapter6/data/output/ch06_workflow_log.txt`: 워크플로우 실행 로그
- `practice/chapter6/data/output/ch06_draft_v1.txt`: 초기 초안
- `practice/chapter6/data/output/ch06_draft_final.txt`: 최종 결과물
- `practice/chapter6/data/output/ch06_result.json`: 실행 결과 요약

---

## 6.10 실패 사례와 디버깅

### 무한 루프 발생

- 원인
  - 검증 함수가 항상 실패를 반환하는 경우
  - 종료 조건이 누락된 경우
- ⚠ 반드시 최대 반복 횟수를 설정하고 조건 분기에서 이를 확인해야 함

```python
if state["revision_count"] >= MAX_REVISIONS:
    return "end"  # 강제 종료
```

### 상태 누락 오류

- 원인: 노드가 필수 상태 필드를 업데이트하지 않으면 다음 노드에서 오류 발생
- 해결책: TypedDict를 사용하면 타입 검사기가 이러한 문제를 미리 발견 가능

### 디버깅 팁

- 각 노드에서 상태를 로깅한다
- 조건 분기 함수에서 결정 이유를 기록한다
- 그래프를 시각화하여 흐름을 확인한다

---

## 핵심 정리

- LangGraph는 노드와 엣지로 워크플로우를 명시적으로 정의한다
- LangGraph 1.0(2025.10)은 v2.0까지 API 안정성을 보장하는 첫 프로덕션 릴리스다
- TypedDict로 상태를 정의하고, Annotated로 리듀서 동작을 지정한다
- 조건부 엣지로 상태에 따른 분기를 구현한다
- 순환 그래프로 재시도/검증 루프를 만들되, 최대 반복 횟수로 무한 루프를 방지한다
- LangSmith 연동으로 중첩 스팬 트레이싱, 평가 워크플로우를 수행한다
- 체크포인터(단기)와 Store API(장기)의 이원 메모리 체계로 대화를 넘어선 학습이 가능하다

---

## 다음 장 예고

- 7장에서는 멀티에이전트 시스템을 다룸
  - 여러 에이전트가 협력하여 복잡한 작업을 수행하는 패턴
  - 에이전트 프레임워크 비교: CrewAI, AutoGen, OpenAI Agents SDK
  - A2A 프로토콜 실전 적용
  - 로우코드 에이전트 빌더

---

## 참고문헌

LangChain. (2025). *LangGraph 1.0 is now generally available*. https://changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available

LangChain. (2025). *LangChain and LangGraph Agent Frameworks Reach v1.0 Milestones*. https://blog.langchain.com/langchain-langgraph-1dot0/

LangChain. (2025). *What's new in LangGraph v1*. https://docs.langchain.com/oss/python/releases/langgraph-v1

LangChain. (2025). *Graph API - LangGraph Documentation*. https://docs.langchain.com/oss/python/langgraph/graph-api

LangChain. (2025). *Memory overview - LangGraph Documentation*. https://docs.langchain.com/oss/python/langgraph/memory

LangChain. (2025). *Trace LangGraph applications with LangSmith*. https://docs.langchain.com/langsmith/trace-with-langgraph

LangChain. (2025). *LangSmith Evaluation*. https://docs.langchain.com/langsmith/evaluation

LangChain. (2025). *Semantic Search for LangGraph Memory*. https://blog.langchain.com/semantic-search-for-langgraph-memory/

MongoDB. (2025). *Powering Long-Term Memory For Agents With LangGraph And MongoDB*. https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph

Redis. (2025). *LangGraph & Redis: Build smarter AI agents with memory persistence*. https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/
