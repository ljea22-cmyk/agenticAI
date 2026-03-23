# Week 2. 에이전트 개발 환경 구축과 실전 준비

> 원본: docs/ch2.md

## 학습 목표

- 재현 가능한 에이전트 개발 환경을 직접 구축할 수 있다
- MCP, Skills, Plugins/App/Connector, Instructions, Hooks, Memory의 역할 차이를 설명할 수 있다
- 실행 결과를 코드, 로그, 산출물, 체크리스트로 남기는 습관을 익힐 수 있다
- GitHub Copilot을 활용한 3주차 MCP·Skills 실습을 바로 수행할 수 있는 준비 상태를 만들 수 있다

---

## 선수 지식

- Python 기초 문법
- VS Code 또는 터미널 사용 경험
- Git의 기본 개념

---

## 2.1 왜 환경이 먼저인가

### 2.1.1 AI가 만든 코드는 왜 자주 깨지는가

- AI가 생성한 코드는 겉으로는 그럴듯해 보여도 실행 환경 차이를 자주 숨김
- 특히 다음 네 가지 문제가 반복됨
  - 패키지 버전 불일치
  - 운영체제 경로 차이
  - 인코딩 차이
  - 환경 변수와 비밀정보 처리 누락
- 예를 들어 AI가 `pandas`의 예전 API를 사용한 코드를 제안하면, 학생의 컴퓨터에서는 바로 `AttributeError`가 발생할 수 있음
- 따라서 에이전트 개발에서 첫 번째 역량은 "코드를 잘 생성하는 것"이 아니라 "같은 결과를 다시 실행할 수 있게 만드는 것"임

### 2.1.2 "내 컴퓨터에서는 된다"가 위험한 이유

- 이 말은 대개 실행 조건이 문서화되지 않았다는 뜻
- 에이전트 실습에서는 이 문제가 더 심각함
  - LLM이 어떤 도구를 호출했는지
  - 어떤 파일을 읽었는지
  - 어떤 환경 변수에 의존했는지
  - 어떤 출력을 남겼는지
  - 위 정보가 빠지면 같은 작업을 다시 재현하기 어려움
- 수업에서는 모든 실습을 다음 네 가지 산출물로 남기는 것을 기본 규칙으로 삼음
  - 코드
  - 실행 로그
  - 출력 파일
  - 체크리스트

### 2.1.3 에이전트 실습에서 환경 문제가 더 치명적인 이유

- 일반 스크립트는 한 번 실행해 보고 끝날 수 있음
- 그러나 에이전트 실습은 여러 층이 함께 동작함
  - 모델 API
  - 도구 호출
  - 외부 파일 또는 API
  - 규칙 파일
  - 출력 저장
- 즉, 한 곳만 어긋나도 전체 실습이 실패함
- 그래서 2주차의 목표는 "파이썬 환경 설정" 그 자체가 아니라, 이후 주차 전체를 받을 수 있는 **에이전트 실습 기반**을 만드는 것임

---

## 2.2 2026년 에이전트 개발의 전체 지도

### 2.2.1 여섯 가지 층위

- 2026년의 에이전트 개발은 하나의 기술로 끝나지 않음
- 최소한 여섯 가지 층을 구분해서 이해해야 함

**표 2.1** 에이전트 개발의 여섯 가지 층위

| 층위 | 역할 | 대표 예시 |
|------|------|----------|
| 도구 연결 | 외부 시스템과 연결 | MCP |
| 작업 규칙 | 어떤 순서와 기준으로 일할지 정의 | Skills, Instructions |
| 자동 실행 | 특정 이벤트 전후 동작 연결 | Hooks |
| 실행 오케스트레이션 | 단일/복수 에이전트의 흐름 제어 | LangChain, LangGraph, Agents SDK |
| 지속 문맥 | 팀 규칙과 장기 컨텍스트 유지 | Memory, Spaces, Project memory |
| 지식 공급 | 외부 문서와 기억을 제공 | RAG |

