"""
10-6-verification.py: 검증 워크플로우 구현

검증 실패 시 재시도 및 사람 승인이 포함된 RAG 검증 파이프라인.
- 교차검증 (Self-consistency)
- 출처 일치 검증 (Grounding check)
- 품질 게이트 (최대 3회 재시도)
- 사람 승인 요청 (재시도 초과 시)
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict, Literal
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

load_dotenv()

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 상수
MAX_RETRIES = 3
CONSISTENCY_THRESHOLD = 0.25  # 25% 이상 키워드 일치 시 통과 (의미론적 유사성 근사)
GROUNDING_THRESHOLD = 0.7     # 70% 이상 근거 시 통과


class VerificationState(TypedDict):
    """검증 워크플로우 상태"""
    query: str
    context: str
    answer: str
    consistency_samples: list[str]
    consistency_score: float
    grounding_score: float
    is_grounded: bool
    is_consistent: bool
    retry_count: int
    needs_human_approval: bool
    human_decision: str
    final_answer: str
    failure_reasons: Annotated[list[str], add]
    verification_log: Annotated[list[dict], add]


def load_documents() -> list[Document]:
    """입력 문서 로드"""
    docs_dir = INPUT_DIR / "docs"
    if not docs_dir.exists():
        # 8장 문서 재사용 시도
        ch8_docs = BASE_DIR.parent / "chapter8" / "data" / "input" / "docs"
        if ch8_docs.exists():
            docs_dir = ch8_docs
        else:
            # 샘플 문서 생성
            docs_dir.mkdir(parents=True, exist_ok=True)
            sample_doc = docs_dir / "sample.txt"
            sample_doc.write_text("""
Python의 asyncio는 비동기 프로그래밍을 위한 표준 라이브러리이다.
이벤트 루프는 비동기 작업을 관리하고 스케줄링하는 핵심 컴포넌트이다.
코루틴은 async def로 정의되며, await 키워드로 다른 코루틴을 호출한다.
태스크는 코루틴을 감싸서 이벤트 루프에서 실행되도록 예약하는 객체이다.
asyncio.create_task()로 코루틴을 태스크로 변환할 수 있다.
asyncio.gather()는 여러 코루틴을 동시에 실행하고 결과를 리스트로 반환한다.
asyncio.wait()는 완료된 태스크와 대기 중인 태스크를 구분하여 반환한다.
""".strip(), encoding="utf-8")

    documents = []
    for file_path in docs_dir.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")
        documents.append(Document(
            page_content=content,
            metadata={"source": file_path.name}
        ))
    return documents


def create_vectorstore(documents: list[Document]) -> Chroma:
    """벡터 저장소 생성"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30
    )
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="ch10_verification"
    )
    return vectorstore


def retrieve_context(vectorstore: Chroma, query: str, k: int = 3) -> str:
    """관련 컨텍스트 검색"""
    docs = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])


# 노드 함수들
def generate_answer(state: VerificationState) -> dict:
    """답변 생성 노드"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """주어진 컨텍스트를 기반으로 질문에 답변하세요.
컨텍스트에 없는 정보는 추측하지 마세요.
답변은 반드시 컨텍스트에서 근거를 찾을 수 있어야 합니다."""),
        ("human", """컨텍스트:
{context}

질문: {query}

답변:""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "context": state["context"],
        "query": state["query"]
    })

    return {
        "answer": response.content,
        "verification_log": [{
            "step": "generate_answer",
            "timestamp": datetime.now().isoformat(),
            "retry_count": state.get("retry_count", 0)
        }]
    }


def check_consistency(state: VerificationState) -> dict:
    """교차검증 노드 (Self-consistency)"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)  # 높은 temperature

    prompt = ChatPromptTemplate.from_messages([
        ("system", "주어진 컨텍스트를 기반으로 질문에 간단히 답변하세요."),
        ("human", """컨텍스트:
{context}

질문: {query}

답변:""")
    ])

    chain = prompt | llm
    samples = []

    # 3번 샘플링
    for _ in range(3):
        response = chain.invoke({
            "context": state["context"],
            "query": state["query"]
        })
        samples.append(response.content)

    # 일관성 점수 계산 (단순화: 키워드 기반)
    original_answer = state["answer"].lower()
    original_keywords = set(original_answer.split())

    match_scores = []
    for sample in samples:
        sample_keywords = set(sample.lower().split())
        if original_keywords:
            overlap = len(original_keywords & sample_keywords) / len(original_keywords)
            match_scores.append(overlap)

    consistency_score = sum(match_scores) / len(match_scores) if match_scores else 0
    is_consistent = consistency_score >= CONSISTENCY_THRESHOLD

    result = {
        "consistency_samples": samples,
        "consistency_score": round(consistency_score, 3),
        "is_consistent": is_consistent,
        "verification_log": [{
            "step": "check_consistency",
            "timestamp": datetime.now().isoformat(),
            "score": round(consistency_score, 3),
            "passed": is_consistent
        }]
    }

    if not is_consistent:
        result["failure_reasons"] = [f"일관성 검증 실패 (점수: {consistency_score:.2f})"]

    return result


def check_grounding(state: VerificationState) -> dict:
    """출처 일치 검증 노드"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """답변이 컨텍스트에 의해 뒷받침되는지 평가하세요.

