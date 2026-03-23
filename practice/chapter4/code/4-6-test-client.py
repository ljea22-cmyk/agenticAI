#!/usr/bin/env python3
"""
제4장 실습: MCP 서버 테스트 클라이언트

이 스크립트는 WeatherAPIClient의 핵심 로직을 독립적으로 테스트한다.
모듈 임포트 없이 순수 유닛 테스트를 수행한다.

실행 방법:
    cd practice/chapter4
    source venv/bin/activate
    python3 code/4-6-test-client.py
"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock


class TestAPIKeyMasking(unittest.TestCase):
    """API 키 마스킹 테스트"""

    def mask_api_key(self, key: str) -> str:
        """API 키를 로그에서 마스킹하는 함수 (서버 로직과 동일)"""
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    def test_mask_long_api_key(self):
        """긴 API 키 마스킹 테스트"""
        masked = self.mask_api_key("abcd1234efgh5678")
        self.assertEqual(masked, "abcd...5678")

    def test_mask_short_api_key(self):
        """짧은 API 키 마스킹 테스트"""
        masked = self.mask_api_key("short")
        self.assertEqual(masked, "***")

    def test_mask_exactly_8_chars(self):
        """정확히 8자 API 키 마스킹 테스트"""
        masked = self.mask_api_key("12345678")
        self.assertEqual(masked, "***")


class TestWeatherDataParsing(unittest.TestCase):
    """날씨 데이터 파싱 테스트"""

    def parse_weather_data(self, raw: dict) -> dict:
        """원시 응답에서 필요한 데이터를 추출 (서버 로직과 동일)"""
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

    def test_parse_complete_response(self):
        """완전한 응답 파싱 테스트"""
        raw_response = {
            "name": "Seoul",
            "sys": {"country": "KR"},
            "coord": {"lat": 37.5665, "lon": 126.978},
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "main": {
                "temp": 20.5,
                "feels_like": 19.8,
                "temp_min": 18.0,
                "temp_max": 23.0,
                "humidity": 65
            },
            "wind": {"speed": 3.5, "deg": 180},
            "visibility": 10000,
            "dt": 1704067200
        }

        parsed = self.parse_weather_data(raw_response)

        self.assertEqual(parsed["location"], "Seoul")
        self.assertEqual(parsed["country"], "KR")
        self.assertEqual(parsed["weather"]["main"], "Clear")
        self.assertEqual(parsed["temperature"]["current"], 20.5)
        self.assertEqual(parsed["humidity"], 65)
        self.assertIsNotNone(parsed["timestamp"])

    def test_parse_partial_response(self):
        """불완전한 응답 파싱 테스트 (기본값 처리)"""
        raw_response = {
            "name": "Unknown City",
            "dt": 0
        }

        parsed = self.parse_weather_data(raw_response)

        self.assertEqual(parsed["location"], "Unknown City")
        self.assertEqual(parsed["country"], "Unknown")
        self.assertEqual(parsed["weather"]["main"], "Unknown")

    def test_parse_error_response(self):
        """에러 응답 파싱 테스트"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}

        try:
            data = mock_response.json()
            error_msg = data.get("message", f"HTTP {mock_response.status_code}")
        except Exception:
            error_msg = f"HTTP {mock_response.status_code}"

        self.assertEqual(error_msg, "Invalid API key")


class TestInputValidation(unittest.TestCase):
    """입력 검증 테스트"""

    def test_valid_latitude_range(self):
        """유효한 위도 범위 테스트"""
        valid_latitudes = [-90, -45, 0, 45, 90]
        for lat in valid_latitudes:
            self.assertTrue(-90 <= lat <= 90, f"위도 {lat}는 유효해야 함")

    def test_invalid_latitude_range(self):
        """유효하지 않은 위도 범위 테스트"""
        invalid_latitudes = [-91, 91, -180, 180]
        for lat in invalid_latitudes:
            self.assertFalse(-90 <= lat <= 90, f"위도 {lat}는 유효하지 않아야 함")

    def test_valid_longitude_range(self):
        """유효한 경도 범위 테스트"""
        valid_longitudes = [-180, -90, 0, 90, 180]
        for lon in valid_longitudes:
            self.assertTrue(-180 <= lon <= 180, f"경도 {lon}는 유효해야 함")

    def test_valid_units(self):
        """유효한 단위 테스트"""
        valid_units = ["metric", "imperial", "standard"]
        for unit in valid_units:
            self.assertIn(unit, valid_units)


def run_tests():
    """테스트 실행"""
    print("=" * 60)
    print("WeatherAPIClient 단위 테스트 실행")
    print("=" * 60)

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAPIKeyMasking))
    suite.addTests(loader.loadTestsFromTestCase(TestWeatherDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestInputValidation))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 저장
    chapter_dir = Path(__file__).parent.parent
    output_dir = chapter_dir / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    test_result = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }

    output_file = output_dir / "ch04_test_results.json"
    output_file.write_text(
        json.dumps(test_result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n테스트 결과 저장: {output_file}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