- 이 수업의 이후 흐름도 이 여섯 층을 점진적으로 쌓는 구조로 이해하면 편함

### 2.2.2 MCP, Skills, Plugins/App/Connector는 어떻게 다른가

- **MCP**
  - 에이전트가 외부 도구나 데이터를 사용할 수 있게 해 주는 표준 인터페이스
  - 질문: "무엇을 호출할 수 있는가?"
- **Skills / Instructions**
  - 에이전트가 작업할 때 따라야 할 절차와 규칙 (업무 매뉴얼에 해당)
  - 예: "결과물은 output/에 저장해", "위험한 명령은 실행 전에 확인받아"
  - 질문: "어떻게 일하게 할 것인가?"
- **Plugins / Apps / Connectors**
  - Skills, MCP, Hooks 등을 하나로 묶어서 설치·공유할 수 있게 포장하는 배포 단위 (공구 세트 패키지에 해당)
  - 예: `copilot plugin install ./my-plugin` 한 줄로 Skills 3개 + MCP 서버 1개를 한번에 설치
  - 질문: "여러 기능을 어떻게 묶어서 배포할 것인가?"


### 2.2.3 Instructions, Hooks, Memory는 왜 따로 봐야 하는가

- **Instructions / Rules / Settings**
  - 기본 행동 규칙을 고정하는 계층
  - 예: 출력은 항상 `output/`, 파괴적 명령은 승인 전 금지
- **Hooks**
  - 특정 이벤트 전후에 자동 실행을 연결하는 계층
  - 예: 작업 후 로그 저장, 명령 전 검증, 테스트 실행
- **Memory / Spaces / Project memory**
  - 한 번의 세션을 넘어 프로젝트 맥락을 유지하는 계층
  - 예: 팀 규칙, 선호 출력 형식, 기본 디렉토리 구조

### 2.2.4 이 수업에서의 해석

- 수업에서는 다음처럼 단순하게 잡음
  - MCP = 도구 연결
  - Skills = 작업 매뉴얼
  - Plugin/App/Connector = 제품별 포장과 연결 방식
  - Instructions = 기본 행동 규칙
  - Hooks = 자동 검사와 자동 실행
  - Memory = 지속 컨텍스트
- 이후 주차에서 프레임워크와 RAG를 배우더라도, 이 구분은 계속 유지해야 함

---

## 2.3 재현 가능한 로컬 개발 환경 구축

### 2.3.1 Python 가상환경 생성

- 프로젝트마다 독립적인 실행 환경을 두기 위해 가상환경을 사용함
- 가장 기본적인 방법은 `venv`

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

- 활성화 후에는 `python`과 `pip`가 가상환경 기준으로 동작함
- 이후 모든 실습은 기본적으로 가상환경 안에서 실행한다고 가정함

### 2.3.2 의존성 고정

- 실습이 끝난 뒤에도 같은 결과를 재현하려면 버전 고정이 필요함
- 최소한 다음 파일은 유지해야 함
  - `requirements.txt`
  - 필요하다면 `requirements-dev.txt`
- 처음에는 단순하게 시작해도 됨

```bash
pip freeze > requirements.txt
```

- 중요한 점:
  - "무조건 freeze를 자주 하라"가 아님
  - **현재 실습이 성공한 환경을 기록하라**가 핵심

### 2.3.3 `.env`와 `.env.example`

- API 키, 토큰, 민감한 설정은 코드에 직접 쓰지 않음
- 다음 두 파일을 구분함
  - `.env`: 실제 값 저장
  - `.env.example`: 필요한 변수 이름과 예시만 공유

예시:

```env
OPENAI_API_KEY=
GITHUB_TOKEN=
PROJECT_NAME=agenticAI
```

- `.env`는 반드시 `.gitignore`에 포함

### 2.3.4 경로와 폴더 구조 표준화

- 실습 파일이 어디에 있어야 하는지 통일하지 않으면 결과를 찾기 어려움
- 수업 권장 구조:

