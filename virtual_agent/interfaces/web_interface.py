"""
Web Interface for Virtual Agent
가상 에이전트 웹 인터페이스
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging

# FastAPI 및 관련 라이브러리
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("⚠️ FastAPI가 설치되지 않았습니다. pip install fastapi uvicorn을 실행하세요.")
    sys.exit(1)

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from core.agent import VirtualAgent
from modules.nlp_processor import NLPProcessor
from modules.task_manager import TaskManager, TaskPriority
from modules.memory_manager import MemoryManager

# Pydantic 모델들
class ChatMessage(BaseModel):
    message: str
    timestamp: str = None
    
class AgentResponse(BaseModel):
    response: str
    timestamp: str
    intent: str = None
    confidence: float = None

class SystemStatus(BaseModel):
    agent_status: Dict[str, Any]
    task_stats: Dict[str, Any]
    memory_stats: Dict[str, Any]
    timestamp: str

class WebInterface:
    """웹 인터페이스"""
    
    def __init__(self):
        self.app = FastAPI(title="Virtual Agent Web Interface", version="1.0.0")
        self.agent = None
        self.nlp = NLPProcessor()
        self.task_manager = TaskManager()
        self.memory_manager = MemoryManager()
        self.connected_clients: List[WebSocket] = []
        
        self._setup_routes()
        self._setup_static_files()
    
    def _setup_routes(self):
        """라우트 설정"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_index():
            """메인 페이지"""
            return self._get_html_template()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket 연결"""
            await websocket.accept()
            self.connected_clients.append(websocket)
            
            try:
                await websocket.send_json({
                    "type": "system",
                    "message": "🤖 가상 에이전트에 연결되었습니다!",
                    "timestamp": datetime.now().isoformat()
                })
                
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(websocket, data)
                    
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
            except Exception as e:
                logging.error(f"WebSocket 오류: {e}")
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
        
        @self.app.post("/api/chat", response_model=AgentResponse)
        async def chat_endpoint(message: ChatMessage):
            """채팅 API"""
            try:
                response = await self._process_message(message.message)
                return response
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status", response_model=SystemStatus)
        async def status_endpoint():
            """상태 API"""
            return SystemStatus(
                agent_status=self.agent._get_status() if self.agent else {},
                task_stats=self.task_manager.get_statistics(),
                memory_stats=self.memory_manager.get_statistics(),
                timestamp=datetime.now().isoformat()
            )
        
        @self.app.get("/api/memories")
        async def memories_endpoint(limit: int = 10, memory_type: str = None):
            """메모리 조회 API"""
            memories = self.memory_manager.search(
                memory_type=memory_type,
                limit=limit
            )
            
            return [
                {
                    "key": memory.key,
                    "value": memory.value,
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    "tags": memory.tags
                }
                for memory in memories
            ]
        
        @self.app.post("/api/memory")
        async def store_memory_endpoint(key: str, value: str, importance: int = 5):
            """메모리 저장 API"""
            success = self.memory_manager.store(
                key=key,
                value=value,
                memory_type="web_input",
                importance=importance
            )
            
            if success:
                return {"status": "success", "message": f"'{key}' 저장됨"}
            else:
                raise HTTPException(status_code=500, detail="메모리 저장 실패")
    
    def _setup_static_files(self):
        """정적 파일 설정"""
        # 정적 파일 디렉토리가 있다면 설정
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    async def _handle_websocket_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """WebSocket 메시지 처리"""
        message_type = data.get("type", "chat")
        
        if message_type == "chat":
            message = data.get("message", "")
            if message:
                response = await self._process_message(message)
                
                await websocket.send_json({
                    "type": "response",
                    "message": response.response,
                    "intent": response.intent,
                    "confidence": response.confidence,
                    "timestamp": response.timestamp
                })
        
        elif message_type == "status":
            status = await self._get_system_status()
            await websocket.send_json({
                "type": "status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _process_message(self, message: str) -> AgentResponse:
        """메시지 처리"""
        # NLP 분석
        nlp_result = self.nlp.process(message)
        intent = nlp_result['intent']['name']
        confidence = nlp_result['intent']['confidence']
        
        # 작업 타입 결정
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
            name=f"웹 요청: {message[:30]}...",
            description=message,
            task_type=task_type,
            priority=priority
        )
        
        # 작업 완료 대기
        max_wait = 15  # 웹에서는 15초로 단축
        waited = 0
        
        while waited < max_wait:
            task = self.task_manager.get_task(task_id)
            
            if task and task.status.value in ["completed", "failed", "cancelled"]:
                if task.status.value == "completed" and task.result and task.result.success:
                    response_text = task.result.data
                else:
                    response_text = f"처리 중 오류가 발생했습니다: {task.result.error if task.result else '알 수 없는 오류'}"
                
                return AgentResponse(
                    response=response_text,
                    timestamp=datetime.now().isoformat(),
                    intent=intent,
                    confidence=confidence
                )
            
            await asyncio.sleep(0.2)
            waited += 0.2
        
        return AgentResponse(
            response="응답 시간이 초과되었습니다. 다시 시도해주세요.",
            timestamp=datetime.now().isoformat(),
            intent=intent,
            confidence=confidence
        )
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            "agent_status": self.agent._get_status() if self.agent else {},
            "task_stats": self.task_manager.get_statistics(),
            "memory_stats": self.memory_manager.get_statistics(),
            "connected_clients": len(self.connected_clients)
        }
    
    def _get_html_template(self) -> str:
        """HTML 템플릿 반환"""
        return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>가상 에이전트 - Virtual Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .message.user .message-content {
            background: #007bff;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.agent .message-content {
            background: white;
            color: #333;
            border: 1px solid #e9ecef;
            border-bottom-left-radius: 4px;
        }
        
        .message.system .message-content {
            background: #28a745;
            color: white;
            font-size: 12px;
            text-align: center;
            max-width: 100%;
            border-radius: 12px;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .message-input:focus {
            border-color: #007bff;
        }
        
        .send-button {
            padding: 12px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .send-button:hover {
            background: #0056b3;
        }
        
        .send-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .status-bar {
            padding: 10px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            font-size: 12px;
            color: #6c757d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .connection-status {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #28a745;
        }
        
        .status-dot.disconnected {
            background: #dc3545;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 16px;
            color: #6c757d;
            font-style: italic;
            font-size: 12px;
        }
        
        @media (max-width: 600px) {
            .container {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 가상 에이전트</h1>
            <p>Virtual Agent - 지능형 대화 시스템</p>
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message system">
                    <div class="message-content">
                        가상 에이전트에 오신 것을 환영합니다! 무엇을 도와드릴까요?
                    </div>
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                🤖 에이전트가 입력 중...
            </div>
            
            <div class="input-container">
                <input type="text" class="message-input" id="messageInput" 
                       placeholder="메시지를 입력하세요..." maxlength="500">
                <button class="send-button" id="sendButton">전송</button>
            </div>
        </div>
        
        <div class="status-bar">
            <div class="connection-status">
                <div class="status-dot" id="statusDot"></div>
                <span id="connectionStatus">연결 중...</span>
            </div>
            <div id="timestamp"></div>
        </div>
    </div>

    <script>
        class VirtualAgentChat {
            constructor() {
                this.ws = null;
                this.isConnected = false;
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.messages = document.getElementById('messages');
                this.statusDot = document.getElementById('statusDot');
                this.connectionStatus = document.getElementById('connectionStatus');
                this.timestamp = document.getElementById('timestamp');
                this.typingIndicator = document.getElementById('typingIndicator');
                
                this.init();
            }
            
            init() {
                this.connectWebSocket();
                this.setupEventListeners();
                this.updateTimestamp();
                setInterval(() => this.updateTimestamp(), 1000);
            }
            
            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    this.isConnected = true;
                    this.updateConnectionStatus('연결됨', true);
                };
                
                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                };
                
                this.ws.onclose = () => {
                    this.isConnected = false;
                    this.updateConnectionStatus('연결 끊김', false);
                    // 재연결 시도
                    setTimeout(() => this.connectWebSocket(), 3000);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket 오류:', error);
                    this.updateConnectionStatus('연결 오류', false);
                };
            }
            
            setupEventListeners() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });
                
                this.messageInput.addEventListener('input', () => {
                    this.sendButton.disabled = !this.messageInput.value.trim();
                });
            }
            
            sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message || !this.isConnected) return;
                
                // 사용자 메시지 표시
                this.addMessage('user', message);
                
                // 서버로 전송
                this.ws.send(JSON.stringify({
                    type: 'chat',
                    message: message
                }));
                
                // 입력 필드 초기화
                this.messageInput.value = '';
                this.sendButton.disabled = true;
                
                // 타이핑 인디케이터 표시
                this.showTypingIndicator();
            }
            
            handleMessage(data) {
                this.hideTypingIndicator();
                
                if (data.type === 'response') {
                    this.addMessage('agent', data.message);
                } else if (data.type === 'system') {
                    this.addMessage('system', data.message);
                }
            }
            
            addMessage(type, content) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = content;
                
                messageDiv.appendChild(contentDiv);
                this.messages.appendChild(messageDiv);
                
                // 스크롤을 맨 아래로
                this.messages.scrollTop = this.messages.scrollHeight;
            }
            
            showTypingIndicator() {
                this.typingIndicator.style.display = 'block';
                this.messages.scrollTop = this.messages.scrollHeight;
            }
            
            hideTypingIndicator() {
                this.typingIndicator.style.display = 'none';
            }
            
            updateConnectionStatus(status, connected) {
                this.connectionStatus.textContent = status;
                this.statusDot.className = `status-dot ${connected ? '' : 'disconnected'}`;
                this.sendButton.disabled = !connected || !this.messageInput.value.trim();
            }
            
            updateTimestamp() {
                const now = new Date();
                this.timestamp.textContent = now.toLocaleTimeString('ko-KR');
            }
        }
        
        // 앱 시작
        document.addEventListener('DOMContentLoaded', () => {
            new VirtualAgentChat();
        });
    </script>
</body>
</html>
        """
    
    async def start(self, agent_name: str = "VirtualAgent", host: str = "0.0.0.0", port: int = 8000):
        """웹 인터페이스 시작"""
        print("🌐 가상 에이전트 웹 인터페이스 시작 중...")
        
        # 에이전트 초기화
        self.agent = VirtualAgent(agent_name, "ko")
        
        # 모듈들 시작
        await self.task_manager.start()
        await self.agent.start()
        
        # 작업 핸들러 등록
        self._register_task_handlers()
        
        print(f"✅ 가상 에이전트 '{agent_name}' 준비 완료!")
        print(f"🌐 웹 인터페이스: http://{host}:{port}")
        
        # 서버 시작
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def _register_task_handlers(self):
        """작업 핸들러 등록"""
        
        async def memory_handler(task):
            """메모리 관련 작업 처리"""
            description = task.description.lower()
            
            if "저장" in description or "기억" in description:
                parts = task.description.split(":")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = ":".join(parts[1:]).strip()
                    self.memory_manager.store(key, value, "web_input", 6)
                    return f"'{key}' 정보를 기억했습니다."
                else:
                    return "저장할 정보의 형식을 확인해주세요. (예: 이름: 김철수)"
            
            elif "찾기" in description or "기억나" in description:
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
                stats = await self._get_system_status()
                return f"시스템 상태:\n• 연결된 클라이언트: {stats['connected_clients']}개\n• 총 작업: {stats['task_stats']['total_tasks']}개\n• 메모리: {stats['memory_stats'].get('total_memories', 0)}개"
            
            elif "시간" in description:
                return datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
            
            return "시스템 작업을 처리했습니다."
        
        # 핸들러 등록
        self.task_manager.register_handler("memory", memory_handler)
        self.task_manager.register_handler("system", system_handler)

async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="가상 에이전트 웹 인터페이스")
    parser.add_argument("--name", "-n", default="VirtualAgent", help="에이전트 이름")
    parser.add_argument("--host", default="0.0.0.0", help="호스트 주소")
    parser.add_argument("--port", "-p", type=int, default=8000, help="포트 번호")
    
    args = parser.parse_args()
    
    web_interface = WebInterface()
    await web_interface.start(args.name, args.host, args.port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 웹 인터페이스가 종료되었습니다!")
    except Exception as e:
        print(f"❌ 시작 중 오류 발생: {e}")
        sys.exit(1)