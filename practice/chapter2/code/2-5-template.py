#!/usr/bin/env python3
"""
실행-검증-산출물 저장 표준 템플릿

이 스크립트는 재현 가능한 실행 환경의 표준 구조를 보여줍니다.
- 환경 검증: Python 버전, 의존성 확인
- 경로 설정: 크로스 플랫폼 호환 경로 처리
- 실행 및 검증: 결과값 검증 로직
- 산출물 저장: 타임스탬프 포함 파일명

사용법:
    cd practice/chapter2
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    pip install -r code/requirements.txt
    python3 code/2-5-template.py
"""

import sys
import json
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple


# ============================================================
# 1. 환경 검증
# ============================================================

def verify_python_version(min_version: Tuple[int, int] = (3, 9)) -> bool:
    """
    Python 버전이 최소 요구사항을 충족하는지 확인합니다.
    
    Args:
        min_version: 최소 요구 버전 (major, minor)
    
    Returns:
        bool: 버전 요구사항 충족 여부
    """
    current = sys.version_info[:2]
    is_valid = current >= min_version
    
    print(f"[환경 검증] Python 버전 확인")
    print(f"  현재 버전: {sys.version}")
    print(f"  최소 요구: {min_version[0]}.{min_version[1]}")
    print(f"  결과: {'✓ 충족' if is_valid else '✗ 미충족'}")
    
    return is_valid


def verify_dependencies() -> Dict[str, str]:
    """
    필수 의존성 패키지의 설치 상태를 확인합니다.
    
    Returns:
        Dict[str, str]: 패키지명과 버전 매핑
    """
    print("\n[환경 검증] 의존성 확인")
    
    # 표준 라이브러리만 사용하므로 외부 의존성 없음
    dependencies = {
        "pathlib": "built-in",
        "json": "built-in", 
        "datetime": "built-in",
        "platform": "built-in"
    }
    
    for pkg, version in dependencies.items():
        print(f"  {pkg}: {version}")
    
    return dependencies


def get_environment_info() -> Dict[str, str]:
    """
    현재 실행 환경 정보를 수집합니다.
    
    Returns:
        Dict[str, str]: 환경 정보 딕셔너리
    """
    # 가상환경 여부 확인
    in_venv = sys.prefix != sys.base_prefix
    
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "in_virtual_env": str(in_venv),
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
    }
    
    return info


# ============================================================
# 2. 경로 설정 (크로스 플랫폼 호환)
# ============================================================

def setup_paths() -> Dict[str, Path]:
    """
    프로젝트 경로를 설정합니다.
    pathlib을 사용하여 크로스 플랫폼 호환성을 보장합니다.
    
    Returns:
        Dict[str, Path]: 경로 딕셔너리
    """
    print("\n[경로 설정] 크로스 플랫폼 경로 구성")
    
    # 스크립트 위치 기준 상대 경로 (핵심!)
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir.parent  # practice/chapter2
    
    paths = {
        "script_dir": script_dir,
        "base_dir": base_dir,
        "data_dir": base_dir / "data",
        "input_dir": base_dir / "data" / "input",
        "output_dir": base_dir / "data" / "output",
    }
    
    # 출력 디렉토리 생성 (없으면)
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    
    for name, path in paths.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {name}: {path} [{exists}]")
    
    return paths


# ============================================================
# 3. 실행 및 검증
# ============================================================

