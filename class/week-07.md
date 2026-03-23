# Week 7. 멀티에이전트 시스템: 프레임워크 비교와 A2A 실전

> 원본: docs/ch7.md

## 학습 목표

- 멀티에이전트 시스템이 필요한 상황을 식별한다
- 주요 프레임워크(LangGraph, OpenAI Agents SDK, Google ADK, CrewAI, AutoGen)의 설계 철학과 차이를 비교한다
- A2A 프로토콜을 활용하여 이종 프레임워크 에이전트를 연동하는 방법을 설명한다
- 로우코드/노코드 도구와 코드 기반 프레임워크의 선택 기준을 판단한다

## 선수 지식

- 6장에서 구현한 LangGraph 워크플로우 개념
- Python TypedDict와 상태 관리
- OpenAI API 사용 경험

---

## 7.1 멀티에이전트 시스템이란?

- 6장의 LangGraph 워크플로우는 단일 LLM이 여러 단계를 수행하는 구조였음
- 작업이 복잡해질수록 하나의 에이전트가 모든 역할을 수행하는 것은 비효율적
- 멀티에이전트 시스템: 여러 AI 에이전트가 각자의 전문 역할을 맡아 협력하는 구조

### 단일 에이전트의 한계

- 첫째: 컨텍스트 윈도우(context window, LLM이 한 번에 처리할 수 있는 텍스트 최대 분량)에 모든 정보를 담기 어려움
- 둘째: 한 번의 프롬프트로 여러 전문 역할을 수행하면 품질이 저하될 수 있음
- 셋째: 복잡한 작업에서 LLM이 단계를 건너뛰거나 환각(hallucination, AI가 사실이 아닌 내용을 그럴듯하게 생성하는 현상)을 일으킬 가능성이 높아짐

### 멀티에이전트가 한계를 극복하는 방식

- 연구자 에이전트: 정보를 수집하는 역할 담당
- 작성자 에이전트: 문서를 작성하는 역할 담당
- 검토자 에이전트: 품질을 검증하는 역할 담당
- 각 에이전트가 특화된 프롬프트와 역할을 가지므로 전문성이 높아짐
- 상호 검증을 통해 환각을 줄일 수 있음

**표 7.1** 단일 에이전트 vs 멀티에이전트

| 특성 | 단일 에이전트 | 멀티에이전트 |
|-----|-------------|-------------|
| 복잡성 | 낮음 | 높음 |
| 전문성 | 일반적 | 역할별 전문화 |
| 컨텍스트 관리 | 단순 | 분산/공유 |
| 비용 | 낮음 | 높음 (API 호출 증가) |
| 적합한 작업 | 단순 Q&A, 도구 호출 | 복잡한 워크플로우, 다단계 분석 |

---

## 7.2 멀티에이전트 아키텍처 패턴

- 멀티에이전트 시스템은 에이전트 간 상호작용 방식에 따라 여러 패턴으로 분류됨

### 계층형 (Hierarchical)

- 관리자 에이전트(오케스트레이터)가 작업을 분배하고 하위 에이전트들이 실행함
- 복잡한 작업을 분해하여 전문 에이전트에게 위임하는 방식
- 관리자가 결과를 수집하고 최종 출력을 구성
- 적합한 사례:
  - 명확한 위계가 필요한 프로젝트 관리
  - 고객 서비스 에스컬레이션(escalation, 문제를 단계적으로 상위 처리 주체에게 넘기는 것)

### 협력형 (Collaborative)

- 에이전트들이 동등한 위치에서 협력
- 각 에이전트가 자신의 전문 분야를 담당하고 결과물을 다음 에이전트에게 전달
- → 예시: "연구자 → 작성자 → 검토자" 파이프라인 (본 장 실습에서 구현)

### 경쟁형 (Adversarial)

- 에이전트들이 서로의 결과를 비판하고 검증하는 구조
- 한 에이전트가 주장을 하면 다른 에이전트가 반박하는 형태
- 적합한 사례:
  - 법률 문서 검토
  - 논쟁적 주제 분석 — 다양한 관점을 확보하는 데 유용

