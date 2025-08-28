"""
Natural Language Processing Module for Virtual Agent
가상 에이전트용 자연어 처리 모듈
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IntentType(Enum):
    GREETING = "greeting"
    QUESTION = "question"
    COMMAND = "command"
    REQUEST = "request"
    INFORMATION = "information"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

@dataclass
class ParsedInput:
    original_text: str
    intent: IntentType
    entities: Dict[str, str]
    confidence: float
    keywords: List[str]
    sentiment: str  # positive, negative, neutral

class NLPProcessor:
    """
    자연어 처리 프로세서
    Natural Language Processing Processor
    """
    
    def __init__(self):
        self.korean_patterns = self._load_korean_patterns()
        self.english_patterns = self._load_english_patterns()
        self.entity_patterns = self._load_entity_patterns()
        
    def _load_korean_patterns(self) -> Dict[IntentType, List[str]]:
        """한국어 패턴 로드"""
        return {
            IntentType.GREETING: [
                r'안녕', r'하이', r'헬로', r'반가', r'처음', r'만나서'
            ],
            IntentType.QUESTION: [
                r'뭐야', r'무엇', r'어떻게', r'왜', r'언제', r'어디서', r'누가',
                r'\?', r'궁금', r'알고싶', r'질문'
            ],
            IntentType.COMMAND: [
                r'해줘', r'실행', r'시작', r'중지', r'멈춰', r'종료', r'켜줘', r'꺼줘'
            ],
            IntentType.REQUEST: [
                r'부탁', r'도와', r'해달라', r'요청', r'필요', r'원해'
            ],
            IntentType.INFORMATION: [
                r'시간', r'날짜', r'날씨', r'정보', r'상태', r'현재'
            ],
            IntentType.GOODBYE: [
                r'안녕히', r'잘가', r'바이', r'종료', r'끝'
            ]
        }
    
    def _load_english_patterns(self) -> Dict[IntentType, List[str]]:
        """영어 패턴 로드"""
        return {
            IntentType.GREETING: [
                r'hello', r'hi', r'hey', r'greetings', r'good morning', r'good afternoon'
            ],
            IntentType.QUESTION: [
                r'what', r'how', r'why', r'when', r'where', r'who', r'\?', r'question'
            ],
            IntentType.COMMAND: [
                r'execute', r'run', r'start', r'stop', r'quit', r'exit', r'turn on', r'turn off'
            ],
            IntentType.REQUEST: [
                r'please', r'help', r'need', r'want', r'request', r'could you'
            ],
            IntentType.INFORMATION: [
                r'time', r'date', r'weather', r'status', r'information', r'current'
            ],
            IntentType.GOODBYE: [
                r'goodbye', r'bye', r'see you', r'farewell', r'quit', r'exit'
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[str, str]:
        """엔티티 패턴 로드"""
        return {
            'time': r'(\d{1,2}:\d{2}|\d{1,2}시|\d{1,2}분)',
            'date': r'(\d{4}-\d{2}-\d{2}|\d{1,2}월\s*\d{1,2}일)',
            'number': r'(\d+)',
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'url': r'(https?://[^\s]+)',
            'name': r'([가-힣]{2,4}|[A-Z][a-z]+\s+[A-Z][a-z]+)'
        }
    
    def process(self, text: str) -> ParsedInput:
        """텍스트 처리 및 분석"""
        logger.info(f"NLP 처리 시작: {text[:50]}...")
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Detect intent
        intent = self._detect_intent(cleaned_text)
        
        # Extract entities
        entities = self._extract_entities(cleaned_text)
        
        # Extract keywords
        keywords = self._extract_keywords(cleaned_text)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(cleaned_text)
        
        # Calculate confidence
        confidence = self._calculate_confidence(cleaned_text, intent)
        
        result = ParsedInput(
            original_text=text,
            intent=intent,
            entities=entities,
            confidence=confidence,
            keywords=keywords,
            sentiment=sentiment
        )
        
        logger.info(f"NLP 처리 완료 - Intent: {intent.value}, Confidence: {confidence:.2f}")
        return result
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep Korean, English, numbers, and basic punctuation
        text = re.sub(r'[^\w\s가-힣.,!?]', '', text)
        
        return text.lower()
    
    def _detect_intent(self, text: str) -> IntentType:
        """의도 감지"""
        intent_scores = {}
        
        # Check Korean patterns
        for intent, patterns in self.korean_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            intent_scores[intent] = score
        
        # Check English patterns
        for intent, patterns in self.english_patterns.items():
            score = intent_scores.get(intent, 0)
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            intent_scores[intent] = score
        
        # Find highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return best_intent[0]
        
        return IntentType.UNKNOWN
    
    def _extract_entities(self, text: str) -> Dict[str, str]:
        """엔티티 추출"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        # Simple keyword extraction - split by spaces and filter
        words = text.split()
        
        # Filter out common stop words
        stop_words = {
            '그', '이', '저', '것', '수', '있', '없', '하', '되', '된', '될', '하는',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Return top 10 keywords
    
    def _analyze_sentiment(self, text: str) -> str:
        """감정 분석"""
        positive_words = [
            '좋', '훌륭', '멋진', '최고', '행복', '기쁜', '즐거운', '만족',
            'good', 'great', 'excellent', 'awesome', 'happy', 'pleased', 'satisfied'
        ]
        
        negative_words = [
            '나쁜', '싫은', '화난', '슬픈', '실망', '짜증', '문제', '오류',
            'bad', 'terrible', 'awful', 'angry', 'sad', 'disappointed', 'problem', 'error'
        ]
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(self, text: str, intent: IntentType) -> float:
        """신뢰도 계산"""
        if intent == IntentType.UNKNOWN:
            return 0.1
        
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on text length and clarity
        if len(text.split()) >= 3:
            confidence += 0.2
        
        # Increase confidence if specific patterns are found
        all_patterns = list(self.korean_patterns.get(intent, [])) + list(self.english_patterns.get(intent, []))
        
        pattern_matches = 0
        for pattern in all_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
        
        if pattern_matches > 0:
            confidence += min(0.3, pattern_matches * 0.1)
        
        return min(1.0, confidence)

# Example usage and testing
if __name__ == "__main__":
    processor = NLPProcessor()
    
    test_inputs = [
        "안녕하세요! 오늘 날씨가 어때요?",
        "시간 좀 알려주세요",
        "에이전트 상태를 확인하고 싶어요",
        "Hello, can you help me?",
        "What time is it now?",
        "Please start the system"
    ]
    
    print("🧠 NLP 프로세서 테스트")
    print("=" * 50)
    
    for text in test_inputs:
        result = processor.process(text)
        print(f"\n입력: {text}")
        print(f"의도: {result.intent.value}")
        print(f"엔티티: {result.entities}")
        print(f"키워드: {result.keywords}")
        print(f"감정: {result.sentiment}")
        print(f"신뢰도: {result.confidence:.2f}")