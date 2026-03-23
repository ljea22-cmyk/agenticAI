#!/usr/bin/env python3
"""
제4장 실습: OpenWeatherMap API를 MCP 서버로 래핑

이 스크립트는 OpenWeatherMap API를 MCP 도구로 제공하는 서버를 구현한다.
- 인증키 관리: .env 파일에서 API 키 로드
- 실패 처리: 타임아웃(10초), 재시도(최대 3회, 지수 백오프)
- 로깅: 요청/응답을 파일로 기록
- 테스트 가능한 구조: API 클라이언트 분리

실행 방법:
    cd practice/chapter4
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\\Scripts\\activate
    pip install -r code/requirements.txt
    python3 code/4-6-weather-mcp-server.py

참고: MCP 서버는 Claude Desktop 또는 MCP 클라이언트와 연결하여 사용
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ============================================================
# 설정 및 초기화
# ============================================================

# 프로젝트 루트 기준 상대 경로 설정
SCRIPT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"
LOG_DIR = CHAPTER_DIR / "logs"

# 디렉토리 생성
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 환경 변수 로드 (.env 파일)
load_dotenv(CHAPTER_DIR / ".env")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "mcp_server.log", encoding="utf-8"),
        logging.StreamHandler()  # 콘솔 출력 (디버깅용)
    ]
)
logger = logging.getLogger(__name__)

# OpenWeatherMap API 설정
OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5"
DEFAULT_TIMEOUT = 10.0  # 초
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # 초 (지수 백오프 기준)


# ============================================================
# API 클라이언트 (테스트 가능한 구조)
# ============================================================

@dataclass
class WeatherResponse:
    """날씨 API 응답을 담는 데이터 클래스"""
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[dict[str, Any]] = None


class WeatherAPIClient:
    """
    OpenWeatherMap API 클라이언트

    테스트 가능한 구조를 위해 API 호출 로직을 분리한다.
    의존성 주입을 통해 모킹이 가능하다.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = OPENWEATHERMAP_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def _mask_api_key(self, key: str) -> str:
        """API 키를 로그에서 마스킹"""
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    async def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any]
    ) -> WeatherResponse:
        """
        API 요청을 수행하고 재시도 로직을 처리한다.

        Args:
            endpoint: API 엔드포인트 (예: "/weather")
            params: 쿼리 파라미터

        Returns:
            WeatherResponse: 성공 시 data 포함, 실패 시 error 포함
        """
        url = f"{self.base_url}{endpoint}"
        params["appid"] = self.api_key

        # 로그에서 API 키 마스킹
        log_params = {k: v for k, v in params.items()}
        log_params["appid"] = self._mask_api_key(self.api_key)
        logger.info(f"API 요청 시작: {endpoint} | params={log_params}")

        last_error = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    start_time = time.time()
                    response = await client.get(url, params=params)
                    elapsed = time.time() - start_time

                    logger.info(
                        f"API 응답 수신: status={response.status_code} | "
                        f"elapsed={elapsed:.2f}s | attempt={attempt + 1}"
                    )

                    # HTTP 에러 체크
                    response.raise_for_status()

                    data = response.json()
                    return WeatherResponse(
                        success=True,
                        data=self._parse_weather_data(data),
                        raw_response=data
                    )

            except httpx.TimeoutException as e:
                last_error = f"타임아웃 ({self.timeout}초 초과)"
                logger.warning(f"타임아웃 발생: attempt={attempt + 1} | error={e}")

            except httpx.HTTPStatusError as e:
                # 재시도 불가능한 에러 (4xx)
                if 400 <= e.response.status_code < 500:
                    error_msg = self._parse_error_response(e.response)
                    logger.error(f"클라이언트 에러: {error_msg}")
                    return WeatherResponse(success=False, error=error_msg)

                # 재시도 가능한 에러 (5xx)
                last_error = f"서버 에러: {e.response.status_code}"
                logger.warning(f"서버 에러 발생: attempt={attempt + 1} | status={e.response.status_code}")

            except httpx.RequestError as e:
                last_error = f"네트워크 오류: {type(e).__name__}"
                logger.warning(f"네트워크 오류: attempt={attempt + 1} | error={e}")

            # 재시도 대기 (지수 백오프)
            if attempt < self.max_retries - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.info(f"재시도 대기: {delay:.1f}초")
                await asyncio.sleep(delay)

        # 모든 재시도 실패
        logger.error(f"최대 재시도 횟수 초과: {last_error}")
        return WeatherResponse(
            success=False,
            error=f"요청 실패 (최대 {self.max_retries}회 재시도 후): {last_error}"
        )

    def _parse_weather_data(self, raw: dict[str, Any]) -> dict[str, Any]:
        """원시 응답에서 필요한 데이터를 추출"""
        return {
            "location": raw.get("name", "Unknown"),
            "country": raw.get("sys", {}).get("country", "Unknown"),
            "coordinates": {
                "lat": raw.get("coord", {}).get("lat"),
                "lon": raw.get("coord", {}).get("lon")
            },
            "weather": {
                "main": raw.get("weather", [{}])[0].get("main", "Unknown"),
                "description": raw.get("weather", [{}])[0].get("description", "Unknown")
            },
            "temperature": {
                "current": raw.get("main", {}).get("temp"),
                "feels_like": raw.get("main", {}).get("feels_like"),
                "min": raw.get("main", {}).get("temp_min"),
                "max": raw.get("main", {}).get("temp_max"),
                "unit": "Kelvin"
            },
            "humidity": raw.get("main", {}).get("humidity"),
            "wind": {
                "speed": raw.get("wind", {}).get("speed"),
                "direction": raw.get("wind", {}).get("deg")
            },
            "visibility": raw.get("visibility"),
            "timestamp": datetime.utcfromtimestamp(
                raw.get("dt", 0)
            ).isoformat() + "Z"
        }

    def _parse_error_response(self, response: httpx.Response) -> str:
        """에러 응답에서 메시지 추출"""
        try:
            data = response.json()
            return data.get("message", f"HTTP {response.status_code}")
        except Exception:
            return f"HTTP {response.status_code}"

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        units: str = "metric"
    ) -> WeatherResponse:
        """
        현재 날씨 조회

        Args:
            lat: 위도
            lon: 경도
            units: 단위 (metric: 섭씨, imperial: 화씨, standard: 켈빈)

        Returns:
            WeatherResponse: 날씨 데이터 또는 에러
        """
        params = {
            "lat": lat,
            "lon": lon,
            "units": units
        }
        return await self._make_request("/weather", params)