### 순차형 (Sequential)

- 에이전트들이 파이프라인(pipeline, 작업이 한 단계에서 다음 단계로 순서대로 흐르는 구조) 형태로 순서대로 작업을 수행
- 앞 에이전트의 출력이 다음 에이전트의 입력이 됨
- 적합한 사례:
  - 문서 생성
  - 번역
  - 요약 — 단계가 명확한 작업에 적합

---

## 7.3 프레임워크 비교: 2026년 기준

- 멀티에이전트 시스템 구현 프레임워크는 2025년을 기점으로 급격히 다양화됨
- 각 프레임워크의 설계 철학과 차이를 이해해야 프로젝트에 적합한 선택이 가능

### LangGraph

- 6장에서 학습한 것처럼 노드(node, 에이전트나 처리 단계)와 엣지(edge, 노드 간 연결·흐름)로 에이전트 간 흐름을 명시적으로 정의
- 조건 분기와 순환 구조를 자유롭게 표현할 수 있어 복잡한 워크플로우에 적합
- 1.0 릴리스(2025년 10월)로 API 안정성이 보장됨
- Store API를 통한 장기 메모리도 지원

### OpenAI Agents SDK

- 5장에서 소개한 OpenAI Agents SDK는 핸드오프(handoff, 에이전트 간 제어권·작업 이양) 메커니즘으로 멀티에이전트를 구현
- 에이전트 간 위임을 `transfer_to_<agent_name>` 도구로 처리
- `on_handoff` 콜백(callback, 특정 이벤트 발생 시 자동 호출되는 함수)으로 위임 시점의 컨텍스트를 가공 가능
- 코드량이 적고 직관적
- ⚠ LangGraph 수준의 세밀한 상태 제어는 어려움

### Google ADK (Agent Development Kit)

- Google이 2025년 4월 Cloud Next에서 공개한 프레임워크
- 세 가지 워크플로우 에이전트를 제공:
  - `SequentialAgent`: 하위 에이전트를 순차 실행
  - `ParallelAgent`: 하위 에이전트를 동시(병렬) 실행
  - `LoopAgent`: 조건이 충족될 때까지 반복 실행
- `sub_agents` 매개변수로 트리(tree, 계층 구조) 형태의 계층적 멀티에이전트 구성 가능
- Gemini 모델에 최적화되어 있으나 다른 모델도 지원

### CrewAI

- 역할 기반(role-based) 에이전트 설계를 강조하는 프레임워크
- 에이전트에게 명확한 역할(role), 목표(goal), 배경(backstory)을 부여
- 태스크(task) 단위로 작업을 정의
- YAML 기반 설정을 지원하여 코드 없이 에이전트를 정의 가능
- 빠른 프로토타이핑에 적합
- 학습 곡선이 낮음

### AutoGen v0.4 / AG2

- Microsoft Research가 개발한 프레임워크
- v0.4(2025년 1월)에서 비동기 이벤트 기반 액터 모델(actor model, 각 에이전트가 독립적인 실행 단위로 메시지를 주고받는 구조)로 완전 재설계됨
- 3계층 API 구조:
  - AgentChat: 대화형 에이전트 인터페이스
  - Core: 핵심 런타임 및 메시지 처리
  - Extensions: 외부 통합 및 확장
- Magentic-One: 5개 전문 에이전트가 협업하는 범용 멀티에이전트 시스템
  - Orchestrator: 전체 조율 및 계획 수립
  - WebSurfer: 웹 검색 및 탐색
  - FileSurfer: 파일 시스템 탐색
  - Coder: 코드 작성 및 실행
  - ComputerTerminal: 터미널 명령 실행
  - Task Ledger/Progress Ledger로 협업 상태를 추적
- ⚠ AutoGen 0.2 아키텍처를 유지하는 AG2 포크(fork, 독립적으로 분기된 별도 프로젝트)가 별도로 진행 중임

**표 7.2** 멀티에이전트 프레임워크 비교 (2026년 기준)

