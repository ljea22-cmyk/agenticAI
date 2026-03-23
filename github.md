### 주의사항: 모든 컴퓨터 조작에서 한글 사용금지하고 반드시 영어문자를 사용해야 한다. 폴더명, 파일명 등등. 한글 사랑과 별개의 문제로서 피할 수 없는 문제이다. 

### 검색 - cmd - 작업표시줄에 고정 

# Git & GitHub & Copilit 가이드

## 1단계: Git 설치 (3분)

**Windows**: https://git-scm.com/download/win → 다운로드 후 설치 (기본값 OK)

**macOS**: 터미널에서 실행

```bash
xcode-select --install
```

설치 확인:

```bash
git --version
```

## 2단계: GitHub 가입 (2분)

1. https://github.com 접속
2. "Sign up" → 학교 이메일로 가입
3. 이메일 인증 

또는 구글 아이디 로그인도 됨

username 반드시 복사해놓을것 

## 3단계: 로컬 연결 (1분)

> VSCode 통합 터미널(Ctrl+`), CMD, PowerShell 중 어디서든 실행 가능

```bash
git config --global user.name "홍길동"   <- 복사해놓은 유저네임 사용
git config --global user.email "학교이메일@ac.kr"
```


# GitHub Copilot 대학생 무료 사용 방법

GitHub는 **Copilot Free** (제한된 무료 플랜)와 **Copilot Pro** (고급 기능 풀버전)을 구분해서 운영하고 있으며,

**검증된 학생**은 **Copilot Pro**를 **학생 신분 유지 기간 동안 완전 무료**로 사용할 수 있습니다.

### 현재(2026년) 상황 요약

| 구분               | 대상자                     | 가격     | 주요 제한사항                                   | 모델/기능 수준          |
| ------------------ | -------------------------- | -------- | ----------------------------------------------- | ----------------------- |
| Copilot Free       | 누구나                     | 무료     | 월 2,000 코드 완성, 50 채팅 등 매우 제한적      | 기본 모델               |
| Copilot Pro        | 일반인                     | 월 $10   | 300 premium requests + 추가 과금 가능           | 최신 모델 풀 액세스     |
| Copilot Pro (학생) | GitHub Education 검증 학생 | **무료** | 월 300 premium requests (초과 시 다음달 초기화) | Pro 풀 기능 + 최신 모델 |

→ **우리가 원하는 건 Copilot Pro 무료**이며, 이를 위해서는 **GitHub Student Developer Pack** 승인이 필수입니다.

### 2026년 최신 정확한 등록 절차 (단계별)

1. **GitHub 계정 준비**
   - 이미 계정이 있다면 로그인
   - 없다면 [https://github.com](https://github.com/) 에서 새로 생성 (학교 이메일)
   - 기존 계정이 있으면 설정(https://github.com/settings/emails)에서 학교 이메일(.ac.kr)을 추가
   - **학교 이메일을 primary email(기본 이메일)로 설정** (드롭다운에서 선택 후 Save → 인증 인식을 도움. 나중에 개인 이메일로 되돌릴 수 있음)
   - 이메일 추가 후 verification link(인증 링크)를 클릭해 verified 상태로 만들기
2. **GitHub Student Developer Pack 신청 페이지 이동**

   https://education.github.com/pack

   또는 [https://education.github.com](https://education.github.com/) → "Get your pack" 클릭

3. **학생 신분 증명** (가장 중요한 단계)

   대부분의 한국 대학생이 성공하는 순서 (우선순위 높은 순) :

   | 순위 | 증빙 방법                       | 성공률    | 소요시간    | 비고                                        |
   | ---- | ------------------------------- | --------- | ----------- | ------------------------------------------- |
   | 1    | 학교 공식 이메일 (.ac.kr)       | 매우 높음 | 즉시~수시간 | 대부분 자동 승인                            |
   | 2    | 학생증 사진 (재학증명서) 업로드 | 높음      | 1~5일       | 선명하게 촬영, 이름·학번·유효기간 보여야 함 |
   | 3    | 재학증명서 PNG 파일 업로드           | 높음      | 1~7일       | 최근 3개월 이내 발급본                      |
   | 4    | 등록금 영수증 + 신분증          | 중간      | 3~10일      | 최후의 수단                                 |

   → **한국 4년제 대학 재학생이라면 대부분 학교 이메일만으로 1~24시간 내 자동 승인**됩니다.
   -> 재학증명서는 영문으로 받고 파일이 pdf 형태이니 아래의 사이트에서 이미지 파일로 변환한다. 
   [text](https://smallpdf.com/kr/pdf-to-jpg?mu=b5Vg&mau=b5Vg&utm_campaign=21930591768_179389838308_pdf%20%EC%9D%B4%EB%AF%B8%EC%A7%80%EB%B3%80%ED%99%98&utm_source=google&utm_medium=cpc&gad_source=1&gad_campaignid=21930591768&gbraid=0AAAAAoxWdI5FDXktGvqJ9ZNyQLXTc8MDQ&gclid=CjwKCAiAtq_NBhA_EiwA78nNWFiUmnB1IOiTjRV7UCOpP2bQMjfGXFEvuXCIDTDwhh8wizmKkR-nyxoC0hQQAvD_BwE)

4. **승인 확인**
   - https://education.github.com/pack 에서 "Your pack" 상태 확인
   - 승인 메일 도착 (보통 "You're all set!" 제목)
5. **Copilot Pro 무료 활성화** (승인 후 바로 가능)

   두 가지 방법 중 편한 것 선택:

   방법 A (가장 확실)
   - https://github.com/settings/copilot 이동
   - "Code, planning, and automation" → Copilot 클릭
   - 학생 혜택으로 무료 가입 버튼 나타남 → 클릭

   방법 B
   - https://github.com/features/copilot 로 이동
   - 학생으로 인식되면 "무료로 시작" 또는 "Claim free access" 버튼 등장

   방법 C (학생/교사 전용 무료 signup 페이지)
   - https://github.com/github-copilot/free_signup 으로 직접 이동

   > **주의**: 신용카드 입력이 요구되면 진행하지 마십시오. 학생 혜택은 완전 무료이며 결제 정보가 필요하지 않습니다.

6. **VS Code 등 에디터에서 사용 시작**
   - GitHub 계정으로 Copilot 확장 로그인
   - 학생 혜택이 정상 적용되어 풀 Pro 기능 사용 가능

### 주의사항 (2026년 기준 자주 발생하는 문제)

- 승인 후에도 바로 안 보일 때 → 72시간까지 기다린 뒤 재로그인 시도 (Incognito/시크릿 모드 사용 추천). 혜택 동기화에 72시간~최대 2주가 소요될 수 있음
- "무료 버튼이 안 보임" → 캐시 지우기 / 다른 브라우저 시도 / primary email을 학교 이메일로 재설정 후 대기 / https://github.com/settings/copilot 직접 들어가기
- 인증 실패 시 → GitHub Support(https://support.github.com/contact/education)에 티켓 제출 (카테고리: "Student having trouble redeeming offers")
- 월 300 premium requests 제한은 학생도 동일 (과거에는 무제한이었으나 2025년 중반부터 변경됨)
- 졸업하면 자동으로 Pro 유료 전환됨 → 재학생 기간에 최대한 활용 권장
- 공식 문서 참조: https://docs.github.com/en/education

위 방법은 2026년 2월 6일 기준 GitHub 공식 문서 및 실제 학생 사례들을 종합한 **현재 가장 정확한 절차**입니다.

학교 이메일이 있다면 거의 100% 성공한다고 봐도 무방합니다.
---


## 🚀 시작하기

### 1단계: VSCode 설치

1. https://code.visualstudio.com/ 에서 다운로드 후 설치
2. 설치 시 **"Add to PATH" 옵션 체크** 권장
3. 설치 후 실행하여 다음 확장(Extensions)을 설치:
   - **Python** (Microsoft) — Python 개발 지원
   - **Jupyter** (Microsoft) — 노트북(.ipynb) 실행 지원

> 좌측 사이드바 확장 아이콘(□) 클릭 → 검색창에 "Python", "Jupyter" 입력 → Install  
> 파일 메뉴 - 자동 저장 클릭

### 2단계: Python 설치

1. https://www.python.org/downloads/ 에서 **Python 3.12** 이상 다운로드
2. 설치 프로그램 실행
3. **⚠️ 첫 화면에서 반드시 "Add python.exe to PATH" 체크** ← 가장 중요!
4. **"Install Now"** 클릭

설치 확인 (Windows: `Win+R` → `cmd` 입력 → 확인):

```bash
python --version
```

`Python 3.x.x`가 출력되면 성공입니다. 만약 `'python' is not recognized...` 오류가 나면 PATH 등록이 안 된 것이므로 Python을 제거 후 3번을 확인하며 재설치하세요. 

### 3단계: Copilot 확장 설치

1. VS Code를 실행한다.
2. 왼쪽 사이드바에서 **Extensions**(확장) 아이콘을 클릭한다.
3. 검색창에 `GitHub Copilot`을 입력하고 **GitHub Copilot** 확장을 설치한다.
4. 같은 방법으로 **GitHub Copilot Chat** 확장도 설치한다.
5. Command Palette(Ctrl+Shift+P 또는 Cmd+Shift+P)를 열고 "Copilot: Sign In"을 선택하여 GitHub 계정으로 로그인한다.
6. 우측 하단 상태바에서 Copilot 아이콘이 활성화되었는지 확인한다.


### 4단계: 저장소 클론

명령 프롬프트 열기 (Windows: `Win+R` → `cmd` 입력 → 확인):

```bash
cd C:\
git clone https://github.com/LeeSeogMin/agenticAI.git
```

`C:\agenticAI` 폴더가 생성되면 성공입니다.

---



# GitHub Copilot에서 MCP(Model Context Protocol) 사용 방법

**MCP 정의 및 객관적 평가**:

MCP는 Anthropic(Claude 개발사)이 주도한 오픈 표준 프로토콜로, GitHub Copilot(특히 Agent 모드)의 기능을 외부 도구/API/데이터 소스(예: GitHub 리포, Figma, DB)와 연동하여 확장합니다. Copilot Free/Pro(학생 무료 포함)에서 지원되며, VS Code 1.102+에서 GA(General Availability). 그러나 엔터프라이즈/조직 계정은 "MCP servers in Copilot" 정책 활성화 필수. 학생 계정(Pro 무료)은 quota(월 300 premium requests) 내에서 동일하게 동작하나, Claude 모델 사용 시 무한 루프 버그 보고됨(quota 소모, VS Code 크래시 유발 – GitHub 이슈 #165430 참조).

**Copilot Pro(학생 무료)와 MCP 호환성**:

- 학생 Developer Pack 승인 후 [https://github.com/settings/copilot에서](https://github.com/settings/copilot%EC%97%90%EC%84%9C) Pro 활성화 → Agent 모드/MCP 풀 액세스.
- 제한: MCP 도구 호출 시 premium requests 차감(초과 시 다음달 리셋). Claude Code MCP 직접 통합은 비공식(제안 단계, GitHub Discussion #166967). bkit/clawdbot/OpenClaw는 Claude 전용(별도 MCP 서버); Copilot과 직접 연동 안 됨 – 검색 결과 0.

### 지원 환경 및 요구사항 (데이터 기반 표)

| 항목              | 세부사항                                                                                                                      | 학생 Pro 적용 여부                                            |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **IDE**           | VS Code 1.102+ (Insiders 권장), JetBrains, Xcode, Copilot CLI                                                                 | O (VS Code 최적)                                              |
| **Copilot**       | Pro 이상 (Free: 기본 Chat만; 학생 무료 Pro 풀 기능)                                                                           | O                                                             |
| **MCP 서버 예시** | GitHub MCP (리포/이슈/PR 관리), Figma MCP (디자인→코드), Mermaid MCP (다이어그램 생성), Postgres MCP (DB 쿼리)                | O (Registry: https://github.com/modelcontextprotocol/servers) |
| **인증**          | GitHub PAT(토큰) 또는 OAuth (Remote 서버)                                                                                     | O (학생 계정 호환)                                            |
| **제한**          | Tool 호출 허용 팝업 발생; 엔터프: 정책 확인 ([docs.github.com/copilot/administer](http://docs.github.com/copilot/administer)) | quota 300회/월                                                |

### 단계별 설정 및 사용법 (VS Code 중심, Copilot 학생 Pro 기준)

1. **VS Code + Copilot 설치/활성화**
   - VS Code 1.102+ 다운로드 ([https://code.visualstudio.com](https://code.visualstudio.com/)).
   - Extensions: GitHub Copilot, Copilot Chat 설치 → GitHub 로그인 (학생 Pro 자동 적용).
   - Command Palette (Ctrl+Shift+P) → "Copilot: Sign In" → 학생 계정 확인.
2. **Agent 모드 활성화** (MCP 필수)
   - Copilot Chat 열기 (Ctrl+Shift+I 또는 사이드바 아이콘).
   - 상단 모드 전환: **Agent** 선택 (Ask/Edit/Agent 중).
   - 설정: File > Preferences > Settings > "chat.agent.enabled": true (JSON: `"github.copilot.chat.agent.enabled": true`).
3. **MCP 서버 추가 (가장 일반: GitHub MCP Remote 서버)**
   - 방법 : 명령 팔레트 → **MCP: Add Server** → Registry에서 "github" 선택 (OAuth 자동).

4. **다른 MCP 서버 추가 (예: Mermaid 다이어그램 – 사용자 과거 Mermaid 요청 반영)**
   - Registry (https://github.com/mcp) 검색 → Mermaid MCP (https://github.com/Narasimhaponnada/mermaid-mcp).
   - 사용 예: Agent Chat에 "@mermaid Create a GeoAI workflow flowchart" 입력 → Mermaid 코드 출력.
5. **실제 사용 예시 (Claude Code/bkit 스타일 프로젝트 연동)**

   | 프롬프트 예시                                              | MCP 도구 호출 | 예상 출력/동작                            |
   | ---------------------------------------------------------- | ------------- | ----------------------------------------- |
   | "@github List open issues in my GeoAI repo"                | GitHub MCP    | 리포 이슈 목록 + 요약 (PR 자동 생성 가능) |
   | "@mermaid Generate Mermaid diagram for Causal AI pipeline" | Mermaid MCP   | Mermaid 코드 (GIS/ML 워크플로 시각화)     |
   | "@postgres Query my research DB for NRRF data"             | Postgres MCP  | SQL 실행 결과 (데이터 분석 보조)          |
   - 코드 예시 (GIS 프로젝트): Copilot Agent가 MCP 호출 후 Python GIS 코드 생성.
     ```python
     import geopandas as gpd
     # MCP via GitHub: Fetch latest NRRF funding data from issues
     gdf = gpd.read_file("haenam_shp.shp")  # Jeollanam-do 예시
     # Causal AI 임베딩 (LLM API)
     ```

# **GitHub Copilot에서 "skills" (Agent Skills) 사용 방법**

GitHub Copilot의 **skills**는 2025년 말~2026년 초에 정식/GA 단계로 도입된 **Agent Skills** 기능을 의미합니다.

이는 **Copilot이 특정 도메인·작업에 특화된 지침·스크립트·리소스를 자동 로드**하여 더 정확하고 반복 가능한 결과를 내도록 돕는 확장 메커니즘입니다.

**MCP**와의 차이점 (객관적 비교, 2026년 기준)

| 항목       | Agent Skills                                                  | MCP (Model Context Protocol)                            |
| ---------- | ------------------------------------------------------------- | ------------------------------------------------------- |
| 목적       | Copilot에게 "이 작업은 이렇게 해"라는 전문 지식·규칙 주입     | 외부 도구·API·데이터 소스(리포, DB, Figma 등) 직접 호출 |
| 형태       | .github/skills/ 폴더 내 [SKILL.md](http://skill.md/) + 파일들 | MCP 서버 실행 → @github, @postgres 등으로 호출          |
| 자동 로드  | 프롬프트와 관련성 판단 시 자동 컨텍스트 주입                  | 사용자가 명시적으로 @tool 호출 필요                     |
| 주 사용처  | Copilot Chat (Agent 모드), Copilot CLI, VS Code               | 동일 + 외부 시스템 연동 강점                            |
| quota 영향 | premium request 차감 (학생 Pro 300회/월)                      | 동일                                                    |
| 난이도     | Markdown 작성만으로 가능 (스크립트 옵션)                      | 서버 설정·Docker 등 필요                                |

→ **단순 반복 작업·코딩 스타일·프로젝트 규칙 강제** → Skills

→ **GitHub 이슈·PR 생성, DB 쿼리 등 외부 액션** → MCP

### Skills 사용을 위한 전제 조건 (2026년 2월 기준)

- GitHub Copilot **Pro** 이상 (학생 무료 Pro 포함)
- VS Code **1.108+** (안정 버전) 또는 Insiders
- Copilot Chat에서 **Agent 모드** 활성화
  - 설정 → "github.copilot.chat.agent.enabled": true

### Skills 만드는·사용하는 정확한 단계 (프로젝트 단위 추천)

1. **저장소에 skills 폴더 생성**

   리포지토리 루트에 아래 경로 생성 (권장 위치)

   ```
   .github/skills/
   ```

2. **하나의 skill 폴더 만들기**

   예: 단위 테스트 자동 생성 skill

   ```
   .github/skills/unit-test-generator/
   ```

3. **필수 파일: [SKILL.md](http://skill.md/) 작성** (대소문자 구분)

   Markdown + YAML frontmatter 형식

   ````markdown
   ---
   name: Unit Test Generator
   description: Python/JS 함수나 컴포넌트에 대한 단위 테스트를 pytest 또는 Jest 스타일로 자동 생성합니다. 커버리지 80% 이상 목표.
   when: "테스트 작성", "unit test", "test cases", "pytest", "jest" 키워드 포함 시
   priority: high
   ---

   ## 지침 (반드시 따라야 함)

   1. 주어진 함수/컴포넌트의 입력·출력·엣지 케이스를 분석하세요.
   2. pytest (Python) 또는 Jest (JS/TS) 형식으로 작성
   3. mock은 최소화하고 실제 동작 위주
   4. 각 테스트에 명확한 docstring 추가
   5. 커버리지 목표: 최소 80%

   ## 예제 코드 (참고용)

   ```python
   # 예시 입력 함수
   def add(a: int, b: int) -> int:
       return a + b

   # 생성해야 할 테스트
   def test_add():
       assert add(1, 2) == 3
       assert add(-1, 1) == 0
       assert add(0, 0) == 0
   ```
   ````

   ```

   ```

# 깃허브 사용 가이드

이 문서는 본 프로젝트의 GitHub 활용법과 핵심 규칙을 간결하게 안내합니다.

## 저장소 구조

- 주요 파일: README.md, requirements.txt 등

## 브랜치 전략

- 기본: main
- 기능: feature/{주제}
- 버그: fix/{이슈번호}
- 문서: docs/{장번호}
  → 모든 작업은 Pull Request(PR)로 병합

## 커밋 메시지

- 한글로 작성 (예: "3장 초안 작성")
- 작업 목적을 명확히

## PR 리뷰

- 최소 1인 이상 리뷰 후 병합
- 코드/문서 품질, 실행 결과 확인

## 이슈 관리

- 모든 작업은 이슈로 등록 (버그, 개선, 질문 등)
- 라벨(버그, 문서, 실습 등) 활용

## 기타

- 대용량 파일: git-lfs 권장
- 개인정보/키/비밀번호 업로드 금지

## 참고 자료

- [GitHub 공식 문서](https://docs.github.com/)
- [깃허브 한글 가이드](https://www.progit.kr/)
  | 4 | **Context7 MCP** | 최신 외부 문서·라이브러리·API 레퍼런스 자동 가져오기 | ★★☆☆☆ | React·Next.js·Tailwind·Node.js 등 빠르게 변하는 웹 생태계 대응 최고 | Registry 또는 npm 설치 후 추가 |
  | 5 | **Vercel MCP** / **Next.js DevTools MCP** | Vercel 배포·프리뷰 URL 생성, Next.js 특화 도구 | ★★☆☆☆ | Next.js·React 기반 풀스택 개발 시 배포·환경 관리 편의성 극대화 | Registry에서 "vercel" 또는 "next-devtools" 검색 |
- **Playwright MCP** + **GitHub MCP** 조합이 웹 개발자 70~80%가 실제로 가장 많이 쓰는 기본 세트입니다.
- 프론트엔드 위주라면 → Playwright + Chrome DevTools + Context7
- 풀스택/배포 위주라면 → GitHub + Vercel/Next.js + Playwright

### 웹 개발에 가장 추천하는 Agent Skills ([SKILL.md](http://skill.md/) 기반)

Agent Skills는 프로젝트별로 `.github/skills/` 폴더에 넣어 자동 로드되는 방식입니다.

커뮤니티에서 가장 많이 공유·사용되는 웹 개발용 스킬들 (2026년 기준)

| 추천 Skill 이름             | 언제/어떤 프롬프트에 자동 발동되는가                  | 주요 내용 (SKILL.md에 들어가는 지침 요약)                                | 난이도 | 어디서 얻거나 만드는가             |
| --------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------ | ------ | ---------------------------------- |
| **webapp-testing**          | "test", "e2e", "playwright test", "unit test" 포함 시 | Playwright로 E2E 테스트 작성, Jest/Vitest 단위 테스트, 80% 커버리지 목표 | ★★☆☆☆  | VS Code 문서 예시 그대로 복사 가능 |
| **tailwind-responsive**     | "responsive", "tailwind", "mobile-first" 키워드       | Tailwind 클래스 순서·반응형 브레이크포인트·dark mode 일관성 강제         | ★☆☆☆☆  | antfu/skills 저장소 참고           |
| **nextjs-best-practices**   | "nextjs", "app router", "server component" 포함 시    | App Router vs Pages, Server/Client 컴포넌트 구분, metadata·loading UI    | ★★☆☆☆  | antfu/skills 또는 직접 작성        |
| **api-error-handling**      | "api", "fetch", "axios", "error", "try-catch"         | 표준 에러 응답 형식, Sentry/Rollbar 연동, 타입 안전한 에러 처리          | ★★☆☆☆  | 커뮤니티 공유 스킬 많음            |
| **component-documentation** | "document", "JSDoc", "Storybook" 키워드               | JSDoc + Storybook 형식 자동 생성, PropTypes/TS 인터페이스 강조           | ★☆☆☆☆  | 간단히 직접 만들기 추천            |

**가장 현실적인 시작 조합** (웹 프로그래밍 학생·주니어 기준)

1. **MCP** 먼저 설정
   - GitHub MCP (필수)
   - Playwright MCP (E2E·디버깅용)
   - Context7 MCP (문서 최신화용)
2. **Skills**는 프로젝트 루트에 하나씩 추가
   - `.github/skills/nextjs-best-practices/` 또는 `webapp-testing/`
   - 프롬프트에 "테스트 작성해줘" 또는 "이 컴포넌트 responsive하게 고쳐줘"라고만 해도 자동 적용됨

**주의할 점** (객관적 사실 기반)

- MCP 서버 3개 이상 동시에 쓰면 premium request(학생 300회/월) 소모가 빨라짐 → 정말 필요한 1~2개만 먼저.
- Skills는 quota 소모가 상대적으로 적음 → 프로젝트마다 3~5개 정도 넣어두는 게 효율적.
- Playwright MCP는 localhost 외부 사이트 접근 제한이 기본 → 필요 시 브라우저 허용 설정 변경해야 함.

필요하면 특정 프레임워크(React, Next.js, Vue, Node.js 등)에 맞춘 구체적인 [SKILL.md](http://skill.md/) 예시나 MCP 설정 json 코드를 추가로 드릴 수 있습니다.

# 데이터사이언스에 가장 추천하는 MCP 서버

| 순위 | MCP 서버 이름                  | 주요 기능 (데이터 분석 관점)                                                    | 설치 난이도 | quota 소모 정도 | 왜 데이터 작업에 가장 유용한가 (객관적 평가)                                               | 설치 방법 (VS Code 기준)                                                       |
| ---- | ------------------------------ | ------------------------------------------------------------------------------- | ----------- | --------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| 1    | **Pandas MCP Server**          | pandas DataFrame 로드·전처리·groupby·merge·통계·plot 생성 자동 실행             | ★★☆☆☆       | 중상            | pandas 기반 EDA·전처리·시각화의 70~80%를 자연어로 처리 가능 → 가장 직접적 생산성 향상      | Registry 검색 "pandas" 또는 marlonluo2018/pandas-mcp-server 설치               |
| 2    | **Jupyter MCP Server**         | Jupyter 노트북 실시간 제어 (셀 실행·출력 캡처·플롯 표시·노트북 생성/편집)       | ★★☆☆☆       | 중              | 데이터사이언스 워크플로 대부분이 Jupyter 기반 → 전체 노트북 자동 생성·디버깅·시각화에 최적 | datalayer/jupyter-mcp-server 또는 modelcontextprotocol/servers 내 Jupyter 참조 |
| 3    | **SQL / Postgres / MSSQL MCP** | 자연어 → SQL 변환·쿼리 실행·스키마 탐색·결과 반환 (PostgreSQL, SQL Server 등)   | ★★☆☆☆       | 중              | 실무 데이터 대부분 RDBMS → "지난 3개월 매출 TOP10 보여줘" 같은 프롬프트로 바로 결과 도출   | Registry "postgres" 또는 Microsoft SQL Server MCP                              |
| 4    | **Data Exploration MCP**       | CSV·Parquet 파일 자동 탐색·요약 통계·상관분석·아웃라이어 탐지·인사이트 제안     | ★☆☆☆☆       | 중하            | 초기 데이터 이해 단계(EDA)에서 시간 절약 극대화 — 최소 노력으로 insight 도출               | modelcontextprotocol/servers 내 Data Exploration                               |
| 5    | **Matplotlib / ECharts MCP**   | matplotlib·seaborn·ECharts 기반 차트 자동 생성 (bar, line, scatter, heatmap 등) | ★★☆☆☆       | 중              | 시각화 요청 시 코드 작성 없이 바로 플롯 출력 — 보고서·대시보드 제작 시 강력                | Registry "echarts" 또는 matplotlib 관련 서버                                   |

**가장 현실적인 시작 조합** (quota 효율 고려)

- Pandas MCP + Jupyter MCP → pandas 중심 분석 + 노트북 전체 관리
- - SQL MCP (데이터 소스가 DB인 경우)
    → 위 2~3개만 켜도 대부분의 데이터사이언스 태스크(EDA → 전처리 → 모델링 준비 → 시각화)를 커버합니다.

# 데이터 분석·데이터사이언스에 가장 추천하는 Agent Skills (.github/skills/ 폴더)

Skills는 MCP보다 quota 소모가 적고, 프로젝트·팀 내 일관된 분석 스타일 강제에 유리합니다.

| 추천 Skill 이름                | 자동 발동 키워드 예시                        | [SKILL.md](http://skill.md/) 주요 지침 요약                                                               | 난이도 | 추천 이유 (객관적)                                      |
| ------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------- |
| **pandas-eda-standard**        | "eda", "explore", "summary", "describe"      | [df.info](http://df.info/)(), df.describe(), 결측치·이상치 처리, 상관계수, 분포 히스토그램 자동 생성 목표 | ★☆☆☆☆  | 모든 pandas 프로젝트 시작점 통일 — 반복 작업 90% 자동화 |
| **sql-query-best-practice**    | "sql", "query", "select", "join", "group by" | CTE 사용, 인덱스 고려, LIMIT 추가, 명확한 alias, window function 우선 활용                                | ★★☆☆☆  | SQL 생성 시 실무 수준 쿼리 강제 — 유지보수성 향상       |
| **data-viz-publication-ready** | "plot", "visualize", "chart", "seaborn"      | seaborn/matplotlib 스타일 통일, 한글 폰트·타이틀·범례·주석 필수, publication 퀄리티 목표                  | ★★☆☆☆  | 논문·보고서용 시각화 일관성 확보 — 수작업 최소화        |
| **feature-engineering-recipe** | "feature", "engineering", "create feature"   | 스케일링·인코딩·파생변수·PCA·interaction term 생성 템플릿, 피처 중요도 순위 출력                          | ★★★☆☆  | 모델링 전 단계 반복 패턴 강제 — 실험 속도 향상          |
| **jupyter-notebook-structure** | "notebook", "jupyter", "markdown cell"       | 표준 섹션 구조(Markdown 헤더 + 목차 + import → load → eda → modeling → eval) 자동 적용                    | ★☆☆☆☆  | 팀 공유 노트북 가독성·재현성 극대화                     |

**가장 현실적인 시작 조합**

- pandas-eda-standard + data-viz-publication-ready
- 프로젝트마다 2~4개 Skills만 넣어두면 Agent 모드에서 "이 데이터로 EDA 해줘" 또는 "시각화 만들어줘" 프롬프트만으로도 고퀄 결과가 나옵니다.

**주의사항 & quota 관리 팁** (2026년 2월 기준 학생 Pro 기준)

- MCP 서버 3개 이상 동시 실행 시 premium request 소모 급증 → 처음엔 Pandas MCP + Jupyter MCP 2개만 테스트
- Skills는 거의 quota를 먹지 않음 → 마음껏 여러 개 만들어 두는 게 이득
- Jupyter MCP 사용 시 로컬 Jupyter 서버가 켜져 있어야 함 (vscode jupyter extension 필수)
- Pandas MCP 등은 임의 코드 실행 가능 → 신뢰할 수 있는 데이터셋만 연결 (보안상 중요)
- 복잡한 통계·ML 모델 학습은 여전히 MCP보다 직접 코드 + @data 에이전트 조합이 안정적

필요하면 특정 작업(예: 시계열 분석, geospatial 데이터, A/B 테스트 등)에 특화된 MCP/Skills 설정 예시(json 또는 md)를 추가로 제공할 수 있습니다.

---

만일 github copilot 실패햇을때 아래를 사용합니다. 

## Gemini CLI 설치 및 실행

### 1단계: Node.js 설치 확인
- Gemini CLI는 npm 방식 설치를 권장하므로 Node.js 필수
- https://nodejs.org 에서 LTS 버전 다운로드 후 설치
- npm은 Node.js와 함께 자동 설치됨

### 2단계: vscode 에서 새터미널 열기
- PowerShell 실행

### 3단계: Gemini CLI 설치
```bash
npm install -g @google/gemini-cli 

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned 
```

### 4단계: 실행
```bash
gemini   

중간에 브라우저에서 구글로 로그인하는 과정을 거치니 브라우저를 잘 살핀다. 

구글로그인 후에 성공했다는 메시지와 함께 r 을 입력하라는 메시지가 나오니 따라서 하면 잠시 후에 로그인된다. 

터미널에서 마우스 우클릭 후 패널위치를 오른쪽으로 한다. 
```

### 5단계: 인증 설정
처음 실행 시 다음 중 선택:
- **Google 계정 로그인** (권장)
- **Gemini API Key**
- **Vertex AI**
