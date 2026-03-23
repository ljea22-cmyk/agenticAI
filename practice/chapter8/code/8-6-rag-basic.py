#!/usr/bin/env python3
"""
제8장 실습: RAG 기본 구현

이 스크립트는 ChromaDB와 LangChain을 사용하여 문서 기반 Q&A 시스템을 구현한다.
문서를 청킹하고, 임베딩하여 저장한 후, 질문에 대해 검색하고 답변을 생성한다.

실행 방법:
    cd practice/chapter8
    python3 -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    python3 code/8-6-rag-basic.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

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


def get_embeddings() -> OpenAIEmbeddings:
    """OpenAI 임베딩 인스턴스를 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return OpenAIEmbeddings(api_key=api_key)


def get_llm() -> ChatOpenAI:
    """OpenAI LLM 인스턴스를 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=api_key
    )


# ============================================================
# 문서 로드 및 청킹
# ============================================================

def load_documents() -> list[Document]:
    """입력 디렉토리에서 문서를 로드한다."""
    print(f"\n[1] 문서 로드 중: {INPUT_DIR}")

    loader = DirectoryLoader(
        str(INPUT_DIR),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()

    print(f"    로드된 문서 수: {len(documents)}")
    for doc in documents:
        filename = Path(doc.metadata.get("source", "unknown")).name
        print(f"    - {filename}: {len(doc.page_content)}자")

    return documents


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> list[Document]:
    """문서를 청크로 분할한다."""
    print(f"\n[2] 문서 청킹 (크기: {chunk_size}, 오버랩: {chunk_overlap})")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    print(f"    생성된 청크 수: {len(chunks)}")

    # 청크에 ID와 소스 정보 추가
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        source_path = chunk.metadata.get("source", "unknown")
        chunk.metadata["source_name"] = Path(source_path).name

    return chunks


# ============================================================
# 벡터 저장소
# ============================================================

def create_vector_store(chunks: list[Document]) -> Chroma:
    """청크를 임베딩하고 벡터 저장소에 저장한다."""
    print(f"\n[3] 벡터 저장소 생성 중...")

    embeddings = get_embeddings()

    # 기존 저장소 삭제 후 새로 생성
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="asyncio_docs"
    )

    print(f"    저장된 벡터 수: {len(chunks)}")
    print(f"    저장 위치: {CHROMA_DIR}")

    return vector_store


def load_vector_store() -> Chroma:
    """기존 벡터 저장소를 로드한다."""
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="asyncio_docs"
    )


# ============================================================
# RAG 체인
# ============================================================

def format_docs_with_sources(docs: list[Document]) -> str:
    """검색된 문서를 출처와 함께 포맷팅한다."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_name", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "?")
        formatted.append(
            f"[출처 {i}: {source}, 청크 {chunk_id}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(formatted)


def create_rag_chain(vector_store: Chroma):
    """RAG 체인을 생성한다."""
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 Python asyncio 전문가입니다.
주어진 컨텍스트를 바탕으로 질문에 답변하세요.

답변 규칙:
1. 컨텍스트에 있는 정보만 사용하세요.
2. 답변 끝에 사용한 출처를 명시하세요.
3. 컨텍스트에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답하세요.

컨텍스트:
{context}"""),
        ("human", "{question}")
    ])

    llm = get_llm()

    chain = (
        {
            "context": retriever | format_docs_with_sources,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


# ============================================================
# 메인 실행
# ============================================================

def run_rag_qa(questions: list[str]) -> dict:
    """RAG Q&A를 실행한다."""
    print("\n" + "=" * 60)
    print("RAG 기반 Q&A 시스템")
    print("=" * 60)

    start_time = time.time()
    results = {
        "questions": [],
        "index_stats": {},
        "executed_at": datetime.now().isoformat()
    }

    try:
        # 1. 문서 로드
        documents = load_documents()

        # 2. 청킹
        chunks = chunk_documents(documents)

        # 3. 벡터 저장소 생성
        vector_store = create_vector_store(chunks)

        # 인덱스 통계 저장
        results["index_stats"] = {
            "total_documents": len(documents),
            "total_chunks": len(chunks),
            "chunk_size": 500,
            "chunk_overlap": 50,
            "embedding_model": "text-embedding-ada-002"
        }

        # 4. RAG 체인 생성
        print("\n[4] RAG 체인 생성 완료")
        chain, retriever = create_rag_chain(vector_store)

        # 5. Q&A 실행
        print("\n[5] 질문 처리 중...")
        print("-" * 60)

        for question in questions:
            print(f"\n질문: {question}")

            q_start = time.time()

            # 검색 및 답변 생성
            retrieved_docs = retriever.invoke(question)
            answer = chain.invoke(question)

            q_elapsed = time.time() - q_start

            print(f"\n답변:\n{answer}")
            print(f"\n(소요 시간: {q_elapsed:.2f}초)")
            print("-" * 60)

            # 결과 저장
            results["questions"].append({
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "source": doc.metadata.get("source_name"),
                        "chunk_id": doc.metadata.get("chunk_id")
                    }
                    for doc in retrieved_docs
                ],
                "elapsed_seconds": round(q_elapsed, 2)
            })

        elapsed_time = time.time() - start_time
        results["total_elapsed_seconds"] = round(elapsed_time, 2)
        results["success"] = True

        # 결과 저장
        save_results(results)

        print(f"\n{'=' * 60}")
        print(f"완료! 총 소요 시간: {elapsed_time:.2f}초")
        print(f"{'=' * 60}")

        return results

    except Exception as e:
        print(f"\n[오류] {e}")
        results["success"] = False
        results["error"] = str(e)
        return results


def save_results(results: dict):
    """결과를 파일로 저장한다."""
    # Q&A 결과 저장
    qa_file = OUTPUT_DIR / "ch08_qa_result.json"
    with open(qa_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] Q&A 결과: {qa_file}")

    # 인덱스 통계 저장
    stats_file = OUTPUT_DIR / "ch08_index_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(results["index_stats"], f, ensure_ascii=False, indent=2)
    print(f"[저장] 인덱스 통계: {stats_file}")

    # 첫 번째 답변 저장
    if results.get("questions"):
        answer_file = OUTPUT_DIR / "ch08_answer.txt"
        first_qa = results["questions"][0]
        content = f"질문: {first_qa['question']}\n\n답변:\n{first_qa['answer']}"
        with open(answer_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[저장] 답변 샘플: {answer_file}")


def main():
    """메인 실행 함수"""
    questions = [
        "asyncio.gather()와 asyncio.wait()의 차이점은 무엇인가요?",
        "비동기 함수에서 블로킹 코드를 피하려면 어떻게 해야 하나요?",
        "코루틴이란 무엇이고 어떻게 정의하나요?"
    ]

    results = run_rag_qa(questions)
    return results.get("success", False)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
