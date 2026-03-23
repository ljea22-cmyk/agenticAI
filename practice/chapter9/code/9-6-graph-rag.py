#!/usr/bin/env python3
"""
제9장 실습: 그래프 기반 RAG 구현

이 스크립트는 LLM을 사용하여 문서에서 엔티티와 관계를 추출하고,
지식 그래프를 구축하여 검색에 활용하는 간소화된 GraphRAG를 구현한다.

실행 방법:
    cd practice/chapter9
    python3 -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    python3 code/9-6-graph-rag.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import networkx as nx
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
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
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def get_llm() -> ChatOpenAI:
    """OpenAI LLM 인스턴스를 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)


def get_embeddings() -> OpenAIEmbeddings:
    """OpenAI 임베딩 인스턴스를 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return OpenAIEmbeddings(api_key=api_key)


# ============================================================
# 문서 로드
# ============================================================

def load_documents() -> list:
    """문서를 로드한다."""
    loader = DirectoryLoader(
        str(INPUT_DIR),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    return loader.load()


# ============================================================
# 지식 그래프 추출
# ============================================================

def extract_entities_and_relations(text: str, llm: ChatOpenAI) -> dict:
    """텍스트에서 엔티티와 관계를 추출한다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """텍스트에서 엔티티(개념, 함수, 모듈 등)와 그들 간의 관계를 추출하세요.

JSON 형식으로 응답하세요:
{{
    "entities": [
        {{"name": "엔티티명", "type": "타입(함수/모듈/개념/키워드)"}}
    ],
    "relations": [
        {{"source": "엔티티1", "relation": "관계", "target": "엔티티2"}}
    ]
}}

관계 유형 예시: "사용한다", "포함한다", "대체한다", "반환한다", "호출한다" """),
        ("human", "{text}")
    ])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"text": text})

    try:
        # JSON 블록 추출
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response

        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return {"entities": [], "relations": []}


def build_knowledge_graph(documents: list, llm: ChatOpenAI) -> tuple[nx.DiGraph, dict]:
    """문서에서 지식 그래프를 구축한다."""
    print("\n[1] 지식 그래프 구축 중...")

    graph = nx.DiGraph()
    all_entities = []
    all_relations = []
    entity_sources = {}  # 엔티티가 등장한 문서 추적

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    for doc in documents:
        source_name = Path(doc.metadata.get("source", "unknown")).name
        chunks = splitter.split_text(doc.page_content)

        for chunk in chunks:
            result = extract_entities_and_relations(chunk, llm)

            for entity in result.get("entities", []):
                name = entity["name"]
                if name not in [e["name"] for e in all_entities]:
                    all_entities.append(entity)
                    graph.add_node(name, type=entity.get("type", "unknown"))

                if name not in entity_sources:
                    entity_sources[name] = []
                if source_name not in entity_sources[name]:
                    entity_sources[name].append(source_name)

            for rel in result.get("relations", []):
                source = rel["source"]
                target = rel["target"]
                relation = rel["relation"]

                if not graph.has_node(source):
                    graph.add_node(source, type="unknown")
                if not graph.has_node(target):
                    graph.add_node(target, type="unknown")

                graph.add_edge(source, target, relation=relation)
                all_relations.append(rel)

    print(f"    추출된 엔티티: {len(all_entities)}개")
    print(f"    추출된 관계: {len(all_relations)}개")

    kg_data = {
        "entities": all_entities,
        "relations": all_relations,
        "entity_sources": entity_sources
    }

    return graph, kg_data


# ============================================================
# 그래프 기반 검색
# ============================================================

def find_relevant_entities(query: str, graph: nx.DiGraph, llm: ChatOpenAI) -> list[str]:
    """쿼리와 관련된 엔티티를 찾는다."""
    entities = list(graph.nodes())

    prompt = ChatPromptTemplate.from_messages([
        ("system", """질문과 가장 관련 있는 엔티티를 선택하세요.
엔티티 목록: {entities}

쉼표로 구분된 엔티티 이름만 반환하세요. 최대 5개까지 선택하세요."""),
        ("human", "{query}")
    ])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"entities": ", ".join(entities), "query": query})

    selected = [e.strip() for e in response.split(",") if e.strip() in entities]
    return selected[:5]


