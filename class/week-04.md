# Week 4. 첫 MCP 서버 만들기: 외부 API 래핑과 A2A 개요

> 원본: docs/ch4.md

## 학습 목표

- 외부 API를 MCP 서버로 래핑할 때 고려할 사항(인증/실패/로깅/테스트)을 설명한다
- OAuth 2.1 기반 원격 MCP 서버 인증의 흐름과 핵심 개념을 이해한다
- A2A(Agent-to-Agent) 프로토콜의 개념과 MCP와의 관계를 설명한다
- MCP, A2A, 직접 API 호출 중 상황에 맞는 프로토콜을 선택할 수 있다

---

## 선수 지식

- 3장에서 다룬 MCP 도구(tool) 설계 원칙과 명세 작성 방법을 이해하고 있어야 한다
- Python 기본 문법과 비동기 프로그래밍(async/await)에 대한 기초 지식이 있으면 따라오기 수월하다

---

## 4.1 외부 API 래핑의 목표와 고려사항

- MCP 서버로 외부 API를 래핑하는 것의 본질
  - 단순히 "호출을 감싸는 것"이 아니다
  - 에이전트가 안정적으로 사용할 수 있는 "계약(contract, 인터페이스 약속)"을 만드는 것이다
  - 3장: 도구 명세 = "무엇을 할 것인가"
  - 이 장: "어떻게 안전하게 할 것인가"를 다룬다

- 외부 API의 불확실성
  - 외부 API는 우리가 통제할 수 없는 영역이다
  - 네트워크는 언제든 끊길 수 있다
  - 서버는 과부하 상태일 수 있다
  - 인증 토큰은 만료될 수 있다
  - ⚠ 이런 불확실성을 MCP 서버 내부에서 처리하지 않으면, 에이전트는 예측할 수 없는 실패를 경험하게 된다

**표 4.1** 외부 API 호출 시 문제 유형과 대응 전략

| 문제 유형 | 원인 | 대응 전략 |
|----------|------|----------|
| 네트워크 오류 | 연결 실패, DNS 오류 | 재시도(지수 백오프) |
| 인증 실패 | 잘못된 키, 만료된 키 | 명확한 에러 메시지, 키 검증 |
| 레이트 리밋 | 요청 과다 | 대기 후 재시도, 캐싱 |
| 응답 지연 | 서버 과부하 | 타임아웃 설정, 취소 |
| 잘못된 응답 | API 스키마 변경 | 응답 검증, 폴백 처리 |

- 실습 예제: OpenWeatherMap API
  - 무료 티어를 제공한다
  - API 키 발급이 간단하다
  - 요청/응답 구조가 명확하다
  - 날씨 정보는 실시간 데이터이므로 실제 실행 결과를 확인하기에 적합하다

---

## 4.2 인증키 관리: .env와 환경 변수

- API 키를 코드에 하드코딩할 때 발생하는 보안 문제
  - 가장 흔한 실수: API 키가 포함된 코드를 Git 저장소에 커밋하는 것
    - 공개 저장소라면 즉시 노출된다
    - 비공개 저장소라도 팀원 변경이나 저장소 유출 시 위험해진다
  - 로그 파일에 요청 URL이 기록될 때
    - 쿼리 파라미터로 포함된 키가 함께 노출되는 경우도 있다