평가 기준:
- 답변의 각 주장이 컨텍스트에서 근거를 찾을 수 있는가?
- 컨텍스트에 없는 정보를 추가했는가?

JSON 형식으로 응답하세요:
{{"grounding_score": 0.0-1.0, "unsupported_claims": ["목록"], "reasoning": "설명"}}"""),
        ("human", """컨텍스트:
{context}

답변:
{answer}

평가:""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "context": state["context"],
        "answer": state["answer"]
    })

    try:
        # JSON 파싱
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        evaluation = json.loads(content.strip())
        grounding_score = float(evaluation.get("grounding_score", 0))
    except (json.JSONDecodeError, ValueError, KeyError):
        # 파싱 실패 시 기본값
        grounding_score = 0.5

    is_grounded = grounding_score >= GROUNDING_THRESHOLD

    result = {
        "grounding_score": round(grounding_score, 3),
        "is_grounded": is_grounded,
        "verification_log": [{
            "step": "check_grounding",
            "timestamp": datetime.now().isoformat(),
            "score": round(grounding_score, 3),
            "passed": is_grounded
        }]
    }

    if not is_grounded:
        result["failure_reasons"] = [f"출처 검증 실패 (점수: {grounding_score:.2f})"]

    return result


def quality_gate(state: VerificationState) -> dict:
    """품질 게이트 노드"""
    passed = state["is_consistent"] and state["is_grounded"]
    retry_count = state.get("retry_count", 0)

    log_entry = {
        "step": "quality_gate",
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "retry_count": retry_count,
        "consistency_score": state.get("consistency_score", 0),
        "grounding_score": state.get("grounding_score", 0)
    }

    if passed:
        return {
            "final_answer": state["answer"],
            "verification_log": [log_entry]
        }
    elif retry_count >= MAX_RETRIES:
        return {
            "needs_human_approval": True,
            "verification_log": [{
                **log_entry,
                "action": "escalate_to_human"
            }]
        }
    else:
        return {
            "retry_count": retry_count + 1,
            "verification_log": [{
                **log_entry,
                "action": "retry"
            }]
        }


def request_human_approval(state: VerificationState) -> dict:
    """사람 승인 요청 노드 (시뮬레이션)"""
    # 실제 환경에서는 interrupt() 사용
    # 여기서는 시뮬레이션: 검증 점수에 따라 자동 결정

    avg_score = (state.get("consistency_score", 0) + state.get("grounding_score", 0)) / 2

    # 시뮬레이션: 평균 점수 0.5 이상이면 승인
    if avg_score >= 0.5:
        decision = "approved"
        final_answer = state["answer"]
    else:
        decision = "rejected"
        final_answer = "[검증 실패] 신뢰할 수 있는 답변을 생성할 수 없습니다."

    return {
        "human_decision": decision,
        "final_answer": final_answer,
        "verification_log": [{
            "step": "human_approval",
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "avg_score": round(avg_score, 3)
        }]
    }


def route_after_gate(state: VerificationState) -> Literal["generate", "human", "end"]:
    """품질 게이트 후 라우팅"""
    if state.get("final_answer"):
        return "end"
    elif state.get("needs_human_approval"):
        return "human"
    else:
        return "generate"


def build_verification_graph() -> StateGraph:
    """검증 워크플로우 그래프 구성"""
    graph = StateGraph(VerificationState)

    # 노드 추가
    graph.add_node("generate", generate_answer)
    graph.add_node("consistency", check_consistency)
    graph.add_node("grounding", check_grounding)
    graph.add_node("gate", quality_gate)
    graph.add_node("human", request_human_approval)

    # 엣지 추가
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "consistency")
    graph.add_edge("consistency", "grounding")
    graph.add_edge("grounding", "gate")
    graph.add_conditional_edges(
        "gate",
        route_after_gate,
        {
            "generate": "generate",
            "human": "human",
            "end": END
        }
    )
    graph.add_edge("human", END)

    return graph.compile()


