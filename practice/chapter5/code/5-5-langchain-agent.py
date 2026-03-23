#!/usr/bin/env python3
"""
제5장 실습: LangChain + OpenAI 도구 사용 에이전트

이 스크립트는 LangChain과 OpenAI API를 사용하여 도구를 호출하는 에이전트를 구현한다.
2개 이상의 도구(날씨 조회, 파일 저장)를 연결하고, 실행 과정을 로그로 기록한다.

실행 방법:
    cd practice/chapter5
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\\Scripts\\activate
    pip install -r code/requirements.txt
    cp code/.env.example code/.env  # API 키 설정
    python3 code/5-5-langchain-agent.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LangChain 및 LangGraph 임포트
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.prebuilt import create_react_agent

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


# ============================================================
# 5.4 입력 검증: Pydantic 모델
# ============================================================

class WeatherInput(BaseModel):
    """날씨 조회 도구의 입력 스키마"""
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="위도 (-90 ~ 90)"
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="경도 (-180 ~ 180)"
    )


class FileSaveInput(BaseModel):
    """파일 저장 도구의 입력 스키마"""
    filename: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="저장할 파일 이름 (확장자 포함)"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="파일에 저장할 내용"
    )


class CityCoordinatesInput(BaseModel):
    """도시 좌표 조회 도구의 입력 스키마"""
    city_name: str = Field(
        ...,
        min_length=1,
        description="좌표를 조회할 도시 이름 (예: Seoul, Tokyo)"
    )


# ============================================================
# 5.3 관측 가능성: 커스텀 콜백 핸들러
# ============================================================

class AgentLoggingCallback(BaseCallbackHandler):
    """에이전트 실행 과정을 로깅하는 콜백 핸들러"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.logs: list[dict] = []
        self.start_time: datetime | None = None

    def _log(self, event_type: str, data: dict[str, Any]) -> None:
        """로그 이벤트 기록"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data
        }
        self.logs.append(entry)
        logger.info(f"[{event_type}] {data}")

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs) -> None:
        """체인 시작 시 호출"""
        self.start_time = datetime.now()
        self._log("chain_start", {"inputs": str(inputs)[:200]})

    def on_chain_end(self, outputs: dict, **kwargs) -> None:
        """체인 종료 시 호출"""
        elapsed = None
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
        self._log("chain_end", {
            "outputs": str(outputs)[:200],
            "elapsed_seconds": elapsed
        })

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """도구 실행 시작 시 호출"""
        tool_name = serialized.get("name", "unknown")
        self._log("tool_start", {"tool": tool_name, "input": input_str[:200]})

    def on_tool_end(self, output: str, **kwargs) -> None:
        """도구 실행 종료 시 호출"""
        self._log("tool_end", {"output": output[:200]})

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """도구 에러 발생 시 호출"""
        self._log("tool_error", {"error": str(error)})

    def save_logs(self) -> None:
        """로그를 파일로 저장"""
        log_text = "\n".join([
            f"[{log['timestamp']}] {log['event']}: {json.dumps({k: v for k, v in log.items() if k not in ['timestamp', 'event']}, ensure_ascii=False)}"
            for log in self.logs
        ])
        self.log_file.write_text(log_text, encoding="utf-8")
        logger.info(f"로그 저장 완료: {self.log_file}")


# ============================================================
# 도구 함수 정의
# ============================================================

# 주요 도시 좌표 데이터베이스
CITY_COORDINATES = {
    "seoul": {"lat": 37.5665, "lon": 126.9780, "name": "Seoul"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
    "london": {"lat": 51.5074, "lon": -0.1278, "name": "London"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
    "beijing": {"lat": 39.9042, "lon": 116.4074, "name": "Beijing"},
    "busan": {"lat": 35.1796, "lon": 129.0756, "name": "Busan"},
}


def get_city_coordinates(city_name: str) -> str:
    """
    도시 이름으로 좌표를 조회한다.

    Args:
        city_name: 조회할 도시 이름

    Returns:
        도시 좌표 정보 (JSON 문자열)
    """
    city_key = city_name.lower().strip()

    if city_key in CITY_COORDINATES:
        coords = CITY_COORDINATES[city_key]
        return json.dumps({
            "success": True,
            "city": coords["name"],
            "latitude": coords["lat"],
            "longitude": coords["lon"]
        }, ensure_ascii=False)

    # 부분 매칭 시도
    for key, coords in CITY_COORDINATES.items():
        if city_key in key or key in city_key:
            return json.dumps({
                "success": True,
                "city": coords["name"],
                "latitude": coords["lat"],
                "longitude": coords["lon"]
            }, ensure_ascii=False)

    return json.dumps({
        "success": False,
        "error": f"'{city_name}' 도시를 찾을 수 없습니다. 지원 도시: {', '.join(CITY_COORDINATES.keys())}"
    }, ensure_ascii=False)


def get_weather(latitude: float, longitude: float) -> str:
    """
    지정된 좌표의 현재 날씨를 조회한다.
    Open-Meteo API를 사용하여 실제 날씨 데이터를 가져온다.

    Args:
        latitude: 위도 (-90 ~ 90)
        longitude: 경도 (-180 ~ 180)

    Returns:
        날씨 정보 (JSON 문자열)
    """
    try:
        # Open-Meteo API 사용 (API 키 불필요)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m",
                       "weather_code", "wind_speed_10m"],
            "timezone": "auto"
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})

        # 날씨 코드를 설명으로 변환
        weather_codes = {
            0: "맑음", 1: "대체로 맑음", 2: "부분적 흐림", 3: "흐림",
            45: "안개", 48: "짙은 안개",
            51: "이슬비", 53: "이슬비", 55: "강한 이슬비",
            61: "약한 비", 63: "비", 65: "강한 비",
            71: "약한 눈", 73: "눈", 75: "강한 눈",
            80: "소나기", 81: "소나기", 82: "강한 소나기",
            95: "뇌우", 96: "뇌우(우박)", 99: "강한 뇌우(우박)"
        }
        weather_code = current.get("weather_code", 0)
        condition = weather_codes.get(weather_code, "알 수 없음")

        result = {
            "success": True,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": data.get("timezone", "Unknown")
            },
            "current": {
                "temperature_celsius": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "condition": condition,
                "weather_code": weather_code,
                "wind_speed_kmh": current.get("wind_speed_10m")
            },
            "retrieved_at": datetime.now().isoformat()
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except httpx.TimeoutException:
        return json.dumps({
            "success": False,
            "error": "날씨 API 요청 시간 초과"
        }, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "success": False,
            "error": f"날씨 API 오류: HTTP {e.response.status_code}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"예상치 못한 오류: {str(e)}"
        }, ensure_ascii=False)


def save_to_file(filename: str, content: str) -> str:
    """
    텍스트 내용을 파일로 저장한다.

    Args:
        filename: 저장할 파일 이름
        content: 저장할 내용

    Returns:
        저장 결과 (JSON 문자열)
    """
    try:
        # 안전한 파일명으로 변환
        safe_filename = "".join(
            c for c in filename
            if c.isalnum() or c in "._-"
        )
        if not safe_filename:
            safe_filename = "output.txt"

        file_path = OUTPUT_DIR / safe_filename
        file_path.write_text(content, encoding="utf-8")

        return json.dumps({
            "success": True,
            "message": f"파일 저장 완료",
            "path": str(file_path),
            "size_bytes": len(content.encode("utf-8"))
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"파일 저장 실패: {str(e)}"
        }, ensure_ascii=False)


# ============================================================
# LangGraph 도구 정의 (@tool 데코레이터 사용)
# ============================================================

# 5.2 툴 선택 실패를 줄이는 프롬프트 구조
# 도구 설명에 목적, 입력, 출력, 제약을 명확히 기술

@tool
def get_city_coordinates_tool(city_name: str) -> str:
    """도시 이름으로 위도와 경도 좌표를 조회합니다.

    사용 시점: 사용자가 도시 이름만 알려주고 좌표를 모를 때 이 도구를 먼저 호출하세요.
    입력: 도시 이름 (예: Seoul, Tokyo, New York)
    출력: 위도, 경도 좌표 (JSON)
    제약: 일부 주요 도시만 지원됩니다.

    Args:
        city_name: 조회할 도시 이름
    """
    return get_city_coordinates(city_name)


@tool
def get_weather_tool(latitude: float, longitude: float) -> str:
    """지정된 위도/경도의 현재 날씨 정보를 조회합니다.

    사용 시점: 특정 위치의 날씨를 알고 싶을 때 사용하세요.
    입력: latitude (위도, -90~90), longitude (경도, -180~180)
    출력: 기온, 습도, 날씨 상태, 풍속 (JSON)
    제약: 좌표가 필요합니다. 도시 이름만 있다면 먼저 get_city_coordinates_tool을 호출하세요.

    Args:
        latitude: 위도 (-90 ~ 90)
        longitude: 경도 (-180 ~ 180)
    """
    return get_weather(latitude, longitude)


@tool
def save_to_file_tool(filename: str, content: str) -> str:
    """텍스트 내용을 파일로 저장합니다.

    사용 시점: 정보를 파일로 저장해달라는 요청이 있을 때 사용하세요.
    입력: filename (파일 이름), content (저장할 내용)
    출력: 저장 결과 (JSON)
    제약: 파일 이름은 영문, 숫자, 점, 밑줄, 하이픈만 허용됩니다.

    Args:
        filename: 저장할 파일 이름 (확장자 포함)
        content: 파일에 저장할 내용
    """
    return save_to_file(filename, content)


def create_agent(callback_handler: AgentLoggingCallback):
    """LangGraph 기반 에이전트를 생성한다."""

    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key
    )

    # 도구 목록
    tools = [get_city_coordinates_tool, get_weather_tool, save_to_file_tool]

    # 시스템 프롬프트
    system_prompt = """당신은 날씨 정보를 조회하고 파일로 저장하는 도우미입니다.

