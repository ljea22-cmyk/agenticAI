# Week 10. GraphRAG/LightRAG/KAG — 관계 기반 추론으로 확장

> 원본: docs/ch9.md

## 학습 목표

- 벡터 RAG의 한계와 그래프 기반 접근의 필요성을 이해한다
- 지식 그래프의 기본 개념(엔티티, 관계, 트리플)을 학습한다
- GraphRAG와 LightRAG의 아키텍처와 차이점을 비교한다
- 동일 질의로 벡터 RAG와 그래프 RAG의 결과를 비교 분석한다
- 그래프 기반 RAG의 적합한 사용 사례를 식별한다

## 선수 지식

- 8장에서 구현한 벡터 RAG 개념
- 임베딩과 벡터 유사도 검색
- LangChain 기본 사용법

---

## 9.1 벡터 RAG의 한계

- 8장에서 구현한 벡터 RAG는 많은 상황에서 효과적
- 그러나 특정 유형의 질문에서는 한계를 노출함

### 단순 유사도 매칭의 한계

- 벡터 검색의 동작 원리
  - 쿼리와 문서 청크 간의 의미적 유사도를 계산
  - 특정 개념을 직접 묻는 질문에는 잘 작동함
    - → 예시: "asyncio.gather()의 사용법" 같은 구체적 질문
- ⚠ 전역적 질문(global question)에는 적합하지 않음
  - → 예시: "데이터에서 가장 중요한 5가지 테마는 무엇인가?"
  - 이유: 쿼리를 올바른 정보로 안내할 방향성이 없기 때문

### 다중 홉 질문의 어려움

- 다중 홉(multi-hop) 질문이란
  - "A가 B에 영향을 주고, B가 C에 영향을 준다면, A와 C의 관계는?" 유형의 질문
  - 여러 청크에 걸친 연쇄적 추론이 필요한 질문
- ⚠ 벡터 검색으로 답하기 어려운 이유
  - 각 청크가 독립적으로 검색됨
  - 따라서 청크 간 연결 고리가 없어 추론 성능이 떨어짐

### 관계 정보의 부재

- 벡터 임베딩의 특성
  - 텍스트의 의미(semantics)를 포착하는 데 효과적
  - 그러나 엔티티 간의 명시적 관계(explicit relation)는 표현하지 못함
- ⚠ 한계 상황 예시
  - → 예시: "코루틴과 태스크의 관계"를 묻는 질문
    - 벡터 RAG는 두 개념이 언급된 청크를 찾을 수는 있음
    - 그러나 그 관계를 직접적으로 추론하지는 못함

---

## 9.2 지식 그래프 기초

- 지식 그래프(Knowledge Graph)란
  - 엔티티(개체)와 그들 간의 관계를 그래프 구조로 표현한 것
  - 벡터 RAG의 한계를 극복하는 핵심 도구

### 엔티티와 관계

- 엔티티(Entity)
  - 문서에서 추출된 핵심 개념, 함수, 모듈 등
  - → 예시: "asyncio.create_task()", "코루틴", "이벤트 루프"
- 관계(Relation)
  - 두 엔티티 간의 연결을 설명하는 서술어
  - → 예시: "asyncio.create_task()"와 "코루틴" 사이에 "감싼다"라는 관계

### 트리플 구조

- 지식 그래프의 기본 단위: 트리플(Triple)
  - 구조: **주어 - 술어 - 목적어** 형태로 표현

```
(asyncio.create_task) --[감싼다]--> (코루틴)
(이벤트 루프) --[관리한다]--> (비동기 작업)
```

### LLM 기반 추출

- 과거 방식
  - 규칙 기반(rule-based) 또는 통계적 방법으로 엔티티와 관계를 추출
- 현재 방식 (LLM 활용)
  - 더 정확하고 맥락을 이해하는 추출이 가능
  - 프롬프트로 추출 형식을 지정
  - LLM이 JSON 형태로 결과를 반환

```python
result = extract_entities_and_relations(chunk, llm)
# {"entities": [...], "relations": [...]}
```

_전체 코드는 practice/chapter9/code/9-6-graph-rag.py 참고_

---

