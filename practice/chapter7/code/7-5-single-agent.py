#!/usr/bin/env python3
"""
제7장 실습: 단일 에이전트로 기술 문서 작성

이 스크립트는 단일 에이전트가 기술 문서를 작성하는 과정을 구현한다.
하나의 LLM 호출로 조사, 작성, 검토를 모두 수행한다.

실행 방법:
    cd practice/chapter7
    python3 -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    python3 code/7-5-single-agent.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

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
# 단일 에이전트 구현
# ============================================================

def single_agent_write_document(topic: str) -> dict:
    """단일 에이전트가 기술 문서를 작성한다.

    Args:
        topic: 문서 주제

    Returns:
        실행 결과 (문서 내용, 메트릭스 등)
    """
    print(f"\n{'='*60}")
    print("단일 에이전트: 기술 문서 작성 시작")
    print(f"주제: {topic}")
    print(f"{'='*60}\n")

    start_time = time.time()
    api_calls = 0

    try:
        llm = get_llm()

        # 단일 프롬프트로 모든 작업 수행
        prompt = f"""당신은 기술 문서 작성 전문가입니다. 다음 주제에 대한 기술 문서를 작성하세요.

주제: {topic}

문서 요구사항:
1. 개념 설명 섹션 (핵심 개념과 원리)
2. 코드 예시 섹션 (실제 사용 가능한 Python 코드)
3. 모범 사례 섹션 (권장 사항과 주의점)

각 섹션은 2-3개의 문단으로 구성하고, 코드 예시는 주석과 함께 작성하세요.
전체 문서는 한국어로 작성하세요.

문서:"""

        print("[단일 에이전트] 문서 생성 중...")
        response = llm.invoke(prompt)
        api_calls += 1

        document = response.content.strip()
        elapsed_time = time.time() - start_time

        print(f"[단일 에이전트] 완료 (소요 시간: {elapsed_time:.2f}초)")

        # 결과 저장
        result = {
            "approach": "single_agent",
            "topic": topic,
            "document": document,
            "metrics": {
                "api_calls": api_calls,
                "elapsed_seconds": round(elapsed_time, 2),
                "document_length": len(document)
            },
            "executed_at": datetime.now().isoformat(),
            "success": True
        }

        # 문서 파일 저장
        doc_file = OUTPUT_DIR / "ch07_document_single.txt"
        doc_file.write_text(document, encoding="utf-8")
        print(f"[단일 에이전트] 문서 저장: {doc_file}")

        # 결과 JSON 저장
        result_file = OUTPUT_DIR / "ch07_single_result.json"
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[단일 에이전트] 결과 저장: {result_file}")

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[단일 에이전트] 오류: {e}")

        result = {
            "approach": "single_agent",
            "topic": topic,
            "document": "",
            "metrics": {
                "api_calls": api_calls,
                "elapsed_seconds": round(elapsed_time, 2),
                "document_length": 0
            },
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }

        result_file = OUTPUT_DIR / "ch07_single_result.json"
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

    result = single_agent_write_document(topic)

    print(f"\n{'='*60}")
    print("실행 결과 요약")
    print(f"{'='*60}")
    print(f"  성공: {result['success']}")
    print(f"  API 호출 수: {result['metrics']['api_calls']}")
    print(f"  소요 시간: {result['metrics']['elapsed_seconds']}초")
    print(f"  문서 길이: {result['metrics']['document_length']}자")
    print(f"{'='*60}\n")

    return result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
