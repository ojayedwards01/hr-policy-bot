"""
Enterprise Query Processor
=========================

Core query processing engine with comprehensive preprocessing,
validation, and context-aware query enhancement.

Author: Enterprise HR Bot Team
Version: 2.0.0
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type classification for specialized processing"""
    PERSON_LOOKUP = "person_lookup"
    POLICY_INQUIRY = "policy_inquiry"
    PROCEDURE_INQUIRY = "procedure_inquiry"
    GENERAL_INFO = "general_info"
    TRAVEL_RELATED = "travel_related"
    BENEFITS_RELATED = "benefits_related"
    GREETING = "greeting"
    UNCLEAR = "unclear"


@dataclass
class QueryContext:
    """Enhanced query context with conversation history and user metadata"""
    user_id: str
    session_id: str
    platform: str  # web, slack, email
    conversation_history: List[Dict[str, Any]]
    original_query: str
    processed_query: str
    query_type: QueryType
    confidence_score: float
    processing_time: float
    extracted_entities: Dict[str, List[str]]
    query_intent: str
    priority_keywords: List[str]


class EnterpriseQueryProcessor:
    """
    Enterprise-grade query processor with advanced preprocessing,
    entity extraction, and conversation-aware enhancement.
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # HR-specific entity patterns
        self.person_patterns = [
            r'\b(?:prof(?:essor)?|dr\.?|mr\.?|ms\.?|mrs\.?)\s+([a-z]+(?:\s+[a-z]+)*)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # John Smith format
            r'\b([A-Z]\.\s*[A-Z][a-z]+)\b',  # J. Smith format
        ]
        
        self.policy_keywords = {
            'travel': ['travel', 'trip', 'conference', 'business travel', 'reimbursement', 'expense'],
            'leave': ['leave', 'vacation', 'pto', 'sick', 'maternity', 'paternity', 'sabbatical'],
            'benefits': ['benefit', 'insurance', 'health', 'dental', 'retirement', '401k', 'pension'],
            'hiring': ['hire', 'hiring', 'recruitment', 'position', 'job', 'appointment', 'onboarding'],
            'promotion': ['promotion', 'tenure', 'advancement', 'rank', 'professor', 'associate'],
            'research': ['research', 'grant', 'funding', 'publication', 'conference', 'sabbatical'],
            'administrative': ['policy', 'procedure', 'guideline', 'handbook', 'manual', 'form']
        }
        
        self.africa_keywords = [
            'africa', 'kigali', 'rwanda', 'cmu africa', 'carnegie mellon africa',
            'cmu-africa', 'campus', 'local', 'international'
        ]
        
        self.greeting_patterns = [
            r'^(hi|hello|hey|good\s+(morning|afternoon|evening))\b',
            r'^(thanks?|thank\s+you)\b',
            r'^(goodbye|bye|see\s+you)\b'
        ]
        
        logger.info("Enterprise Query Processor initialized")

    async def process_query(self, 
                          query: str, 
                          user_id: str, 
                          session_id: str, 
                          platform: str = "web",
                          conversation_history: Optional[List[Dict]] = None) -> QueryContext:
        """
        Process query with comprehensive analysis and enhancement
        
        Args:
            query: Raw user query
            user_id: Unique user identifier
            session_id: Session identifier for conversation tracking
            platform: Interface platform (web, slack, email)
            conversation_history: Previous conversation context
            
        Returns:
            QueryContext: Processed query with full context and metadata
        """
        start_time = time.time()
        
        # Initialize context
        conversation_history = conversation_history or []
        
        # Parallel processing of query analysis
        loop = asyncio.get_event_loop()
        
        # Run analysis tasks concurrently
        tasks = [
            loop.run_in_executor(self.executor, self._clean_query, query),
            loop.run_in_executor(self.executor, self._classify_query_type, query),
            loop.run_in_executor(self.executor, self._extract_entities, query),
            loop.run_in_executor(self.executor, self._analyze_intent, query),
            loop.run_in_executor(self.executor, self._extract_priority_keywords, query)
        ]
        
        results = await asyncio.gather(*tasks)
        cleaned_query, query_type, entities, intent, priority_keywords = results
        
        # Enhance query with conversation context
        enhanced_query = await self._enhance_with_context(
            cleaned_query, conversation_history, entities
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(query_type, entities, intent)
        
        processing_time = time.time() - start_time
        
        context = QueryContext(
            user_id=user_id,
            session_id=session_id,
            platform=platform,
            conversation_history=conversation_history,
            original_query=query,
            processed_query=enhanced_query,
            query_type=query_type,
            confidence_score=confidence,
            processing_time=processing_time,
            extracted_entities=entities,
            query_intent=intent,
            priority_keywords=priority_keywords
        )
        
        logger.info(f"🔍 Query processed: {query_type.value} (confidence: {confidence:.2f}, time: {processing_time:.3f}s)")
        return context

    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Standardize common variations
        replacements = {
            r'\bcmu\s*africa\b': 'CMU-Africa',
            r'\bcarnegie\s*mellon\s*africa\b': 'CMU-Africa',
            r'\bprof\.?\b': 'professor',
            r'\bdr\.?\b': 'doctor',
            r'\bhr\b': 'human resources',
            r'\bpto\b': 'paid time off',
        }
        
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned

    def _classify_query_type(self, query: str) -> QueryType:
        """Classify query type for specialized processing"""
        query_lower = query.lower()
        
        # Check for greetings
        if any(re.search(pattern, query_lower) for pattern in self.greeting_patterns):
            return QueryType.GREETING
        
        # Check for person lookup patterns
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.person_patterns):
            return QueryType.PERSON_LOOKUP
        
        # Check for policy/procedure keywords
        travel_count = sum(1 for keyword in self.policy_keywords['travel'] if keyword in query_lower)
        if travel_count >= 1:
            return QueryType.TRAVEL_RELATED
        
        benefits_count = sum(1 for keyword in self.policy_keywords['benefits'] if keyword in query_lower)
        if benefits_count >= 1:
            return QueryType.BENEFITS_RELATED
        
        # Check for policy vs procedure
        policy_indicators = ['policy', 'rule', 'guideline', 'regulation', 'what is']
        procedure_indicators = ['how to', 'how do i', 'steps', 'process', 'procedure', 'apply', 'submit']
        
        if any(indicator in query_lower for indicator in procedure_indicators):
            return QueryType.PROCEDURE_INQUIRY
        elif any(indicator in query_lower for indicator in policy_indicators):
            return QueryType.POLICY_INQUIRY
        
        return QueryType.GENERAL_INFO

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract named entities and key terms from query"""
        entities = {
            'people': [],
            'locations': [],
            'organizations': [],
            'topics': [],
            'amounts': [],
            'dates': []
        }
        
        # Extract person names
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                name = match.group(1) if match.lastindex else match.group(0)
                entities['people'].append(name.strip())
        
        # Extract locations
        location_patterns = [
            r'\b(kigali|rwanda|pittsburgh|pennsylvania|africa)\b',
            r'\b(campus|office|building|room)\s+(\w+)\b'
        ]
        for pattern in location_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            entities['locations'].extend([match.group(0) for match in matches])
        
        # Extract organizations/departments
        org_patterns = [
            r'\b(cmu|carnegie mellon|hr|human resources|finance|it|computing)\b',
            r'\b(school of \w+|college of \w+|department of \w+)\b'
        ]
        for pattern in org_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            entities['organizations'].extend([match.group(0) for match in matches])
        
        # Extract amounts and dates
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+\s*(?:dollars?|usd)\b'
        date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*\d{4}\b'
        
        entities['amounts'] = re.findall(amount_pattern, query, re.IGNORECASE)
        entities['dates'] = re.findall(date_pattern, query, re.IGNORECASE)
        
        return entities

    def _analyze_intent(self, query: str) -> str:
        """Analyze user intent from query"""
        query_lower = query.lower()
        
        # Question patterns
        if query_lower.startswith(('how', 'what', 'when', 'where', 'who', 'why')):
            return 'information_seeking'
        
        if query_lower.startswith(('can i', 'may i', 'am i allowed', 'is it possible')):
            return 'permission_inquiry'
        
        if query_lower.startswith(('i need', 'help me', 'assist me')):
            return 'assistance_request'
        
        if any(word in query_lower for word in ['apply', 'submit', 'request', 'form']):
            return 'action_required'
        
        if any(word in query_lower for word in ['find', 'locate', 'contact', 'reach']):
            return 'contact_seeking'
        
        return 'general_inquiry'

    def _extract_priority_keywords(self, query: str) -> List[str]:
        """Extract high-priority keywords for enhanced retrieval"""
        priority_keywords = []
        query_lower = query.lower()
        
        # Add topic-specific keywords
        for topic, keywords in self.policy_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                priority_keywords.extend([kw for kw in keywords if kw in query_lower])
        
        # Add Africa-specific keywords
        priority_keywords.extend([kw for kw in self.africa_keywords if kw in query_lower])
        
        # Extract key nouns and verbs
        important_terms = re.findall(r'\b(?:policy|procedure|research|conference|process|requirement|deadline|application|form|document|guideline|handbook|manual)\b', query_lower)
        priority_keywords.extend(important_terms)
        
        return list(set(priority_keywords))  # Remove duplicates

    async def _enhance_with_context(self, 
                                  query: str, 
                                  conversation_history: List[Dict], 
                                  entities: Dict[str, List[str]]) -> str:
        """Enhance query with conversation context and extracted entities"""
        if not conversation_history:
            return query
        
        # Look for context from recent queries
        recent_context = []
        for entry in conversation_history[-3:]:  # Last 3 exchanges
            if 'question' in entry:
                # Extract relevant context from previous questions
                prev_entities = self._extract_entities(entry['question'])
                if prev_entities['people'] and not entities['people']:
                    recent_context.append(f"referring to {', '.join(prev_entities['people'])}")
                if prev_entities['topics']:
                    recent_context.append(f"related to {', '.join(prev_entities['topics'])}")
        
        if recent_context:
            enhanced_query = f"{query} (context: {'; '.join(recent_context)})"
            return enhanced_query
        
        return query

    def _calculate_confidence(self, 
                            query_type: QueryType, 
                            entities: Dict[str, List[str]], 
                            intent: str) -> float:
        """Calculate confidence score for query processing quality"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear query types
        if query_type in [QueryType.GREETING, QueryType.PERSON_LOOKUP]:
            confidence += 0.3
        elif query_type != QueryType.UNCLEAR:
            confidence += 0.2
        
        # Boost confidence for entity extraction success
        entity_count = sum(len(entities[key]) for key in entities)
        confidence += min(entity_count * 0.05, 0.2)
        
        # Boost confidence for clear intent
        if intent in ['information_seeking', 'permission_inquiry', 'assistance_request']:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def get_query_enhancement_suggestions(self, context: QueryContext) -> List[str]:
        """Provide suggestions for query enhancement based on analysis"""
        suggestions = []
        
        if context.confidence_score < 0.6:
            suggestions.append("Query could be more specific")
        
        if not context.extracted_entities['people'] and context.query_type == QueryType.PERSON_LOOKUP:
            suggestions.append("Person name not clearly identified")
        
        if context.query_type == QueryType.UNCLEAR:
            suggestions.append("Query intent unclear - consider rephrasing")
        
        return suggestions
