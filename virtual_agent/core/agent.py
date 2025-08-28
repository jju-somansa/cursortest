"""
Virtual Agent Core Module
가상 에이전트 핵심 모듈
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import time

@dataclass
class Task:
    """작업 데이터 클래스"""
    id: str
    description: str
    priority: int = 1
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = None
    completed_at: str = None
    result: Any = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Memory:
    """메모리 데이터 클래스"""
    key: str
    value: Any
    timestamp: str = None
    importance: int = 1
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class VirtualAgent:
    """
    가상 에이전트 메인 클래스
    Virtual Agent Main Class
    """
    
    def __init__(self, name: str = "VirtualAgent", language: str = "ko"):
        self.name = name
        self.language = language
        self.is_running = False
        self.tasks: Dict[str, Task] = {}
        self.memory: Dict[str, Memory] = {}
        self.capabilities = []
        self.logger = self._setup_logger()
        
        # 기본 능력 등록
        self._register_default_capabilities()
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(f"VirtualAgent_{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _register_default_capabilities(self):
        """기본 능력 등록"""
        self.capabilities = [
            "자연어 처리 (Natural Language Processing)",
            "작업 관리 (Task Management)", 
            "메모리 관리 (Memory Management)",
            "대화 처리 (Conversation Handling)",
            "시스템 모니터링 (System Monitoring)"
        ]
    
    async def start(self):
        """에이전트 시작"""
        self.is_running = True
        self.logger.info(f"🤖 가상 에이전트 '{self.name}' 시작됨")
        self.logger.info(f"📋 등록된 능력: {', '.join(self.capabilities)}")
        
        # 백그라운드 작업 시작
        asyncio.create_task(self._background_tasks())
        
        return f"가상 에이전트 '{self.name}'이(가) 성공적으로 시작되었습니다!"
    
    async def stop(self):
        """에이전트 중지"""
        self.is_running = False
        self.logger.info(f"🛑 가상 에이전트 '{self.name}' 중지됨")
        return f"가상 에이전트 '{self.name}'이(가) 중지되었습니다."
    
    async def _background_tasks(self):
        """백그라운드 작업 실행"""
        while self.is_running:
            await self._process_pending_tasks()
            await self._cleanup_old_memories()
            await asyncio.sleep(1)  # 1초마다 체크
    
    async def _process_pending_tasks(self):
        """대기 중인 작업 처리"""
        pending_tasks = [task for task in self.tasks.values() if task.status == "pending"]
        
        for task in pending_tasks[:3]:  # 최대 3개씩 처리
            await self._execute_task(task)
    
    async def _execute_task(self, task: Task):
        """작업 실행"""
        try:
            task.status = "running"
            self.logger.info(f"📋 작업 실행 중: {task.description}")
            
            # 작업 유형에 따른 처리
            if "인사" in task.description or "hello" in task.description.lower():
                task.result = f"안녕하세요! 저는 {self.name}입니다."
            elif "시간" in task.description or "time" in task.description.lower():
                task.result = f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elif "상태" in task.description or "status" in task.description.lower():
                task.result = self._get_status()
            else:
                task.result = f"작업 '{task.description}'을(를) 처리했습니다."
            
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            self.logger.info(f"✅ 작업 완료: {task.description}")
            
        except Exception as e:
            task.status = "failed"
            task.result = f"오류: {str(e)}"
            self.logger.error(f"❌ 작업 실패: {task.description} - {str(e)}")
    
    def add_task(self, description: str, priority: int = 1) -> str:
        """작업 추가"""
        task_id = f"task_{len(self.tasks) + 1}_{int(time.time())}"
        task = Task(id=task_id, description=description, priority=priority)
        self.tasks[task_id] = task
        
        self.logger.info(f"📝 새 작업 추가: {description}")
        return task_id
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """작업 결과 조회"""
        if task_id in self.tasks:
            return asdict(self.tasks[task_id])
        return None
    
    def remember(self, key: str, value: Any, importance: int = 1):
        """메모리에 정보 저장"""
        memory = Memory(key=key, value=value, importance=importance)
        self.memory[key] = memory
        self.logger.info(f"🧠 메모리 저장: {key}")
    
    def recall(self, key: str) -> Any:
        """메모리에서 정보 회상"""
        if key in self.memory:
            return self.memory[key].value
        return None
    
    async def _cleanup_old_memories(self):
        """오래된 메모리 정리"""
        # 중요도가 낮고 오래된 메모리 삭제 (실제 구현에서는 더 정교한 로직 필요)
        pass
    
    def _get_status(self) -> Dict:
        """에이전트 상태 반환"""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "total_tasks": len(self.tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == "pending"]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
            "memory_items": len(self.memory),
            "capabilities": self.capabilities,
            "uptime": datetime.now().isoformat()
        }
    
    async def process_message(self, message: str) -> str:
        """메시지 처리"""
        self.logger.info(f"💬 메시지 수신: {message}")
        
        # 간단한 명령 처리
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["안녕", "hello", "hi", "헬로"]):
            return f"안녕하세요! 저는 {self.name}입니다. 무엇을 도와드릴까요?"
        
        elif any(word in message_lower for word in ["상태", "status", "어떻게"]):
            status = self._get_status()
            return f"현재 상태: 실행 중 ✅\n작업: {status['total_tasks']}개 (대기: {status['pending_tasks']}개, 완료: {status['completed_tasks']}개)\n메모리: {status['memory_items']}개 항목"
        
        elif any(word in message_lower for word in ["시간", "time", "몇시"]):
            return f"현재 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}"
        
        elif any(word in message_lower for word in ["능력", "capability", "뭘할수있어"]):
            return f"제가 할 수 있는 일들:\n" + "\n".join([f"• {cap}" for cap in self.capabilities])
        
        else:
            # 일반 작업으로 처리
            task_id = self.add_task(f"메시지 처리: {message}")
            return f"메시지를 작업으로 등록했습니다. (작업 ID: {task_id})\n처리 중이니 잠시만 기다려주세요."

if __name__ == "__main__":
    # 테스트 실행
    async def test_agent():
        agent = VirtualAgent("TestAgent", "ko")
        await agent.start()
        
        # 테스트 메시지들
        messages = ["안녕하세요", "상태 확인", "현재 시간", "능력 보여줘"]
        
        for msg in messages:
            response = await agent.process_message(msg)
            print(f"사용자: {msg}")
            print(f"에이전트: {response}\n")
            await asyncio.sleep(2)
        
        await agent.stop()
    
    asyncio.run(test_agent())