## 9.3 GraphRAG: Microsoft의 접근

- 개발 주체: Microsoft
- 개요
  - 대규모 텍스트 데이터셋에서 지식 그래프를 자동으로 구축하고 활용하는 시스템
  - 2024년 GitHub에 공개
  - 2025년까지 활발히 발전 중

### 아키텍처 개요

- 작동 방식: 두 단계(인덱싱 → 쿼리)
- 1단계: 인덱싱(Indexing)
  - 소스 문서로부터 엔티티 지식 그래프를 추출
  - 관련 엔티티 그룹(커뮤니티, community)을 탐지
  - 각 커뮤니티에 대한 요약(summary)을 사전(pre) 생성
- 2단계: 쿼리(Query)
  - 각 커뮤니티 요약을 사용하여 부분 응답 생성
  - 부분 응답들을 통합하여 최종 응답 완성

### 글로벌 검색 vs 로컬 검색

- GraphRAG가 제공하는 두 가지 검색 전략
- 글로벌 검색(Global Search)
  - 전체 데이터를 아우르는 질문에 적합
  - → 예시: "데이터셋의 주요 테마는?"
- 로컬 검색(Local Search)
  - 특정 엔티티나 관계에 대한 상세 질문에 사용
  - → 예시: 특정 함수의 동작 방식 등 세부 정보 조회

### 트레이드오프

- ⚠ GraphRAG의 주요 단점: 높은 인덱싱 비용
  - 원인
    - 모든 문서에서 엔티티와 관계를 추출하는 과정에 LLM 호출 필요
    - 커뮤니티를 탐지하고 요약을 생성하는 과정 포함
  - 규모에 따른 효과
    - 100만 토큰 규모의 데이터셋에서는 포괄성과 다양성이 크게 향상됨
  - 판단 기준
    - 비용과 시간 투자를 정당화할 수 있는지 사전 검토 필요

---

## 9.4 LightRAG: 경량화된 그래프 RAG

- 개발 주체: 홍콩대학교 데이터과학 연구팀 (HKUDS)
- 발표: EMNLP 2025
- 목표
  - GraphRAG의 복잡성을 줄이면서도 성능을 유지하는 경량 그래프 RAG 프레임워크

### 핵심 특징

- 듀얼 레벨 검색 시스템(Dual-level Retrieval)
  - 로컬 레벨: 세부 정보 검색 (특정 엔티티, 구체적 내용)
  - 글로벌 레벨: 거시적 개념 검색 (전체적 주제, 패턴)
  - 두 레벨을 통합하여 포괄적인 검색 수행
- 모듈형 설계(Modular Design)
  - 문서 파싱 / 인덱스 구축 / 검색 / 생성 단계가 분리됨
  - 각 모듈을 독립적으로 교체하거나 최적화 가능

### GraphRAG와의 비교

**표 9.1** GraphRAG vs LightRAG 비교

| 기준 | GraphRAG | LightRAG |
|-----|----------|----------|
| 개발사 | Microsoft | HKUDS |
| 인덱싱 비용 | 높음 | 낮음 |
| 증분 업데이트 | 제한적 | 지원 |
| 검색 전략 | 글로벌/로컬 분리 | 듀얼 레벨 통합 |
| 쿼리 지연 | 표준 | ~30% 감소 |
| 적합한 사용 | 대규모 분석 | 빠른 프로토타입 |

### 성능

- LightRAG 저자들의 벤치마크 결과
  - Naive RAG 및 GraphRAG 대비 쿼리 지연(query latency) 감소
  - 답변 품질 향상
- 강점
  - 인덱싱 비용이 낮음
  - → 빠른 프로토타이핑(rapid prototyping)에 적합

---

## 9.5 KAG: 지식 증강 생성

- KAG = Knowledge Augmented Generation (지식 증강 생성)
- 기반 엔진: OpenSPG
- 목적: 전문 도메인 지식베이스를 위한 Q&A 솔루션 제공
- 특성: 논리적 추론(logical reasoning) 프레임워크

### 핵심 특징

- 도메인 특화 지식 그래프 구축
  - 일반적인 지식 그래프가 아닌 특정 분야에 최적화된 스키마 사용
  - → 예시: 의료, 법률, 금융 등 전문 도메인
