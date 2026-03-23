"""
6주차 실습: 날씨 MCP 서버 구현

OpenWeatherMap API를 래핑하는 MCP 서버이다.
도구(get_weather)와 리소스(cities://list)를 제공한다.

실행 방법:
    pip install mcp httpx python-dotenv
    npx @modelcontextprotocol/inspector python weather_server.py

사전 준비:
    .env 파일에 OPENWEATHER_API_KEY를 설정한다.
    https://openweathermap.org/api 에서 무료 API 키를 발급받는다.
"""

import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

mcp = FastMCP("weather-server")


@mcp.tool()
async def get_weather(city: str) -> str:
    """지정한 도시의 현재 기온과 날씨 상태를 조회한다.

    사용자가 특정 도시의 날씨를 물을 때 사용한다.
    도시명은 한국어('서울') 또는 영문('Tokyo')으로 입력 가능하다.

    Args:
        city: 조회할 도시 이름. 예: '서울', 'Tokyo', '부산'
    """
    if not city.strip():
        return "오류: 도시 이름이 비어 있다. 도시명을 입력해 달라."

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                BASE_URL,
                params={
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric",
                    "lang": "kr",
                },
            )
            resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"]
        return f"{city}: {temp}°C, 습도 {humidity}%, {desc}"
    except httpx.TimeoutException:
        return f"오류: {city} 날씨 조회 시 타임아웃이 발생했다. 잠시 후 다시 시도해 달라."
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"오류: '{city}'에 해당하는 도시를 찾을 수 없다. 도시명을 확인해 달라."
        return f"오류: API가 {e.response.status_code} 상태를 반환했다."


@mcp.resource("cities://list")
async def list_cities() -> str:
    """지원하는 도시 목록을 반환한다.

    사용자가 어떤 도시의 날씨를 조회할 수 있는지 알고 싶을 때 참고한다.
    """
    cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "제주"]
    return ", ".join(cities)


if __name__ == "__main__":
    mcp.run(transport="stdio")
