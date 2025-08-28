"""
Command Line Interface for Virtual Agent
가상 에이전트 명령줄 인터페이스
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any
import argparse
from pathlib import Path

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from core.agent import VirtualAgent
from modules.nlp_processor import NLPProcessor
from modules.task_manager import TaskManager, TaskPriority
from modules.memory_manager import MemoryManager

class CLIInterface:
    """명령줄 인터페이스"""
    
    def __init__(self):
        self.agent = None
        self.nlp = NLPProcessor()
        self.task_manager = TaskManager()
        self.memory_manager = MemoryManager()
        self.running = False
        
    async def start(self, agent_name: str = "VirtualAgent"):
        """인터페이스 시작"""
        print("🤖 가상 에이전트 시작 중...")
        
        # 에이전트 초기화
        self.agent = VirtualAgent(agent_name, "ko")
        
        # 모듈들 시작
        await self.task_manager.start()
        await self.agent.start()
        
        # 작업 핸들러 등록
        self._register_task_handlers()
        
        self.running = True
        
        print(f"✅ 가상 에이전트 '{agent_name}' 준비 완료!")
        print("💡 도움말을 보려면 'help' 또는 '도움말'을 입력하세요.")
        print("🚪 종료하려면 'exit', 'quit', '종료'를 입력하세요.")
        print("-" * 50)
        
        # 메인 루프
        await self._main_loop()
    
    def _register_task_handlers(self):
        """작업 핸들러 등록"""
        
        async def memory_handler(task):
            """메모리 관련 작업 처리"""
            description = task.description.lower()
            
            if "저장" in description or "기억" in description:
                # 간단한 키-값 추출 (실제로는 더 정교한 NLP 필요)
                parts = task.description.split(":")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = ":".join(parts[1:]).strip()
                    self.memory_manager.store(key, value, "user_input", 5)
                    return f"'{key}' 정보를 기억했습니다."
                else:
                    return "저장할 정보의 형식을 확인해주세요. (예: 이름: 김철수)"
            
            elif "찾기" in description or "기억나" in description:
                # 키워드로 검색
                query = description.replace("찾기", "").replace("기억나", "").strip()
                results = self.memory_manager.search(query=query, limit=3)
                
                if results:
                    response = "찾은 정보:\n"
                    for result in results:
                        response += f"• {result.key}: {result.value}\n"
                    return response
                else:
                    return f"'{query}'에 대한 정보를 찾을 수 없습니다."
            
            return "메모리 작업을 처리했습니다."
        
        async def system_handler(task):
            """시스템 관련 작업 처리"""
            description = task.description.lower()
            
            if "상태" in description:
                stats = {
                    "agent_status": self.agent._get_status(),
                    "task_stats": self.task_manager.get_statistics(),
                    "memory_stats": self.memory_manager.get_statistics()
                }
                return json.dumps(stats, indent=2, ensure_ascii=False)
            
            elif "시간" in description:
                return datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
            
            return "시스템 작업을 처리했습니다."
        
        # 핸들러 등록
        self.task_manager.register_handler("memory", memory_handler)
        self.task_manager.register_handler("system", system_handler)
    
    async def _main_loop(self):
        """메인 입력 루프"""
        while self.running:
            try:
                # 사용자 입력 받기
                user_input = await self._get_user_input()
                
                if not user_input.strip():
                    continue
                
                # 종료 명령 확인
                if user_input.lower() in ['exit', 'quit', '종료', '끝']:
                    await self._shutdown()
                    break
                
                # 도움말 명령 확인
                if user_input.lower() in ['help', '도움말', 'h']:
                    self._show_help()
                    continue
                
                # 특수 명령 처리
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    continue
                
                # 일반 메시지 처리
                await self._process_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Ctrl+C 감지됨. 종료 중...")
                await self._shutdown()
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
    
    async def _get_user_input(self) -> str:
        """사용자 입력 받기 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, "👤 사용자: ")
    
    async def _process_message(self, message: str):
        """메시지 처리"""
        print("🤖 처리 중...")
        
        # NLP 분석
        nlp_result = self.nlp.process(message)
        intent = nlp_result['intent']['name']
        
        # 의도에 따른 작업 생성
        task_type = "general"
        priority = TaskPriority.NORMAL
        
        if intent in ["memory_operation"]:
            task_type = "memory"
            priority = TaskPriority.HIGH
        elif intent in ["status_inquiry", "time_inquiry"]:
            task_type = "system"
            priority = TaskPriority.NORMAL
        
        # 작업 생성
        task_id = self.task_manager.create_task(
            name=f"사용자 요청: {message[:30]}...",
            description=message,
            task_type=task_type,
            priority=priority
        )
        
        # 작업 완료까지 대기
        max_wait = 30  # 최대 30초 대기
        waited = 0
        
        while waited < max_wait:
            task = self.task_manager.get_task(task_id)
            
            if task and task.status.value in ["completed", "failed", "cancelled"]:
                if task.status.value == "completed" and task.result:
                    if task.result.success:
                        print(f"🤖 에이전트: {task.result.data}")
                    else:
                        print(f"❌ 오류: {task.result.error}")
                elif task.status.value == "failed":
                    print(f"❌ 작업 실패: {task.result.error if task.result else '알 수 없는 오류'}")
                else:
                    print("⚠️ 작업이 취소되었습니다.")
                break
            
            await asyncio.sleep(0.5)
            waited += 0.5
        else:
            print("⏰ 응답 시간이 초과되었습니다.")
    
    async def _handle_command(self, command: str):
        """특수 명령 처리"""
        cmd_parts = command[1:].split()
        cmd = cmd_parts[0].lower()
        
        if cmd == "status" or cmd == "상태":
            await self._show_status()
        
        elif cmd == "tasks" or cmd == "작업":
            await self._show_tasks()
        
        elif cmd == "memory" or cmd == "메모리":
            await self._show_memory()
        
        elif cmd == "clear" or cmd == "지우기":
            os.system('clear' if os.name == 'posix' else 'cls')
        
        elif cmd == "save" or cmd == "저장":
            if len(cmd_parts) >= 3:
                key = cmd_parts[1]
                value = " ".join(cmd_parts[2:])
                self.memory_manager.store(key, value, "user_command", 7)
                print(f"✅ '{key}' 저장됨: {value}")
            else:
                print("❌ 사용법: /save <키> <값>")
        
        elif cmd == "recall" or cmd == "불러오기":
            if len(cmd_parts) >= 2:
                key = cmd_parts[1]
                value = self.memory_manager.retrieve(key)
                if value:
                    print(f"🧠 {key}: {value}")
                else:
                    print(f"❌ '{key}'를 찾을 수 없습니다.")
            else:
                print("❌ 사용법: /recall <키>")
        
        else:
            print(f"❌ 알 수 없는 명령: {cmd}")
            print("💡 /help를 입력하여 사용 가능한 명령을 확인하세요.")
    
    async def _show_status(self):
        """상태 표시"""
        print("\n📊 === 시스템 상태 ===")
        
        # 에이전트 상태
        agent_status = self.agent._get_status()
        print(f"🤖 에이전트: {agent_status['name']} ({'실행 중' if agent_status['is_running'] else '중지됨'})")
        
        # 작업 통계
        task_stats = self.task_manager.get_statistics()
        print(f"📋 작업: 총 {task_stats['total_tasks']}개 (실행 중: {task_stats['running_tasks']}개)")
        
        # 메모리 통계
        memory_stats = self.memory_manager.get_statistics()
        print(f"🧠 메모리: 총 {memory_stats.get('total_memories', 0)}개 (캐시: {memory_stats.get('cached_memories', 0)}개)")
        
        print("-" * 30)
    
    async def _show_tasks(self):
        """작업 목록 표시"""
        print("\n📋 === 작업 목록 ===")
        
        stats = self.task_manager.get_statistics()
        for status, count in stats['by_status'].items():
            if count > 0:
                print(f"{status}: {count}개")
        
        # 최근 작업들 표시
        recent_tasks = list(self.task_manager.tasks.values())[-5:]
        if recent_tasks:
            print("\n최근 작업:")
            for task in recent_tasks:
                status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "cancelled": "⚠️"}
                emoji = status_emoji.get(task.status.value, "❓")
                print(f"{emoji} {task.name} ({task.status.value})")
        
        print("-" * 30)
    
    async def _show_memory(self):
        """메모리 정보 표시"""
        print("\n🧠 === 메모리 정보 ===")
        
        stats = self.memory_manager.get_statistics()
        print(f"총 메모리: {stats.get('total_memories', 0)}개")
        print(f"캐시된 메모리: {stats.get('cached_memories', 0)}개")
        
        # 타입별 통계
        by_type = stats.get('by_type', {})
        if by_type:
            print("\n타입별:")
            for mem_type, count in by_type.items():
                print(f"  {mem_type}: {count}개")
        
        # 최근 메모리들
        recent_memories = self.memory_manager.search(limit=5)
        if recent_memories:
            print("\n최근 메모리:")
            for memory in recent_memories:
                print(f"  • {memory.key}: {str(memory.value)[:50]}...")
        
        print("-" * 30)
    
    def _show_help(self):
        """도움말 표시"""
        help_text = """
🤖 === 가상 에이전트 도움말 ===

📝 기본 사용법:
  • 자연어로 대화하세요 (예: "안녕하세요", "현재 시간 알려줘")
  • 정보를 기억시키세요 (예: "이름: 김철수")
  • 정보를 찾아보세요 (예: "이름 찾기")

🔧 특수 명령어:
  /status, /상태     - 시스템 상태 확인
  /tasks, /작업      - 작업 목록 보기
  /memory, /메모리   - 메모리 정보 보기
  /clear, /지우기    - 화면 지우기
  /save <키> <값>    - 정보 저장
  /recall <키>       - 정보 불러오기
  /help, help        - 이 도움말 보기

🚪 종료:
  exit, quit, 종료, 끝

💡 팁:
  • Ctrl+C로 언제든 종료할 수 있습니다
  • 에이전트는 대화 내용을 기억합니다
  • 중요한 정보는 높은 우선순위로 저장됩니다

-" * 50
        """
        print(help_text)
    
    async def _shutdown(self):
        """시스템 종료"""
        print("🛑 시스템 종료 중...")
        
        self.running = False
        
        if self.task_manager:
            await self.task_manager.stop()
        
        if self.agent:
            await self.agent.stop()
        
        print("✅ 가상 에이전트가 안전하게 종료되었습니다.")
        print("👋 안녕히 가세요!")

async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="가상 에이전트 CLI")
    parser.add_argument("--name", "-n", default="VirtualAgent", help="에이전트 이름")
    
    args = parser.parse_args()
    
    cli = CLIInterface()
    await cli.start(args.name)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 안녕히 가세요!")
    except Exception as e:
        print(f"❌ 시작 중 오류 발생: {e}")
        sys.exit(1)