- 표준적인 해결 방법: 환경 변수 사용
  - Python에서는 `python-dotenv` 패키지를 사용한다
  - `.env` 파일에서 환경 변수를 로드할 수 있다

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENWEATHERMAP_API_KEY")
```

_전체 코드는 practice/chapter4/code/4-6-weather-mcp-server.py 참고_

- `.env` 파일 관리 규칙
  - ⚠ `.env` 파일은 반드시 `.gitignore`에 추가해야 한다
  - 대신 `.env.example` 파일을 만들어 필요한 환경 변수 목록을 공유하는 것이 좋은 관례이다

```
# .env.example
OPENWEATHERMAP_API_KEY=your_api_key_here
```

- 환경 변수 우선순위
  - 시스템에 이미 설정된 환경 변수가 있으면 `.env` 파일의 값보다 우선한다
  - 이 동작은 `python-dotenv`의 기본 설정이다
  - 프로덕션 환경에서 `.env` 파일 없이 시스템 환경 변수만으로 동작하게 할 때 유용하다

---

## 4.3 실패 처리: 타임아웃, 재시도, 에러 응답

- 실패 처리가 필요한 이유
  - 외부 API는 언제든 실패할 수 있다
  - "성공 경로"뿐 아니라 "실패 경로"도 설계해야 한다

- 실패 처리의 핵심 세 가지
  - 첫째: 무한 대기를 방지하는 타임아웃 설정
  - 둘째: 일시적 오류에 대응하는 재시도 전략
  - 셋째: 클라이언트가 이해할 수 있는 에러 응답 형식

### 타임아웃 설정

- 네트워크 요청에는 반드시 타임아웃을 설정해야 한다
- ⚠ 타임아웃 없이 요청을 보내면
  - 서버가 응답하지 않을 때 무한히 대기하게 된다
- `httpx` 라이브러리에서는 `timeout` 파라미터로 초 단위 타임아웃을 지정한다
- 일반적으로 외부 API 호출에는 10~30초 사이의 타임아웃이 적절하다

### 재시도 전략

- 모든 오류가 재시도 대상은 아니다
  - 재시도하면 안 되는 오류 (결과가 달라지지 않으므로 즉시 실패 반환)
    - 인증 실패(401): 키가 틀렸거나 만료된 경우
    - 잘못된 요청(400): 요청 자체가 잘못된 경우
  - 재시도하면 성공 가능성이 있는 오류
    - 서버 오류(5xx): 서버 측 일시적 장애
    - 네트워크 오류: 연결 일시 끊김

- 지수 백오프(exponential backoff, 재시도 대기 시간을 지수적으로 늘리는 방식) 적용
  - 첫 번째 재시도: 1초 후
  - 두 번째 재시도: 2초 후
  - 세 번째 재시도: 4초 후
  - 이유: 서버가 과부하 상태일 때 부하를 가중시키지 않으면서도 복구 후 빠르게 요청을 처리할 수 있다

```python
for attempt in range(max_retries):
    response = requests.get(url, timeout=10)
    if response.ok:
        break
    time.sleep(2 ** attempt)  # 지수 백오프: 1, 2, 4초
```

_전체 코드는 practice/chapter4/code/4-6-weather-mcp-server.py 참고_

### MCP 에러 응답 형식

- MCP 도구가 실패할 때 에러 반환 방식
  - ⚠ 단순히 예외를 발생시키는 것보다 구조화된 JSON 응답을 반환하는 것이 더 좋다
  - 이유: 에이전트가 실패를 처리하기 쉽다

→ 예시:
```json
{
  "success": false,
  "error": "API 요청 실패: 인증키가 유효하지 않습니다"
}
```

---

## 4.4 로깅: 요청과 응답을 추적 가능하게

- 로깅이 필수인 이유
  - 운영 환경에서 문제가 발생했을 때 원인을 파악하려면 로깅이 필수다
  - ⚠ 언제, 어떤 요청을 보냈고, 응답이 무엇이었는지 기록하지 않으면 문제 재현조차 어려워진다

- Python `logging` 모듈 활용
  - 로그 레벨별로 메시지를 분류할 수 있다
  - 파일이나 콘솔에 출력할 수 있다
  - 로그 레벨 (심각도 순서):
    - DEBUG: 상세 디버깅 정보
    - INFO: 일반 정보
    - WARNING: 경고
    - ERROR: 오류

```python
import logging