def run_sample_task(paths: Dict[str, Path]) -> Dict[str, Any]:
    """
    샘플 작업을 실행하고 결과를 반환합니다.
    
    이 예제에서는 환경 정보를 수집하고 경로 테스트를 수행합니다.
    
    Args:
        paths: 경로 딕셔너리
        
    Returns:
        Dict[str, Any]: 실행 결과
    """
    print("\n[작업 실행] 샘플 작업 수행 중...")
    
    result = {
        "task_name": "환경 정보 수집 및 경로 테스트",
        "execution_time": datetime.now().isoformat(),
        "environment": get_environment_info(),
        "paths_verified": {},
        "cross_platform_test": {},
    }
    
    # 경로 존재 여부 검증
    for name, path in paths.items():
        result["paths_verified"][name] = {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else None,
            "is_absolute": path.is_absolute(),
        }
    
    # 크로스 플랫폼 경로 테스트
    test_path = paths["base_dir"] / "data" / "test_file.txt"
    result["cross_platform_test"] = {
        "constructed_path": str(test_path),
        "as_posix": test_path.as_posix(),  # 항상 /로 구분
        "path_parts": list(test_path.parts[-3:]),  # 마지막 3개 요소
    }
    
    print("  작업 완료!")
    return result


def verify_result(result: Dict[str, Any]) -> bool:
    """
    실행 결과를 검증합니다.
    
    Args:
        result: 실행 결과 딕셔너리
        
    Returns:
        bool: 검증 통과 여부
    """
    print("\n[결과 검증] 실행 결과 확인")
    
    checks = []
    
    # 1. 필수 키 존재 확인
    required_keys = ["task_name", "execution_time", "environment", "paths_verified"]
    for key in required_keys:
        exists = key in result
        checks.append(exists)
        print(f"  필수 키 '{key}': {'✓' if exists else '✗'}")
    
    # 2. 환경 정보 확인
    env = result.get("environment", {})
    has_python_version = "python_version" in env
    checks.append(has_python_version)
    print(f"  Python 버전 정보: {'✓' if has_python_version else '✗'}")
    
    # 3. 가상환경 확인
    in_venv = env.get("in_virtual_env") == "True"
    checks.append(in_venv)
    print(f"  가상환경 실행: {'✓ (권장)' if in_venv else '✗ (비권장)'}")
    
    # 4. 출력 디렉토리 존재 확인
    output_verified = result.get("paths_verified", {}).get("output_dir", {})
    output_exists = output_verified.get("exists", False)
    checks.append(output_exists)
    print(f"  출력 디렉토리: {'✓' if output_exists else '✗'}")
    
    all_passed = all(checks)
    print(f"\n  전체 검증: {'✓ 통과' if all_passed else '✗ 일부 실패'}")
    
    return all_passed


# ============================================================
# 4. 산출물 저장
# ============================================================

def save_output(result: Dict[str, Any], output_dir: Path) -> Path:
    """
    실행 결과를 JSON 파일로 저장합니다.
    파일명에 타임스탬프를 포함하여 실행 이력을 추적합니다.
    
    Args:
        result: 저장할 결과 데이터
        output_dir: 출력 디렉토리
        
    Returns:
        Path: 저장된 파일 경로
    """
    print("\n[산출물 저장] JSON 파일 생성")
    
    # 타임스탬프 포함 파일명
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.json"
    output_path = output_dir / filename
    
    # JSON 저장 (한글 포함, 들여쓰기)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"  파일 경로: {output_path}")
    print(f"  파일 크기: {output_path.stat().st_size} bytes")
    
    return output_path


# ============================================================
# 메인 실행
# ============================================================

def main() -> int:
    """
    메인 실행 함수.
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    print("=" * 60)
    print("실행-검증-산출물 저장 표준 템플릿")
    print("=" * 60)
    
    # 1. 환경 검증
    if not verify_python_version((3, 9)):
        print("\n[오류] Python 3.9 이상이 필요합니다.")
        return 1
    
    verify_dependencies()
    
    # 2. 경로 설정
    paths = setup_paths()
    
    # 3. 실행 및 검증
    result = run_sample_task(paths)
    
    if not verify_result(result):
        print("\n[경고] 일부 검증이 실패했습니다.")
        # 계속 진행 (결과는 저장)
    
    # 4. 산출물 저장
    output_path = save_output(result, paths["output_dir"])
    
    print("\n" + "=" * 60)
    print("실행 완료!")
    print(f"산출물: {output_path}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
