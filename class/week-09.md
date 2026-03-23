# Week 9. RAG의 기본과 에이전트 메모리 아키텍처

> 원본: docs/ch8.md

## 학습 목표

- RAG(검색 증강 생성)가 필요한 상황과 전체 아키텍처를 이해한다
- 에이전트 메모리를 4가지 유형으로 분류하고 각각의 구현 전략을 설명한다
  - Working Memory(작업 메모리)
  - Episodic Memory(일화 메모리)
  - Semantic Memory(의미 메모리)
  - Procedural Memory(절차 메모리)
- RAG와 에이전트 메모리의 차이와 상호보완 관계를 판단한다
- 답변에 인용/출처를 포함하는 방법을 구현한다

---

## 선수 지식

- 7장에서 학습한 멀티에이전트 개념
- Python 기본 문법
- OpenAI API 사용 경험

---

## 8.1 RAG가 필요한 이유

- 7장에서 학습한 에이전트는 LLM의 내재된 지식만으로 답변을 생성했음
- LLM에는 명확한 한계가 존재함
  - 학습 데이터의 지식 컷오프(knowledge cutoff, 모델이 학습한 데이터의 마지막 날짜) 이후 정보를 알지 못함
  - 조직 내부 문서나 도메인 특화 지식에 접근할 수 없음
  - 출처 없이 답변하므로 검증이 어려움
- RAG(Retrieval Augmented Generation, 검색 증강 생성)는 이러한 한계를 극복하는 기술
  - 외부 지식을 검색하여 LLM의 컨텍스트에 주입
  - 주입된 정보를 바탕으로 답변을 생성하는 하이브리드 아키텍처(두 방식을 결합한 구조)
  - 2025년 기준 프로덕션 AI 애플리케이션의 약 60%가 RAG를 사용

- RAG의 핵심 이점
  - **즉각적인 지식 갱신**
    - 문서를 추가하거나 업데이트하면 즉시 지식이 반영됨
    - 파인튜닝(fine-tuning, 모델 재학습)처럼 모델을 재학습할 필요가 없음
  - **출처 명시 가능**
    - 답변에 출처를 명시할 수 있어 검증 가능성이 높아짐
  - **환각 감소**
    - 외부 지식에 근거하므로 환각(hallucination, 모델이 사실과 다른 내용을 그럴듯하게 만들어내는 현상)이 감소함

**표 8.1** RAG vs 파인튜닝 비교

| 기준 | RAG | 파인튜닝 |
|-----|-----|---------|
| 지식 업데이트 | 문서 추가로 즉시 | 재학습 필요 |
| 비용 | 임베딩/검색 비용 | 학습 비용 높음 |
| 출처 추적 | 가능 | 불가능 |
| 환각 감소 | 근거 기반 답변 | 제한적 |
| 적합한 상황 | 자주 변경되는 지식 | 스타일/형식 변경 |

---

## 8.2 RAG 아키텍처 개요

- RAG 시스템은 크게 두 단계로 구성됨
  - 인덱싱(오프라인): 사전에 문서를 처리하여 저장하는 단계
  - 검색-생성(온라인): 사용자 질문에 실시간으로 응답하는 단계

### 인덱싱 단계

- 문서를 수집하고 처리하여 검색 가능한 형태로 저장하는 과정
- 처리 순서
  1. 문서를 청크(chunk, 작은 조각)로 분할
  2. 각 청크를 임베딩(embedding) 모델로 벡터(숫자 배열)로 변환
  3. 변환된 벡터를 벡터 데이터베이스에 저장

### 검색-생성 단계

- 사용자 질문이 들어오면 실시간으로 처리하는 과정
- 처리 순서
  1. 사용자 질문을 벡터로 변환
  2. 벡터 데이터베이스에서 유사한 청크를 검색
  3. 검색된 청크를 LLM의 컨텍스트(입력)에 포함
  4. LLM이 컨텍스트를 참조하여 답변을 생성

### 임베딩과 벡터 유사도

- 임베딩(embedding): 텍스트를 고차원 벡터(수백~수천 차원의 숫자 배열)로 변환하는 과정
  - 의미적으로 유사한 텍스트는 벡터 공간에서 가까운 위치에 놓임
    - → 예시: "강아지"와 "개"의 임베딩 벡터는 서로 가깝고, "자동차"의 임베딩 벡터와는 멀리 위치함