```text
agenticAI/                  # 클론된 저장소 루트
  class/                    # 주차별 강의 자료
  practice/                 # 기존 실습 자료
  code/                     # 실습 코드
  data/                     # 입력 데이터
  output/                   # 실행 결과
  logs/                     # 실행 로그
  docs/                     # 설명과 설계 기록
  .env.example
  requirements.txt
  checklist.md
```

- 실습은 **클론된 `agenticAI/` 저장소 안에서 바로 수행**함
- 별도 디렉토리를 만들지 않고 저장소 루트의 `code/`, `output/`, `logs/`, `docs/`를 사용함
- `output/`에는 실행 결과
- `logs/`에는 실행 로그
- `docs/`에는 간단한 설명과 설계 기록을 둠

### 2.3.5 `.gitignore`의 최소 규칙

```gitignore
.venv/
__pycache__/
*.pyc
.env
output/
logs/
```

- 이 규칙은 "무조건 숨기기"가 아니라
  - 민감정보 보호
  - 불필요한 파일 제외
  - 협업 혼란 방지
를 위한 최소 장치임

### 2.3.6 GitHub Copilot 실습 환경 확인

- 2주차부터의 실습은 **GitHub Copilot 중심**으로 진행함
- 권장 환경
  - VS Code 최신 안정 버전
  - GitHub Copilot 확장
  - GitHub Copilot Chat 확장
- 기본 확인 절차
  1. VS Code에서 Copilot Chat을 연다
  2. 채팅 패널에서 **Agent** 모드를 선택할 수 있는지 확인한다
  3. 간단한 프롬프트를 보내 응답이 오는지 확인한다
  4. 터미널 명령 제안이 나타날 경우 승인 절차가 어떻게 보이는지 확인한다
- 이후 3주차 MCP 실습에서는 Agent 모드가 기본 진입점이 됨
- Skills 실습까지 바로 이어서 하려면 다음 중 하나를 권장함
  - VS Code Insiders
  - GitHub Copilot CLI

### 2.3.7 Copilot 실습에 필요한 최소 설정 메모

- Agent mode
  - 복수 파일 수정, 터미널 명령 제안, 반복 수정이 필요한 작업에 사용
- MCP
  - 외부 도구 연결이 필요한 작업에 사용
- Skills
  - 반복 작업 규칙과 절차를 주입할 때 사용
- Custom instructions
  - 저장소 또는 사용자 수준 기본 규칙을 둘 때 사용
- Hooks
  - 작업 전후 자동 검증을 붙일 때 사용
- Memory / Spaces
  - 반복되는 프로젝트 맥락을 유지할 때 사용
- 주의
  - 현재 공식 문서 기준으로 Agent Skills는 Copilot coding agent, Copilot CLI, VS Code Insiders에서 우선 지원됨

---

## 2.4 에이전트 실습용 프로젝트 템플릿 만들기

### 2.4.1 표준 실행 규칙

- 모든 실습은 다음 세 가지 질문에 답할 수 있어야 함
  1. 무엇을 실행했는가
  2. 어디에 결과가 저장되었는가
  3. 어떻게 검증했는가

- 따라서 실습용 스크립트는 가능한 한 다음 패턴을 따름
  - 입력을 명확히 받는다
  - 출력 파일 경로를 정한다
  - 실행 결과를 저장한다
  - 오류가 나면 로그를 남긴다

### 2.4.2 "실행-검증-저장" 패턴

- 수업에서 반복해서 사용할 기본 패턴:
  1. 실행한다
  2. 결과를 확인한다
  3. 산출물을 파일로 저장한다

- 이 패턴이 중요한 이유:
  - AI가 "성공했다"고 말하는 것과 실제 성공은 다름
  - 파일로 남겨야 나중에 다시 볼 수 있음
  - 팀원이 같은 결과를 확인할 수 있음

예시 코드:

```python
from pathlib import Path

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

result_path = output_dir / "hello.txt"
result_path.write_text("agent starter is ready\n", encoding="utf-8")

print(f"saved: {result_path}")
```

