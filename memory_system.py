"""
Advanced Memory System for Virtual Agent
가상 에이전트용 고급 메모리 시스템
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import os

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryImportance(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MemoryEntry:
    id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    category: str
    tags: List[str]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'importance': self.importance.value,
            'category': self.category,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'context': self.context or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            importance=MemoryImportance(data['importance']),
            category=data['category'],
            tags=data['tags'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=data['access_count'],
            context=data.get('context', {})
        )

class MemorySystem:
    """
    고급 메모리 시스템
    Advanced Memory System with multiple memory types and intelligent retrieval
    """
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
        
        # Memory configuration
        self.short_term_limit = 100  # Maximum short-term memories
        self.consolidation_threshold = 50  # When to consolidate memories
        self.decay_factor = 0.95  # Memory decay rate
        
        logger.info("🧠 메모리 시스템 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    context TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            ''')
            
            conn.commit()
    
    def store_memory(self, 
                    content: str, 
                    memory_type: MemoryType = MemoryType.SHORT_TERM,
                    importance: MemoryImportance = MemoryImportance.MEDIUM,
                    category: str = "general",
                    tags: List[str] = None,
                    context: Dict[str, Any] = None) -> str:
        """메모리 저장"""
        
        if tags is None:
            tags = []
        
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            category=category,
            tags=tags,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            context=context
        )
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO memories 
                    (id, content, memory_type, importance, category, tags, 
                     created_at, last_accessed, access_count, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.importance.value,
                    memory.category,
                    json.dumps(memory.tags),
                    memory.created_at.isoformat(),
                    memory.last_accessed.isoformat(),
                    memory.access_count,
                    json.dumps(memory.context or {})
                ))
                conn.commit()
        
        logger.info(f"💾 메모리 저장: {category} - {content[:50]}...")
        
        # Check if consolidation is needed
        self._check_consolidation()
        
        return memory_id
    
    def retrieve_memories(self, 
                         query: str = None,
                         memory_type: MemoryType = None,
                         category: str = None,
                         tags: List[str] = None,
                         importance_min: MemoryImportance = None,
                         limit: int = 10) -> List[MemoryEntry]:
        """메모리 검색"""
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Build query
                sql = "SELECT * FROM memories WHERE 1=1"
                params = []
                
                if memory_type:
                    sql += " AND memory_type = ?"
                    params.append(memory_type.value)
                
                if category:
                    sql += " AND category = ?"
                    params.append(category)
                
                if importance_min:
                    sql += " AND importance >= ?"
                    params.append(importance_min.value)
                
                if query:
                    sql += " AND (content LIKE ? OR category LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
                
                if tags:
                    for tag in tags:
                        sql += " AND tags LIKE ?"
                        params.append(f"%{tag}%")
                
                sql += " ORDER BY importance DESC, last_accessed DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                
                memories = []
                for row in rows:
                    memory_data = {
                        'id': row[0],
                        'content': row[1],
                        'memory_type': row[2],
                        'importance': row[3],
                        'category': row[4],
                        'tags': json.loads(row[5]),
                        'created_at': row[6],
                        'last_accessed': row[7],
                        'access_count': row[8],
                        'context': json.loads(row[9]) if row[9] else {}
                    }
                    memories.append(MemoryEntry.from_dict(memory_data))
                
                # Update access count for retrieved memories
                if memories:
                    memory_ids = [m.id for m in memories]
                    placeholders = ','.join(['?' for _ in memory_ids])
                    conn.execute(f'''
                        UPDATE memories 
                        SET access_count = access_count + 1,
                            last_accessed = ?
                        WHERE id IN ({placeholders})
                    ''', [datetime.now().isoformat()] + memory_ids)
                    conn.commit()
        
        logger.info(f"🔍 메모리 검색 완료: {len(memories)}개 발견")
        return memories
    
    def get_recent_memories(self, 
                           hours: int = 24, 
                           limit: int = 50) -> List[MemoryEntry]:
        """최근 메모리 조회"""
        since = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM memories 
                    WHERE created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (since.isoformat(), limit))
                
                rows = cursor.fetchall()
                memories = []
                
                for row in rows:
                    memory_data = {
                        'id': row[0],
                        'content': row[1],
                        'memory_type': row[2],
                        'importance': row[3],
                        'category': row[4],
                        'tags': json.loads(row[5]),
                        'created_at': row[6],
                        'last_accessed': row[7],
                        'access_count': row[8],
                        'context': json.loads(row[9]) if row[9] else {}
                    }
                    memories.append(MemoryEntry.from_dict(memory_data))
        
        return memories
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Total memories
                total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                
                # By type
                type_stats = {}
                for memory_type in MemoryType:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM memories WHERE memory_type = ?",
                        (memory_type.value,)
                    ).fetchone()[0]
                    type_stats[memory_type.value] = count
                
                # By importance
                importance_stats = {}
                for importance in MemoryImportance:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM memories WHERE importance = ?",
                        (importance.value,)
                    ).fetchone()[0]
                    importance_stats[f"level_{importance.value}"] = count
                
                # Recent activity
                recent_24h = conn.execute('''
                    SELECT COUNT(*) FROM memories 
                    WHERE created_at >= ?
                ''', (
                    (datetime.now() - timedelta(hours=24)).isoformat(),
                )).fetchone()[0]
        
        return {
            'total_memories': total,
            'by_type': type_stats,
            'by_importance': importance_stats,
            'recent_24h': recent_24h
        }
    
    def _check_consolidation(self):
        """메모리 통합 확인"""
        short_term_count = len(self.retrieve_memories(
            memory_type=MemoryType.SHORT_TERM,
            limit=1000
        ))
        
        if short_term_count > self.consolidation_threshold:
            logger.info("🔄 메모리 통합 시작")
            self._consolidate_memories()
    
    def _consolidate_memories(self):
        """메모리 통합 수행"""
        # Get old short-term memories
        old_memories = self.retrieve_memories(
            memory_type=MemoryType.SHORT_TERM,
            limit=1000
        )
        
        # Sort by importance and access count
        old_memories.sort(key=lambda m: (m.importance.value, m.access_count), reverse=True)
        
        # Keep important ones, convert others to long-term or delete
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                for memory in old_memories[self.short_term_limit:]:
                    if memory.importance.value >= MemoryImportance.MEDIUM.value or memory.access_count > 2:
                        # Convert to long-term
                        conn.execute('''
                            UPDATE memories 
                            SET memory_type = ?
                            WHERE id = ?
                        ''', (MemoryType.LONG_TERM.value, memory.id))
                    else:
                        # Delete low-importance memories
                        conn.execute('DELETE FROM memories WHERE id = ?', (memory.id,))
                
                conn.commit()
        
        logger.info("✅ 메모리 통합 완료")
    
    def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def update_memory(self, memory_id: str, **updates) -> bool:
        """메모리 업데이트"""
        allowed_fields = ['content', 'importance', 'category', 'tags', 'context']
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                set_clauses = []
                params = []
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        if field == 'importance' and isinstance(value, MemoryImportance):
                            value = value.value
                        elif field in ['tags', 'context']:
                            value = json.dumps(value)
                        
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if set_clauses:
                    sql = f"UPDATE memories SET {', '.join(set_clauses)} WHERE id = ?"
                    params.append(memory_id)
                    
                    cursor = conn.execute(sql, params)
                    conn.commit()
                    return cursor.rowcount > 0
        
        return False
    
    def search_similar_memories(self, content: str, limit: int = 5) -> List[MemoryEntry]:
        """유사한 메모리 검색"""
        # Simple similarity based on keyword matching
        keywords = content.lower().split()
        
        memories = self.retrieve_memories(limit=100)
        scored_memories = []
        
        for memory in memories:
            memory_words = memory.content.lower().split()
            common_words = set(keywords) & set(memory_words)
            similarity_score = len(common_words) / max(len(keywords), 1)
            
            if similarity_score > 0:
                scored_memories.append((memory, similarity_score))
        
        # Sort by similarity score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        return [memory for memory, score in scored_memories[:limit]]
    
    def export_memories(self, file_path: str):
        """메모리 내보내기"""
        memories = self.retrieve_memories(limit=10000)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_memories': len(memories),
            'memories': [memory.to_dict() for memory in memories]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📤 메모리 내보내기 완료: {file_path}")
    
    def import_memories(self, file_path: str):
        """메모리 가져오기"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        for memory_data in data.get('memories', []):
            try:
                memory = MemoryEntry.from_dict(memory_data)
                
                with self.lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute('''
                            INSERT OR REPLACE INTO memories 
                            (id, content, memory_type, importance, category, tags, 
                             created_at, last_accessed, access_count, context)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            memory.id,
                            memory.content,
                            memory.memory_type.value,
                            memory.importance.value,
                            memory.category,
                            json.dumps(memory.tags),
                            memory.created_at.isoformat(),
                            memory.last_accessed.isoformat(),
                            memory.access_count,
                            json.dumps(memory.context or {})
                        ))
                        conn.commit()
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"메모리 가져오기 오류: {e}")
        
        logger.info(f"📥 메모리 가져오기 완료: {imported_count}개")

# Example usage and testing
if __name__ == "__main__":
    # Test the memory system
    memory_system = MemorySystem("test_memory.db")
    
    print("🧠 메모리 시스템 테스트")
    print("=" * 50)
    
    # Store some test memories
    memory_system.store_memory(
        "사용자가 안녕하세요라고 인사했습니다",
        MemoryType.EPISODIC,
        MemoryImportance.MEDIUM,
        "user_interaction",
        ["greeting", "user"]
    )
    
    memory_system.store_memory(
        "에이전트 시작 시간은 오후 3시입니다",
        MemoryType.SEMANTIC,
        MemoryImportance.HIGH,
        "system_info",
        ["time", "startup"]
    )
    
    memory_system.store_memory(
        "날씨 정보 조회 방법을 학습했습니다",
        MemoryType.PROCEDURAL,
        MemoryImportance.HIGH,
        "learning",
        ["weather", "procedure"]
    )
    
    # Test retrieval
    print("\n🔍 메모리 검색 테스트:")
    memories = memory_system.retrieve_memories(query="사용자", limit=5)
    for memory in memories:
        print(f"- [{memory.category}] {memory.content}")
    
    # Test statistics
    print("\n📊 메모리 통계:")
    stats = memory_system.get_memory_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Clean up test database
    if os.path.exists("test_memory.db"):
        os.remove("test_memory.db")