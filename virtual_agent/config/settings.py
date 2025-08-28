"""
Configuration Settings for Virtual Agent
가상 에이전트 설정
"""

import os
from pathlib import Path
from typing import Dict, Any

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

class AgentConfig:
    """에이전트 기본 설정"""
    
    # 에이전트 기본 정보
    DEFAULT_NAME = "VirtualAgent"
    DEFAULT_LANGUAGE = "ko"
    VERSION = "1.0.0"
    
    # 작업 관리 설정
    MAX_CONCURRENT_TASKS = 5
    DEFAULT_TASK_TIMEOUT = 300  # 5분
    MAX_TASK_RETRIES = 3
    
    # 메모리 관리 설정
    MAX_MEMORY_CACHE_SIZE = 1000
    MEMORY_CLEANUP_DAYS = 30
    DEFAULT_MEMORY_IMPORTANCE = 5
    
    # 로깅 설정
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "agent.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

class WebConfig:
    """웹 인터페이스 설정"""
    
    # 서버 설정
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 8000
    
    # WebSocket 설정
    MAX_CONNECTIONS = 100
    HEARTBEAT_INTERVAL = 30
    
    # API 설정
    API_TIMEOUT = 30
    MAX_MESSAGE_LENGTH = 1000

class CLIConfig:
    """CLI 인터페이스 설정"""
    
    # 입력 설정
    MAX_INPUT_LENGTH = 500
    PROMPT_SYMBOL = "👤 사용자: "
    AGENT_SYMBOL = "🤖 에이전트: "
    
    # 응답 대기 시간
    MAX_RESPONSE_WAIT = 30

class NLPConfig:
    """자연어 처리 설정"""
    
    # 의도 분석 설정
    MIN_CONFIDENCE_THRESHOLD = 0.3
    DEFAULT_INTENT = "general_query"
    
    # 언어별 설정
    SUPPORTED_LANGUAGES = ["ko", "en"]
    
    # 엔티티 추출 설정
    MAX_ENTITIES_PER_TEXT = 10

class DatabaseConfig:
    """데이터베이스 설정"""
    
    # SQLite 설정
    DB_PATH = DATA_DIR / "agent.db"
    MEMORY_DB_PATH = DATA_DIR / "memory.db"
    
    # 연결 설정
    CONNECTION_TIMEOUT = 30
    MAX_CONNECTIONS = 10
    
    # 백업 설정
    AUTO_BACKUP = True
    BACKUP_INTERVAL_HOURS = 24
    MAX_BACKUPS = 7

def get_config() -> Dict[str, Any]:
    """전체 설정 반환"""
    return {
        "agent": {
            "name": AgentConfig.DEFAULT_NAME,
            "language": AgentConfig.DEFAULT_LANGUAGE,
            "version": AgentConfig.VERSION,
            "max_concurrent_tasks": AgentConfig.MAX_CONCURRENT_TASKS,
            "task_timeout": AgentConfig.DEFAULT_TASK_TIMEOUT,
            "max_retries": AgentConfig.MAX_TASK_RETRIES,
        },
        "memory": {
            "cache_size": AgentConfig.MAX_MEMORY_CACHE_SIZE,
            "cleanup_days": AgentConfig.MEMORY_CLEANUP_DAYS,
            "default_importance": AgentConfig.DEFAULT_MEMORY_IMPORTANCE,
        },
        "web": {
            "host": WebConfig.DEFAULT_HOST,
            "port": WebConfig.DEFAULT_PORT,
            "max_connections": WebConfig.MAX_CONNECTIONS,
            "api_timeout": WebConfig.API_TIMEOUT,
        },
        "cli": {
            "max_input_length": CLIConfig.MAX_INPUT_LENGTH,
            "max_response_wait": CLIConfig.MAX_RESPONSE_WAIT,
        },
        "nlp": {
            "min_confidence": NLPConfig.MIN_CONFIDENCE_THRESHOLD,
            "supported_languages": NLPConfig.SUPPORTED_LANGUAGES,
        },
        "database": {
            "db_path": str(DatabaseConfig.DB_PATH),
            "memory_db_path": str(DatabaseConfig.MEMORY_DB_PATH),
            "connection_timeout": DatabaseConfig.CONNECTION_TIMEOUT,
        },
        "logging": {
            "level": AgentConfig.LOG_LEVEL,
            "format": AgentConfig.LOG_FORMAT,
            "file": str(AgentConfig.LOG_FILE),
            "max_size": AgentConfig.MAX_LOG_SIZE,
            "backup_count": AgentConfig.LOG_BACKUP_COUNT,
        }
    }

def load_config_from_file(config_file: str = None) -> Dict[str, Any]:
    """파일에서 설정 로드"""
    if config_file is None:
        config_file = BASE_DIR / "config" / "config.json"
    
    config = get_config()
    
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # 설정 병합
            def merge_config(base, override):
                for key, value in override.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        merge_config(base[key], value)
                    else:
                        base[key] = value
            
            merge_config(config, file_config)
            
        except Exception as e:
            print(f"⚠️ 설정 파일 로드 중 오류: {e}")
            print("기본 설정을 사용합니다.")
    
    return config

def save_config_to_file(config: Dict[str, Any], config_file: str = None):
    """설정을 파일에 저장"""
    if config_file is None:
        config_file = BASE_DIR / "config" / "config.json"
    
    try:
        import json
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 설정이 저장되었습니다: {config_file}")
        
    except Exception as e:
        print(f"❌ 설정 저장 중 오류: {e}")

# 환경 변수에서 설정 오버라이드
def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """환경 변수로 설정 오버라이드"""
    
    # 에이전트 설정
    if os.getenv("AGENT_NAME"):
        config["agent"]["name"] = os.getenv("AGENT_NAME")
    
    if os.getenv("AGENT_LANGUAGE"):
        config["agent"]["language"] = os.getenv("AGENT_LANGUAGE")
    
    # 웹 설정
    if os.getenv("WEB_HOST"):
        config["web"]["host"] = os.getenv("WEB_HOST")
    
    if os.getenv("WEB_PORT"):
        try:
            config["web"]["port"] = int(os.getenv("WEB_PORT"))
        except ValueError:
            pass
    
    # 로그 레벨
    if os.getenv("LOG_LEVEL"):
        config["logging"]["level"] = os.getenv("LOG_LEVEL").upper()
    
    return config

# 기본 설정 로드
DEFAULT_CONFIG = load_config_from_file()
DEFAULT_CONFIG = apply_env_overrides(DEFAULT_CONFIG)

if __name__ == "__main__":
    # 설정 테스트
    import json
    
    config = get_config()
    print("=== 기본 설정 ===")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    # 설정 파일 저장 테스트
    save_config_to_file(config)
    
    # 설정 파일 로드 테스트
    loaded_config = load_config_from_file()
    print("\n=== 로드된 설정 ===")
    print(json.dumps(loaded_config, indent=2, ensure_ascii=False))