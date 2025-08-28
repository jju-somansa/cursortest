"""
Task Management Module
작업 관리 모듈
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskResult:
    """작업 결과"""
    success: bool
    data: Any = None
    error: str = None
    execution_time: float = 0.0

@dataclass
class Task:
    """작업 클래스"""
    id: str
    name: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    timeout: int = 300  # 5분 기본 타임아웃
    retry_count: int = 0
    max_retries: int = 3
    result: TaskResult = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class TaskManager:
    """작업 관리자"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger("TaskManager")
        self.is_running = False
        
    def register_handler(self, task_type: str, handler: Callable):
        """작업 핸들러 등록"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"작업 핸들러 등록: {task_type}")
    
    def create_task(self, 
                   name: str, 
                   description: str,
                   task_type: str = "general",
                   priority: TaskPriority = TaskPriority.NORMAL,
                   timeout: int = 300,
                   metadata: Dict[str, Any] = None) -> str:
        """새 작업 생성"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        task.metadata["task_type"] = task_type
        self.tasks[task_id] = task
        
        self.logger.info(f"새 작업 생성: {name} (ID: {task_id})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """상태별 작업 조회"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_pending_tasks(self) -> List[Task]:
        """대기 중인 작업 조회 (우선순위 순)"""
        pending = self.get_tasks_by_status(TaskStatus.PENDING)
        return sorted(pending, key=lambda t: (t.priority.value, t.created_at), reverse=True)
    
    async def start(self):
        """작업 관리자 시작"""
        self.is_running = True
        self.logger.info("작업 관리자 시작됨")
        
        # 백그라운드 작업 처리 시작
        asyncio.create_task(self._process_tasks())
        asyncio.create_task(self._monitor_tasks())
    
    async def stop(self):
        """작업 관리자 중지"""
        self.is_running = False
        
        # 실행 중인 작업들 취소
        for task_id, running_task in self.running_tasks.items():
            running_task.cancel()
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.CANCELLED
        
        self.logger.info("작업 관리자 중지됨")
    
    async def _process_tasks(self):
        """작업 처리 루프"""
        while self.is_running:
            try:
                # 실행 가능한 작업 수 계산
                available_slots = self.max_concurrent_tasks - len(self.running_tasks)
                
                if available_slots > 0:
                    pending_tasks = self.get_pending_tasks()
                    
                    for task in pending_tasks[:available_slots]:
                        await self._execute_task(task)
                
                await asyncio.sleep(1)  # 1초마다 체크
                
            except Exception as e:
                self.logger.error(f"작업 처리 중 오류: {e}")
                await asyncio.sleep(5)
    
    async def _execute_task(self, task: Task):
        """작업 실행"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self.logger.info(f"작업 실행 시작: {task.name} (ID: {task.id})")
        
        # 비동기 작업 생성
        async_task = asyncio.create_task(self._run_task_with_timeout(task))
        self.running_tasks[task.id] = async_task
        
        # 작업 완료 후 정리를 위한 콜백 설정
        async_task.add_done_callback(lambda t: self._task_completed(task.id))
    
    async def _run_task_with_timeout(self, task: Task) -> TaskResult:
        """타임아웃과 함께 작업 실행"""
        start_time = datetime.now()
        
        try:
            # 작업 타입에 따른 핸들러 선택
            task_type = task.metadata.get("task_type", "general")
            handler = self.task_handlers.get(task_type, self._default_handler)
            
            # 타임아웃과 함께 실행
            result_data = await asyncio.wait_for(
                handler(task), 
                timeout=task.timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                success=True,
                data=result_data,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                success=False,
                error=f"작업 타임아웃 ({task.timeout}초)",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _task_completed(self, task_id: str):
        """작업 완료 처리"""
        if task_id in self.running_tasks:
            async_task = self.running_tasks.pop(task_id)
            task = self.tasks[task_id]
            
            try:
                result = async_task.result()
                task.result = result
                
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    self.logger.info(f"작업 완료: {task.name} (실행시간: {result.execution_time:.2f}초)")
                else:
                    # 재시도 로직
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = TaskStatus.PENDING
                        self.logger.warning(f"작업 재시도: {task.name} ({task.retry_count}/{task.max_retries})")
                    else:
                        task.status = TaskStatus.FAILED
                        self.logger.error(f"작업 실패: {task.name} - {result.error}")
                        
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                self.logger.info(f"작업 취소됨: {task.name}")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = TaskResult(success=False, error=str(e))
                self.logger.error(f"작업 처리 중 예외: {task.name} - {e}")
            
            task.completed_at = datetime.now()
    
    async def _monitor_tasks(self):
        """작업 모니터링"""
        while self.is_running:
            try:
                # 오래된 완료/실패 작업 정리
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                old_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and task.completed_at and task.completed_at < cutoff_time
                ]
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                
                if old_tasks:
                    self.logger.info(f"오래된 작업 {len(old_tasks)}개 정리됨")
                
                await asyncio.sleep(3600)  # 1시간마다 정리
                
            except Exception as e:
                self.logger.error(f"작업 모니터링 중 오류: {e}")
                await asyncio.sleep(300)  # 5분 후 재시도
    
    async def _default_handler(self, task: Task) -> Any:
        """기본 작업 핸들러"""
        # 간단한 작업 시뮬레이션
        await asyncio.sleep(1)
        return f"작업 '{task.name}' 처리 완료"
    
    def get_statistics(self) -> Dict[str, Any]:
        """작업 통계"""
        total = len(self.tasks)
        by_status = {}
        
        for status in TaskStatus:
            count = len(self.get_tasks_by_status(status))
            by_status[status.value] = count
        
        return {
            "total_tasks": total,
            "running_tasks": len(self.running_tasks),
            "by_status": by_status,
            "max_concurrent": self.max_concurrent_tasks
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            return True
        elif task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PENDING:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            self.tasks[task_id].completed_at = datetime.now()
            return True
        
        return False

# 테스트 코드
if __name__ == "__main__":
    async def test_task_manager():
        tm = TaskManager(max_concurrent_tasks=3)
        
        # 테스트 핸들러 등록
        async def test_handler(task: Task):
            await asyncio.sleep(2)
            return f"테스트 작업 완료: {task.name}"
        
        tm.register_handler("test", test_handler)
        
        await tm.start()
        
        # 테스트 작업들 생성
        for i in range(5):
            tm.create_task(
                name=f"테스트 작업 {i+1}",
                description=f"테스트용 작업 {i+1}번",
                task_type="test",
                priority=TaskPriority.NORMAL
            )
        
        # 잠시 대기하며 진행 상황 확인
        for _ in range(10):
            stats = tm.get_statistics()
            print(f"통계: {stats}")
            await asyncio.sleep(1)
        
        await tm.stop()
    
    asyncio.run(test_task_manager())