- 유사도 계산 방법
  - 코사인 유사도(cosine similarity): 두 벡터 간의 각도로 유사도를 측정 (1에 가까울수록 유사)
  - 유클리드 거리(Euclidean distance): 두 벡터 간의 직선 거리로 유사도를 측정 (0에 가까울수록 유사)

---

## 8.3 벡터 데이터베이스: ChromaDB

- 벡터 데이터베이스: 고차원 벡터를 효율적으로 저장하고 검색하는 특수 목적 데이터베이스
- ChromaDB
  - 오픈소스 벡터 데이터베이스
  - 로컬 개발과 프로토타이핑(빠른 시제품 제작)에 적합

```python
from langchain_community.vectorstores import Chroma

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings
)
```

_전체 코드는 practice/chapter8/code/8-6-rag-basic.py 참고_

### 주요 벡터 데이터베이스 비교

| 데이터베이스 | 특징 | 적합한 사용 |
|------------|------|-----------|
| ChromaDB | 오픈소스, 로컬 실행 | 프로토타이핑, 소규모 |
| Pinecone | 관리형 서비스, 확장성 | 프로덕션, 대규모 |
| Milvus | 오픈소스, 분산 처리 | 엔터프라이즈 |
| Weaviate | 그래프 기능 포함 | 관계 기반 검색 |

---

## 8.4 청킹 전략: 문서를 효과적으로 분할하기

- 청킹(chunking): 문서를 검색에 적합한 크기의 조각으로 나누는 과정
- 청킹은 RAG 성능에 큰 영향을 미침
  - ⚠ 청크가 너무 작으면 컨텍스트가 부족하여 LLM이 정확한 답변을 생성하기 어려움
  - ⚠ 청크가 너무 크면 관련 없는 정보가 포함되어 검색 정확도가 떨어짐

### 고정 크기 청킹

