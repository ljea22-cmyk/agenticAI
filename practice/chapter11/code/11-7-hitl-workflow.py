"""
11-7-hitl-workflow.py: Human-in-the-Loop 워크플로우 구현

위험도에 따른 차등 승인 로직과 감사 로그를 포함한 HITL 워크플로우.
- 저위험: 자동 승인
- 중위험: 단일 승인 필요
- 고위험: 반드시 승인 후 실행
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict, Literal
from operator import add
from enum import Enum

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

load_dotenv()

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class RiskLevel(str, Enum):
    """작업 위험도 레벨"""
    LOW = "low"       # 자동 승인
    MEDIUM = "medium" # 단일 승인
    HIGH = "high"     # 필수 승인


class ActionType(str, Enum):
    """작업 유형"""
    READ = "read"       # 조회 (저위험)
    MODIFY = "modify"   # 수정 (중위험)
    DELETE = "delete"   # 삭제 (고위험)
    SEND = "send"       # 외부 전송 (고위험)


# 작업 유형별 위험도 매핑
RISK_MAPPING = {
    ActionType.READ: RiskLevel.LOW,
    ActionType.MODIFY: RiskLevel.MEDIUM,
    ActionType.DELETE: RiskLevel.HIGH,
    ActionType.SEND: RiskLevel.HIGH,
}


class AuditLog:
    """감사 로그 관리"""

    def __init__(self):
        self.logs = []

    def log(self, event_type: str, details: dict):
        """이벤트 로깅"""
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **details
        }
        self.logs.append(entry)
        return entry

    def save(self, path: Path):
        """로그 저장"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_events": len(self.logs),
                "events": self.logs
            }, f, ensure_ascii=False, indent=2)


# 전역 감사 로그
audit_log = AuditLog()


class HITLState(TypedDict):
    """HITL 워크플로우 상태"""
    request_id: str
    action_type: str
    target: str
    description: str
    risk_level: str
    requires_approval: bool
    approval_status: str  # pending, approved, rejected
    approver: str
    approval_reason: str
    execution_status: str  # pending, executed, blocked
    execution_result: str
    messages: Annotated[list[str], add]


def classify_risk(state: HITLState) -> dict:
    """작업 위험도 분류 노드"""
    action = ActionType(state["action_type"])
    risk = RISK_MAPPING.get(action, RiskLevel.MEDIUM)

    requires_approval = risk in [RiskLevel.MEDIUM, RiskLevel.HIGH]

    audit_log.log("risk_classification", {
        "request_id": state["request_id"],
        "action_type": state["action_type"],
        "risk_level": risk.value,
        "requires_approval": requires_approval
    })

    return {
        "risk_level": risk.value,
        "requires_approval": requires_approval,
        "messages": [f"위험도 분류: {risk.value} (승인 필요: {requires_approval})"]
    }


def request_approval(state: HITLState) -> dict:
    """승인 요청 노드 (시뮬레이션)"""
    # 실제 환경에서는 interrupt() 사용
    # 여기서는 시뮬레이션: 위험도에 따라 자동 결정

    risk = RiskLevel(state["risk_level"])

    # 시뮬레이션 로직:
    # - 중위험: 80% 확률 승인
    # - 고위험: 모든 DELETE는 거부, SEND는 승인
    if risk == RiskLevel.MEDIUM:
        approved = True
        approver = "auto_reviewer"
        reason = "중위험 작업 자동 승인"
    elif risk == RiskLevel.HIGH:
        if state["action_type"] == ActionType.DELETE.value:
            approved = False
            approver = "security_admin"
            reason = "삭제 작업은 추가 검토 필요"
        else:
            approved = True
            approver = "senior_admin"
            reason = "고위험 작업 승인됨"
    else:
        approved = True
        approver = "system"
        reason = "저위험 작업 자동 승인"

    approval_status = "approved" if approved else "rejected"

    audit_log.log("approval_request", {
        "request_id": state["request_id"],
        "action_type": state["action_type"],
        "risk_level": state["risk_level"],
        "approver": approver,
        "decision": approval_status,
        "reason": reason
    })

    return {
        "approval_status": approval_status,
        "approver": approver,
        "approval_reason": reason,
        "messages": [f"승인 요청 결과: {approval_status} (승인자: {approver})"]
    }


def execute_action(state: HITLState) -> dict:
    """작업 실행 노드"""
    # 작업 실행 시뮬레이션
    action = state["action_type"]
    target = state["target"]

    if action == ActionType.READ.value:
        result = f"[{target}] 조회 완료: 3개의 레코드 반환"
    elif action == ActionType.MODIFY.value:
        result = f"[{target}] 수정 완료: 1개의 레코드 업데이트"
    elif action == ActionType.DELETE.value:
        result = f"[{target}] 삭제 완료: 1개의 레코드 제거"
    elif action == ActionType.SEND.value:
        result = f"[{target}] 전송 완료: 외부 시스템에 데이터 전송"
    else:
        result = "알 수 없는 작업"

    audit_log.log("action_executed", {
        "request_id": state["request_id"],
        "action_type": action,
        "target": target,
        "result": result,
        "approved_by": state.get("approver", "system")
    })

    return {
        "execution_status": "executed",
        "execution_result": result,
        "messages": [f"작업 실행됨: {result}"]
    }


def block_action(state: HITLState) -> dict:
    """작업 차단 노드"""
    audit_log.log("action_blocked", {
        "request_id": state["request_id"],
        "action_type": state["action_type"],
        "reason": state.get("approval_reason", "승인 거부")
    })

    return {
        "execution_status": "blocked",
        "execution_result": f"작업이 차단되었습니다: {state.get('approval_reason', '승인 거부')}",
        "messages": [f"작업 차단됨: {state.get('approval_reason', '승인 거부')}"]
    }