logging.basicConfig(
    filename="logs/mcp_server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
```

_전체 코드는 practice/chapter4/code/4-6-weather-mcp-server.py 참고_

- ⚠ 로깅 시 주의할 점: 민감 정보 마스킹
  - 로그에 그대로 기록하면 안 되는 정보: API 키, 사용자 개인정보, 인증 토큰
  - 실습 코드에서는 API 키를 마스킹하는 함수를 구현했다
  - → 예시: `abcd1234efgh5678` → `abcd...5678` 형태로 변환하여 기록

- ⚠ STDIO 기반 MCP 서버에서 특히 주의할 점
  - `print()` 함수를 사용하면 안 된다
  - 이유: MCP 프로토콜은 표준 출력(stdout)을 통해 통신하므로
    - `print()`로 출력한 내용이 프로토콜 메시지와 섞여 통신이 깨질 수 있다
  - 대안: `logging` 모듈을 사용하면 표준 에러(stderr)로 출력되어 안전하다

### 실패 사례: 로그에 API 키가 노출된 경우

- 사건 경위
  - 한 개발팀에서 날씨 MCP 서버를 운영하다가 보안 문제가 발생했다
  - 디버깅을 위해 요청 URL 전체를 로그에 기록했다
  - 쿼리 파라미터에 포함된 API 키가 그대로 노출되었다
  - 로그 파일이 모니터링 시스템으로 전송되면서 더 넓은 범위로 유출되었다

- 대응책 두 가지
  - 첫째: 로그 기록 전에 민감 정보를 마스킹한다
  - 둘째: 요청 URL 대신 엔드포인트와 파라미터를 분리하여 기록하고, API 키는 기록에서 제외한다
  - 실습 코드의 `_mask_api_key()` 함수가 이 패턴을 보여준다

---

## 4.5 테스트 가능한 구조: 의존성 분리

- 외부 API 의존 코드의 테스트 어려움
  - API 서버가 항상 동작한다고 보장할 수 없다
  - 테스트할 때마다 실제 요청을 보내면 비용이 발생할 수 있다
  - 테스트할 때마다 실제 요청을 보내면 레이트 리밋에 걸릴 수 있다

- 해결 방법: 의존성 분리 + 모킹(mocking, 가짜 객체로 실제 의존성을 대체하는 테스트 기법) 가능한 구조
  - 핵심: 의존성 주입(dependency injection, 필요한 객체를 외부에서 제공받는 설계 패턴)
    - API 클라이언트를 함수 내부에서 직접 생성하는 대신 외부에서 주입받도록 설계한다
    - 결과: 테스트 시에는 실제 클라이언트 대신 가짜(mock) 클라이언트를 주입할 수 있다

- 실습 코드의 구조
  - `WeatherAPIClient` 클래스로 API 호출 로직을 캡슐화했다
  - 이 클래스의 메서드들은 실제 API 호출 없이도 단위 테스트가 가능하다

**표 4.2** 단위 테스트 결과

| 테스트 항목 | 테스트 수 | 통과 | 실패 |
|------------|---------|------|------|
| API 키 마스킹 | 3 | 3 | 0 |
| 날씨 데이터 파싱 | 3 | 3 | 0 |
| 입력 검증 | 4 | 4 | 0 |
| **합계** | **10** | **10** | **0** |

- 테스트 결과는 `practice/chapter4/data/output/ch04_test_results.json`에 저장되어 있다

---

## 4.6 OAuth 2.1 인증: 원격 MCP 서버의 인증 프레임워크

- 배경
  - 4.2절: 로컬 환경에서 `.env`로 API 키를 관리하는 방법을 다루었다
  - 원격 MCP 서버를 운영하려면 클라이언트 인증이 필요하다
  - MCP 스펙은 2025년 3월부터 OAuth 2.1을 표준 인증 프레임워크로 채택했다
  - 이후 두 차례의 개정을 거쳐 보안 모델이 크게 강화되었다

### OAuth 2.1 도입과 진화

- 2025년 3월 스펙 (첫 도입)
  - MCP 서버가 리소스 서버와 인가 서버(authorization server, 토큰 발급을 담당하는 서버)의 역할을 동시에 수행했다
  - ⚠ 이 구조는 간단하지만 엔터프라이즈 환경에서 문제가 있었다
    - 이유: 조직은 이미 Okta, Azure AD 같은 중앙 인가 서버를 운영하고 있다
    - 각 MCP 서버마다 별도의 인가 기능을 구현하는 것은 비효율적이다

- 2025년 6월 스펙 (개선)
  - 리소스 서버(MCP 서버)와 인가 서버를 명확히 분리했다
  - RFC 9728(Protected Resource Metadata)을 필수로 적용했다
    - MCP 서버는 토큰을 검증만 한다
    - 토큰 발급은 외부 인가 서버가 담당한다
  - RFC 8707(Resource Indicators)을 도입했다
    - 클라이언트가 토큰 요청 시 대상 MCP 서버를 명시하도록 했다
    - 결과: 악의적인 서버가 다른 서버용 토큰을 탈취하는 공격을 방지한다

- 2025년 11월 스펙 (추가 강화)
  - PKCE(Proof Key for Code Exchange, 코드 탈취 공격을 방지하는 보안 확장)가 필수가 되었다
  - CIMD(Client ID Metadata Document, 클라이언트 등록을 간소화하는 문서 형식)가 도입되었다

### 인증 흐름 요약

- 원격 MCP 서버의 OAuth 2.1 인증 흐름 (단계별)
  1. MCP 클라이언트가 서버에 접속하면, 서버는 Protected Resource Metadata(RFC 9728)로 인가 서버 정보를 제공한다
  2. 클라이언트는 인가 서버에 PKCE를 포함한 인가 요청을 보낸다
  3. 사용자가 브라우저에서 인증하고 권한을 부여한다
  4. 클라이언트는 인가 코드와 PKCE 검증자를 교환하여 액세스 토큰을 받는다
  5. 클라이언트는 이 토큰으로 MCP 서버에 요청한다

- 실습과의 관계
  - 이 장의 실습에서는 로컬 STDIO 방식을 사용하므로 OAuth 인증이 필요하지 않다
  - ⚠ 프로덕션 환경에서 원격 MCP 서버를 배포할 때는 OAuth 2.1 인증을 반드시 구현해야 한다

---

## 4.7 A2A(Agent-to-Agent) 프로토콜 개요

- MCP와 A2A의 역할 구분
  - MCP: "에이전트와 도구 간" 통신을 표준화한다
  - A2A: "에이전트와 에이전트 간" 통신을 표준화한다

- A2A 프로토콜 소개
  - Google이 2025년 4월에 발표했다
  - 같은 해 6월 Linux Foundation에 이관했다
  - 목적: 서로 다른 프레임워크로 만들어진 에이전트들이 상호 운용할 수 있는 표준을 제공한다
  - 2026년 3월 기준으로 다수의 기술 기업과 플랫폼 벤더가 참여하고 있지만, 참여 조직 수는 발표 시점마다 달라지므로 공식 프로젝트 페이지를 확인하는 것이 안전하다

### A2A의 핵심 개념

- Agent Card (능력 광고)
  - A2A 서버는 `/.well-known/agent-card.json` 경로에 JSON 메타데이터를 게시한다
  - Agent Card에 포함되는 정보:
    - 에이전트의 이름
    - 설명
    - 지원 기능(스트리밍, 푸시 알림)
    - 인증 요구사항
  - 클라이언트 에이전트는 이 카드를 읽고 상대방의 능력을 파악한 후 작업을 위임할지 결정한다

- Client/Remote 모델
  - 클라이언트 에이전트: 작업을 위임하는 쪽
  - 리모트 에이전트: 작업을 수행하는 쪽
  - MCP의 클라이언트/서버 구조와 유사하다
  - 차이점: A2A에서는 양쪽 모두 자율적인 에이전트라는 점이 다르다

- 태스크 생명주기
  - A2A의 태스크는 일곱 가지 상태를 가진다:
    - `submitted`: 접수
    - `working`: 처리 중
    - `input-required`: 추가 입력 필요
    - `completed`: 완료
    - `failed`: 실패
    - `canceled`: 취소
    - `unknown`: 미확인
  - MCP의 Tasks primitive(3.2절)와 유사한 비동기 패턴이다

- 멀티모달 Parts (다양한 데이터 형식을 하나의 태스크에서 처리하는 구조)
  - A2A의 메시지와 아티팩트는 Part로 구성된다
  - Part의 세 가지 유형:
    - TextPart: 텍스트
    - FilePart: 파일
    - DataPart: 구조화된 JSON
  - 결과: 텍스트·이미지·파일·구조화 데이터를 하나의 태스크에서 주고받을 수 있다

- 기술 스택
  - JSON-RPC 2.0 over HTTP(S)를 사용한다
  - v0.3(2025년 7월)부터 gRPC도 지원한다

---

## 4.8 프로토콜 선택 기준: MCP vs A2A vs 직접 API 호출

- 에이전트 시스템을 설계할 때 "어떤 프로토콜을 사용할 것인가"는 중요한 의사결정 포인트다

**표 4.3** 프로토콜 선택 가이드

| 기준 | 직접 API 호출 | MCP | A2A |
|------|-------------|-----|-----|
| 통신 대상 | 단일 외부 서비스 | 에이전트 ↔ 도구/데이터 | 에이전트 ↔ 에이전트 |
| 적합한 상황 | 단순 통합, 일회성 호출 | 도구 재사용, 여러 클라이언트 지원 | 이종 에이전트 협업, 멀티벤더 |
| 표준화 수준 | 각 API마다 상이 | JSON-RPC 2.0, 도구/리소스 스키마 | JSON-RPC 2.0, Agent Card, Task |
| 초기 비용 | 낮음 | 중간 (서버 구현) | 높음 (에이전트 인프라) |
| 재사용성 | 낮음 (하드코딩) | 높음 (플랫폼 독립) | 높음 (프레임워크 독립) |

- 직접 API 호출이 적합한 경우
  - 외부 서비스를 한 곳에서만 사용한다
  - 도구를 재사용할 필요가 없다
  - 단순한 요청-응답으로 충분하다
  - → 예시: 특정 스크립트에서 날씨 API를 한 번 호출하는 정도라면 MCP 서버를 만들 필요가 없다

- MCP가 적합한 경우
  - 동일한 도구를 여러 AI 클라이언트(Claude, ChatGPT developer mode, Codex, 커스텀 에이전트)에서 사용한다
  - 도구의 접근 제어와 감사가 중요하다
  - → 예시: 이 장에서 만든 날씨 서버처럼, 한 번 잘 만들어두면 여러 프로젝트에서 재사용할 수 있다

- A2A가 적합한 경우
  - 서로 다른 팀이나 조직이 만든 에이전트들이 협업해야 한다
  - → 예시: 헬프데스크 에이전트가 모니터링 에이전트에게 서버 상태를 확인하고, 배포 에이전트에게 롤백을 요청하는 시나리오

- 실무에서의 MCP + A2A 조합 사용
  - 실무에서는 MCP와 A2A를 함께 사용하는 경우가 많다
  - 구조:
    - MCP로 개별 도구와 데이터 소스에 접근한다
    - A2A로 에이전트 간 작업을 위임한다
  - A2A의 실전 구현은 제7장에서 다룬다

---

## 4.9 실습: OpenWeatherMap API를 MCP 서버로 래핑

- 이 절의 목표
  - 앞서 설명한 원칙들을 적용하여 실제 MCP 서버를 구현한다
  - OpenWeatherMap의 Current Weather API를 래핑한다
  - 위도와 경도를 입력받아 현재 날씨 정보를 반환하는 도구를 만든다

### 환경 설정

- Python 가상환경 생성 및 의존성 설치

```bash
cd practice/chapter4
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

- `.env` 파일 생성 및 API 키 설정
  - API 키는 https://openweathermap.org/api 에서 무료로 발급받을 수 있다

```
OPENWEATHERMAP_API_KEY=your_api_key_here
```

### MCP 서버 구조

- FastMCP를 사용하여 MCP 서버를 구현한다
  - FastMCP의 특징: Python 타입 힌트와 docstring을 분석하여 자동으로 도구 스키마를 생성한다

```python
mcp = FastMCP("weather-server")

@mcp.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """지정된 위치의 현재 날씨를 조회합니다."""
```

_전체 코드는 practice/chapter4/code/4-6-weather-mcp-server.py 참고_

### 핵심 구현 요소

- 인증키 관리
  - `.env` 파일에서 API 키를 로드한다
  - 로그에는 마스킹된 형태로 기록한다

- 입력 검증
  - 위도는 -90~90 범위를 벗어나면 에러를 반환한다
  - 경도는 -180~180 범위를 벗어나면 에러를 반환한다

- 실패 처리
  - 타임아웃: 10초
  - 최대 재시도: 3회
  - 재시도 방식: 지수 백오프 적용

- 로깅
  - 모든 요청과 응답을 `logs/mcp_server.log`에 기록한다

- 응답 구조화
  - 원시 API 응답에서 필요한 정보만 추출한다
  - 일관된 형태로 반환한다

### 테스트 실행

- 테스트 클라이언트를 실행하여 핵심 로직을 검증할 수 있다

```bash
python3 code/4-6-test-client.py
```

- 테스트가 성공하면 `data/output/ch04_test_results.json`에 결과가 저장된다

### 의사결정 포인트

- HTTP 클라이언트 선택: `requests` vs `httpx`
  - MCP 서버는 비동기로 동작하므로 비동기를 기본 지원하는 `httpx`가 더 적합하다
  - ⚠ `requests`도 사용할 수 있지만, 별도의 스레드 풀이 필요해 복잡해진다

- 재시도 횟수와 타임아웃 결정
  - ⚠ 너무 짧으면 일시적 오류에 취약하다
  - ⚠ 너무 길면 사용자 경험이 나빠진다
  - 일반적인 웹 API의 적절한 출발점: 타임아웃 10초, 재시도 3회
  - 실제 운영에서는 API의 특성에 맞게 조정해야 한다

- 에러 메시지 상세도 결정
  - ⚠ 너무 상세하면 내부 구현이 노출될 수 있다
  - ⚠ 너무 간략하면 디버깅이 어렵다
  - 권장 방식: 클라이언트에게는 "인증 실패" 같은 개요만 전달하고, 상세 정보는 서버 로그에 기록한다

---

## 핵심 정리

- 외부 API를 MCP 서버로 래핑할 때는 인증, 실패 처리, 로깅, 테스트 가능한 구조를 함께 고려해야 한다
- API 키는 `.env` 파일로 분리하고, `.gitignore`에 추가하여 저장소에 커밋되지 않도록 한다
- 타임아웃과 재시도(지수 백오프)로 일시적 오류에 대응하고, 재시도 불가능한 오류는 즉시 반환한다
- 로깅은 문제 추적에 필수이지만, 민감 정보는 마스킹해야 한다
- 원격 MCP 서버는 OAuth 2.1(PKCE 필수)로 인증하며, 리소스 서버와 인가 서버를 분리한다
- MCP(에이전트↔도구)와 A2A(에이전트↔에이전트)는 상호보완적 프로토콜이다. 상황에 맞는 프로토콜을 선택한다

## 다음 장 예고

- 다음 장에서는 이 장에서 만든 MCP 서버를 LangChain 에이전트와 연결한다
- 다룰 내용:
  - 에이전트가 MCP 도구를 선택하고 호출하는 과정
  - 구조화된 출력(Structured Outputs)으로 도구 호출의 신뢰성을 높이는 방법
  - OpenAI Agents SDK와의 비교

---

## 참고문헌

Anthropic. (2025). Model Context Protocol - Build Server. https://modelcontextprotocol.io/docs/develop/build-server

Anthropic. (2025). MCP Authorization Specification. https://modelcontextprotocol.io/specification/draft/basic/authorization

Google. (2025). Announcing the Agent2Agent Protocol (A2A). Google Developers Blog. https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

Linux Foundation. (2025). Linux Foundation Launches the Agent2Agent Protocol Project. https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project

A2A Protocol. (2025). A2A Protocol Specification. https://a2a-protocol.org/latest/specification/

OpenWeatherMap. (2025). Current Weather Data API. https://openweathermap.org/current

Python Software Foundation. (2025). logging - Logging facility for Python. https://docs.python.org/3/library/logging.html

theskumar. (2025). python-dotenv. https://github.com/theskumar/python-dotenv
