#!/usr/bin/env python3
"""
Virtual Agent System
가상 에이전트 시스템

A comprehensive virtual agent with natural language processing,
task management, and autonomous capabilities.
"""

import asyncio
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    LEARNING = "learning"
    SLEEPING = "sleeping"

@dataclass
class Task:
    id: str
    description: str
    priority: int
    created_at: datetime.datetime
    status: str = "pending"
    result: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Memory:
    timestamp: datetime.datetime
    content: str
    category: str
    importance: int = 1
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'category': self.category,
            'importance': self.importance
        }

class VirtualAgent:
    """
    가상 에이전트 - Virtual Agent
    
    A sophisticated virtual agent capable of:
    - Natural language understanding
    - Task management and execution
    - Memory and learning
    - Autonomous operation
    """
    
    def __init__(self, name: str = "Virtual Agent"):
        self.name = name
        self.state = AgentState.IDLE
        self.tasks: List[Task] = []
        self.memories: List[Memory] = []
        self.running = False
        self.capabilities = {
            'natural_language': True,
            'task_management': True,
            'memory_system': True,
            'learning': True,
            'autonomous_operation': True
        }
        
        logger.info(f"가상 에이전트 '{self.name}' 초기화 완료")
        
    def start(self):
        """에이전트 시작"""
        self.running = True
        self.state = AgentState.IDLE
        logger.info(f"🤖 {self.name} 시작됨")
        
        # Start main loop in a separate thread
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        return f"✅ 가상 에이전트 '{self.name}'가 성공적으로 시작되었습니다!"
    
    def stop(self):
        """에이전트 중지"""
        self.running = False
        self.state = AgentState.SLEEPING
        logger.info(f"🛑 {self.name} 중지됨")
        return f"⏹️ 가상 에이전트 '{self.name}'가 중지되었습니다."
    
    def _main_loop(self):
        """메인 실행 루프"""
        while self.running:
            try:
                if self.state == AgentState.IDLE:
                    self._check_for_tasks()
                elif self.state == AgentState.EXECUTING:
                    self._execute_tasks()
                elif self.state == AgentState.THINKING:
                    self._think_and_plan()
                
                time.sleep(1)  # Prevent busy waiting
                
            except Exception as e:
                logger.error(f"메인 루프 오류: {e}")
                time.sleep(5)
    
    def _check_for_tasks(self):
        """대기 중인 작업 확인"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        if pending_tasks:
            self.state = AgentState.EXECUTING
            logger.info(f"📋 {len(pending_tasks)}개의 대기 중인 작업 발견")
    
    def _execute_tasks(self):
        """작업 실행"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        if not pending_tasks:
            self.state = AgentState.IDLE
            return
        
        # Execute highest priority task
        task = max(pending_tasks, key=lambda t: t.priority)
        task.status = "executing"
        
        logger.info(f"🔄 작업 실행 중: {task.description}")
        
        # Simulate task execution
        result = self._process_task(task)
        task.result = result
        task.status = "completed"
        
        # Add to memory
        self.add_memory(f"작업 완료: {task.description} - 결과: {result}", "task_execution", 2)
        
        logger.info(f"✅ 작업 완료: {task.description}")
        
        # Check if more tasks remain
        remaining_tasks = [t for t in self.tasks if t.status == "pending"]
        if not remaining_tasks:
            self.state = AgentState.IDLE
    
    def _process_task(self, task: Task) -> str:
        """작업 처리 로직"""
        # This is where you'd implement actual task processing
        # For now, we'll simulate with a simple response
        
        if "안녕" in task.description or "hello" in task.description.lower():
            return f"안녕하세요! 저는 {self.name}입니다. 무엇을 도와드릴까요?"
        elif "시간" in task.description or "time" in task.description.lower():
            return f"현재 시간은 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}입니다."
        elif "상태" in task.description or "status" in task.description.lower():
            return f"현재 상태: {self.state.value}, 메모리: {len(self.memories)}개, 작업: {len(self.tasks)}개"
        else:
            return f"'{task.description}' 작업을 처리했습니다."
    
    def _think_and_plan(self):
        """사고 및 계획 수립"""
        logger.info("🤔 사고 및 계획 수립 중...")
        
        # Analyze memories and create new tasks if needed
        recent_memories = self.memories[-10:] if self.memories else []
        
        # Simple planning logic
        if len(recent_memories) > 5:
            self.add_task("메모리 정리 및 최적화", priority=3)
        
        self.state = AgentState.IDLE
    
    def add_task(self, description: str, priority: int = 1) -> str:
        """새 작업 추가"""
        task = Task(
            id=f"task_{len(self.tasks) + 1}",
            description=description,
            priority=priority,
            created_at=datetime.datetime.now()
        )
        self.tasks.append(task)
        logger.info(f"📝 새 작업 추가: {description} (우선순위: {priority})")
        return f"✅ 작업이 추가되었습니다: {description}"
    
    def add_memory(self, content: str, category: str = "general", importance: int = 1):
        """메모리 추가"""
        memory = Memory(
            timestamp=datetime.datetime.now(),
            content=content,
            category=category,
            importance=importance
        )
        self.memories.append(memory)
        logger.info(f"🧠 메모리 추가: {category} - {content[:50]}...")
    
    def process_input(self, user_input: str) -> str:
        """사용자 입력 처리"""
        logger.info(f"💬 사용자 입력: {user_input}")
        
        # Add input to memory
        self.add_memory(f"사용자 입력: {user_input}", "user_interaction", 2)
        
        # Create task from input
        self.add_task(f"사용자 요청 처리: {user_input}", priority=5)
        
        return f"📨 입력을 받았습니다: '{user_input}'. 처리 중입니다..."
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            'name': self.name,
            'state': self.state.value,
            'running': self.running,
            'tasks': {
                'total': len(self.tasks),
                'pending': len([t for t in self.tasks if t.status == "pending"]),
                'completed': len([t for t in self.tasks if t.status == "completed"])
            },
            'memories': len(self.memories),
            'capabilities': self.capabilities
        }
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """최근 활동 반환"""
        activities = []
        
        # Recent tasks
        for task in self.tasks[-limit:]:
            activities.append({
                'type': 'task',
                'timestamp': task.created_at.isoformat(),
                'description': task.description,
                'status': task.status
            })
        
        # Recent memories
        for memory in self.memories[-limit:]:
            activities.append({
                'type': 'memory',
                'timestamp': memory.timestamp.isoformat(),
                'content': memory.content,
                'category': memory.category
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]

def main():
    """메인 함수 - 가상 에이전트 시작"""
    print("🚀 가상 에이전트 시스템 시작")
    print("=" * 50)
    
    # Create and start agent
    agent = VirtualAgent("AI Assistant")
    start_result = agent.start()
    print(start_result)
    
    print("\n📋 사용 가능한 명령어:")
    print("- 'status': 에이전트 상태 확인")
    print("- 'tasks': 작업 목록 보기")
    print("- 'memories': 메모리 보기")
    print("- 'activities': 최근 활동 보기")
    print("- 'stop': 에이전트 중지")
    print("- 'quit': 프로그램 종료")
    print("- 기타 메시지: 에이전트에게 전달")
    
    try:
        while True:
            user_input = input("\n💬 입력: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                break
            elif user_input.lower() == 'stop':
                print(agent.stop())
            elif user_input.lower() == 'status':
                status = agent.get_status()
                print(f"📊 에이전트 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
            elif user_input.lower() == 'tasks':
                print(f"📋 작업 목록 ({len(agent.tasks)}개):")
                for task in agent.tasks[-10:]:
                    print(f"  - [{task.status}] {task.description}")
            elif user_input.lower() == 'memories':
                print(f"🧠 메모리 ({len(agent.memories)}개):")
                for memory in agent.memories[-5:]:
                    print(f"  - [{memory.category}] {memory.content[:100]}...")
            elif user_input.lower() == 'activities':
                activities = agent.get_recent_activities(5)
                print("📈 최근 활동:")
                for activity in activities:
                    print(f"  - [{activity['type']}] {activity.get('description', activity.get('content', ''))[:100]}...")
            else:
                response = agent.process_input(user_input)
                print(response)
                
    except KeyboardInterrupt:
        print("\n\n⚡ 키보드 인터럽트 감지")
    finally:
        agent.stop()
        print("👋 가상 에이전트 시스템 종료")

if __name__ == "__main__":
    main()