| 기준 | LangGraph | Agents SDK | Google ADK | CrewAI | AutoGen v0.4 |
|-----|-----------|------------|------------|--------|-------------|
| 설계 철학 | 그래프 워크플로우 | 핸드오프 기반 | 계층적 에이전트 트리 | 역할 기반 팀 | 이벤트 기반 액터 |
| 멀티에이전트 방식 | 노드·엣지 | transfer_to | sub_agents | Crew/Task | GroupChat/Teams |
| 학습 곡선 | 높음 | 낮음 | 중간 | 낮음 | 높음 |
| 상태 제어 | 매우 세밀 | 제한적 | 중간 | 추상화 | 중간 |
| 모델 종속성 | 없음 | OpenAI 우선 | Gemini 우선 | 없음 | 없음 |
| 적합한 사용 | 복잡한 워크플로우 | 빠른 위임 체인 | Google 생태계 | 빠른 프로토타입 | 대화형 협업 |

---

## 7.4 Human-in-the-loop 설계

- Human-in-the-loop(HITL): 자동화와 인간 판단을 결합하는 설계 패턴
- 고위험 작업에서는 에이전트의 결정을 사람이 검토하고 승인해야 함

### 승인이 필요한 작업

- 모든 작업에 인간 승인이 필요한 것은 아님 — 다음 조건에 해당할 때 승인 단계를 추가:
  - 외부 시스템에 영향을 미치는 작업
    - → 예시: 이메일 전송, 결제 처리
  - 되돌리기 어려운 작업
    - → 예시: 데이터 삭제, 계정 변경
  - 민감한 정보를 다루는 작업
    - → 예시: 개인정보, 비밀
  - 비용이 높은 작업
    - → 예시: 대량 API 호출, 서버 프로비저닝(provisioning, 서버 자원을 할당·설정하는 과정)

### 승인 요청 UX 설계

- 승인 요청은 명확하고 간결해야 함
- 에이전트가 수행하려는 작업, 예상 결과, 위험 요소를 제시
- 승인 / 거부 / 수정 옵션을 제공
- 타임아웃(timeout, 일정 시간이 지나면 자동으로 처리하는 시간 제한)을 설정하여 무한 대기 방지
  - 타임아웃 시 안전한 기본값(예: 거부)으로 폴백(fallback, 기본 동작으로 되돌아가는 것)

### 프레임워크별 지원 방식

- AutoGen:
  - `human_input_mode` 파라미터로 인간 개입 시점을 제어
  - `ALWAYS`로 설정: 매 단계마다 승인을 요청
  - `TERMINATE`로 설정: 종료 전에만 확인
- LangGraph:
  - `interrupt_before` 파라미터로 특정 노드 실행 전 중단
  - 중단된 지점에서 인간 입력을 받아 실행 재개 가능

---

## 7.5 A2A 실전: 이종 프레임워크 에이전트 연동

- 4장에서 A2A(Agent-to-Agent) 프로토콜의 개념을 소개함
- 이 절에서는 실제로 서로 다른 프레임워크로 만든 에이전트를 A2A로 연동하는 방법을 다룸

### 7.5.1 에이전트 카드 (Agent Card)

- A2A에서 에이전트의 신원과 능력을 선언하는 JSON 문서
- `/.well-known/agent.json` 경로에 게시
  - 클라이언트 에이전트가 이를 발견하고 어떤 작업을 위임할 수 있는지 판단
- 에이전트 카드에 명시하는 항목:
  - 이름 (name)
  - 버전 (version)
  - URL
  - 지원 능력 (capabilities): streaming 여부 등
  - 기술 목록 (skills): 에이전트가 수행할 수 있는 구체적인 작업 단위

```json
{
  "name": "weather-agent",
  "version": "1.0",
  "url": "https://weather.example.com",
  "capabilities": {"streaming": true},
  "skills": [{"id": "forecast", "name": "날씨 예보"}]
}
```

### 7.5.2 태스크 위임 흐름

