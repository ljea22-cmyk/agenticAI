"""
7주차 실습: 날씨 MCP 서버 안정성 강화

6주차 서버에 입력 검증, 재시도 로직, 로깅을 추가한 버전이다.

실행 방법:
    pip install mcp httpx python-dotenv
    npx @modelcontextprotocol/inspector python weather_server.py
"""

import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("weather_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger("weather-server")

# --- 상수 ---
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
MAX_CITY_LENGTH = 100

mcp = FastMCP("weather-server")


# --- 유틸리티 함수 ---
def validate_city(city: str) -> str | None:
    """도시명을 검증한다. 오류 시 에러 메시지, 정상 시 None을 반환한다."""
    if not city or not city.strip():
        return "오류: 도시 이름이 비어 있다. 도시명을 입력해 달라. 예: '서울', 'Tokyo'"
    if len(city.strip()) > MAX_CITY_LENGTH:
        return f"오류: 도시 이름이 너무 길다. {MAX_CITY_LENGTH}자 이내로 입력해 달라."
    return None


async def fetch_with_retry(url: str, params: dict, max_retries: int = 3) -> dict:
    """지수 백오프 재시도로 HTTP GET 요청을 수행한다."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2**attempt
            logger.warning(
                "재시도 %d/%d: %s초 대기", attempt + 1, max_retries, wait_time
            )
            await asyncio.sleep(wait_time)


# --- MCP 도구 ---
@mcp.tool()
async def get_weather(city: str) -> str:
    """지정한 도시의 현재 기온과 날씨 상태를 조회한다.

    사용자가 특정 도시의 날씨를 물을 때 사용한다.
    도시명은 한국어('서울') 또는 영문('Tokyo')으로 입력 가능하다.

    Args:
        city: 조회할 도시 이름. 예: '서울', 'Tokyo', '부산'
    """
    logger.info("get_weather 호출: city=%s", city)

    error = validate_city(city)
    if error:
        logger.warning("입력 검증 실패: %s", error)
        return error

    city = city.strip()
    try:
        data = await fetch_with_retry(
            BASE_URL,
            params={
                "q": city,
                "appid": API_KEY,
                "units": "metric",
                "lang": "kr",
            },
        )
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"]
        result = f"{city}: {temp}°C, 습도 {humidity}%, {desc}"
        logger.info("get_weather 완료: %s", result)
        return result
    except httpx.TimeoutException:
        msg = f"오류: {city} 날씨 조회 시 타임아웃이 발생했다. 잠시 후 다시 시도해 달라."
        logger.error(msg)
        return msg
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            msg = f"오류: '{city}'에 해당하는 도시를 찾을 수 없다. 도시명을 확인해 달라."
        else:
            msg = f"오류: API가 {e.response.status_code} 상태를 반환했다."
        logger.error(msg)
        return msg
    except Exception as e:
        msg = f"오류: 예상치 못한 문제가 발생했다. ({type(e).__name__})"
        logger.error(msg, exc_info=True)
        return msg


@mcp.resource("cities://list")
async def list_cities() -> str:
    """지원하는 도시 목록을 반환한다."""
    cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "제주"]
    return ", ".join(cities)


if __name__ == "__main__":
    mcp.run(transport="stdio")