### 2.4.3 이후 주차를 위한 연결 지점

- 3주차에는 이 템플릿에 MCP 설정과 skill 파일이 추가됨
- 5주차 이후에는 같은 구조 안에서 LangChain, LangGraph, 멀티에이전트 실습이 이루어짐
- 즉, 2주차 템플릿은 일회성 과제가 아니라 학기 전체의 바탕이 됨

---

## 2.5 체크리스트 기반 검증 습관

### 2.5.1 작업 전 체크리스트

- 실행 전에 먼저 정리해야 할 항목
  - 작업 범위
  - 입력값
  - 제약 조건
  - 검증 방법
  - 안전 항목

예시:

```markdown
- 작업 범위: starter 프로젝트 구조 생성
- 입력: Python 3.11, 로컬 터미널
- 제약: API 키를 코드에 넣지 않음
- 검증: output/hello.txt 생성 여부 확인
- 안전: .env는 커밋하지 않음
```

### 2.5.2 작업 후 체크리스트

- 실습 후에는 같은 문서를 기준으로 결과를 다시 점검함
  - 실제 실행했는가
  - 출력 파일이 생성되었는가
  - 로그가 남았는가
  - 제약을 어기지 않았는가
  - 문제가 있었다면 무엇을 수정했는가

### 2.5.3 체크리스트는 계획표이자 검수표

- 체크리스트는 단순 메모가 아님
- 역할이 두 가지 있음
  - 작업 전: 계획표
  - 작업 후: 검수표
- 이 습관은 3주차 이후 MCP, Skills, LangGraph, RAG 실습에도 그대로 적용됨

---

## 2.6 실습 1: 에이전트 스타터 프로젝트 구축

### 실습 목표

- GitHub Copilot이 안정적으로 작업할 수 있는 재현 가능한 실습 프로젝트를 직접 만든다

### 수행 단계

1. 클론된 `agenticAI/` 저장소로 이동한다
2. 가상환경 `.venv`를 생성하고 활성화한다 (이미 `venv/`가 있으면 그것을 사용해도 됨)
3. 저장소 루트에 `code/`, `output/`, `logs/`, `docs/` 디렉토리가 없으면 만든다
4. `.env.example`와 `requirements.txt`를 확인하고 없으면 만든다
5. `code/env_check.py` 또는 `code/hello_agent.py`를 작성한다
6. 실행 결과를 `output/`에 저장한다

### GitHub Copilot 활용 방식

- Copilot Chat의 **Agent 모드**를 열고 다음과 같이 요청한다

```text
이 저장소를 에이전트 실습용 구조로 정리해줘.
다음 조건을 지켜줘:
- code, output, logs, docs 디렉토리가 없으면 만든다
- .env.example, requirements.txt, checklist.md를 확인하고 없으면 만든다
- output/hello.txt를 생성하는 최소 실행 스크립트를 code/hello_agent.py로 작성한다
- 터미널 명령은 실행 전에 나에게 보여준다
```

- 학생이 직접 확인해야 할 것
  - Copilot이 어떤 파일을 만들었는가
  - 터미널 명령을 언제 제안했는가
  - 생성된 파일 구조가 요구사항과 일치하는가
  - `output/hello.txt`가 실제로 생성되는가

### 권장 확인 항목

- [ ] 가상환경이 활성화되었는가
- [ ] `requirements.txt`가 존재하는가
- [ ] `.env.example`가 존재하는가
- [ ] 실행 결과 파일이 `output/`에 저장되었는가
- [ ] 체크리스트 문서를 작성했는가

---

## 2.7 실습 2: 첫 규칙 파일 만들기

### 실습 목표

- GitHub Copilot이 규칙의 영향을 어떻게 받는지 체감한다

### 과제 설명

- 학생은 "이 프로젝트에서 AI가 따라야 할 규칙"을 짧은 파일로 작성한다
- 형식은 자유이지만 다음 내용이 포함되어야 함
  - 출력 파일은 반드시 `output/`에 저장
  - 비밀정보를 코드에 쓰지 않음
  - 실행 전에 체크리스트를 확인
  - 실행 후 로그와 결과를 남김
  - 실패 시 원인과 수정 내용을 기록

