#!/usr/bin/env python3
"""
간단한 가상 에이전트
Simple Virtual Agent
"""

import time
import threading
from datetime import datetime

class SimpleAgent:
    def __init__(self, name="AI봇"):
        self.name = name
        self.running = False
        self.tasks = []
        
    def start(self):
        """에이전트 시작"""
        self.running = True
        print(f"🤖 {self.name} 시작!")
        
        # 백그라운드에서 실행
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        
    def _run(self):
        """메인 실행 루프"""
        while self.running:
            if self.tasks:
                task = self.tasks.pop(0)
                print(f"✅ 작업 처리: {task}")
            time.sleep(2)
    
    def add_task(self, task):
        """작업 추가"""
        self.tasks.append(task)
        print(f"📝 새 작업: {task}")
    
    def chat(self, message):
        """채팅"""
        if "안녕" in message:
            return f"안녕하세요! 저는 {self.name}입니다!"
        elif "시간" in message:
            return f"현재 시간: {datetime.now().strftime('%H:%M:%S')}"
        elif "작업" in message:
            return f"현재 {len(self.tasks)}개 작업 대기중"
        else:
            return f"'{message}' 메시지를 받았습니다!"
    
    def stop(self):
        """중지"""
        self.running = False
        print(f"⏹️ {self.name} 중지")

# 사용법
if __name__ == "__main__":
    agent = SimpleAgent("도우미봇")
    agent.start()
    
    print("\n명령어:")
    print("- 'quit': 종료")
    print("- '작업 [내용]': 작업 추가")
    print("- 기타: 채팅")
    
    while True:
        user_input = input("\n입력: ").strip()
        
        if user_input == "quit":
            agent.stop()
            break
        elif user_input.startswith("작업 "):
            task = user_input[3:]
            agent.add_task(task)
        else:
            response = agent.chat(user_input)
            print(f"🤖: {response}")