#!/usr/bin/env python3
"""
Virtual Agent Quick Start Script
가상 에이전트 빠른 시작 스크립트
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python 버전: {sys.version.split()[0]}")

def install_dependencies():
    """의존성 패키지 설치"""
    print("📦 의존성 패키지 설치 중...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 의존성 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        print("💡 수동으로 설치해보세요: pip install -r requirements.txt")
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    directories = ["data", "logs"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 디렉토리 생성: {directory}/")

def show_menu():
    """메뉴 표시"""
    print("\n" + "="*60)
    print("🤖 가상 에이전트 (Virtual Agent) 시작")
    print("="*60)
    print("1. CLI 모드로 시작")
    print("2. 웹 모드로 시작")
    print("3. 테스트 모드로 실행")
    print("4. 도움말 보기")
    print("5. 종료")
    print("="*60)

def run_mode(mode):
    """모드별 실행"""
    try:
        if mode == "cli":
            subprocess.run([sys.executable, "main.py", "--mode", "cli"])
        elif mode == "web":
            print("🌐 웹 브라우저에서 http://localhost:8000 을 열어주세요.")
            subprocess.run([sys.executable, "main.py", "--mode", "web"])
        elif mode == "test":
            subprocess.run([sys.executable, "main.py", "--mode", "test"])
        elif mode == "help":
            subprocess.run([sys.executable, "main.py", "--help"])
    except KeyboardInterrupt:
        print("\n👋 안녕히 가세요!")
    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 가상 에이전트 시작 스크립트")
    print("-" * 40)
    
    # Python 버전 확인
    check_python_version()
    
    # 필요한 디렉토리 생성
    create_directories()
    
    # 의존성 설치 확인
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    # 자동 설치 시도
    print("\n🔍 의존성 패키지 확인 중...")
    try:
        import fastapi
        import uvicorn
        print("✅ 주요 패키지가 이미 설치되어 있습니다.")
    except ImportError:
        print("📦 필요한 패키지를 설치합니다...")
        if not install_dependencies():
            print("❌ 패키지 설치에 실패했습니다.")
            print("💡 수동으로 다음 명령을 실행해주세요:")
            print("   pip install -r requirements.txt")
            sys.exit(1)
    
    # 메뉴 루프
    while True:
        show_menu()
        
        try:
            choice = input("\n선택하세요 (1-5): ").strip()
            
            if choice == "1":
                print("🖥️  CLI 모드를 시작합니다...")
                run_mode("cli")
            elif choice == "2":
                print("🌐 웹 모드를 시작합니다...")
                run_mode("web")
            elif choice == "3":
                print("🧪 테스트 모드를 실행합니다...")
                run_mode("test")
            elif choice == "4":
                run_mode("help")
            elif choice == "5":
                print("👋 안녕히 가세요!")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-5 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n👋 안녕히 가세요!")
            break
        except EOFError:
            print("\n\n👋 안녕히 가세요!")
            break

if __name__ == "__main__":
    main()