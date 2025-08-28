"""
Memory Management Module
메모리 관리 모듈
"""

import json
import pickle
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import hashlib

@dataclass
class MemoryItem:
    """메모리 아이템"""
    key: str
    value: Any
    memory_type: str = "general"  # general, conversation, task, system
    importance: int = 1  # 1-10 (10이 가장 중요)
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

class MemoryManager:
    """메모리 관리자"""
    
    def __init__(self, data_dir: str = "/workspace/virtual_agent/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "memory.db"
        self.memory_cache: Dict[str, MemoryItem] = {}
        self.max_cache_size = 1000
        self.logger = logging.getLogger("MemoryManager")
        
        self._init_database()
        self._load_cache()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value_json TEXT,
                    memory_type TEXT,
                    importance INTEGER,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER,
                    tags_json TEXT,
                    metadata_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON memories(last_accessed)
            """)
    
    def _load_cache(self):
        """캐시 로드"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM memories 
                    ORDER BY importance DESC, last_accessed DESC 
                    LIMIT ?
                """, (self.max_cache_size,))
                
                for row in cursor.fetchall():
                    memory_item = self._row_to_memory_item(row)
                    self.memory_cache[memory_item.key] = memory_item
                    
            self.logger.info(f"메모리 캐시 로드 완료: {len(self.memory_cache)}개 항목")
            
        except Exception as e:
            self.logger.error(f"캐시 로드 중 오류: {e}")
    
    def _row_to_memory_item(self, row) -> MemoryItem:
        """DB 행을 MemoryItem으로 변환"""
        key, value_json, memory_type, importance, created_at, last_accessed, access_count, tags_json, metadata_json = row
        
        return MemoryItem(
            key=key,
            value=json.loads(value_json),
            memory_type=memory_type,
            importance=importance,
            created_at=datetime.fromisoformat(created_at),
            last_accessed=datetime.fromisoformat(last_accessed),
            access_count=access_count,
            tags=json.loads(tags_json) if tags_json else [],
            metadata=json.loads(metadata_json) if metadata_json else {}
        )
    
    def _memory_item_to_row(self, item: MemoryItem) -> tuple:
        """MemoryItem을 DB 행으로 변환"""
        return (
            item.key,
            json.dumps(item.value, ensure_ascii=False, default=str),
            item.memory_type,
            item.importance,
            item.created_at.isoformat(),
            item.last_accessed.isoformat(),
            item.access_count,
            json.dumps(item.tags, ensure_ascii=False),
            json.dumps(item.metadata, ensure_ascii=False, default=str)
        )
    
    def store(self, 
             key: str, 
             value: Any, 
             memory_type: str = "general",
             importance: int = 1,
             tags: List[str] = None,
             metadata: Dict[str, Any] = None) -> bool:
        """메모리 저장"""
        try:
            memory_item = MemoryItem(
                key=key,
                value=value,
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # 캐시에 저장
            self.memory_cache[key] = memory_item
            
            # DB에 저장
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (key, value_json, memory_type, importance, created_at, last_accessed, access_count, tags_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, self._memory_item_to_row(memory_item))
            
            self.logger.info(f"메모리 저장: {key} (타입: {memory_type}, 중요도: {importance})")
            
            # 캐시 크기 관리
            self._manage_cache_size()
            
            return True
            
        except Exception as e:
            self.logger.error(f"메모리 저장 중 오류: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """메모리 조회"""
        try:
            # 캐시에서 먼저 확인
            if key in self.memory_cache:
                item = self.memory_cache[key]
                item.last_accessed = datetime.now()
                item.access_count += 1
                
                # DB 업데이트
                self._update_access_info(key, item.last_accessed, item.access_count)
                
                return item.value
            
            # DB에서 조회
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM memories WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    item = self._row_to_memory_item(row)
                    item.last_accessed = datetime.now()
                    item.access_count += 1
                    
                    # 캐시에 추가
                    self.memory_cache[key] = item
                    
                    # DB 업데이트
                    self._update_access_info(key, item.last_accessed, item.access_count)
                    
                    return item.value
            
            return None
            
        except Exception as e:
            self.logger.error(f"메모리 조회 중 오류: {e}")
            return None
    
    def _update_access_info(self, key: str, last_accessed: datetime, access_count: int):
        """접근 정보 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE memories 
                    SET last_accessed = ?, access_count = ?
                    WHERE key = ?
                """, (last_accessed.isoformat(), access_count, key))
        except Exception as e:
            self.logger.error(f"접근 정보 업데이트 중 오류: {e}")
    
    def search(self, 
              query: str = None,
              memory_type: str = None,
              tags: List[str] = None,
              min_importance: int = None,
              limit: int = 10) -> List[MemoryItem]:
        """메모리 검색"""
        try:
            conditions = []
            params = []
            
            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type)
            
            if min_importance:
                conditions.append("importance >= ?")
                params.append(min_importance)
            
            if tags:
                # 태그 검색 (JSON 내부 검색)
                for tag in tags:
                    conditions.append("tags_json LIKE ?")
                    params.append(f'%"{tag}"%')
            
            if query:
                # 키나 값에서 검색
                conditions.append("(key LIKE ? OR value_json LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"""
                    SELECT * FROM memories 
                    {where_clause}
                    ORDER BY importance DESC, last_accessed DESC
                    LIMIT ?
                """, params + [limit])
                
                results = []
                for row in cursor.fetchall():
                    results.append(self._row_to_memory_item(row))
                
                return results
                
        except Exception as e:
            self.logger.error(f"메모리 검색 중 오류: {e}")
            return []
    
    def delete(self, key: str) -> bool:
        """메모리 삭제"""
        try:
            # 캐시에서 삭제
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # DB에서 삭제
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
                deleted = cursor.rowcount > 0
            
            if deleted:
                self.logger.info(f"메모리 삭제: {key}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"메모리 삭제 중 오류: {e}")
            return False
    
    def _manage_cache_size(self):
        """캐시 크기 관리"""
        if len(self.memory_cache) > self.max_cache_size:
            # 중요도와 최근 접근 시간을 기준으로 정렬
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: (x[1].importance, x[1].last_accessed),
                reverse=True
            )
            
            # 상위 항목들만 유지
            self.memory_cache = dict(sorted_items[:self.max_cache_size])
            
            self.logger.info(f"캐시 크기 관리: {self.max_cache_size}개 항목으로 축소")
    
    def cleanup_old_memories(self, days: int = 30):
        """오래된 메모리 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM memories 
                    WHERE importance < 5 AND last_accessed < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
            
            # 캐시에서도 제거
            keys_to_remove = [
                key for key, item in self.memory_cache.items()
                if item.importance < 5 and item.last_accessed < cutoff_date
            ]
            
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            self.logger.info(f"오래된 메모리 정리: {deleted_count}개 항목 삭제")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"메모리 정리 중 오류: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """메모리 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 전체 통계
                cursor = conn.execute("SELECT COUNT(*) FROM memories")
                total_count = cursor.fetchone()[0]
                
                # 타입별 통계
                cursor = conn.execute("""
                    SELECT memory_type, COUNT(*) 
                    FROM memories 
                    GROUP BY memory_type
                """)
                by_type = dict(cursor.fetchall())
                
                # 중요도별 통계
                cursor = conn.execute("""
                    SELECT importance, COUNT(*) 
                    FROM memories 
                    GROUP BY importance
                    ORDER BY importance DESC
                """)
                by_importance = dict(cursor.fetchall())
            
            return {
                "total_memories": total_count,
                "cached_memories": len(self.memory_cache),
                "by_type": by_type,
                "by_importance": by_importance,
                "cache_hit_ratio": len(self.memory_cache) / max(total_count, 1)
            }
            
        except Exception as e:
            self.logger.error(f"통계 조회 중 오류: {e}")
            return {}
    
    def export_memories(self, file_path: str, memory_type: str = None) -> bool:
        """메모리 내보내기"""
        try:
            memories = self.search(memory_type=memory_type, limit=10000)
            
            export_data = []
            for memory in memories:
                export_data.append({
                    "key": memory.key,
                    "value": memory.value,
                    "memory_type": memory.memory_type,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    "tags": memory.tags,
                    "metadata": memory.metadata
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"메모리 내보내기 완료: {len(export_data)}개 항목 -> {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"메모리 내보내기 중 오류: {e}")
            return False

# 테스트 코드
if __name__ == "__main__":
    mm = MemoryManager()
    
    # 테스트 데이터 저장
    test_data = [
        ("user_name", "김철수", "conversation", 8, ["user", "personal"]),
        ("last_task", "파일 정리", "task", 5, ["task", "completed"]),
        ("system_config", {"theme": "dark", "language": "ko"}, "system", 9, ["config"]),
        ("conversation_1", "안녕하세요", "conversation", 3, ["greeting"]),
        ("important_note", "중요한 회의 내용", "general", 10, ["important", "meeting"])
    ]
    
    for key, value, mem_type, importance, tags in test_data:
        mm.store(key, value, mem_type, importance, tags)
    
    # 검색 테스트
    print("=== 검색 테스트 ===")
    results = mm.search(memory_type="conversation")
    for result in results:
        print(f"키: {result.key}, 값: {result.value}, 중요도: {result.importance}")
    
    # 조회 테스트
    print(f"\n=== 조회 테스트 ===")
    print(f"사용자 이름: {mm.retrieve('user_name')}")
    print(f"시스템 설정: {mm.retrieve('system_config')}")
    
    # 통계
    print(f"\n=== 통계 ===")
    stats = mm.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))