def get_subgraph_context(graph: nx.DiGraph, entities: list[str], kg_data: dict) -> str:
    """선택된 엔티티와 연결된 서브그래프 컨텍스트를 생성한다."""
    context_parts = []

    for entity in entities:
        if not graph.has_node(entity):
            continue

        # 엔티티 정보
        node_type = graph.nodes[entity].get("type", "unknown")
        sources = kg_data["entity_sources"].get(entity, [])
        context_parts.append(f"[엔티티: {entity} (타입: {node_type}, 출처: {', '.join(sources)})]")

        # 나가는 관계
        for _, target, data in graph.out_edges(entity, data=True):
            relation = data.get("relation", "관련됨")
            context_parts.append(f"  → {entity} --({relation})--> {target}")

        # 들어오는 관계
        for source, _, data in graph.in_edges(entity, data=True):
            relation = data.get("relation", "관련됨")
            context_parts.append(f"  ← {source} --({relation})--> {entity}")

    return "\n".join(context_parts)


def graph_rag_query(
    query: str,
    graph: nx.DiGraph,
    kg_data: dict,
    documents: list,
    llm: ChatOpenAI
) -> dict:
    """그래프 기반 RAG 쿼리를 실행한다."""
    start_time = time.time()

    # 1. 관련 엔티티 찾기
    relevant_entities = find_relevant_entities(query, graph, llm)

    # 2. 서브그래프 컨텍스트 생성
    graph_context = get_subgraph_context(graph, relevant_entities, kg_data)

    # 3. 관련 문서 텍스트 수집
    relevant_sources = set()
    for entity in relevant_entities:
        sources = kg_data["entity_sources"].get(entity, [])
        relevant_sources.update(sources)

    doc_context = ""
    for doc in documents:
        source_name = Path(doc.metadata.get("source", "unknown")).name
        if source_name in relevant_sources:
            doc_context += f"\n[{source_name}]\n{doc.page_content[:500]}...\n"

    # 4. 답변 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 Python asyncio 전문가입니다.
지식 그래프 정보와 문서 컨텍스트를 바탕으로 질문에 답변하세요.

지식 그래프 관계:
{graph_context}

관련 문서:
{doc_context}

답변에 사용한 엔티티와 출처를 명시하세요."""),
        ("human", "{query}")
    ])

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({
        "graph_context": graph_context,
        "doc_context": doc_context,
        "query": query
    })

    elapsed = time.time() - start_time

    return {
        "query": query,
        "answer": answer,
        "relevant_entities": relevant_entities,
        "sources": list(relevant_sources),
        "elapsed_seconds": round(elapsed, 2)
    }


# ============================================================
# 메인 실행
# ============================================================

def run_graph_rag(questions: list[str]) -> dict:
    """그래프 기반 RAG를 실행한다."""
    print("\n" + "=" * 60)
    print("그래프 기반 RAG 시스템")
    print("=" * 60)

    start_time = time.time()
    llm = get_llm()

    # 문서 로드
    documents = load_documents()
    print(f"\n로드된 문서: {len(documents)}개")

    # 지식 그래프 구축
    graph, kg_data = build_knowledge_graph(documents, llm)

    # 지식 그래프 저장
    kg_file = OUTPUT_DIR / "ch09_knowledge_graph.json"
    with open(kg_file, "w", encoding="utf-8") as f:
        json.dump(kg_data, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] 지식 그래프: {kg_file}")

    # Q&A 실행
    print("\n[2] 질문 처리 중...")
    print("-" * 60)

    results = {
        "approach": "graph_rag",
        "questions": [],
        "kg_stats": {
            "entities": len(kg_data["entities"]),
            "relations": len(kg_data["relations"])
        },
        "executed_at": datetime.now().isoformat()
    }

    for query in questions:
        print(f"\n질문: {query}")

        result = graph_rag_query(query, graph, kg_data, documents, llm)

        print(f"\n답변:\n{result['answer'][:300]}...")
        print(f"\n관련 엔티티: {', '.join(result['relevant_entities'])}")
        print(f"(소요 시간: {result['elapsed_seconds']}초)")
        print("-" * 60)

        results["questions"].append(result)

    elapsed = time.time() - start_time
    results["total_elapsed_seconds"] = round(elapsed, 2)
    results["success"] = True

    # 결과 저장
    result_file = OUTPUT_DIR / "ch09_graph_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] 그래프 RAG 결과: {result_file}")

    print(f"\n{'=' * 60}")
    print(f"완료! 총 소요 시간: {elapsed:.2f}초")
    print(f"{'=' * 60}")

    return results


def main():
    """메인 실행 함수"""
    questions = [
        "asyncio.gather()와 asyncio.wait()의 관계는 무엇인가요?",
        "코루틴과 태스크는 어떤 관계가 있나요?",
        "비동기 프로그래밍에서 이벤트 루프의 역할은 무엇인가요?"
    ]

    results = run_graph_rag(questions)
    return results.get("success", False)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
