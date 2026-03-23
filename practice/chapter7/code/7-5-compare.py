#!/usr/bin/env python3
"""
제7장 실습: 단일 에이전트 vs 멀티에이전트 비교 분석

이 스크립트는 두 접근법의 결과를 비교 분석한다.

실행 방법:
    cd practice/chapter7
    source venv/bin/activate
    python3 code/7-5-compare.py
"""

import json
from pathlib import Path

CHAPTER_DIR = Path(__file__).parent.parent
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"


def load_results() -> tuple[dict, dict]:
    """단일/멀티 에이전트 결과를 로드한다."""
    single_file = OUTPUT_DIR / "ch07_single_result.json"
    multi_file = OUTPUT_DIR / "ch07_multi_result.json"

    with open(single_file, encoding="utf-8") as f:
        single_result = json.load(f)

    with open(multi_file, encoding="utf-8") as f:
        multi_result = json.load(f)

    return single_result, multi_result


def compare_results(single: dict, multi: dict) -> dict:
    """두 결과를 비교 분석한다."""
    comparison = {
        "topic": single["topic"],
        "single_agent": {
            "api_calls": single["metrics"]["api_calls"],
            "elapsed_seconds": single["metrics"]["elapsed_seconds"],
            "document_length": single["metrics"]["document_length"],
            "success": single["success"]
        },
        "multi_agent": {
            "api_calls": multi["metrics"]["api_calls"],
            "revision_count": multi["metrics"].get("revision_count", 0),
            "elapsed_seconds": multi["metrics"]["elapsed_seconds"],
            "document_length": multi["metrics"]["document_length"],
            "success": multi["success"]
        },
        "comparison": {
            "api_calls_ratio": round(
                multi["metrics"]["api_calls"] / single["metrics"]["api_calls"],
                2
            ),
            "time_ratio": round(
                multi["metrics"]["elapsed_seconds"] / single["metrics"]["elapsed_seconds"],
                2
            ),
            "length_difference": (
                multi["metrics"]["document_length"] - single["metrics"]["document_length"]
            )
        },
        "analysis": ""
    }

    # 분석 결과 작성
    api_ratio = comparison["comparison"]["api_calls_ratio"]
    time_ratio = comparison["comparison"]["time_ratio"]
    len_diff = comparison["comparison"]["length_difference"]

    analysis = []
    analysis.append(f"멀티에이전트는 단일 에이전트 대비 API를 {api_ratio}배 호출했다.")
    analysis.append(f"실행 시간은 {time_ratio}배 소요되었다.")

    if len_diff > 0:
        analysis.append(f"멀티에이전트가 {len_diff}자 더 긴 문서를 생성했다.")
    elif len_diff < 0:
        analysis.append(f"단일 에이전트가 {abs(len_diff)}자 더 긴 문서를 생성했다.")
    else:
        analysis.append("두 접근법이 동일한 길이의 문서를 생성했다.")

    comparison["analysis"] = " ".join(analysis)

    return comparison


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("단일 에이전트 vs 멀티에이전트 비교 분석")
    print("=" * 60)

    single, multi = load_results()
    comparison = compare_results(single, multi)

    # 결과 출력
    print(f"\n주제: {comparison['topic']}")
    print("\n[단일 에이전트]")
    print(f"  API 호출: {comparison['single_agent']['api_calls']}회")
    print(f"  소요 시간: {comparison['single_agent']['elapsed_seconds']}초")
    print(f"  문서 길이: {comparison['single_agent']['document_length']}자")

    print("\n[멀티에이전트]")
    print(f"  API 호출: {comparison['multi_agent']['api_calls']}회")
    print(f"  수정 횟수: {comparison['multi_agent']['revision_count']}회")
    print(f"  소요 시간: {comparison['multi_agent']['elapsed_seconds']}초")
    print(f"  문서 길이: {comparison['multi_agent']['document_length']}자")

    print("\n[비교 분석]")
    print(f"  API 호출 비율: {comparison['comparison']['api_calls_ratio']}배")
    print(f"  시간 비율: {comparison['comparison']['time_ratio']}배")
    print(f"  길이 차이: {comparison['comparison']['length_difference']}자")
    print(f"\n결론: {comparison['analysis']}")

    # 결과 저장
    result_file = OUTPUT_DIR / "ch07_comparison.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    print(f"\n비교 결과 저장: {result_file}")

    print("=" * 60)


if __name__ == "__main__":
    main()