def route_after_classification(state: HITLState) -> Literal["approve", "execute"]:
    """위험도 분류 후 라우팅"""
    if state["requires_approval"]:
        return "approve"
    return "execute"


def route_after_approval(state: HITLState) -> Literal["execute", "block"]:
    """승인 후 라우팅"""
    if state["approval_status"] == "approved":
        return "execute"
    return "block"


def build_hitl_graph() -> StateGraph:
    """HITL 워크플로우 그래프 구성"""
    graph = StateGraph(HITLState)

    # 노드 추가
    graph.add_node("classify", classify_risk)
    graph.add_node("approve", request_approval)
    graph.add_node("execute", execute_action)
    graph.add_node("block", block_action)

    # 엣지 추가
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classification,
        {"approve": "approve", "execute": "execute"}
    )
    graph.add_conditional_edges(
        "approve",
        route_after_approval,
        {"execute": "execute", "block": "block"}
    )
    graph.add_edge("execute", END)
    graph.add_edge("block", END)

    return graph.compile()


def process_request(action_type: str, target: str, description: str) -> dict:
    """요청 처리"""
    request_id = str(uuid.uuid4())[:8]

    initial_state: HITLState = {
        "request_id": request_id,
        "action_type": action_type,
        "target": target,
        "description": description,
        "risk_level": "",
        "requires_approval": False,
        "approval_status": "pending",
        "approver": "",
        "approval_reason": "",
        "execution_status": "pending",
        "execution_result": "",
        "messages": []
    }

    workflow = build_hitl_graph()
    start_time = time.time()
    result = workflow.invoke(initial_state)
    elapsed = time.time() - start_time

    return {
        "request_id": request_id,
        "action_type": action_type,
        "target": target,
        "risk_level": result.get("risk_level", ""),
        "required_approval": result.get("requires_approval", False),
        "approval_status": result.get("approval_status", ""),
        "approver": result.get("approver", ""),
        "execution_status": result.get("execution_status", ""),
        "execution_result": result.get("execution_result", ""),
        "elapsed_seconds": round(elapsed, 3)
    }


def main():
    """메인 실행"""
    print("=" * 60)
    print("11장 실습: Human-in-the-Loop 워크플로우")
    print("=" * 60)

    # 테스트 요청 목록
    test_requests = [
        {
            "action_type": ActionType.READ.value,
            "target": "users_table",
            "description": "사용자 목록 조회"
        },
        {
            "action_type": ActionType.MODIFY.value,
            "target": "config_settings",
            "description": "설정값 수정"
        },
        {
            "action_type": ActionType.DELETE.value,
            "target": "user_data",
            "description": "사용자 데이터 삭제"
        },
        {
            "action_type": ActionType.SEND.value,
            "target": "external_api",
            "description": "외부 API로 데이터 전송"
        }
    ]

    print("\n[1] 워크플로우 실행 중...")
    results = []

    for i, req in enumerate(test_requests, 1):
        print(f"\n요청 {i}: {req['description']}")
        print(f"    - 작업: {req['action_type']}")
        print(f"    - 대상: {req['target']}")

        result = process_request(**req)
        results.append(result)

        print(f"    - 위험도: {result['risk_level']}")
        print(f"    - 승인 필요: {result['required_approval']}")
        print(f"    - 승인 상태: {result['approval_status']}")
        print(f"    - 실행 상태: {result['execution_status']}")
        print(f"    - 결과: {result['execution_result'][:50]}...")

    # 결과 저장
    hitl_result = {
        "executed_at": datetime.now().isoformat(),
        "summary": {
            "total_requests": len(results),
            "executed": sum(1 for r in results if r['execution_status'] == 'executed'),
            "blocked": sum(1 for r in results if r['execution_status'] == 'blocked'),
            "by_risk_level": {
                "low": sum(1 for r in results if r['risk_level'] == 'low'),
                "medium": sum(1 for r in results if r['risk_level'] == 'medium'),
                "high": sum(1 for r in results if r['risk_level'] == 'high')
            }
        },
        "results": results
    }

    result_path = OUTPUT_DIR / "ch11_hitl_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(hitl_result, f, ensure_ascii=False, indent=2)
    print(f"\n[2] 실행 결과 저장: {result_path}")

    # 감사 로그 저장
    audit_path = OUTPUT_DIR / "ch11_audit_log.json"
    audit_log.save(audit_path)
    print(f"    감사 로그 저장: {audit_path}")

    # 요약 출력
    print("\n" + "=" * 60)
    print("HITL 워크플로우 결과 요약")
    print("=" * 60)
    print(f"총 요청: {hitl_result['summary']['total_requests']}개")
    print(f"실행됨: {hitl_result['summary']['executed']}개")
    print(f"차단됨: {hitl_result['summary']['blocked']}개")
    print(f"위험도별: 저({hitl_result['summary']['by_risk_level']['low']}) / "
          f"중({hitl_result['summary']['by_risk_level']['medium']}) / "
          f"고({hitl_result['summary']['by_risk_level']['high']})")

    # 감사 로그 요약
    print(f"\n감사 로그 이벤트: {len(audit_log.logs)}개")
    for log in audit_log.logs:
        print(f"  [{log['event_type']}] {log.get('action_type', '')} - "
              f"{log.get('decision', log.get('result', ''))[:30]}")

    return hitl_result


if __name__ == "__main__":
    main()
