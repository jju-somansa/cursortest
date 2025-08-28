"""
Natural Language Processing Module
자연어 처리 모듈
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class Intent:
    """의도 클래스"""
    name: str
    confidence: float
    entities: Dict[str, Any] = None

class NLPProcessor:
    """자연어 처리 프로세서"""
    
    def __init__(self):
        self.intents = self._load_intents()
        self.entities = self._load_entities()
    
    def _load_intents(self) -> Dict[str, List[str]]:
        """의도 패턴 로드"""
        return {
            "greeting": [
                r"안녕|hello|hi|헬로|하이|반가워",
                r"좋은\s*(아침|오후|저녁|밤)",
                r"처음\s*뵙겠습니다"
            ],
            "status_inquiry": [
                r"상태|status|어떻게|괜찮|잘\s*있어",
                r"뭐\s*하고\s*있어|무엇을\s*하고",
                r"어떤\s*상태"
            ],
            "time_inquiry": [
                r"시간|time|몇\s*시|언제",
                r"지금\s*몇\s*시",
                r"현재\s*시간"
            ],
            "capability_inquiry": [
                r"능력|capability|뭘\s*할\s*수\s*있어|무엇을\s*할\s*수",
                r"기능|function|할\s*수\s*있는\s*것",
                r"도움|help|헬프"
            ],
            "task_request": [
                r"해\s*줘|해\s*주세요|부탁|요청",
                r"실행|execute|run|처리",
                r"작업|task|일"
            ],
            "memory_operation": [
                r"기억|remember|저장|save",
                r"잊어|forget|삭제|delete",
                r"생각나|recall|불러와"
            ],
            "farewell": [
                r"안녕|bye|goodbye|잘\s*가|나중에",
                r"끝|종료|stop|그만",
                r"고마워|감사|thanks"
            ]
        }
    
    def _load_entities(self) -> Dict[str, List[str]]:
        """엔티티 패턴 로드"""
        return {
            "time_expressions": [
                r"(\d{1,2})시",
                r"(\d{1,2}):\d{2}",
                r"(오전|오후|아침|점심|저녁|밤)",
                r"(오늘|내일|어제|모레)"
            ],
            "numbers": [
                r"(\d+)",
                r"(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열)"
            ],
            "names": [
                r"([가-힣]{2,4})\s*(씨|님|선생님)",
                r"([A-Za-z]+)\s*(씨|님|sir|mr|ms)"
            ]
        }
    
    def analyze_intent(self, text: str) -> Intent:
        """의도 분석"""
        text_lower = text.lower()
        best_intent = None
        best_confidence = 0.0
        
        for intent_name, patterns in self.intents.items():
            confidence = 0.0
            
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    confidence += 0.3
            
            # 키워드 매칭으로 추가 점수
            if intent_name == "greeting" and any(word in text_lower for word in ["안녕", "hello", "hi"]):
                confidence += 0.4
            elif intent_name == "status_inquiry" and any(word in text_lower for word in ["상태", "어떻게"]):
                confidence += 0.4
            elif intent_name == "time_inquiry" and any(word in text_lower for word in ["시간", "몇시"]):
                confidence += 0.4
            elif intent_name == "capability_inquiry" and any(word in text_lower for word in ["능력", "뭘할수있어"]):
                confidence += 0.4
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_name
        
        # 기본 의도
        if best_intent is None or best_confidence < 0.3:
            best_intent = "general_query"
            best_confidence = 0.1
        
        return Intent(name=best_intent, confidence=best_confidence)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """엔티티 추출"""
        entities = {}
        
        for entity_type, patterns in self.entities.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    matches.extend(found)
            
            if matches:
                entities[entity_type] = matches
        
        return entities
    
    def process(self, text: str) -> Dict[str, Any]:
        """텍스트 전체 처리"""
        intent = self.analyze_intent(text)
        entities = self.extract_entities(text)
        
        return {
            "original_text": text,
            "intent": {
                "name": intent.name,
                "confidence": intent.confidence
            },
            "entities": entities,
            "processed_at": __import__('datetime').datetime.now().isoformat()
        }
    
    def get_response_template(self, intent_name: str) -> str:
        """의도별 응답 템플릿"""
        templates = {
            "greeting": "안녕하세요! 저는 가상 에이전트입니다. 무엇을 도와드릴까요?",
            "status_inquiry": "현재 정상적으로 작동 중입니다. 모든 시스템이 활성화되어 있어요.",
            "time_inquiry": "현재 시간을 확인해드리겠습니다.",
            "capability_inquiry": "제가 할 수 있는 일들을 알려드리겠습니다.",
            "task_request": "요청하신 작업을 처리하겠습니다.",
            "memory_operation": "메모리 작업을 수행하겠습니다.",
            "farewell": "안녕히 가세요! 언제든 다시 찾아주세요.",
            "general_query": "질문을 이해했습니다. 최선을 다해 도와드리겠습니다."
        }
        
        return templates.get(intent_name, templates["general_query"])

# 테스트 코드
if __name__ == "__main__":
    nlp = NLPProcessor()
    
    test_texts = [
        "안녕하세요",
        "현재 상태가 어떻게 되나요?",
        "지금 몇 시인가요?",
        "당신은 뭘 할 수 있나요?",
        "파일을 저장해 주세요",
        "안녕히 가세요"
    ]
    
    for text in test_texts:
        result = nlp.process(text)
        print(f"입력: {text}")
        print(f"의도: {result['intent']['name']} (신뢰도: {result['intent']['confidence']:.2f})")
        print(f"엔티티: {result['entities']}")
        print(f"응답 템플릿: {nlp.get_response_template(result['intent']['name'])}")
        print("-" * 50)