- 다중 홉 추론(multi-hop reasoning) 지원
  - 여러 엔티티에 걸친 정보를 연결하고 합성
- DIKW 모델 기반 정보 계층화
  - DIKW = Data(데이터) - Information(정보) - Knowledge(지식) - Wisdom(지혜)
  - 정보를 계층적으로 구조화하여 추론 품질 향상

### GraphRAG/LightRAG와의 관계

- KAG가 해결하고자 하는 문제
  - 벡터 RAG의 모호성(ambiguity)
  - GraphRAG의 노이즈(noise) 문제
- 2025년 업데이트 주요 내용
  - "Lightweight Build" 모드 도입
  - 결과: 토큰 비용을 89% 절감
- 세 프레임워크의 관계: 경쟁이 아닌 보완 관계
  - 동적 환경 → RAG (빠른 업데이트, 유연성)
  - 구조화된 도메인 → KAG (전문 지식의 정밀 표현)
  - 복잡한 관계 추론 → GraphRAG / LightRAG (엔티티 간 연결 추론)

---

## 9.6 실습: 벡터 RAG vs 그래프 RAG 비교

### 실습 목표

- 동일한 문서에서 지식 그래프를 추출한다
- 벡터 RAG와 그래프 기반 RAG로 동일한 질문에 답변한다
- 두 방식의 결과를 비교 분석한다

### 실습 환경 설정

```bash
cd practice/chapter9
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
cp code/.env.example code/.env  # OPENAI_API_KEY 설정
```

### 그래프 RAG 실행

```bash
python3 code/9-6-graph-rag.py
python3 code/9-6-compare.py
```

### 실행 결과

**표 9.2** 벡터 RAG vs 그래프 RAG 비교

| 항목 | 벡터 RAG | 그래프 RAG |
|-----|---------|-----------|
| 총 실행 시간 | 21.72초 | 59.00초 |
| 청크/엔티티 수 | 11개 청크 | 41개 엔티티 |
| 관계 수 | - | 44개 |

- 실행 시간 비교
  - 그래프 RAG는 벡터 RAG 대비 약 2.7배 시간 소요
  - 이유: 지식 그래프 구축 과정에서 추가 LLM 호출이 필요하기 때문
- 답변 품질 비교
  - "A와 B의 관계" 같은 관계 중심 질문에서는 그래프 RAG가 더 명확한 답변을 제공

### 질문별 비교 예시

- 질문: "코루틴과 태스크는 어떤 관계가 있나요?"
- 그래프 RAG의 처리 방식
  - "코루틴", "asyncio.create_task", "비동기 작업" 등 관련 엔티티를 명시적으로 식별
  - 식별된 엔티티들 간의 관계를 바탕으로 답변을 구성
  - → 결과: 관계 중심의 명확한 구조적 답변 생성

### 실습 산출물

- `practice/chapter9/data/output/ch09_knowledge_graph.json`: 추출된 지식 그래프
- `practice/chapter9/data/output/ch09_vector_result.json`: 벡터 RAG 결과
- `practice/chapter9/data/output/ch09_graph_result.json`: 그래프 RAG 결과
- `practice/chapter9/data/output/ch09_comparison.json`: 비교 분석

---

## 9.7 그래프 RAG 선택 가이드

### 벡터 RAG가 적합한 경우

- 단순 검색 질문
  - 특정 정보를 검색하는 단순 질문에 강함
  - → 예시: "asyncio.gather()의 매개변수는?"
  - 이유: 하나의 청크에서 답을 찾을 수 있는 경우 빠르고 정확한 결과 반환
- 실시간 응답이 필요한 경우
  - 낮은 응답 지연(latency)이 요구되는 환경에 적합
- 인덱싱 비용 최소화가 필요한 경우
  - 구축 비용을 줄여야 할 때 벡터 RAG가 경제적
- 문서가 자주 업데이트되는 환경
  - 재인덱싱 비용이 낮은 벡터 RAG가 유리
  - 그래프 RAG는 그래프 재구축 비용이 추가로 발생

### 그래프 RAG가 필요한 경우