- 클라이언트 에이전트가 리모트 에이전트에 작업을 위임하는 흐름:
  1. 클라이언트가 `SendMessage`를 호출
  2. 리모트가 Task 객체를 반환
  3. 클라이언트가 태스크 상태를 추적 — 세 가지 추적 방식:
     - 폴링(polling, 주기적으로 상태를 확인하는 방식)
     - 스트리밍(streaming, 실시간으로 상태 변화를 수신하는 방식)
     - 푸시(push, 서버가 완료 시 클라이언트에게 알림을 보내는 방식)
- 태스크 상태 전이:
  - `submitted` → `working` → `completed` / `failed` / `input_required`
- `input_required` 상태가 되면:
  - 추가 정보를 보내 대화를 계속할 수 있음

### 7.5.3 이종 프레임워크 연동

- A2A의 핵심 가치: 프레임워크에 구속되지 않는 에이전트 간 통신
  - → 예시: Google ADK로 만든 오케스트레이터가 LangGraph 에이전트에게 분석 작업을, CrewAI 에이전트에게 보고서 작성을 위임 가능
  - 각 에이전트는 내부 구현과 무관하게 A2A 표준 인터페이스만 준수하면 됨
    - 표준 인터페이스: 에이전트 카드 + 태스크 프로토콜
- MCP vs A2A 역할 구분:
  - MCP(Model Context Protocol): "에이전트와 도구(tool)"의 표준
  - A2A: "에이전트와 에이전트" 간 통신의 표준
  - 두 프로토콜은 경쟁 관계가 아닌 상호 보완 관계
- 실무 3층 구조:
  - ADK (에이전트 개발)
  - MCP (도구 연동)
  - A2A (에이전트 간 통신)

---

## 7.6 로우코드/노코드 대안: 언제 시각적 도구가 적합한가

- 코드 기반 프레임워크가 유일한 선택지는 아님
- 로우코드/노코드 도구:
  - 시각적 인터페이스로 에이전트 워크플로우를 구성
  - 특정 상황에서 코드 기반보다 효율적

### 7.6.1 주요 도구

#### n8n

- GitHub 스타 17만 이상의 범용 워크플로우 자동화 플랫폼
- 400개 이상의 통합 노드 제공
- 지원 기능:
  - MCP 지원
  - 네이티브 Python 실행
  - Redis/Vector 메모리 노드
- 강점: 기존 SaaS 서비스를 연결하는 "신경계" 역할

#### Dify

- GitHub 스타 12만 이상의 AI 네이티브 앱 개발 플랫폼
- 지원 기능:
  - LLM 오케스트레이션(orchestration, 여러 LLM 호출을 조율하는 것)
  - 비주얼 프롬프트 스튜디오
  - RAG(Retrieval-Augmented Generation, 외부 지식 검색을 결합한 생성) 내장
  - 원클릭 배포
- 강점: LLM 추론을 중심으로 하는 "두뇌" 역할에 특화

#### n8n + Dify 통합 패턴

- 두 도구는 경쟁 관계가 아니라 보완 관계
- 실무 통합 패턴:
  1. n8n으로 외부 시스템 연결
  2. Dify로 AI 추론 파이프라인 구축
  3. API/웹훅(webhook, HTTP를 통해 이벤트를 실시간으로 전달하는 방식)으로 두 도구를 통합

### 7.6.2 선택 기준

**표 7.3** 코드 기반 vs 로우코드/노코드

| 기준 | 코드 기반 프레임워크 | 로우코드/노코드 |
|------|-------------------|---------------|
| 적합한 팀 | 개발 역량 있는 팀 | 다양한 기술 수준의 팀 |
| 프로토타이핑 속도 | 중간~느림 | 매우 빠름 |
| 제어 수준 | 세밀 | 제한적 |
| 프로덕션 적합성 | 높음 | 중간 |
| 디버깅 | 코드 수준 추적 | 시각적 플로우 추적 |
| 규정 준수/감사 | 코드 리뷰 가능 | 플랫폼 의존적 |

- 로우코드/노코드가 적합한 경우:
  - 빠른 프로토타이핑이 필요한 경우
  - 통합 중심 워크플로우인 경우
  - 비개발자 참여가 중요한 경우
