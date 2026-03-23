#!/usr/bin/env python3
"""
제7장 실습: 멀티에이전트로 기술 문서 작성

이 스크립트는 세 에이전트(연구자, 작성자, 검토자)가 협력하여
기술 문서를 작성하는 과정을 LangGraph로 구현한다.

실행 방법:
    cd practice/chapter7
    python3 -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    python3 code/7-5-multi-agent.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from operator import add
from typing_extensions import TypedDict

# ============================================================
# 설정
# ============================================================

load_dotenv(Path(__file__).parent / ".env")

CHAPTER_DIR = Path(__file__).parent.parent
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_llm() -> ChatOpenAI:
    """OpenAI LLM 인스턴스를 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=api_key
    )


# ============================================================
# 상태 정의
# ============================================================

class DocumentState(TypedDict):
    """멀티에이전트 워크플로우 상태"""
    topic: str
    research: str
    draft: str
    feedback: Annotated[list[str], add]
    final_document: str
    revision_count: int
    is_approved: bool
    api_calls: int


# ============================================================
# 에이전트 노드 정의
# ============================================================

def researcher_node(state: DocumentState) -> dict:
    """연구자 에이전트: 주제를 조사하고 핵심 정보를 수집한다."""
    print(f"\n[연구자] 주제 조사 시작: {state['topic']}")

    llm = get_llm()

    prompt = f"""당신은 기술 분야 연구 전문가입니다. 다음 주제에 대해 조사하고 핵심 정보를 정리하세요.

주제: {state['topic']}

다음 항목을 포함하세요:
1. 핵심 개념 정의
2. 주요 특징 및 장점
3. 실무에서의 활용 사례
4. 관련 기술 및 라이브러리

조사 결과를 구조화된 형태로 작성하세요."""

    response = llm.invoke(prompt)
    research = response.content.strip()

    print(f"[연구자] 조사 완료 ({len(research)}자)")

    return {
        "research": research,
        "api_calls": state["api_calls"] + 1
    }


def writer_node(state: DocumentState) -> dict:
    """작성자 에이전트: 연구 결과를 바탕으로 문서를 작성한다."""
    print(f"\n[작성자] 문서 작성 시작 (수정 횟수: {state['revision_count']})")

    llm = get_llm()

    # 피드백이 있으면 수정 요청
    if state["feedback"]:
        feedback_text = "\n".join(f"- {fb}" for fb in state["feedback"])
        prompt = f"""당신은 기술 문서 작성 전문가입니다.
검토자의 피드백을 반영하여 문서를 수정하세요.

원본 문서:
{state['draft']}

피드백:
{feedback_text}

피드백을 반영하여 개선된 문서를 작성하세요. 전체 문서를 다시 작성하세요."""
    else:
        prompt = f"""당신은 기술 문서 작성 전문가입니다.
연구자가 조사한 내용을 바탕으로 기술 문서를 작성하세요.

연구 내용:
{state['research']}

문서 요구사항:
1. 개념 설명 섹션 (핵심 개념과 원리)
2. 코드 예시 섹션 (실제 사용 가능한 Python 코드)
3. 모범 사례 섹션 (권장 사항과 주의점)

각 섹션은 2-3개의 문단으로 구성하고, 코드 예시는 주석과 함께 작성하세요.
전체 문서는 한국어로 작성하세요."""

    response = llm.invoke(prompt)
    draft = response.content.strip()

    print(f"[작성자] 문서 작성 완료 ({len(draft)}자)")

    return {
        "draft": draft,
        "revision_count": state["revision_count"] + 1,
        "api_calls": state["api_calls"] + 1
    }


def reviewer_node(state: DocumentState) -> dict:
    """검토자 에이전트: 문서를 검토하고 피드백을 제공한다."""
    print(f"\n[검토자] 문서 검토 시작")

    llm = get_llm()

    prompt = f"""당신은 기술 문서 품질 검토 전문가입니다.
다음 문서를 검토하고 품질을 평가하세요.

문서:
{state['draft']}

평가 기준:
1. 기술적 정확성
2. 설명의 명확성
3. 코드 예시의 실용성
4. 구조의 논리성

JSON 형식으로 응답하세요:
{{
    "is_approved": true/false,
    "feedback": ["피드백1", "피드백2"] (승인 시 빈 배열)
}}

문서가 충분히 좋으면 is_approved를 true로 설정하세요.
수정이 필요하면 구체적인 피드백을 제공하세요."""

    response = llm.invoke(prompt)
    content = response.content.strip()

    # JSON 파싱
    try:
        # JSON 블록 추출
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content

        result = json.loads(json_str)
        is_approved = result.get("is_approved", False)
        new_feedback = result.get("feedback", [])
    except (json.JSONDecodeError, IndexError):
        # 파싱 실패 시 승인으로 처리
        is_approved = True
        new_feedback = []

    status = "승인" if is_approved else f"수정 요청 ({len(new_feedback)}개 피드백)"
    print(f"[검토자] 검토 완료: {status}")

    return {
        "is_approved": is_approved,
        "feedback": new_feedback,
        "api_calls": state["api_calls"] + 1
    }


