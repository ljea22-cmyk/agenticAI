"""
12-7-operations.py: 운영 도구 구현

비용 추정, 메트릭 수집, 운영 체크리스트 생성을 포함한 LLM 운영 도구.
- 토큰 기반 비용 추정
- 요청/응답 메트릭 수집
- 프로덕션 체크리스트 생성
"""

import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import tiktoken
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# API 가격 (2025년 기준, USD per 1M tokens)
PRICING = {
    "gpt-4o": {"input": 5.00, "output": 20.00},
    "gpt-4o-mini": {"input": 0.60, "output": 2.40},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},  # 최신 가격
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-haiku": {"input": 0.25, "output": 1.25},
}


@dataclass
class TokenUsage:
    """토큰 사용량"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class CostEstimate:
    """비용 추정"""
    model: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


@dataclass
class RequestMetrics:
    """요청 메트릭"""
    request_id: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    success: bool
    timestamp: str


class CostCalculator:
    """비용 계산기"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model("gpt-4o")

    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        return len(self.encoding.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> CostEstimate:
        """비용 추정"""
        pricing = PRICING.get(self.model, PRICING["gpt-4o-mini"])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return CostEstimate(
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(input_cost + output_cost, 6)
        )


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self.metrics: list[RequestMetrics] = []
        self.calculator = CostCalculator()

    def record(self, request_id: str, model: str, prompt: str, response: str,
               latency_ms: float, success: bool = True):
        """요청 메트릭 기록"""
        input_tokens = self.calculator.count_tokens(prompt)
        output_tokens = self.calculator.count_tokens(response)

        calc = CostCalculator(model)
        estimate = calc.estimate_cost(input_tokens, output_tokens)

        metric = RequestMetrics(
            request_id=request_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=estimate.total_cost_usd,
            success=success,
            timestamp=datetime.now().isoformat()
        )
        self.metrics.append(metric)
        return metric

    def get_summary(self) -> dict:
        """메트릭 요약"""
        if not self.metrics:
            return {"error": "No metrics collected"}

        total_requests = len(self.metrics)
        successful = sum(1 for m in self.metrics if m.success)
        total_input = sum(m.input_tokens for m in self.metrics)
        total_output = sum(m.output_tokens for m in self.metrics)
        total_cost = sum(m.cost_usd for m in self.metrics)
        avg_latency = sum(m.latency_ms for m in self.metrics) / total_requests

        return {
            "total_requests": total_requests,
            "successful_requests": successful,
            "success_rate": round(successful / total_requests * 100, 1),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_cost_per_request_usd": round(total_cost / total_requests, 6)
        }


def generate_checklist() -> str:
    """프로덕션 운영 체크리스트 생성"""
    checklist = """# 프로덕션 운영 체크리스트

## 1. 배포 전 체크리스트

### 환경 설정
- [ ] 환경 변수 설정 완료 (.env 파일 또는 시크릿 매니저)
- [ ] API 키가 코드에 하드코딩되지 않음
- [ ] 프로덕션용 API 키 발급 완료
- [ ] 의존성 버전 고정 (requirements.txt)

### 코드 품질
- [ ] 에러 핸들링 구현 (API 실패, 타임아웃)
- [ ] 재시도 로직 구현 (지수 백오프)
- [ ] 입력 검증 구현
- [ ] 로깅 구현

### 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 부하 테스트 완료 (예상 트래픽 기준)

## 2. 모니터링 체크리스트

### 로깅
- [ ] 요청/응답 로깅 활성화
- [ ] 에러 로깅 활성화
- [ ] 민감 정보 마스킹

### 메트릭
- [ ] 요청 수 추적
- [ ] 응답 시간 추적
- [ ] 토큰 사용량 추적
- [ ] 에러율 추적
- [ ] 비용 추적

### 알림
- [ ] 에러율 임계값 알림 설정
- [ ] 응답 시간 임계값 알림 설정
- [ ] 비용 임계값 알림 설정

## 3. 보안 체크리스트

### API 키 관리
- [ ] API 키가 환경 변수 또는 시크릿 매니저에 저장됨
- [ ] API 키 로테이션 절차 수립
- [ ] API 키 접근 권한 제한

### 접근 제어
- [ ] 최소 권한 원칙 적용
- [ ] API 요청 인증 구현
- [ ] 요청 레이트 리밋 설정

### 데이터 보호
- [ ] 민감 데이터 암호화
- [ ] PII 마스킹
- [ ] 감사 로그 활성화

## 4. 비용 관리 체크리스트

### 비용 추정
- [ ] 예상 월간 비용 계산 완료
- [ ] 비용 한도 설정

### 최적화
- [ ] 적절한 모델 선택 (작업별 최적 모델)
- [ ] 프롬프트 최적화 (불필요한 토큰 제거)
- [ ] 캐싱 전략 수립
- [ ] 응답 길이 제한 설정

### 모니터링
- [ ] 일별/주별 비용 리포트 설정
- [ ] 비용 이상 알림 설정

## 5. 장애 대응 체크리스트

### 준비
- [ ] 장애 대응 절차 문서화
- [ ] 롤백 절차 수립
- [ ] 연락망 정리

### 복구
- [ ] 백업 API 키 준비
- [ ] 폴백 모델 설정 (예: GPT-4o → GPT-4o-mini)
- [ ] 서킷 브레이커 구현

---
생성일: {date}
"""
    return checklist.format(date=datetime.now().strftime("%Y-%m-%d"))


def run_sample_requests(collector: MetricsCollector) -> list[dict]:
    """샘플 요청 실행"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompts = [
        "Python에서 리스트와 튜플의 차이점을 간단히 설명해주세요.",
        "async/await 키워드의 용도를 한 문장으로 설명해주세요.",
        "REST API와 GraphQL의 주요 차이점 3가지를 나열해주세요."
    ]

    results = []

    for i, prompt in enumerate(prompts, 1):
        request_id = f"req_{i:03d}"
        start_time = time.time()

        try:
            response = llm.invoke(prompt)
            latency_ms = (time.time() - start_time) * 1000

            metric = collector.record(
                request_id=request_id,
                model="gpt-4o-mini",
                prompt=prompt,
                response=response.content,
                latency_ms=latency_ms,
                success=True
            )

            results.append({
                "request_id": request_id,
                "prompt": prompt[:50] + "...",
                "response_length": len(response.content),
                "tokens": metric.input_tokens + metric.output_tokens,
                "cost_usd": metric.cost_usd,
                "latency_ms": metric.latency_ms
            })

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            collector.record(
                request_id=request_id,
                model="gpt-4o-mini",
                prompt=prompt,
                response="",
                latency_ms=latency_ms,
                success=False
            )
            results.append({
                "request_id": request_id,
                "error": str(e)
            })

    return results


def main():
    """메인 실행"""
    print("=" * 60)
    print("12장 실습: 운영 도구")
    print("=" * 60)

    # 1. 비용 추정
    print("\n[1] 비용 추정...")
    calculator = CostCalculator("gpt-4o-mini")

    # 예상 사용량 시나리오
    scenarios = [
        {"name": "일일 소규모", "input": 10_000, "output": 5_000},
        {"name": "일일 중규모", "input": 100_000, "output": 50_000},
        {"name": "일일 대규모", "input": 1_000_000, "output": 500_000},
    ]

    cost_estimates = []
    for scenario in scenarios:
        estimate = calculator.estimate_cost(scenario["input"], scenario["output"])
        cost_estimates.append({
            "scenario": scenario["name"],
            "model": estimate.model,
            "input_tokens": estimate.input_tokens,
            "output_tokens": estimate.output_tokens,
            "daily_cost_usd": estimate.total_cost_usd,
            "monthly_cost_usd": round(estimate.total_cost_usd * 30, 4)
        })
        print(f"    {scenario['name']}: ${estimate.total_cost_usd:.4f}/일, "
              f"${estimate.total_cost_usd * 30:.2f}/월")

    # 비용 추정 저장
    cost_result = {
        "generated_at": datetime.now().isoformat(),
        "model": "gpt-4o-mini",
        "pricing": PRICING["gpt-4o-mini"],
        "scenarios": cost_estimates
    }
    cost_path = OUTPUT_DIR / "ch12_cost_estimate.json"
    with open(cost_path, "w", encoding="utf-8") as f:
        json.dump(cost_result, f, ensure_ascii=False, indent=2)
    print(f"    저장: {cost_path}")

    # 2. 메트릭 수집
    print("\n[2] 메트릭 수집 (샘플 요청 실행)...")
    collector = MetricsCollector()
    request_results = run_sample_requests(collector)

    for result in request_results:
        if "error" in result:
            print(f"    {result['request_id']}: 실패 - {result['error']}")
        else:
            print(f"    {result['request_id']}: {result['tokens']} 토큰, "
                  f"${result['cost_usd']:.6f}, {result['latency_ms']:.0f}ms")

    summary = collector.get_summary()
    print(f"\n    총 요청: {summary['total_requests']}개")
    print(f"    성공률: {summary['success_rate']}%")
    print(f"    총 토큰: {summary['total_tokens']:,}개")
    print(f"    총 비용: ${summary['total_cost_usd']:.6f}")
    print(f"    평균 응답 시간: {summary['avg_latency_ms']:.0f}ms")

    # 메트릭 저장
    metrics_result = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "requests": [asdict(m) for m in collector.metrics]
    }
    metrics_path = OUTPUT_DIR / "ch12_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_result, f, ensure_ascii=False, indent=2)
    print(f"    저장: {metrics_path}")

    # 3. 체크리스트 생성
    print("\n[3] 운영 체크리스트 생성...")
    checklist = generate_checklist()
    checklist_path = OUTPUT_DIR / "ch12_checklist.md"
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(checklist)
    print(f"    저장: {checklist_path}")

    # 요약 출력
    print("\n" + "=" * 60)
    print("운영 도구 실행 결과 요약")
    print("=" * 60)
    print(f"비용 추정: {len(cost_estimates)}개 시나리오")
    print(f"메트릭 수집: {summary['total_requests']}개 요청, "
          f"총 ${summary['total_cost_usd']:.6f}")
    print(f"체크리스트: 5개 섹션 생성")

    return {
        "cost_estimates": cost_estimates,
        "metrics_summary": summary,
        "checklist_generated": True
    }


if __name__ == "__main__":
    main()