# ============================================================
# MCP 서버 정의
# ============================================================

# API 키 확인
api_key = os.getenv("OPENWEATHERMAP_API_KEY")
if not api_key:
    logger.warning("OPENWEATHERMAP_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

# FastMCP 서버 초기화
mcp = FastMCP("weather-server")

# API 클라이언트 인스턴스 (전역)
weather_client: Optional[WeatherAPIClient] = None

def get_weather_client() -> WeatherAPIClient:
    """API 클라이언트 인스턴스 반환 (지연 초기화)"""
    global weather_client
    if weather_client is None:
        key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not key:
            raise ValueError("OPENWEATHERMAP_API_KEY 환경 변수가 설정되지 않았습니다.")
        weather_client = WeatherAPIClient(api_key=key)
    return weather_client


@mcp.tool()
async def get_current_weather(
    latitude: float,
    longitude: float,
    units: str = "metric"
) -> str:
    """
    지정된 위치의 현재 날씨를 조회합니다.

    Args:
        latitude: 위도 (-90 ~ 90)
        longitude: 경도 (-180 ~ 180)
        units: 온도 단위 (metric: 섭씨, imperial: 화씨, standard: 켈빈)

    Returns:
        날씨 정보를 포함한 JSON 문자열
    """
    logger.info(f"get_current_weather 호출: lat={latitude}, lon={longitude}, units={units}")

    # 입력 검증
    if not -90 <= latitude <= 90:
        error_msg = f"위도는 -90에서 90 사이여야 합니다: {latitude}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)

    if not -180 <= longitude <= 180:
        error_msg = f"경도는 -180에서 180 사이여야 합니다: {longitude}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)

    if units not in ("metric", "imperial", "standard"):
        error_msg = f"units는 metric, imperial, standard 중 하나여야 합니다: {units}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)

    try:
        client = get_weather_client()
        response = await client.get_current_weather(latitude, longitude, units)

        if response.success:
            # 성공 시 결과 저장
            result = {
                "success": True,
                "data": response.data,
                "queried_at": datetime.utcnow().isoformat() + "Z"
            }

            # 결과 파일 저장
            output_file = OUTPUT_DIR / "ch04_weather_response.json"
            output_file.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.info(f"결과 저장 완료: {output_file}")

            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_result = {
                "success": False,
                "error": response.error
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        logger.exception("예상치 못한 오류 발생")
        return json.dumps({"error": f"내부 오류: {type(e).__name__}"}, ensure_ascii=False)


# ============================================================
# 테스트 및 데모 실행
# ============================================================

async def demo_weather_query():
    """
    데모용 날씨 조회 실행

    이 함수는 MCP 서버 없이도 API 클라이언트를 직접 테스트한다.
    """
    print("=" * 60)
    print("OpenWeatherMap API 데모 실행")
    print("=" * 60)

    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        print("\n[오류] OPENWEATHERMAP_API_KEY가 설정되지 않았습니다.")
        print("1. https://openweathermap.org/api 에서 API 키 발급")
        print("2. practice/chapter4/.env 파일 생성")
        print("3. OPENWEATHERMAP_API_KEY=your_key 추가")
        return

    # 서울의 좌표
    lat, lon = 37.5665, 126.9780
    print(f"\n조회 위치: 서울 (lat={lat}, lon={lon})")

    client = WeatherAPIClient(api_key=api_key)
    response = await client.get_current_weather(lat, lon, units="metric")

    if response.success:
        print("\n[성공] 날씨 정보:")
        print(json.dumps(response.data, ensure_ascii=False, indent=2))

        # 결과 저장
        output_file = OUTPUT_DIR / "ch04_weather_response.json"
        result = {
            "success": True,
            "data": response.data,
            "raw_response": response.raw_response,
            "queried_at": datetime.utcnow().isoformat() + "Z"
        }
        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n결과 저장: {output_file}")

        # 로그 파일 복사
        log_file = LOG_DIR / "mcp_server.log"
        if log_file.exists():
            output_log = OUTPUT_DIR / "ch04_server_log.txt"
            output_log.write_text(log_file.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"로그 저장: {output_log}")
    else:
        print(f"\n[실패] {response.error}")


def main():
    """메인 진입점"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # 데모 모드: API 직접 테스트
        asyncio.run(demo_weather_query())
    else:
        # MCP 서버 모드
        print("MCP 서버 시작...")
        print("Claude Desktop 또는 MCP 클라이언트와 연결하세요.")
        print("데모 실행: python3 4-6-weather-mcp-server.py --demo")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