### 실습 포인트

- 이 파일은 아직 정식 Skills 문법을 배우는 단계는 아님
- 목적은 "규칙을 적어 두면 결과의 일관성이 올라간다"는 점을 먼저 체감하는 것
- 3주차에서는 이 규칙 개념을 MCP 및 실제 skill 파일과 연결함

### GitHub Copilot 활용 방식

- 먼저 규칙 파일 없이 Agent 모드에서 다음 작업을 요청한다

```text
code/hello_agent.py를 개선하고 실행 로그를 남겨줘.
```

- 다음으로 `docs/agent-rules.md` 같은 규칙 파일을 만든 뒤 다시 요청한다

```text
docs/agent-rules.md의 규칙을 따르면서 code/hello_agent.py를 개선하고 실행 로그를 남겨줘.
```

- 비교할 항목
  - 출력 위치가 더 일관적인가
  - 로그를 더 잘 남기는가
  - 검증 항목을 명시하는가
  - 불필요한 파일을 덜 만드는가

### 확장 활동 1: 이 규칙을 instruction으로 올릴 것인가 판단하기

- 학생은 자신이 만든 규칙 중 무엇이 "매번 공통 적용"인지 구분한다
- 예:
  - 항상 `output/`에 저장 → instruction이나 settings에 적합
  - 이번 과제에서만 특정 형식 사용 → task-specific rule에 적합

### 확장 활동 2: 어떤 검증을 hook으로 바꿀 수 있는가

- 다음 중 하나를 골라 자동화 후보로 적는다
  - 출력 파일 생성 여부 확인
  - 로그 남기기
  - 테스트 실행 여부 확인
  - 위험 명령 차단

### 확장 활동 3: 무엇을 memory에 남길 것인가

- 학생은 프로젝트가 계속 기억해야 할 항목 3개를 적는다
- 예:
  - 기본 출력 위치
  - 기본 검증 절차
  - 금지 명령 목록

---

## 2.8 제출물

- `agenticAI/` 저장소 내 실습 디렉토리 (`code/`, `output/`, `logs/`, `docs/`)
- `requirements.txt`
- `.env.example`
- `checklist.md`
- 규칙 파일 1개
- 실행 로그 1개 이상
- 출력 파일 1개 이상

---

## 2.9 핵심 정리

- 에이전트 개발의 출발점은 화려한 자동화가 아니라 재현 가능한 환경이다
- MCP, Skills, Plugins/App/Connector, Instructions, Hooks, Memory는 같은 것이 아니라 서로 다른 층위다
- 좋은 실습은 코드만 남기는 것이 아니라, 실행 로그와 검증 기준까지 함께 남긴다
- 2주차의 산출물은 3주차 MCP·Skills 실습의 기반이 된다

---

## 부록 A. Claude Code로 같은 실습을 수행하는 방법

- 이 부록은 본문과 같은 실습을 **Claude Code**로 수행하는 최신 공식 흐름을 정리한 것임
- Claude Code는 터미널 중심 도구이지만, VS Code 통합 기능을 함께 사용할 수 있음

### A.1 VS Code에서 Claude Code 시작

1. VS Code를 연다
2. 통합 터미널을 연다
3. `claude`를 실행한다
4. 필요하면 `/config`에서 diff viewer를 `auto`로 맞춘다

- 최신 공식 문서 기준 특징
  - 통합 터미널에서 `claude`를 실행하면 VS Code 통합이 자동 활성화될 수 있음
  - 선택 영역 공유, 진단 공유, IDE diff 보기 기능을 사용할 수 있음

### A.2 Claude Code로 2주차 실습 수행 예시

- starter 프로젝트 생성 요청 예시