- `RecursiveCharacterTextSplitter`: 지정된 크기로 문서를 분할하는 도구
  - 단순히 글자 수만 세는 것이 아니라 문장이나 문단 경계를 존중하여 분할
  - 업계 권장 설정
    - 청크 크기: 256~512 토큰(token, LLM이 처리하는 최소 언어 단위)
    - 오버랩(overlap, 청크 간 겹치는 부분): 10~20%

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)
```

### 의미 기반 청킹

- 문장의 임베딩 유사도를 기준으로 분할 지점을 결정하는 방식
  - 의미적으로 연관된 문장을 같은 청크에 유지하여 검색 품질이 향상됨
  - → 예시: "파이썬 문법"에 관한 여러 문장이 하나의 청크로 묶여, 관련 질문 시 함께 검색됨
  - ⚠ 모든 문장의 임베딩을 계산해야 하므로 고정 크기 청킹보다 비용이 높음

### 트레이드오프 (Trade-off, 한 가지를 얻으면 다른 것을 잃는 관계)

- 작은 청크의 특성
  - 쿼리(query, 검색 질문)와 정확히 매칭될 가능성이 높음
  - ⚠ 주변 컨텍스트를 잃어 답변이 불완전해질 수 있음
- 큰 청크의 특성
  - 충분한 컨텍스트를 보존함
  - ⚠ 임베딩이 희석(diluted)되어 벡터 검색의 정확도가 떨어질 수 있음
- 실험을 통해 데이터와 사용 사례에 맞는 최적값을 찾아야 함

---

## 8.5 검색 품질 향상

- 기본 벡터 검색만으로는 충분하지 않을 수 있음
- 검색 품질을 향상시키는 기법을 추가로 적용해야 함

### 하이브리드 검색 (Hybrid Search)

- 키워드 검색(BM25)과 벡터 검색을 결합하는 방식
  - **벡터 검색**의 역할: 의미적 유사성(뜻이 비슷한 표현)을 포착
    - → 예시: "강아지 먹이"와 "개 사료"를 같은 의미로 인식
  - **키워드 검색(BM25)**의 역할: 정확한 용어 매칭에 강함
    - → 예시: "asyncio.gather()"와 같은 특정 함수명을 정확히 검색
  - 두 결과를 융합(fusion)하여 더 나은 검색 결과를 얻음

### 리랭킹 (Reranking, 재정렬)

- 초기 검색 결과를 더 정교한 모델로 재정렬하는 기법
  - Cross-encoder 모델이 쿼리와 각 문서의 관련성을 직접 평가하여 순위를 조정
    - Bi-encoder(일반 임베딩 모델): 쿼리와 문서를 각각 독립적으로 인코딩하여 빠르지만 정밀도가 낮음
    - Cross-encoder: 쿼리와 문서를 함께 입력하여 정밀도가 높지만 느림
  - ⚠ Cross-encoder는 계산 비용이 높으므로 Top-K(상위 K개) 결과에만 적용

### 쿼리 확장 (Query Expansion)

- 사용자 쿼리를 여러 형태로 확장하여 더 넓은 범위를 검색하는 기법
  - LLM을 사용하여 쿼리를 재작성(paraphrase)
  - 동의어를 추가하여 검색 범위를 넓힘
    - → 예시: "자동차 수리" 쿼리를 "차량 정비", "카 리페어" 등으로 확장

---

## 8.6 인용과 출처 추적

- RAG의 핵심 장점 중 하나: 출처(source)를 명시할 수 있음
  - 출처를 포함하면 답변의 신뢰성이 높아짐
  - 사용자가 원본 문서를 직접 확인하여 검증 가능

### 청크 메타데이터 관리

- 각 청크에 메타데이터(metadata, 데이터에 대한 정보)를 저장하는 방식
  - 저장하는 메타데이터 종류
    - 원본 문서 정보(파일명, 경로)
    - 청크 ID(고유 식별자)
    - 페이지 번호
  - 검색 결과와 함께 메타데이터를 반환하여 출처를 추적

```python
chunk.metadata["source_name"] = Path(source_path).name
chunk.metadata["chunk_id"] = i
```

### 답변에 출처 포함

- 프롬프트(prompt, LLM에게 전달하는 지시문)에서 LLM에게 출처를 명시하도록 지시
  - 처리 방식
    1. 검색된 문서에 출처 레이블(label, 꼬리표)을 붙임
    2. LLM이 이를 참조하여 답변에 인용(citation)을 포함
      - → 예시: "asyncio.gather()는 모든 코루틴이 완료될 때까지 기다립니다. [출처: asyncio_tasks.txt]"

---

## 8.7 에이전트 메모리 분류 체계

- RAG와 에이전트 메모리의 개념 구분
  - RAG: "외부 지식을 검색하여 답변하는 구조"
  - 에이전트 메모리: "에이전트가 경험을 축적하고 활용하는 구조"
- 인지과학(인간의 인지 과정을 연구하는 학문)의 메모리 분류를 빌려 에이전트 메모리를 4가지 유형으로 분류

### 8.7.1 Working Memory (작업 메모리)

- 현재 컨텍스트 윈도우(context window, LLM이 한 번에 처리할 수 있는 텍스트 범위)에 담긴 정보
  - 해당 정보의 종류
    - 시스템 프롬프트(system prompt, LLM의 동작을 설정하는 지시문)
    - 대화 히스토리(history, 이전 대화 내용)
    - 검색 결과
  - 가장 직접적이고 즉각적으로 접근 가능한 메모리
  - ⚠ 토큰(token) 한도에 의해 용량이 제한됨
- 6장의 LangGraph State 객체도 하나의 워크플로우(workflow, 작업 흐름) 내 작업 메모리로 볼 수 있음

### 8.7.2 Episodic Memory (일화 메모리)

- 과거 이벤트(사건)와 결과를 시간순으로 저장하는 메모리
  - → 예시: "어제 사용자가 파이썬 비동기 프로그래밍에 대해 질문했고, asyncio.gather()를 추천했다"
- 에이전트가 이전 상호작용(interaction, 사용자와의 대화)의 맥락을 기억하여 일관된 응답을 제공하는 데 활용됨
- 특정 경험의 구체적인 내용이 담긴 메모리

### 8.7.3 Semantic Memory (의미 메모리)

- 일화(에피소드)에서 일반화(패턴 추출)된 지식을 저장하는 메모리
  - → 예시: "이 사용자는 한국어를 선호하고, 코드 예제를 중시한다"
  - 특정 이벤트에 종속되지 않으므로 다양한 상황에 적용 가능
  - 개별 경험에서 뽑아낸 일반적인 패턴화된 정보

### 8.7.4 Procedural Memory (절차 메모리)

- 학습된 도구 사용 패턴과 작업 수행 방법을 저장하는 메모리
  - → 예시: "날씨 질문에는 weather_tool을 호출하고, 결과를 한국어로 요약한다"
  - 행동 규칙(behavior rule) 형태로 저장됨
  - 구현 방법
    - 프롬프트 패턴으로 명시
    - 파인튜닝(fine-tuning)으로 모델에 내재화(모델 자체에 학습시킴)

**표 8.2** 에이전트 메모리 4가지 유형

| 유형 | 내용 | 지속성 | 예시 |
|------|------|--------|------|
| Working | 현재 컨텍스트 | 세션 내 | 대화 히스토리, 검색 결과 |
| Episodic | 과거 이벤트 | 장기 | "어제 질문에 X를 추천했다" |
| Semantic | 일반화된 지식 | 장기 | "사용자는 한국어를 선호한다" |
| Procedural | 행동 규칙 | 영구 | "날씨 질문 → weather_tool" |

---

## 8.8 메모리 구현 전략

- 각 메모리 유형은 서로 다른 기술로 구현함

### 8.8.1 Episodic Memory 구현

- 일반적인 구현 방법: 벡터 데이터베이스에 시간 메타데이터를 함께 저장
  - 처리 순서
    1. 각 상호작용(사용자와의 대화)을 임베딩(벡터로 변환)
    2. 타임스탬프(timestamp, 발생 시각)·사용자 ID·세션(session) ID를 메타데이터로 추가
    3. 검색 시 시간 가중치(time weight)를 적용하여 최근 경험에 더 높은 우선순위 부여
- 대표적인 구현 도구
  - 6장에서 다룬 LangGraph의 Store API
    - `put`: 메모리 저장
    - `get`: 특정 메모리 조회
    - `search`: 유사한 메모리 검색

### 8.8.2 Semantic Memory 구현

- 구현 방법 1: 지식 그래프(knowledge graph) 사용
  - 일화 메모리에서 패턴을 추출하여 지식 그래프에 저장
  - 엔티티(entity, 개체)와 관계를 노드(node, 점)·엣지(edge, 선)로 표현
  - 구조화된 지식을 질의(query)할 수 있음
  - 9장에서 다루는 GraphRAG가 이 접근의 확장
- 구현 방법 2: JSON 문서 방식(더 단순한 방법)
  - 사용자 프로필을 JSON 문서로 유지하면서 주기적으로 갱신
  - → 예시: `{"preferred_language": "Korean", "prefers_code_examples": true}`

### 8.8.3 Procedural Memory 구현

- 구현 방법 1: 시스템 프롬프트에 행동 규칙을 명시
- 구현 방법 2: 파인튜닝(fine-tuning)으로 모델에 내재화
- 구현 방법 3: Few-shot 예제(few-shot example, 소수의 예시를 통한 학습) 활용
  - 학습된 도구 사용 패턴을 프롬프트에 예제 형태로 포함
- 구현 방법 4: 파인튜닝 데이터셋 구축 (비용이 허용되는 경우)
  - 성공적인 도구 호출 이력을 수집하여 파인튜닝 데이터로 활용

### 8.8.4 LangGraph + 외부 저장소 조합

- 프로덕션(실제 서비스) 수준의 메모리 시스템 구성
  - LangGraph의 체크포인터(checkpointer, 상태 저장 도구)와 Store API를 외부 저장소와 결합하여 구현
  - 저장소별 역할 분담
    - **MongoDB** (`langgraph-store-mongodb`): Episodic/Semantic 메모리에 적합
      - 문서형 데이터베이스로 비정형 데이터 저장에 유리
    - **Redis** (`langgraph-checkpoint-redis`): Working Memory와 빠른 캐시(cache, 임시 고속 저장소)에 적합
      - 인메모리(in-memory) 데이터베이스로 읽기/쓰기 속도가 매우 빠름
  - 이 조합의 장점
    - 메모리 유형별로 최적의 저장소를 선택 가능
    - LangGraph의 통합 API로 일관되게 접근 가능

---

## 8.9 RAG와 메모리: 상호보완 관계

- RAG와 에이전트 메모리는 종종 혼동되지만 목적이 다름
  - **RAG**의 목적: 외부 지식을 검색하여 모델이 알지 못하는 정보를 제공
  - **에이전트 메모리**의 목적: 에이전트의 경험을 축적하여 이전 상호작용의 맥락을 유지

**표 8.3** RAG vs 에이전트 메모리

| 기준 | RAG | 에이전트 메모리 |
|------|-----|---------------|
| 목적 | 외부 지식 접근 | 경험 축적·활용 |
| 데이터 원천 | 문서 코퍼스 | 과거 상호작용 |
| 갱신 주기 | 문서 변경 시 | 매 상호작용마다 |
| 검색 대상 | 문서 청크 | 에피소드, 사용자 선호 |
| 대표 기술 | 벡터 DB + 임베딩 | Store API + 시간 메타데이터 |

- 실제 에이전트 애플리케이션은 두 접근을 결합하여 사용
  - RAG로 도메인 지식(domain knowledge, 특정 분야의 전문 지식)을 검색
  - Episodic Memory로 이전 질의 결과를 참조
  - 이 결합의 효과
    - 중복 검색을 줄임 (이미 검색한 내용을 재활용)
    - 응답의 일관성(consistency)을 높임
- 이 장의 실습 구성
  1. 기본 RAG 구현
  2. Episodic Memory를 추가한 개선판 구현

---

## 8.10 실습: 문서 기반 Q&A 시스템

### 실습 목표

1. 문서를 청킹하고 ChromaDB에 저장한다
2. 질문에 대해 관련 문서를 검색한다
3. 검색 결과를 바탕으로 LLM이 답변을 생성한다
4. 답변에 출처를 포함하여 반환한다

### 실습 환경 설정

```bash
cd practice/chapter8
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
cp code/.env.example code/.env  # OPENAI_API_KEY 설정
python3 code/8-6-rag-basic.py
```

### 실행 결과

**표 8.4** RAG 시스템 실행 결과

| 항목 | 값 |
|-----|-----|
| 입력 문서 수 | 3개 |
| 생성된 청크 수 | 11개 |
| 청크 크기 | 500자 |
| 오버랩 | 50자 |
| 총 실행 시간 | 22.43초 |

### 질문 및 답변 예시

- 질문: "asyncio.gather()와 asyncio.wait()의 차이점은 무엇인가요?"
- → 예시: 답변 — asyncio.gather()는 모든 코루틴이 완료될 때까지 기다린 후 결과를 리스트 형태로 반환한다. 반면 asyncio.wait()는 완료된 태스크와 대기 중인 태스크를 구분하여 반환하며, 더 세밀한 제어가 가능하다. [출처: asyncio_tasks.txt]

### 실습 산출물

- `practice/chapter8/data/output/ch08_qa_result.json`: Q&A 결과
- `practice/chapter8/data/output/ch08_index_stats.json`: 인덱스 통계
- `practice/chapter8/data/output/ch08_answer.txt`: 생성된 답변

---

## 8.11 프로덕션 체크리스트

- 프로덕션(실제 서비스) 환경에서 RAG 시스템을 운영할 때 고려해야 할 사항

### 캐싱 전략 (Caching Strategy)

- 캐싱(caching): 반복적으로 사용하는 결과를 미리 저장해두는 기법
  - 임베딩 결과를 캐싱하여 동일 문서에 대한 중복 계산을 방지
  - 자주 묻는 질문(FAQ)에 대한 답변을 캐싱하여 응답 시간과 비용을 절감
  - ⚠ 문서가 업데이트되면 관련 캐시를 무효화(invalidate)해야 함 — 오래된 캐시가 잘못된 답변을 유발할 수 있음

### 비용 최적화

- 임베딩 모델 선택이 비용에 큰 영향을 미침
  - **OpenAI text-embedding-3-small**: 성능과 비용의 균형이 좋음
  - **OpenAI text-embedding-3-large**: 더 높은 정확도를 제공하지만 비용이 높음
  - **로컬 모델** (예: all-MiniLM-L6-v2): API 비용 없이 자체 서버에서 실행하여 비용을 크게 줄일 수 있음
- 배치 처리(batch processing, 여러 요청을 묶어서 한꺼번에 처리)로 API 호출을 최소화

### 평가 지표

- 검색 품질 평가 지표
  - **precision@k** (정밀도@k): 상위 k개 결과 중 실제로 관련 있는 결과의 비율
  - **recall@k** (재현율@k): 전체 관련 문서 중 상위 k개 결과에 포함된 비율
- 답변 품질 평가 기준
  - 정확성(accuracy): 사실과 일치하는가
  - 관련성(relevance): 질문에 맞는 답변인가
  - 완전성(completeness): 필요한 정보를 모두 포함하는가
- 정기적인 평가와 A/B 테스트(두 가지 버전을 비교하는 실험)로 시스템을 지속적으로 개선

### 모니터링

- 지속적으로 추적해야 할 항목
  - 검색 실패율: 관련 문서를 찾지 못하는 비율
  - 응답 시간: 사용자가 답변을 받기까지 걸리는 시간
  - 사용자 피드백: 답변의 유용성에 대한 사용자 평가
- 임베딩 버전을 관리하여 문서-벡터 매핑(mapping, 대응 관계)을 추적
  - ⚠ 임베딩 모델이 변경되면 기존 벡터와 새 벡터가 호환되지 않으므로 재인덱싱 필요

**표 8.5** RAG 프로덕션 체크리스트

| 영역 | 체크 항목 |
|-----|---------|
| 검색 | 적절한 Top-K 설정, 필터링 조건, 리랭킹 적용 |
| 비용 | 임베딩 캐싱, 배치 처리, 모델 선택 |
| 품질 | 정기적 평가, 사용자 피드백 수집 |
| 운영 | 로깅, 오류 모니터링, 버전 관리 |

---

## 8.12 실패 사례와 교훈

### 검색 실패: 관련 문서를 찾지 못함

- 발생 원인
  - 질문과 문서의 표현 방식이 다르면 임베딩 유사도가 낮아져 검색에 실패
    - → 예시: 질문에 "차 수리"라고 했는데 문서에 "vehicle maintenance"로만 기술된 경우
- 완화 방법
  - 쿼리 확장(query expansion) 적용: 질문을 다양한 표현으로 변환하여 검색
  - 하이브리드 검색 적용: 키워드 검색과 벡터 검색을 병행
  - 문서 작성 시 다양한 표현을 미리 포함

### 컨텍스트 과부하 (Context Overload)

- 발생 원인
  - 너무 많은 청크를 LLM에 전달했을 때 발생
    - 컨텍스트 윈도우를 초과하여 오류 발생
    - 관련 없는 정보로 인해 답변 품질이 저하됨
- 완화 방법
  - ⚠ 적절한 Top-K 값을 설정하여 전달하는 청크 수를 제한
  - 필요시 요약(summarization) 또는 압축(compression)을 적용하여 컨텍스트 크기를 줄임

### 오래된 정보 (Stale Information)

- 발생 원인
  - 문서가 업데이트되었지만 벡터 인덱스(index, 검색용 색인)에 반영되지 않은 경우
    - → 예시: 제품 가격이 변경되었는데 인덱스에는 이전 가격이 남아있어 잘못된 답변 생성
- 완화 방법
  - ⚠ 문서 변경 감지(change detection) 시스템 구축
  - 자동 재인덱싱(re-indexing) 파이프라인(pipeline, 자동화된 처리 흐름)을 구축하여 변경 시 즉시 반영

---

## 핵심 정리

- RAG는 외부 지식을 검색하여 LLM 답변의 품질과 신뢰성을 향상시킴
- RAG는 두 단계로 구성됨
  - 인덱싱: 청킹 → 임베딩 → 저장
  - 검색-생성: 질문 벡터화 → 유사 청크 검색 → LLM 답변 생성
- 에이전트 메모리는 4가지 유형으로 분류됨
  - Working: 현재 컨텍스트 (세션 내 유지)
  - Episodic: 과거 경험 (장기 유지)
  - Semantic: 일반화된 지식 (장기 유지)
  - Procedural: 행동 규칙 (영구 유지)
- RAG와 에이전트 메모리는 상호보완적 관계
  - RAG: 외부 지식 검색
  - 에이전트 메모리: 에이전트 경험 축적
- 프로덕션 메모리 시스템 구현 조합
  - LangGraph Store API + MongoDB(Episodic/Semantic) + Redis(Working Memory/캐시)
- 출처를 명시하여 답변의 검증 가능성을 높임

---

## 다음 장 예고

- 9장 주제: GraphRAG와 LightRAG
  - 벡터 검색의 한계를 극복하는 방법
  - 엔티티 간 관계를 활용한 그래프(graph) 기반 검색
  - 복잡한 질문(여러 개념의 관계를 파악해야 하는 질문)에 답하는 방법을 살펴봄

---

## 참고문헌

Eden AI. (2025). *The 2025 Guide to Retrieval-Augmented Generation (RAG)*. https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag

Firecrawl. (2025). *Best Chunking Strategies for RAG in 2025*. https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025

LangChain. (2025). *Memory overview - LangGraph Documentation*. https://docs.langchain.com/oss/python/langgraph/memory

LangChain. (2025). *Launching Long-Term Memory Support in LangGraph*. https://www.blog.langchain.com/launching-long-term-memory-support-in-langgraph/

MongoDB. (2025). *Powering Long-Term Memory For Agents With LangGraph And MongoDB*. https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph

Redis. (2025). *LangGraph & Redis: Build smarter AI agents with memory persistence*. https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/

Weaviate. (2024). *Chunking Strategies to Improve Your RAG Performance*. https://weaviate.io/blog/chunking-strategies-for-rag