사용자의 요청을 분석하고 적절한 도구를 선택하여 실행하세요.

도구 사용 지침:
1. 도시 이름만 주어지면 먼저 get_city_coordinates_tool로 좌표를 조회하세요.
2. 좌표를 얻은 후 get_weather_tool로 날씨를 조회하세요.
3. 저장 요청이 있으면 save_to_file_tool로 결과를 저장하세요.

항상 한국어로 응답하세요."""

    # LangGraph ReAct 에이전트 생성
    agent = create_react_agent(
        llm,
        tools,
        prompt=system_prompt
    )

    return agent


# ============================================================
# 메인 실행
# ============================================================

def main():
    """메인 실행 함수"""

    logger.info("=" * 60)
    logger.info("제5장 실습: LangChain 에이전트 시작")
    logger.info("=" * 60)

    # 콜백 핸들러 생성
    log_file = OUTPUT_DIR / "ch05_agent_log.txt"
    callback_handler = AgentLoggingCallback(log_file)

    try:
        # 에이전트 생성
        agent = create_agent(callback_handler)

        # 테스트 쿼리
        test_query = "서울의 현재 날씨를 조회하고, 결과를 ch05_weather_report.txt 파일로 저장해주세요."

        logger.info(f"사용자 입력: {test_query}")
        logger.info("-" * 60)

        # 에이전트 실행 (LangGraph는 messages 형태로 입력)
        from langchain_core.messages import HumanMessage

        callback_handler._log("agent_start", {"query": test_query})

        result = agent.invoke(
            {"messages": [HumanMessage(content=test_query)]},
            config={"callbacks": [callback_handler]}
        )

        # 최종 메시지 추출
        final_message = result["messages"][-1].content if result["messages"] else "No output"

        logger.info("-" * 60)
        logger.info(f"최종 응답: {final_message}")

        callback_handler._log("agent_end", {"output": final_message[:500]})

        # 결과 저장
        result_data = {
            "query": test_query,
            "output": final_message,
            "executed_at": datetime.now().isoformat(),
            "success": True
        }

        result_file = OUTPUT_DIR / "ch05_result.json"
        result_file.write_text(
            json.dumps(result_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"결과 저장: {result_file}")

    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        # API 키 없이도 테스트 결과 생성
        result_data = {
            "query": "서울의 현재 날씨를 조회하고, 결과를 ch05_weather_report.txt 파일로 저장해주세요.",
            "output": "",
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }
        result_file = OUTPUT_DIR / "ch05_result.json"
        result_file.write_text(
            json.dumps(result_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return False

    except Exception as e:
        logger.error(f"실행 오류: {e}")
        callback_handler._log("error", {"message": str(e)})
        return False

    finally:
        # 로그 저장
        callback_handler.save_logs()

    logger.info("=" * 60)
    logger.info("실습 완료")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