```text
이 저장소를 에이전트 실습용 starter 프로젝트로 정리해줘.
다음 항목이 필요해:
- code, output, logs, docs 디렉토리
- .env.example
- requirements.txt
- checklist.md
- output/hello.txt를 만드는 최소 실행 스크립트
작업 후 어떤 파일을 만들었는지와 검증 방법도 정리해줘.
```

- 규칙 파일 적용 예시

```text
docs/agent-rules.md를 읽고 그 규칙을 지키면서 hello_agent.py를 수정해줘.
수정 후 실행 로그와 출력 파일도 남겨줘.
```

### A.3 Claude Code 사용 시 확인할 점

- 파일 변경 내용을 IDE diff에서 검토했는가
- 실행 명령과 수정 내용이 일치하는가
- 출력 파일과 로그가 실제로 남았는가
- 규칙 파일을 반영했는가

---

## 부록 B. ChatGPT / Codex로 같은 실습을 수행하는 방법

- OpenAI 쪽 표면은 2026년 3월 현재 크게 세 층으로 나누어 이해하는 것이 좋음
  - ChatGPT Apps: ChatGPT 안에서 외부 도구와 데이터를 붙이는 표면
  - Codex app / IDE / CLI: 실제 코딩 작업을 수행하는 에이전트 표면
  - MCP / Skills / Rules: 도구 연결과 작업 규칙을 구성하는 계층

### B.1 어떤 표면을 사용할 것인가

- **ChatGPT Apps**
  - ChatGPT 대화 안에서 외부 앱을 연결하고 검색·참조·작업을 수행할 때 사용
- **Codex**
  - 저장소를 직접 열고 파일 편집, 명령 실행, 테스트를 포함한 코딩 작업을 할 때 사용

### B.2 2주차 실습에 맞는 사용 방식

- starter 프로젝트 구축과 실행 결과 저장은 **Codex app / CLI / IDE extension**이 더 적합함
- 외부 서비스 연결 구조를 미리 체험하는 데에는 **ChatGPT Apps**가 이해하기 쉬움

### B.3 Codex로 2주차 실습 수행 예시

- Codex app 또는 CLI/IDE extension에서 다음처럼 요청

```text
이 저장소를 에이전트 실습용 starter 프로젝트로 정리해줘.
필요한 항목:
- code, output, logs, docs 디렉토리
- .env.example
- requirements.txt
- checklist.md
- output/hello.txt를 생성하는 최소 실행 스크립트
실행 결과와 검증 항목도 함께 남겨줘.
```

- 확인할 점
  - 결과 파일이 실제로 생성되는가
  - 로그와 체크리스트가 남는가
  - 규칙 없이 수행했을 때와 규칙을 준 뒤 결과가 달라지는가

### B.4 ChatGPT Apps와의 연결 감각 익히기

- ChatGPT에서는 2025년 12월부터 connectors가 **apps**로 통합되어 안내됨
- 학생은 이 시점에 "제품 안에서 기능을 붙인다"는 감각만 먼저 잡으면 충분함
- 3주차에서 MCP와 Apps의 관계를 더 정확히 구분한다

---

## 참고 자료

- GitHub Copilot agent mode: https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-your-ide
- GitHub Agent Skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- GitHub Copilot CLI: https://docs.github.com/en/free-pro-team%40latest/copilot/how-tos/copilot-cli/use-copilot-cli
- Claude Code IDE integration: https://docs.anthropic.com/en/docs/claude-code/ide-integrations
- Claude Code settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Claude Code common workflows: https://docs.anthropic.com/en/docs/claude-code/common-workflows
- Claude Code hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Codex app: https://openai.com/index/introducing-the-codex-app/
- Codex with ChatGPT plans: https://help.openai.com/en/articles/11369540/
- Apps in ChatGPT: https://help.openai.com/en/articles/11487775-connectors-in-chatgpt

---

## 다음 주 예고

- 3주차에서는 실제로 MCP 서버를 연결하고 호출해 본다
- 같은 작업에 규칙 파일을 적용하여 결과의 차이를 비교한다
- 최소 MCP 서버를 직접 구현하고 단독 테스트한다