def run_verification(query: str, vectorstore: Chroma) -> dict:
    """검증 워크플로우 실행"""
    context = retrieve_context(vectorstore, query)

    initial_state: VerificationState = {
        "query": query,
        "context": context,
        "answer": "",
        "consistency_samples": [],
        "consistency_score": 0.0,
        "grounding_score": 0.0,
        "is_grounded": False,
        "is_consistent": False,
        "retry_count": 0,
        "needs_human_approval": False,
        "human_decision": "",
        "final_answer": "",
        "failure_reasons": [],
        "verification_log": []
    }

    workflow = build_verification_graph()
    start_time = time.time()
    result = workflow.invoke(initial_state)
    elapsed = time.time() - start_time

    return {
        "query": query,
        "final_answer": result.get("final_answer", ""),
        "verification_passed": bool(result.get("final_answer")) and not result.get("needs_human_approval"),
        "retry_count": result.get("retry_count", 0),
        "consistency_score": result.get("consistency_score", 0),
        "grounding_score": result.get("grounding_score", 0),
        "human_decision": result.get("human_decision", ""),
        "failure_reasons": result.get("failure_reasons", []),
        "elapsed_seconds": round(elapsed, 2)
    }


def main():
    """메인 실행"""
    print("=" * 60)
    print("10장 실습: 검증 워크플로우")
    print("=" * 60)

    # 문서 로드 및 벡터스토어 생성
    print("\n[1] 문서 로드 중...")
    documents = load_documents()
    print(f"    - 로드된 문서: {len(documents)}개")

    print("\n[2] 벡터스토어 생성 중...")
    vectorstore = create_vectorstore(documents)
    print("    - 벡터스토어 생성 완료")

    # 테스트 질문
    questions = [
        "asyncio에서 이벤트 루프의 역할은 무엇인가요?",
        "코루틴과 태스크의 차이점은 무엇인가요?",
        "asyncio.gather()와 asyncio.wait()는 어떻게 다른가요?"
    ]

    print("\n[3] 검증 워크플로우 실행 중...")
    results = []
    failure_log = []

    for i, query in enumerate(questions, 1):
        print(f"\n질문 {i}: {query}")
        result = run_verification(query, vectorstore)
        results.append(result)

        print(f"    - 최종 답변: {result['final_answer'][:50]}...")
        print(f"    - 검증 통과: {result['verification_passed']}")
        print(f"    - 재시도 횟수: {result['retry_count']}")
        print(f"    - 일관성 점수: {result['consistency_score']:.2f}")
        print(f"    - 출처 점수: {result['grounding_score']:.2f}")
        print(f"    - 소요 시간: {result['elapsed_seconds']}초")

        if result['failure_reasons']:
            failure_log.append({
                "query": query,
                "reasons": result['failure_reasons'],
                "final_outcome": "approved" if result['verification_passed'] or result.get('human_decision') == 'approved' else "rejected"
            })

    # 결과 저장
    verification_result = {
        "executed_at": datetime.now().isoformat(),
        "config": {
            "max_retries": MAX_RETRIES,
            "consistency_threshold": CONSISTENCY_THRESHOLD,
            "grounding_threshold": GROUNDING_THRESHOLD
        },
        "summary": {
            "total_questions": len(questions),
            "passed": sum(1 for r in results if r['verification_passed']),
            "failed": sum(1 for r in results if not r['verification_passed']),
            "avg_consistency_score": round(sum(r['consistency_score'] for r in results) / len(results), 3),
            "avg_grounding_score": round(sum(r['grounding_score'] for r in results) / len(results), 3),
            "total_retries": sum(r['retry_count'] for r in results)
        },
        "results": results
    }

    result_path = OUTPUT_DIR / "ch10_verification_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(verification_result, f, ensure_ascii=False, indent=2)
    print(f"\n[4] 검증 결과 저장: {result_path}")

    # 실패 로그 저장
    failure_log_data = {
        "executed_at": datetime.now().isoformat(),
        "failures": failure_log
    }
    failure_path = OUTPUT_DIR / "ch10_failure_log.json"
    with open(failure_path, "w", encoding="utf-8") as f:
        json.dump(failure_log_data, f, ensure_ascii=False, indent=2)
    print(f"    실패 로그 저장: {failure_path}")

    # 요약 출력
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    print(f"총 질문: {verification_result['summary']['total_questions']}개")
    print(f"통과: {verification_result['summary']['passed']}개")
    print(f"실패: {verification_result['summary']['failed']}개")
    print(f"평균 일관성 점수: {verification_result['summary']['avg_consistency_score']:.3f}")
    print(f"평균 출처 점수: {verification_result['summary']['avg_grounding_score']:.3f}")
    print(f"총 재시도 횟수: {verification_result['summary']['total_retries']}회")

    return verification_result


if __name__ == "__main__":
    main()