- 코드 기반 프레임워크가 적합한 경우:
  - 프로덕션 안정성이 우선인 경우
  - 세밀한 상태 제어가 필요한 경우
  - 규정 준수(compliance)와 감사(audit)가 요구되는 경우

---

## 7.7 실습: 단일 에이전트 vs 멀티에이전트 비교

### 실습 목표

- 동일한 작업(기술 문서 작성)을 단일 에이전트로 구현
- 같은 작업을 멀티에이전트(연구자, 작성자, 검토자)로 구현
- 두 접근법의 결과물, 실행 시간, API 호출 수를 비교

### 실습 환경 설정

```bash
cd practice/chapter7
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
cp code/.env.example code/.env  # OPENAI_API_KEY 설정
```

### 단일 에이전트 구현

- 하나의 프롬프트로 조사, 작성, 검토를 모두 수행
- 전체 코드: `practice/chapter7/code/7-5-single-agent.py` 참고

```python
prompt = f"""당신은 기술 문서 작성 전문가입니다.
주제: {topic}
문서 요구사항: 개념 설명, 코드 예시, 모범 사례
"""
response = llm.invoke(prompt)
```

### 멀티에이전트 구현

- 세 개의 전문 에이전트가 순차적으로 협력:
  - 연구자(researcher): 정보 수집
  - 작성자(writer): 문서 작성
  - 검토자(reviewer): 품질 검증
- LangGraph의 StateGraph를 사용하여 워크플로우를 정의
- 전체 코드: `practice/chapter7/code/7-5-multi-agent.py` 참고

```python
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)
```

### 실행 및 비교

```bash
python3 code/7-5-single-agent.py
python3 code/7-5-multi-agent.py
python3 code/7-5-compare.py
```

### 실행 결과

**표 7.4** 단일 에이전트 vs 멀티에이전트 비교 결과

| 항목 | 단일 에이전트 | 멀티에이전트 |
|-----|-------------|-------------|
| API 호출 | 1회 | 3회 |
| 소요 시간 | 14.76초 | 33.31초 |
| 문서 길이 | 2,083자 | 2,146자 |
| 수정 횟수 | - | 1회 |

- 멀티에이전트는 API를 3배 호출하고 시간이 2.26배 소요됨
- 그러나:
  - 연구, 작성, 검토 단계가 분리되어 각 역할에 특화된 프롬프트 사용 가능
  - 검토자가 피드백을 제공하면 작성자가 수정하는 반복 구조도 구현 가능

### 실습 산출물

- `practice/chapter7/data/output/ch07_single_result.json`: 단일 에이전트 결과
- `practice/chapter7/data/output/ch07_multi_result.json`: 멀티에이전트 결과
- `practice/chapter7/data/output/ch07_comparison.json`: 비교 분석
- `practice/chapter7/data/output/ch07_document_single.txt`: 단일 에이전트 생성 문서
- `practice/chapter7/data/output/ch07_document_multi.txt`: 멀티에이전트 생성 문서

---

## 7.8 선택 가이드: 언제 무엇을 사용할 것인가

### 단일 에이전트를 선택해야 하는 경우

- 작업이 단순하고 범위가 명확한 경우
- 빠른 응답이 필요한 경우
- 비용을 최소화해야 하는 경우
- → 예시: 문서 요약, 이메일 응답, 특정 정보 검색

### 멀티에이전트가 효과적인 경우

- 복잡한 다단계 작업인 경우
- 환각 감소를 위해 상호 검증이 필요한 경우
- 긴 컨텍스트를 분산 처리해야 하는 경우
- 병렬 처리로 속도를 향상해야 하는 경우

### 프레임워크 선택 체크리스트

- 빠른 프로토타입이 필요한가? → CrewAI
- 대화형 협업이 핵심인가? → AutoGen
- 복잡한 조건 분기가 필요한가? → LangGraph
- Human-in-the-loop가 중요한가? → AutoGen 또는 LangGraph
- 기존 LangChain 코드가 있는가? → LangGraph

---

