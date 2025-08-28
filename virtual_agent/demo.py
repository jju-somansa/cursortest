#!/usr/bin/env python3
"""
Virtual Agent Demo - No External Dependencies
가상 에이전트 데모 - 외부 의존성 없음
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from core.agent import VirtualAgent
from modules.nlp_processor import NLPProcessor
from modules.task_manager import TaskManager, TaskPriority
from modules.memory_manager import MemoryManager

async def demo_basic_functionality():
    """기본 기능 데모"""
    print("🤖 가상 에이전트 기본 기능 데모")
    print("=" * 50)
    
    # 에이전트 초기화
    agent = VirtualAgent("DemoAgent", "ko")
    nlp = NLPProcessor()
    task_manager = TaskManager()
    memory_manager = MemoryManager()
    
    # 시작
    await agent.start()
    await task_manager.start()
    
    print("✅ 가상 에이전트가 시작되었습니다!\n")
    
    # 테스트 메시지들
    test_messages = [
        "안녕하세요",
        "현재 상태는 어떤가요?", 
        "지금 몇 시인가요?",
        "당신의 능력을 알려주세요",
        "안녕히 가세요"
    ]
    
    print("📝 테스트 대화 시작:")
    print("-" * 30)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[{i}] 👤 사용자: {message}")
        
        # NLP 분석
        nlp_result = nlp.process(message)
        intent = nlp_result['intent']['name']
        confidence = nlp_result['intent']['confidence']
        
        print(f"    🧠 분석: {intent} (신뢰도: {confidence:.2f})")
        
        # 에이전트 응답
        response = await agent.process_message(message)
        print(f"    🤖 에이전트: {response}")
        
        await asyncio.sleep(0.5)  # 잠시 대기
    
    print("\n" + "-" * 30)
    print("📊 메모리 테스트:")
    
    # 메모리 테스트
    memory_manager.store("사용자_이름", "김철수", "demo", 8, ["사용자", "개인정보"])
    memory_manager.store("좋아하는_색", "파란색", "demo", 5, ["취향"])
    memory_manager.store("회의_일정", "내일 오후 2시", "demo", 9, ["중요", "일정"])
    
    print("✅ 테스트 정보 저장 완료")
    
    # 검색 테스트
    search_results = memory_manager.search(memory_type="demo")
    print(f"🔍 저장된 정보 ({len(search_results)}개):")
    for result in search_results:
        print(f"  • {result.key}: {result.value} (중요도: {result.importance})")
    
    # 통계 출력
    print("\n📈 시스템 통계:")
    agent_stats = agent._get_status()
    task_stats = task_manager.get_statistics()
    memory_stats = memory_manager.get_statistics()
    
    print(f"  🤖 에이전트: {agent_stats['name']} ({'실행 중' if agent_stats['is_running'] else '중지됨'})")
    print(f"  📋 작업: 총 {task_stats['total_tasks']}개")
    print(f"  🧠 메모리: 총 {memory_stats.get('total_memories', 0)}개")
    
    # 종료
    await task_manager.stop()
    await agent.stop()
    
    print("\n✅ 데모 완료!")
    print("🎉 가상 에이전트가 성공적으로 작동했습니다!")

async def demo_interactive_mode():
    """대화형 데모 모드"""
    print("🤖 가상 에이전트 대화형 데모")
    print("=" * 50)
    print("💡 'exit' 또는 '종료'를 입력하면 종료됩니다.")
    print("-" * 50)
    
    # 에이전트 초기화
    agent = VirtualAgent("InteractiveAgent", "ko")
    nlp = NLPProcessor()
    memory_manager = MemoryManager()
    
    await agent.start()
    
    print("✅ 가상 에이전트 준비 완료!\n")
    
    while True:
        try:
            # 사용자 입력
            user_input = input("👤 사용자: ").strip()
            
            if not user_input:
                continue
            
            # 종료 명령 확인
            if user_input.lower() in ['exit', 'quit', '종료', '끝']:
                break
            
            # 특수 명령 처리
            if user_input.startswith('/'):
                if user_input == '/status' or user_input == '/상태':
                    stats = agent._get_status()
                    print(f"🤖 에이전트: 현재 상태 - {stats['name']} ({'실행 중' if stats['is_running'] else '중지됨'})")
                    print(f"   총 작업: {stats['total_tasks']}개, 완료: {stats['completed_tasks']}개")
                    continue
                
                elif user_input.startswith('/save '):
                    # /save 키 값 형식
                    parts = user_input[6:].split(' ', 1)
                    if len(parts) == 2:
                        key, value = parts
                        memory_manager.store(key, value, "user_input", 7)
                        print(f"🤖 에이전트: '{key}' 정보를 저장했습니다.")
                    else:
                        print("🤖 에이전트: 사용법: /save <키> <값>")
                    continue
                
                elif user_input.startswith('/recall '):
                    # /recall 키 형식
                    key = user_input[8:].strip()
                    value = memory_manager.retrieve(key)
                    if value:
                        print(f"🤖 에이전트: {key}: {value}")
                    else:
                        print(f"🤖 에이전트: '{key}'를 찾을 수 없습니다.")
                    continue
                
                elif user_input == '/help' or user_input == '/도움말':
                    print("🤖 에이전트: 사용 가능한 명령:")
                    print("   /status, /상태 - 시스템 상태")
                    print("   /save <키> <값> - 정보 저장")
                    print("   /recall <키> - 정보 불러오기")
                    print("   /help, /도움말 - 이 도움말")
                    continue
            
            # NLP 분석
            nlp_result = nlp.process(user_input)
            
            # 메모리 관련 처리
            if "저장" in user_input and ":" in user_input:
                parts = user_input.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    memory_manager.store(key, value, "conversation", 6)
                    print(f"🤖 에이전트: '{key}' 정보를 기억했습니다.")
                    continue
            
            elif "찾기" in user_input or "기억나" in user_input:
                query = user_input.replace("찾기", "").replace("기억나", "").strip()
                results = memory_manager.search(query=query, limit=3)
                if results:
                    print("🤖 에이전트: 찾은 정보:")
                    for result in results:
                        print(f"   • {result.key}: {result.value}")
                else:
                    print(f"🤖 에이전트: '{query}'에 대한 정보를 찾을 수 없습니다.")
                continue
            
            # 일반 응답
            response = await agent.process_message(user_input)
            print(f"🤖 에이전트: {response}")
            
        except KeyboardInterrupt:
            print("\n\n🛑 Ctrl+C 감지됨. 종료합니다...")
            break
        except EOFError:
            print("\n\n👋 안녕히 가세요!")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    await agent.stop()
    print("\n👋 가상 에이전트 데모를 종료합니다!")

def main():
    """메인 함수"""
    print("🚀 가상 에이전트 데모 시작")
    print("=" * 60)
    print("1. 기본 기능 데모 (자동)")
    print("2. 대화형 데모 (수동)")
    print("3. 종료")
    print("=" * 60)
    
    while True:
        try:
            choice = input("\n선택하세요 (1-3): ").strip()
            
            if choice == "1":
                print("\n🎬 기본 기능 데모를 시작합니다...\n")
                asyncio.run(demo_basic_functionality())
                break
            elif choice == "2":
                print("\n💬 대화형 데모를 시작합니다...\n")
                asyncio.run(demo_interactive_mode())
                break
            elif choice == "3":
                print("👋 안녕히 가세요!")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-3 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n👋 안녕히 가세요!")
            break
        except EOFError:
            print("\n\n👋 안녕히 가세요!")
            break

if __name__ == "__main__":
    main()