def finalize_node(state: DocumentState) -> dict:
    """최종 문서를 확정한다."""
    print(f"\n[완료] 문서 확정")
    return {
        "final_document": state["draft"]
    }


# ============================================================
# 조건부 엣지
# ============================================================

def should_continue(state: DocumentState) -> str:
    """검토 결과에 따라 다음 단계를 결정한다."""
    if state["is_approved"]:
        return "finalize"
    elif state["revision_count"] >= 3:
        print("[워크플로우] 최대 수정 횟수 도달, 강제 완료")
        return "finalize"
    else:
        return "writer"


# ============================================================
# 워크플로우 구성
# ============================================================

def build_multi_agent_workflow() -> StateGraph:
    """멀티에이전트 워크플로우를 구성한다."""
    workflow = StateGraph(DocumentState)

    # 노드 추가
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("finalize", finalize_node)

    # 엣지 정의
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "reviewer")
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "writer": "writer",
            "finalize": "finalize"
        }
    )
    workflow.add_edge("finalize", END)

    return workflow.compile()


# ============================================================
# 멀티에이전트 실행
# ============================================================

def multi_agent_write_document(topic: str) -> dict:
    """멀티에이전트가 협력하여 기술 문서를 작성한다.

    Args:
        topic: 문서 주제

    Returns:
        실행 결과 (문서 내용, 메트릭스 등)
    """
    print(f"\n{'='*60}")
    print("멀티에이전트: 기술 문서 작성 시작")
    print(f"주제: {topic}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # 워크플로우 구성 및 실행
        app = build_multi_agent_workflow()

        initial_state = {
            "topic": topic,
            "research": "",
            "draft": "",
            "feedback": [],
            "final_document": "",
            "revision_count": 0,
            "is_approved": False,
            "api_calls": 0
        }

        # 워크플로우 실행
        final_state = app.invoke(initial_state)

        elapsed_time = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"[멀티에이전트] 완료")
        print(f"  - 총 API 호출: {final_state['api_calls']}회")
        print(f"  - 수정 횟수: {final_state['revision_count']}회")
        print(f"  - 소요 시간: {elapsed_time:.2f}초")
        print(f"{'='*60}")

        document = final_state["final_document"]

        # 결과 저장
        result = {
            "approach": "multi_agent",
            "topic": topic,
            "document": document,
            "metrics": {
                "api_calls": final_state["api_calls"],
                "revision_count": final_state["revision_count"],
                "elapsed_seconds": round(elapsed_time, 2),
                "document_length": len(document)
            },
            "executed_at": datetime.now().isoformat(),
            "success": True
        }

        # 문서 파일 저장
        doc_file = OUTPUT_DIR / "ch07_document_multi.txt"
        doc_file.write_text(document, encoding="utf-8")
        print(f"[멀티에이전트] 문서 저장: {doc_file}")

        # 결과 JSON 저장
        result_file = OUTPUT_DIR / "ch07_multi_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[멀티에이전트] 결과 저장: {result_file}")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[멀티에이전트] 오류: {e}")

        result = {
            "approach": "multi_agent",
            "topic": topic,
            "document": "",
            "metrics": {
                "api_calls": 0,
                "revision_count": 0,
                "elapsed_seconds": round(elapsed_time, 2),
                "document_length": 0
            },
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }

        result_file = OUTPUT_DIR / "ch07_multi_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return result


# ============================================================
# 메인 실행
# ============================================================

def main():
    """메인 실행 함수"""
    topic = "Python 비동기 프로그래밍 (asyncio)"

    result = multi_agent_write_document(topic)

    print(f"\n{'='*60}")
    print("실행 결과 요약")
    print(f"{'='*60}")
    print(f"  성공: {result['success']}")
    print(f"  API 호출 수: {result['metrics']['api_calls']}")
    print(f"  수정 횟수: {result['metrics']['revision_count']}")
    print(f"  소요 시간: {result['metrics']['elapsed_seconds']}초")
    print(f"  문서 길이: {result['metrics']['document_length']}자")
    print(f"{'='*60}\n")

    return result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
