#!/usr/bin/env python3
"""
Virtual Agent Main Launcher
가상 에이전트 메인 실행 스크립트
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from config.settings import DEFAULT_CONFIG, apply_env_overrides
from core.agent import VirtualAgent
from interfaces.cli_interface import CLIInterface
from interfaces.web_interface import WebInterface

def setup_logging(config):
    """로깅 설정"""
    log_level = getattr(logging, config["logging"]["level"], logging.INFO)
    
    # 로그 디렉토리 생성
    log_file = Path(config["logging"]["file"])
    log_file.parent.mkdir(exist_ok=True)
    
    # 로깅 설정
    logging.basicConfig(
        level=log_level,
        format=config["logging"]["format"],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

def print_banner():
    """시작 배너 출력"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    🤖 가상 에이전트 (Virtual Agent)           ║
    ║                                                              ║
    ║                     지능형 대화 시스템                        ║
    ║                   Intelligent Conversation System           ║
    ║                                                              ║
    ║                        Version 1.0.0                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def run_cli_mode(config, agent_name):
    """CLI 모드 실행"""
    print("🖥️  CLI 모드로 시작합니다...")
    cli = CLIInterface()
    await cli.start(agent_name)

async def run_web_mode(config, agent_name, host, port):
    """웹 모드 실행"""
    print("🌐 웹 모드로 시작합니다...")
    web = WebInterface()
    await web.start(agent_name, host, port)

async def run_test_mode(config, agent_name):
    """테스트 모드 실행"""
    print("🧪 테스트 모드로 시작합니다...")
    
    # 기본 에이전트 테스트
    agent = VirtualAgent(agent_name, config["agent"]["language"])
    await agent.start()
    
    # 테스트 메시지들
    test_messages = [
        "안녕하세요",
        "현재 상태는 어떤가요?",
        "지금 몇 시인가요?",
        "당신의 능력을 알려주세요",
        "이름: 테스트 사용자",
        "이름 찾기",
        "안녕히 가세요"
    ]
    
    print("\n=== 테스트 시작 ===")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[테스트 {i}] 사용자: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"[테스트 {i}] 에이전트: {response}")
        except Exception as e:
            print(f"[테스트 {i}] 오류: {e}")
        
        await asyncio.sleep(1)  # 1초 대기
    
    print("\n=== 테스트 완료 ===")
    await agent.stop()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="가상 에이전트 (Virtual Agent) - 지능형 대화 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py                          # CLI 모드로 실행
  python main.py --mode web               # 웹 모드로 실행
  python main.py --mode web --port 9000   # 웹 모드, 포트 9000
  python main.py --mode test              # 테스트 모드로 실행
  python main.py --name "MyAgent"         # 에이전트 이름 지정
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["cli", "web", "test"],
        default="cli",
        help="실행 모드 선택 (기본값: cli)"
    )
    
    parser.add_argument(
        "--name", "-n",
        default=None,
        help="에이전트 이름 (기본값: 설정 파일의 값)"
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="웹 모드 호스트 주소 (기본값: 설정 파일의 값)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="웹 모드 포트 번호 (기본값: 설정 파일의 값)"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="설정 파일 경로"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 설정"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Virtual Agent 1.0.0"
    )
    
    args = parser.parse_args()
    
    # 설정 로드
    config = DEFAULT_CONFIG.copy()
    
    if args.config:
        from config.settings import load_config_from_file
        config = load_config_from_file(args.config)
    
    # 명령줄 인수로 설정 오버라이드
    if args.name:
        config["agent"]["name"] = args.name
    
    if args.host:
        config["web"]["host"] = args.host
    
    if args.port:
        config["web"]["port"] = args.port
    
    if args.log_level:
        config["logging"]["level"] = args.log_level
    
    # 환경 변수 적용
    config = apply_env_overrides(config)
    
    # 로깅 설정
    setup_logging(config)
    
    # 배너 출력
    print_banner()
    
    # 설정 정보 출력
    agent_name = config["agent"]["name"]
    print(f"🤖 에이전트 이름: {agent_name}")
    print(f"🌍 언어: {config['agent']['language']}")
    print(f"📊 모드: {args.mode.upper()}")
    
    if args.mode == "web":
        print(f"🌐 웹 주소: http://{config['web']['host']}:{config['web']['port']}")
    
    print("-" * 60)
    
    # 모드별 실행
    try:
        if args.mode == "cli":
            asyncio.run(run_cli_mode(config, agent_name))
        elif args.mode == "web":
            asyncio.run(run_web_mode(
                config, 
                agent_name, 
                config["web"]["host"], 
                config["web"]["port"]
            ))
        elif args.mode == "test":
            asyncio.run(run_test_mode(config, agent_name))
            
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 중단되었습니다.")
        print("👋 안녕히 가세요!")
    except Exception as e:
        logging.error(f"실행 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()