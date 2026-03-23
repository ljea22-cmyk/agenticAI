#!/usr/bin/env python3
"""
제6장 실습: LangGraph로 초안 생성 → 검증 → 수정 워크플로우 구현

이 스크립트는 LangGraph를 사용하여 순환 워크플로우를 구현한다.
1. 초안 생성 (generate_draft)
2. 검증 (validate)
3. 수정 (revise) - 최대 3회 반복

실행 방법:
    cd practice/chapter6
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\\Scripts\\activate
    pip install -r code/requirements.txt
    cp code/.env.example code/.env  # OPENAI_API_KEY 설정
    python3 code/6-6-langgraph-workflow.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from operator import add
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# ============================================================
# 설정
# ============================================================

# 환경 변수 로드
load_dotenv(Path(__file__).parent / ".env")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 출력 디렉토리
CHAPTER_DIR = Path(__file__).parent.parent
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 최대 수정 횟수
MAX_REVISIONS = 3


# ============================================================
# 6.2 상태(State) 모델링
# ============================================================

class WorkflowState(TypedDict):
    """워크플로우 상태 정의

    Attributes:
        topic: 작성할 주제
        draft: 현재 초안
        feedback: 검증 피드백 목록 (누적)
        revision_count: 수정 횟수
        is_valid: 검증 통과 여부
        error: 에러 메시지 (있는 경우)
    """
    topic: str
    draft: str
    feedback: Annotated[list[str], add]  # 피드백 누적
    revision_count: int
    is_valid: bool
    error: str | None


# ============================================================
# LLM 초기화
# ============================================================

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
# 노드 함수 정의
# ============================================================

def generate_draft(state: WorkflowState) -> dict:
    """초안을 생성한다.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        업데이트된 상태 (draft, revision_count)
    """
    logger.info(f"[generate_draft] 주제: {state['topic']}")

    try:
        llm = get_llm()

        prompt = f"""다음 주제에 대해 간결하고 명확한 글을 작성하세요.

주제: {state['topic']}

요구사항:
1. 3-5문단으로 구성
2. 각 문단은 2-3문장
3. 구체적인 예시나 수치 포함
4. 한국어로 작성

글:"""

        response = llm.invoke(prompt)
        draft = response.content.strip()

        # 초안 저장
        draft_file = OUTPUT_DIR / "ch06_draft_v1.txt"
        draft_file.write_text(draft, encoding="utf-8")
        logger.info(f"[generate_draft] 초안 저장: {draft_file}")

        return {
            "draft": draft,
            "revision_count": 0,
            "is_valid": False,
            "error": None
        }

    except Exception as e:
        logger.error(f"[generate_draft] 에러: {e}")
        return {
            "draft": "",
            "error": str(e),
            "is_valid": False
        }


def validate(state: WorkflowState) -> dict:
    """초안을 검증하고 피드백을 생성한다.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        업데이트된 상태 (feedback, is_valid)
    """
    logger.info(f"[validate] 수정 횟수: {state['revision_count']}")

    if state.get("error"):
        return {"is_valid": False, "feedback": ["이전 단계에서 에러 발생"]}

    try:
        llm = get_llm()

        prompt = f"""다음 글을 검증하고 개선점을 제안하세요.

글:
{state['draft']}

검증 기준:
1. 논리적 흐름이 자연스러운가?
2. 구체적인 예시나 수치가 포함되어 있는가?
3. 문법적 오류가 없는가?
4. 주제를 충분히 다루고 있는가?

결과를 다음 형식으로 반환하세요:
통과: [예/아니오]
피드백: [개선이 필요한 점들, 없으면 "없음"]"""

        response = llm.invoke(prompt)
        result = response.content.strip()

        # 결과 파싱
        is_valid = "통과: 예" in result or "통과:예" in result

        # 피드백 추출
        feedback = []
        if "피드백:" in result:
            feedback_text = result.split("피드백:")[-1].strip()
            if feedback_text and feedback_text != "없음":
                feedback = [feedback_text]

        logger.info(f"[validate] 통과: {is_valid}, 피드백: {feedback}")

        return {
            "is_valid": is_valid,
            "feedback": feedback,
            "error": None
        }

    except Exception as e:
        logger.error(f"[validate] 에러: {e}")
        return {
            "is_valid": False,
            "feedback": [f"검증 중 에러: {str(e)}"],
            "error": str(e)
        }


def revise(state: WorkflowState) -> dict:
    """피드백을 반영하여 초안을 수정한다.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        업데이트된 상태 (draft, revision_count)
    """
    revision_num = state["revision_count"] + 1
    logger.info(f"[revise] 수정 #{revision_num}")

    try:
        llm = get_llm()

        # 최근 피드백 가져오기
        recent_feedback = state["feedback"][-1] if state["feedback"] else "없음"

        prompt = f"""다음 글을 피드백을 반영하여 수정하세요.

원본 글:
{state['draft']}

피드백:
{recent_feedback}