## 7.9 실패 사례와 교훈

### 에이전트 간 무한 루프

- ⚠ 두 에이전트가 서로에게 작업을 위임하며 무한히 반복하는 상황 발생 가능
- 원인:
  - 종료 조건이 명확하지 않은 경우
  - 역할 경계가 불분명한 경우
- 방지 방법:
  - 최대 반복 횟수(max iterations)를 설정
  - 각 에이전트의 역할과 종료 조건을 명확히 정의

### 과도한 API 비용

- ⚠ 멀티에이전트는 단일 에이전트 대비 API 호출이 증가함
  - 실습 결과에서도 3배의 API 호출이 발생
- 프로덕션 환경에서의 비용 절감 전략:
  - 캐싱(caching, 이전 결과를 저장해 재사용하는 방식) 활용
  - 더 저렴한 모델 사용 (비용 대비 성능 최적화)
  - 필수적인 경우에만 에이전트 투입

### 불명확한 역할 분담

- ⚠ 에이전트 간 역할이 중복되면:
  - 같은 작업을 반복 수행하는 문제 발생
  - 서로 충돌하는 결과를 생성하는 문제 발생
- 해결 방법:
  - 각 에이전트의 책임(responsibility)을 명확히 정의
  - 출력 형식을 표준화하여 다음 에이전트가 예측 가능하게 입력을 처리할 수 있도록 함

---

## 핵심 정리

- 멀티에이전트 시스템은 전문 역할을 분담하여 복잡한 작업을 수행함
- 아키텍처 패턴:
  - 계층형, 협력형, 경쟁형, 순차형 등 다양한 패턴이 존재
- 주요 프레임워크별 설계 철학:
  - LangGraph: 그래프 워크플로우
  - OpenAI Agents SDK: 핸드오프 기반
  - Google ADK: 계층 트리
  - CrewAI: 역할 기반
  - AutoGen: 이벤트 기반 액터
- A2A 프로토콜로 이종 프레임워크 에이전트를 연동할 수 있음
  - 핵심 구성 요소: 에이전트 카드 + 태스크 위임
- n8n, Dify 등 로우코드 도구는 빠른 프로토타이핑과 통합 중심 워크플로우에 적합함
- Human-in-the-loop로 고위험 작업에서 인간 승인을 받아 안전성을 확보함

---

## 다음 장 예고

- 8장: RAG의 기본과 에이전트 메모리 아키텍처
  - 검색 증강 생성(RAG, Retrieval-Augmented Generation)으로 외부 지식을 활용하는 방법
  - 에이전트 메모리 분류 체계:
    - Working Memory (작업 기억)
    - Episodic Memory (일화 기억)
    - Semantic Memory (의미 기억)
    - Procedural Memory (절차 기억)
  - RAG와 메모리의 상호보완 관계

---

## 참고문헌

LangChain. (2025). *LangGraph Documentation*. https://docs.langchain.com/oss/python/langgraph

OpenAI. (2025). *OpenAI Agents SDK - Handoffs*. https://openai.github.io/openai-agents-python/handoffs/

Google. (2025). *Agent Development Kit - Multi-Agent Systems*. https://google.github.io/adk-docs/agents/multi-agents/

CrewAI. (2025). *CrewAI Documentation*. https://docs.crewai.com/

Microsoft. (2025). *AutoGen Reimagined: Launching AutoGen 0.4*. https://devblogs.microsoft.com/autogen/autogen-reimagined-launching-autogen-0-4/

A2A Protocol. (2025). *Agent-to-Agent Protocol Specification*. https://a2a-protocol.org/latest/specification/

Google. (2025). *Intro to A2A: Purchasing Concierge Codelab*. https://codelabs.developers.google.com/intro-a2a-purchasing-concierge

n8n. (2025). *n8n - Workflow Automation*. https://github.com/n8n-io/n8n

Dify. (2025). *Dify - AI Application Development Platform*. https://github.com/langgenius/dify

ZenML. (2025). *Google ADK vs LangGraph*. https://www.zenml.io/blog/google-adk-vs-langgraph
