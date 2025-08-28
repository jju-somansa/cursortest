# 🤖 가상 에이전트 (Virtual Agent)

지능형 대화 시스템 - Intelligent Conversation System

## 📋 개요

가상 에이전트는 자연어 처리, 작업 관리, 메모리 시스템을 갖춘 지능형 대화 시스템입니다. CLI와 웹 인터페이스를 통해 사용자와 상호작용하며, 다양한 작업을 수행할 수 있습니다.

## ✨ 주요 기능

### 🧠 핵심 기능
- **자연어 처리**: 사용자의 의도를 분석하고 적절한 응답 생성
- **작업 관리**: 비동기 작업 처리 및 우선순위 관리
- **메모리 시스템**: 대화 내용과 중요 정보 저장 및 검색
- **다중 인터페이스**: CLI와 웹 인터페이스 지원

### 🎯 지원 기능
- 인사 및 일반 대화
- 현재 시간 조회
- 시스템 상태 확인
- 정보 저장 및 검색
- 작업 실행 및 모니터링

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 실행 방법

#### CLI 모드 (기본)
```bash
python main.py
```

#### 웹 모드
```bash
python main.py --mode web
```

#### 테스트 모드
```bash
python main.py --mode test
```

### 3. 사용 예시

#### CLI에서 사용
```
👤 사용자: 안녕하세요
🤖 에이전트: 안녕하세요! 저는 VirtualAgent입니다. 무엇을 도와드릴까요?

👤 사용자: 이름: 김철수
🤖 에이전트: '이름' 정보를 기억했습니다.

👤 사용자: 이름 찾기
🤖 에이전트: 찾은 정보:
• 이름: 김철수
```

#### 웹에서 사용
1. 브라우저에서 `http://localhost:8000` 접속
2. 채팅 인터페이스를 통해 대화
3. 실시간 WebSocket 통신으로 즉시 응답

## 📁 프로젝트 구조

```
virtual_agent/
├── main.py                 # 메인 실행 스크립트
├── requirements.txt        # 의존성 패키지
├── README.md              # 프로젝트 문서
├── core/                  # 핵심 모듈
│   └── agent.py           # 가상 에이전트 메인 클래스
├── modules/               # 기능 모듈
│   ├── nlp_processor.py   # 자연어 처리
│   ├── task_manager.py    # 작업 관리
│   └── memory_manager.py  # 메모리 관리
├── interfaces/            # 사용자 인터페이스
│   ├── cli_interface.py   # 명령줄 인터페이스
│   └── web_interface.py   # 웹 인터페이스
├── config/                # 설정
│   └── settings.py        # 설정 관리
├── data/                  # 데이터 저장소
│   └── (SQLite 데이터베이스 파일들)
└── logs/                  # 로그 파일
    └── agent.log
```

## ⚙️ 설정

### 명령줄 옵션

```bash
python main.py --help
```

주요 옵션:
- `--mode`: 실행 모드 (cli, web, test)
- `--name`: 에이전트 이름
- `--host`: 웹 모드 호스트 주소
- `--port`: 웹 모드 포트 번호
- `--log-level`: 로그 레벨

### 환경 변수

- `AGENT_NAME`: 에이전트 이름
- `AGENT_LANGUAGE`: 언어 설정
- `WEB_HOST`: 웹 호스트
- `WEB_PORT`: 웹 포트
- `LOG_LEVEL`: 로그 레벨

## 🔧 CLI 명령어

### 기본 대화
- 자연어로 대화 가능
- 인사, 질문, 요청 등 다양한 상호작용

### 특수 명령어
- `/status` 또는 `/상태`: 시스템 상태 확인
- `/tasks` 또는 `/작업`: 작업 목록 보기
- `/memory` 또는 `/메모리`: 메모리 정보 보기
- `/save <키> <값>`: 정보 저장
- `/recall <키>`: 정보 불러오기
- `/clear` 또는 `/지우기`: 화면 지우기
- `/help`: 도움말 보기

### 종료
- `exit`, `quit`, `종료`, `끝`
- `Ctrl+C`

## 🌐 웹 인터페이스

### 기능
- 실시간 채팅 인터페이스
- WebSocket 기반 즉시 응답
- 반응형 디자인 (모바일 지원)
- 연결 상태 표시
- 타이핑 인디케이터

### API 엔드포인트
- `GET /`: 메인 페이지
- `WebSocket /ws`: 실시간 통신
- `POST /api/chat`: 채팅 API
- `GET /api/status`: 시스템 상태
- `GET /api/memories`: 메모리 조회
- `POST /api/memory`: 메모리 저장

## 🧪 테스트

테스트 모드로 기본 기능 확인:

```bash
python main.py --mode test
```

## 📊 모니터링

### 로그 파일
- 위치: `logs/agent.log`
- 자동 로테이션 지원
- 설정 가능한 로그 레벨

### 시스템 상태
- 에이전트 상태
- 작업 통계
- 메모리 사용량
- 연결된 클라이언트 수 (웹 모드)

## 🔒 보안 고려사항

- 입력 길이 제한
- SQL 인젝션 방지 (SQLite 사용)
- WebSocket 연결 수 제한
- 로그 파일 크기 제한

## 🛠️ 확장 가능성

### 추가 가능한 기능
- 음성 인터페이스 (Speech Recognition)
- 고급 NLP 모델 (Transformers)
- 외부 API 연동
- 플러그인 시스템
- 다중 에이전트 지원

### 데이터베이스 확장
- Redis 캐시 시스템
- MongoDB 문서 저장소
- PostgreSQL 관계형 DB

## 🤝 기여 방법

1. 이슈 리포트
2. 기능 제안
3. 코드 기여
4. 문서 개선

## 📄 라이선스

MIT License

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.

---

**가상 에이전트와 함께 지능형 대화를 경험해보세요! 🚀**