수정된 글:"""

        response = llm.invoke(prompt)
        revised_draft = response.content.strip()

        # 수정본 저장
        draft_file = OUTPUT_DIR / f"ch06_draft_v{revision_num + 1}.txt"
        draft_file.write_text(revised_draft, encoding="utf-8")
        logger.info(f"[revise] 수정본 저장: {draft_file}")

        return {
            "draft": revised_draft,
            "revision_count": revision_num,
            "is_valid": False,  # 다시 검증 필요
            "error": None
        }

    except Exception as e:
        logger.error(f"[revise] 에러: {e}")
        return {
            "error": str(e),
            "revision_count": revision_num
        }


# ============================================================
# 6.3 조건 분기 함수
# ============================================================

def should_continue(state: WorkflowState) -> str:
    """검증 결과에 따라 다음 단계를 결정한다.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        다음 노드 이름 ("end" 또는 "revise")
    """
    # 에러가 있으면 종료
    if state.get("error"):
        logger.info("[should_continue] 에러로 인해 종료")
        return "end"

    # 검증 통과하면 종료
    if state["is_valid"]:
        logger.info("[should_continue] 검증 통과 - 종료")
        return "end"

    # 최대 수정 횟수 초과하면 종료
    if state["revision_count"] >= MAX_REVISIONS:
        logger.info(f"[should_continue] 최대 수정 횟수({MAX_REVISIONS}) 도달 - 종료")
        return "end"

    # 피드백이 있으면 수정
    if state["feedback"]:
        logger.info("[should_continue] 수정 필요")
        return "revise"

    return "end"


# ============================================================
# 6.6 워크플로우 구성
# ============================================================

def build_workflow() -> StateGraph:
    """LangGraph 워크플로우를 구성한다.

    Returns:
        컴파일된 StateGraph
    """
    # 그래프 빌더 생성
    builder = StateGraph(WorkflowState)

    # 노드 추가
    builder.add_node("generate_draft", generate_draft)
    builder.add_node("validate", validate)
    builder.add_node("revise", revise)

    # 엣지 추가
    builder.add_edge(START, "generate_draft")
    builder.add_edge("generate_draft", "validate")
    builder.add_edge("revise", "validate")  # 수정 후 다시 검증

    # 조건부 엣지 추가
    builder.add_conditional_edges(
        "validate",
        should_continue,
        {
            "end": END,
            "revise": "revise"
        }
    )

    # 그래프 컴파일
    return builder.compile()


# ============================================================
# 메인 실행
# ============================================================

def main():
    """메인 실행 함수"""

    logger.info("=" * 60)
    logger.info("제6장 실습: LangGraph 워크플로우 시작")
    logger.info("=" * 60)

    # 로그 파일 설정
    log_entries = []

    def log_event(event: str, data: dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        }
        log_entries.append(entry)
        logger.info(f"[{event}] {data}")

    try:
        # 워크플로우 구성
        workflow = build_workflow()

        # 초기 상태
        topic = "인공지능이 소프트웨어 개발에 미치는 영향"
        initial_state: WorkflowState = {
            "topic": topic,
            "draft": "",
            "feedback": [],
            "revision_count": 0,
            "is_valid": False,
            "error": None
        }

        log_event("workflow_start", {"topic": topic})

        # 워크플로우 실행
        final_state = workflow.invoke(initial_state)

        log_event("workflow_end", {
            "revision_count": final_state["revision_count"],
            "is_valid": final_state["is_valid"],
            "has_error": final_state.get("error") is not None
        })

        # 최종 초안 저장
        if final_state["draft"]:
            final_file = OUTPUT_DIR / "ch06_draft_final.txt"
            final_file.write_text(final_state["draft"], encoding="utf-8")
            logger.info(f"최종 초안 저장: {final_file}")

        # 결과 요약 저장
        result = {
            "topic": topic,
            "revision_count": final_state["revision_count"],
            "is_valid": final_state["is_valid"],
            "feedback_history": final_state["feedback"],
            "error": final_state.get("error"),
            "executed_at": datetime.now().isoformat(),
            "success": final_state.get("error") is None
        }

        result_file = OUTPUT_DIR / "ch06_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"결과 저장: {result_file}")

        # 로그 저장
        log_file = OUTPUT_DIR / "ch06_workflow_log.txt"
        log_text = "\n".join([
            f"[{entry['timestamp']}] {entry['event']}: {json.dumps(entry['data'], ensure_ascii=False)}"
            for entry in log_entries
        ])
        log_file.write_text(log_text, encoding="utf-8")
        logger.info(f"로그 저장: {log_file}")

        # 결과 출력
        logger.info("=" * 60)
        logger.info("워크플로우 완료")
        logger.info(f"  수정 횟수: {final_state['revision_count']}")
        logger.info(f"  검증 통과: {final_state['is_valid']}")
        logger.info(f"  피드백 수: {len(final_state['feedback'])}")
        logger.info("=" * 60)

        return True

    except ValueError as e:
        logger.error(f"설정 오류: {e}")

        # 에러 결과 저장
        result = {
            "topic": "인공지능이 소프트웨어 개발에 미치는 영향",
            "error": str(e),
            "executed_at": datetime.now().isoformat(),
            "success": False
        }
        result_file = OUTPUT_DIR / "ch06_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return False

    except Exception as e:
        logger.error(f"실행 오류: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
