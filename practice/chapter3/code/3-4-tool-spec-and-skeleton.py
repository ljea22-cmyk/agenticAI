from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    errors: list[dict[str, Any]]
    constraints: dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_spec() -> ToolSpec:
    return ToolSpec(
        name="summarize_text",
        description="텍스트를 지정한 길이로 요약합니다(설계 연습용 예시).",
        input_schema={
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "max_chars": {"type": "integer", "minimum": 20, "maximum": 500, "default": 120},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["ok"],
            "properties": {
                "ok": {"type": "boolean"},
                "result": {"type": "object"},
                "error": {"type": "object"},
            },
            "additionalProperties": False,
        },
        errors=[
            {"code": "INVALID_ARGUMENT", "message": "입력 형식이 올바르지 않습니다."},
            {"code": "TOO_LARGE", "message": "입력이 허용 범위를 초과했습니다."},
        ],
        constraints={
            "max_input_chars": 2000,
            "idempotent": True,
            "side_effects": "none",
        },
    )


def validate_request(spec: ToolSpec, request: dict[str, Any]) -> tuple[bool, str]:
    if request.get("tool") != spec.name:
        return False, "tool 이름이 일치하지 않습니다."
    args = request.get("args")
    if not isinstance(args, dict):
        return False, "args는 객체여야 합니다."
    text = args.get("text")
    if not isinstance(text, str) or not text.strip():
        return False, "args.text는 비어있지 않은 문자열이어야 합니다."
    if len(text) > spec.constraints["max_input_chars"]:
        return False, "입력이 허용 범위를 초과했습니다."
    max_chars = args.get("max_chars", 120)
    if not isinstance(max_chars, int) or not (20 <= max_chars <= 500):
        return False, "args.max_chars는 20~500 범위의 정수여야 합니다."
    return True, ""


def handle_request(spec: ToolSpec, request: dict[str, Any]) -> dict[str, Any]:
    ok, message = validate_request(spec, request)
    if not ok:
        return {
            "ok": False,
            "error": {"code": "INVALID_ARGUMENT", "message": message},
            "meta": {"generated_at": utc_now_iso()},
        }

    text: str = request["args"]["text"]
    max_chars: int = request["args"].get("max_chars", 120)
    summary = (text.strip().replace("\n", " "))[:max_chars].rstrip()
    if len(summary) < len(text.strip()):
        summary += "…"
    return {
        "ok": True,
        "result": {"summary": summary, "max_chars": max_chars},
        "meta": {"generated_at": utc_now_iso()},
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    chapter_dir = Path(__file__).resolve().parents[1]
    output_dir = chapter_dir / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    spec = build_spec()
    spec_path = output_dir / "ch03_tool_spec.json"
    request_path = output_dir / "ch03_demo_request.json"
    response_path = output_dir / "ch03_demo_response.json"

    spec_payload = {
        "generated_at": utc_now_iso(),
        "tool": {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_schema,
            "output_schema": spec.output_schema,
            "errors": spec.errors,
            "constraints": spec.constraints,
        },
    }
    request_payload = {
        "tool": spec.name,
        "args": {
            "text": "MCP를 도입하면 도구 호출의 입출력과 오류가 표준화되어, 검증과 운영이 쉬워진다.",
            "max_chars": 40,
        },
    }
    response_payload = handle_request(spec, request_payload)

    write_json(spec_path, spec_payload)
    write_json(request_path, request_payload)
    write_json(response_path, response_payload)

    print(spec_path.as_posix())
    print(request_path.as_posix())
    print(response_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