- 전역적(global) 질문
  - 전체 데이터를 아우르는 질문에 강점
  - → 예시: "전체 데이터의 주요 테마는 무엇인가?"
- 관계 파악이 필요한 질문
  - 엔티티 간 관계를 파악해야 하는 경우
  - 다중 홉 추론이 필요한 복잡한 질문
  - 이러한 경우 벡터 RAG보다 우수한 답변 생성
- 도메인 지식의 구조화가 중요한 분야
  - → 예시: 의료, 법률, 금융 등 전문 도메인
  - 이유: 지식 그래프가 기존 온톨로지(ontology)와 자연스럽게 결합 가능

### 하이브리드 접근

- 실무에서 권장하는 방식
  - 벡터 검색과 그래프 검색을 결합하는 것이 효과적
- 동작 방식
  - 1단계: 벡터 검색으로 관련 청크를 먼저 찾음
  - 2단계: 그래프 순회(graph traversal)로 관련 엔티티를 확장
  - 결과: 맥락(context)을 보강하여 더 풍부한 답변 생성
- 대표 사례
  - LightRAG의 듀얼 레벨 검색이 이러한 하이브리드 접근의 대표적 예

---

## 9.8 실패 사례와 교훈

### 엔티티/관계 추출 오류

- ⚠ LLM 기반 추출은 완벽하지 않음
  - 오류가 발생하는 주요 상황
    - 모호한 표현(ambiguous wording)이 있는 경우
    - 암묵적 관계(implicit relation)가 존재하는 경우
    - 도메인 특화 용어(domain-specific terminology)가 포함된 경우
  - 대응 방법
    - 추출 결과를 검증하는 단계를 파이프라인에 추가
    - 도메인에 맞춘 특화 프롬프트(domain-specific prompt) 설계

### 과도한 인덱싱 비용

- ⚠ 소규모 데이터셋에 GraphRAG를 적용하면 비용 대비 효과가 낮음
  - 이유: 그래프 구축 비용이 검색 성능 향상보다 클 수 있음
  - 대응 방법
    - 데이터 규모를 분석
    - 질문 유형을 분석
    - 그래프 RAG가 정말 필요한지 사전 평가 후 도입 결정

### 그래프 품질 저하

- ⚠ 오래된 정보로 구축된 그래프는 잘못된 답변을 유도
  - 원인: 문서는 업데이트되었으나 그래프는 갱신되지 않은 경우
  - 대응 방법
    - 문서 업데이트 시 그래프도 함께 갱신하는 파이프라인 구축 필요
  - LightRAG의 해결책
    - 증분 업데이트(incremental update)를 지원하여 이 문제를 완화

---

## 핵심 정리

- 벡터 RAG는 전역적 질문, 다중 홉 추론, 관계 파악에 한계가 있음
- 지식 그래프는 엔티티와 관계를 트리플(주어-술어-목적어) 형태로 표현
- GraphRAG는 커뮤니티 요약과 계층적 검색으로 전역적 질문에 강함
- LightRAG는 듀얼 레벨 검색으로 GraphRAG를 경량화한 프레임워크
- 벡터 RAG는 단순 검색에, 그래프 RAG는 관계 추론에 각각 강점이 있음

---

## 다음 장 예고

- 10장 주제: 에이전트 보안과 신뢰성
- 학습 내용
  - OWASP AI Agent Security Top 10에 기반한 보안 위협 분류
  - 다층 가드레일(multi-layer guardrail) 아키텍처
  - 에이전트 평가 프레임워크
  - 검증 실패 시 재시도와 사람 승인(human approval)이 포함된 워크플로우 구현

---

## 참고문헌

Microsoft. (2025). *GraphRAG: A modular graph-based RAG system*. https://github.com/microsoft/graphrag

Microsoft Research. (2024). *GraphRAG: Unlocking LLM discovery on narrative private data*. https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/

HKUDS. (2025). *LightRAG: Simple and Fast Retrieval-Augmented Generation*. https://github.com/HKUDS/LightRAG

OpenSPG. (2025). *KAG: Knowledge Augmented Generation*. https://github.com/OpenSPG/KAG

Edge et al. (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*. arXiv:2404.16130
