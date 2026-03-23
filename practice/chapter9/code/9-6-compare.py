#!/usr/bin/env python3
"""
제9장 실습: 벡터 RAG vs 그래프 RAG 비교

이 스크립트는 동일한 질문에 대해 벡터 RAG와 그래프 RAG의
결과를 비교 분석한다.

실행 방법:
    cd practice/chapter9
    source venv/bin/activate
    python3 code/9-6-compare.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# 설정
# ============================================================

load_dotenv(Path(__file__).parent / ".env")

CHAPTER_DIR = Path(__file__).parent.parent
INPUT_DIR = CHAPTER_DIR / "data" / "input" / "docs"
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"
CHROMA_DIR = CHAPTER_DIR / "data" / "chroma_db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)


def get_embeddings() -> OpenAIEmbeddings:
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAIEmbeddings(api_key=api_key)


# ============================================================
# 벡터 RAG
# ============================================================

def run_vector_rag(questions: list[str]) -> dict:
    """벡터 RAG를 실행한다."""
    print("\n[벡터 RAG] 시작...")

    start_time = time.time()

    # 문서 로드
    loader = DirectoryLoader(
        str(INPUT_DIR), glob="**/*.txt",
        loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()

    # 청킹
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # 벡터 저장소
    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="ch09_vector"
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # RAG 체인
    prompt = ChatPromptTemplate.from_messages([
        ("system", """컨텍스트를 바탕으로 질문에 답변하세요.

컨텍스트:
{context}"""),
        ("human", "{question}")
    ])

    llm = get_llm()

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )

    # 질문 처리
    results = {"approach": "vector_rag", "questions": []}

    for query in questions:
        q_start = time.time()
        answer = chain.invoke(query)
        q_elapsed = time.time() - q_start

        results["questions"].append({
            "query": query,
            "answer": answer,
            "elapsed_seconds": round(q_elapsed, 2)
        })

    elapsed = time.time() - start_time
    results["total_elapsed_seconds"] = round(elapsed, 2)
    results["chunk_count"] = len(chunks)

    print(f"[벡터 RAG] 완료 ({elapsed:.2f}초)")

    return results


# ============================================================
# 비교 분석
# ============================================================

def compare_results(vector_results: dict, graph_results: dict) -> dict:
    """두 결과를 비교 분석한다."""
    comparison = {
        "summary": {
            "vector_rag": {
                "total_time": vector_results["total_elapsed_seconds"],
                "chunk_count": vector_results.get("chunk_count", 0)
            },
            "graph_rag": {
                "total_time": graph_results["total_elapsed_seconds"],
                "entity_count": graph_results["kg_stats"]["entities"],
                "relation_count": graph_results["kg_stats"]["relations"]
            }
        },
        "questions": [],
        "analysis": ""
    }

    for v_q, g_q in zip(vector_results["questions"], graph_results["questions"]):
        comparison["questions"].append({
            "query": v_q["query"],
            "vector_time": v_q["elapsed_seconds"],
            "graph_time": g_q["elapsed_seconds"],
            "graph_entities": g_q.get("relevant_entities", [])
        })

    # 분석 텍스트
    v_time = vector_results["total_elapsed_seconds"]
    g_time = graph_results["total_elapsed_seconds"]
    time_ratio = round(g_time / v_time, 2) if v_time > 0 else 0

    analysis = []
    analysis.append(f"그래프 RAG는 벡터 RAG 대비 {time_ratio}배의 시간이 소요되었다.")
    analysis.append(f"그래프 RAG는 {graph_results['kg_stats']['entities']}개의 엔티티와 "
                   f"{graph_results['kg_stats']['relations']}개의 관계를 추출했다.")
    analysis.append("그래프 RAG는 엔티티 간 관계를 명시적으로 활용하여 "
                   "관계 기반 질문에 더 정확한 답변을 제공한다.")

    comparison["analysis"] = " ".join(analysis)

    return comparison


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("벡터 RAG vs 그래프 RAG 비교")
    print("=" * 60)

    questions = [
        "asyncio.gather()와 asyncio.wait()의 관계는 무엇인가요?",
        "코루틴과 태스크는 어떤 관계가 있나요?",
        "비동기 프로그래밍에서 이벤트 루프의 역할은 무엇인가요?"
    ]

    # 벡터 RAG 실행
    vector_results = run_vector_rag(questions)

    # 그래프 RAG 결과 로드
    graph_file = OUTPUT_DIR / "ch09_graph_result.json"
    if graph_file.exists():
        with open(graph_file, encoding="utf-8") as f:
            graph_results = json.load(f)
    else:
        print("\n[경고] 그래프 RAG 결과가 없습니다. 먼저 9-6-graph-rag.py를 실행하세요.")
        return False

    # 벡터 RAG 결과 저장
    vector_file = OUTPUT_DIR / "ch09_vector_result.json"
    with open(vector_file, "w", encoding="utf-8") as f:
        json.dump(vector_results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] 벡터 RAG 결과: {vector_file}")

    # 비교 분석
    comparison = compare_results(vector_results, graph_results)

    # 결과 출력
    print("\n" + "=" * 60)
    print("비교 결과")
    print("=" * 60)
    print(f"\n[벡터 RAG]")
    print(f"  총 시간: {comparison['summary']['vector_rag']['total_time']}초")
    print(f"  청크 수: {comparison['summary']['vector_rag']['chunk_count']}")

    print(f"\n[그래프 RAG]")
    print(f"  총 시간: {comparison['summary']['graph_rag']['total_time']}초")
    print(f"  엔티티 수: {comparison['summary']['graph_rag']['entity_count']}")
    print(f"  관계 수: {comparison['summary']['graph_rag']['relation_count']}")

    print(f"\n[질문별 비교]")
    for q in comparison["questions"]:
        print(f"  Q: {q['query'][:40]}...")
        print(f"     벡터: {q['vector_time']}초, 그래프: {q['graph_time']}초")
        if q.get("graph_entities"):
            print(f"     관련 엔티티: {', '.join(q['graph_entities'][:3])}")

    print(f"\n[분석] {comparison['analysis']}")

    # 비교 결과 저장
    comp_file = OUTPUT_DIR / "ch09_comparison.json"
    with open(comp_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] 비교 결과: {comp_file}")

    print("\n" + "=" * 60)

    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
