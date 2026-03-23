"""
9주차 실습: api-docs 스킬 테스트용 Flask 앱

이 앱을 대상으로 api-docs 스킬이 올바르게 동작하는지 확인한다.
Copilot Agent 모드에서 "이 API를 문서화해 줘"라고 요청하면
api-docs 스킬이 자동으로 활성화되어야 한다.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/api/users", methods=["GET"])
def get_users():
    """사용자 목록을 반환한다."""
    return jsonify({"users": []})


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """특정 사용자 정보를 반환한다."""
    return jsonify({"id": user_id, "name": "홍길동"})


@app.route("/api/users", methods=["POST"])
def create_user():
    """새 사용자를 생성한다."""
    data = request.get_json()
    return jsonify({"id": 1, **data}), 201
