"""
Hallucination Guard
==================

Enterprise-grade anti-hallucination system with fact verification,
attribution checking, and confidence validation.

Author: Enterprise HR Bot Team
Version: 2.0.0
"""

import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain.schema import Document

logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """Verification strictness levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class FactType(Enum):
    """Types of facts that require verification"""
    CONTACT_INFO = "contact_info"
    MONETARY_AMOUNT = "monetary_amount"
    DATE_DEADLINE = "date_deadline"
    POLICY_STATEMENT = "policy_statement"
    PROCEDURE_STEP = "procedure_step"
    PERSON_INFO = "person_info"
    REQUIREMENT = "requirement"
    GENERAL_FACT = "general_fact"


@dataclass
class FactCheck:
    """Individual fact verification result"""
    fact_text: str
    fact_type: FactType
    is_verified: bool
    confidence: float
    supporting_evidence: List[str]
    source_documents: List[Document]
    verification_method: str
    risk_level: str


@dataclass
class VerificationResult:
    """Comprehensive verification result for entire response"""
    overall_verified: bool
    confidence_score: float
    fact_checks: List[FactCheck]
    unsupported_claims: List[str]
    missing_attributions: List[str]
    risk_assessment: str
    recommendations: List[str]
    verification_time: float


class HallucinationGuard:
    """
    Enterprise-grade hallucination prevention system with comprehensive
    fact verification, attribution checking, and confidence validation.
    """
    
    def __init__(self, verification_level: VerificationLevel = VerificationLevel.STRICT):
        self.verification_level = verification_level
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Fact extraction patterns
        self.fact_patterns = {
            FactType.CONTACT_INFO: [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
                r'\b(?:room|office|building)\s+\w+\b',  # Office locations
            ],
            FactType.MONETARY_AMOUNT: [
                r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
                r'\b\d+\s*(?:dollars?|USD)\b',  # Written amounts
                r'\b\d+\%\s*(?:of|salary|income)\b',  # Percentages
            ],
            FactType.DATE_DEADLINE: [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # Dates
                r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*\d{4}\b',  # Written dates
                r'\b(?:deadline|due date|expires?|effective)\s+\w+\b',  # Deadline references
            ],
            FactType.POLICY_STATEMENT: [
                r'\bmust\s+\w+',  # Requirements
                r'\brequired?\s+to\s+\w+',  # Required actions
                r'\bpolicy\s+states?\s+\w+',  # Policy statements
                r'\bnot\s+(?:allowed|permitted)\s+to\s+\w+',  # Prohibitions
            ],
            FactType.PROCEDURE_STEP: [
                r'\b(?:first|second|third|next|then|finally),?\s+\w+',  # Step sequences
                r'\bstep\s+\d+:?\s+\w+',  # Numbered steps
                r'\bto\s+\w+,\s+you\s+(?:must|need|should)\s+\w+',  # Action instructions
            ],
            FactType.PERSON_INFO: [
                r'\b(?:prof(?:essor)?|dr\.?|mr\.?|ms\.?|mrs\.?)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Person names with titles
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+is\s+(?:the|a)\s+\w+',  # Person roles
            ],
            FactType.REQUIREMENT: [
                r'\byou\s+(?:must|need|should|have to)\s+\w+',  # User requirements
                r'\brequires?\s+\w+',  # General requirements
                r'\bnecessary\s+to\s+\w+',  # Necessity statements
            ]
        }
        
        # High-risk phrases that often indicate hallucination
        self.hallucination_indicators = [
            r'\bi\s+believe\s+\w+',
            r'\bit\s+seems?\s+(?:like|that)\s+\w+',
            r'\bprobably\s+\w+',
            r'\blikely\s+\w+',
            r'\bassuming\s+\w+',
            r'\bi\s+think\s+\w+',
            r'\bmy\s+understanding\s+is\s+\w+',
            r'\bgenerally\s+speaking\s+\w+',
            r'\btypically\s+\w+',
            r'\busually\s+\w+',
        ]
        
        # Attribution phrases to identify sourced information
        self.attribution_patterns = [
            r'\baccording\s+to\s+\w+',
            r'\bas\s+stated\s+in\s+\w+',
            r'\bthe\s+(?:policy|handbook|document)\s+states?\s+\w+',
            r'\bas\s+outlined\s+in\s+\w+',
            r'\bper\s+the\s+\w+',
        ]
        
        # Confidence thresholds based on verification level
        self.confidence_thresholds = {
            VerificationLevel.STRICT: 0.9,
            VerificationLevel.MODERATE: 0.7,
            VerificationLevel.LENIENT: 0.5
        }
        
        logger.info(f"Hallucination Guard initialized with {verification_level.value} verification")

    async def verify_response(self, 
                            response_text: str, 
                            source_documents: List[Document],
                            query_context: Optional[Any] = None) -> VerificationResult:
        """
        Comprehensive verification of response against source documents
        
        Args:
            response_text: Generated response to verify
            source_documents: Retrieved source documents
            query_context: Original query context for additional validation
            
        Returns:
            VerificationResult: Comprehensive verification results
        """
        start_time = time.time()
        
        # Extract facts from response
        extracted_facts = await self._extract_facts(response_text)
        
        # Verify each fact against sources
        fact_checks = await self._verify_facts(extracted_facts, source_documents)
        
        # Check for unsupported claims
        unsupported_claims = await self._find_unsupported_claims(response_text, source_documents)
        
        # Check for proper attribution
        missing_attributions = await self._check_attributions(response_text, source_documents)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(fact_checks)
        
        # Assess risk level
        risk_assessment = self._assess_risk_level(fact_checks, unsupported_claims)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(fact_checks, unsupported_claims, missing_attributions)
        
        # Determine if response is verified
        threshold = self.confidence_thresholds[self.verification_level]
        overall_verified = overall_confidence >= threshold and len(unsupported_claims) == 0
        
        verification_time = time.time() - start_time
        
        result = VerificationResult(
            overall_verified=overall_verified,
            confidence_score=overall_confidence,
            fact_checks=fact_checks,
            unsupported_claims=unsupported_claims,
            missing_attributions=missing_attributions,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            verification_time=verification_time
        )
        
        logger.info(f"🛡️ Verification completed: {overall_verified} (confidence: {overall_confidence:.2f}, time: {verification_time:.3f}s)")
        
        return result

    async def _extract_facts(self, response_text: str) -> Dict[FactType, List[str]]:
        """Extract factual claims from response text"""
        facts = {fact_type: [] for fact_type in FactType}
        
        # Extract facts using parallel processing
        tasks = []
        for fact_type, patterns in self.fact_patterns.items():
            task = asyncio.create_task(self._extract_fact_type(response_text, fact_type, patterns))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        for i, fact_type in enumerate(self.fact_patterns.keys()):
            facts[fact_type] = results[i]
        
        # Extract general factual statements
        facts[FactType.GENERAL_FACT] = await self._extract_general_facts(response_text)
        
        return facts

    async def _extract_fact_type(self, text: str, fact_type: FactType, patterns: List[str]) -> List[str]:
        """Extract specific type of facts using patterns"""
        loop = asyncio.get_event_loop()
        
        def extract():
            found_facts = []
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    fact_text = match.group(0).strip()
                    if fact_text and fact_text not in found_facts:
                        found_facts.append(fact_text)
            return found_facts
        
        return await loop.run_in_executor(self.executor, extract)

    async def _extract_general_facts(self, text: str) -> List[str]:
        """Extract general factual statements"""
        loop = asyncio.get_event_loop()
        
        def extract():
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            factual_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                
                # Look for factual indicators
                factual_indicators = [
                    r'\bis\s+(?:the|a|an)\s+\w+',
                    r'\brequires?\s+\w+',
                    r'\bmust\s+\w+',
                    r'\bshould\s+\w+',
                    r'\bcan\s+\w+',
                    r'\bcosts?\s+\w+',
                    r'\btakes?\s+\w+',
                    r'\bincludes?\s+\w+',
                ]
                
                if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in factual_indicators):
                    factual_sentences.append(sentence)
            
            return factual_sentences
        
        return await loop.run_in_executor(self.executor, extract)

    async def _verify_facts(self, 
                          extracted_facts: Dict[FactType, List[str]], 
                          source_documents: List[Document]) -> List[FactCheck]:
        """Verify extracted facts against source documents"""
        fact_checks = []
        
        # Combine all source text for verification
        source_text = " ".join([doc.page_content for doc in source_documents]).lower()
        
        for fact_type, facts in extracted_facts.items():
            for fact in facts:
                fact_check = await self._verify_single_fact(fact, fact_type, source_text, source_documents)
                fact_checks.append(fact_check)
        
        return fact_checks

    async def _verify_single_fact(self, 
                                fact_text: str, 
                                fact_type: FactType, 
                                source_text: str,
                                source_documents: List[Document]) -> FactCheck:
        """Verify a single fact against sources"""
        loop = asyncio.get_event_loop()
        
        def verify():
            # Direct text matching
            if fact_text.lower() in source_text:
                return FactCheck(
                    fact_text=fact_text,
                    fact_type=fact_type,
                    is_verified=True,
                    confidence=0.9,
                    supporting_evidence=[fact_text],
                    source_documents=source_documents,
                    verification_method="direct_match",
                    risk_level="low"
                )
            
            # Semantic matching for critical facts
            if fact_type in [FactType.CONTACT_INFO, FactType.MONETARY_AMOUNT, FactType.DATE_DEADLINE]:
                # These require exact matches
                return FactCheck(
                    fact_text=fact_text,
                    fact_type=fact_type,
                    is_verified=False,
                    confidence=0.0,
                    supporting_evidence=[],
                    source_documents=[],
                    verification_method="exact_required",
                    risk_level="high"
                )
            
            # Partial matching for other fact types
            fact_words = set(fact_text.lower().split())
            source_words = set(source_text.split())
            overlap = len(fact_words.intersection(source_words))
            overlap_ratio = overlap / len(fact_words) if fact_words else 0
            
            if overlap_ratio >= 0.7:
                return FactCheck(
                    fact_text=fact_text,
                    fact_type=fact_type,
                    is_verified=True,
                    confidence=overlap_ratio,
                    supporting_evidence=[f"Partial match: {overlap}/{len(fact_words)} words"],
                    source_documents=source_documents,
                    verification_method="partial_match",
                    risk_level="medium"
                )
            
            return FactCheck(
                fact_text=fact_text,
                fact_type=fact_type,
                is_verified=False,
                confidence=overlap_ratio,
                supporting_evidence=[],
                source_documents=[],
                verification_method="no_match",
                risk_level="high"
            )
        
        return await loop.run_in_executor(self.executor, verify)

    async def _find_unsupported_claims(self, 
                                     response_text: str, 
                                     source_documents: List[Document]) -> List[str]:
        """Find claims in response that are not supported by sources"""
        loop = asyncio.get_event_loop()
        
        def find_unsupported():
            unsupported = []
            source_text = " ".join([doc.page_content for doc in source_documents]).lower()
            
            # Check for hallucination indicators
            for pattern in self.hallucination_indicators:
                matches = re.finditer(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(response_text), match.end() + 50)
                    context = response_text[context_start:context_end].strip()
                    unsupported.append(f"Uncertain language: {context}")
            
            # Check for specific claims without source support
            sentences = re.split(r'[.!?]+', response_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue
                
                # Look for definitive claims
                if any(phrase in sentence.lower() for phrase in ['the policy states', 'you must', 'the requirement is', 'the deadline is']):
                    # Check if this claim is supported by sources
                    claim_words = set(sentence.lower().split())
                    source_words = set(source_text.split())
                    overlap = len(claim_words.intersection(source_words))
                    overlap_ratio = overlap / len(claim_words) if claim_words else 0
                    
                    if overlap_ratio < 0.5:  # Less than 50% word overlap
                        unsupported.append(sentence)
            
            return unsupported
        
        return await loop.run_in_executor(self.executor, find_unsupported)

    async def _check_attributions(self, 
                                response_text: str, 
                                source_documents: List[Document]) -> List[str]:
        """Check for proper attribution of sourced information"""
        loop = asyncio.get_event_loop()
        
        def check_attributions():
            missing_attributions = []
            
            # Look for factual statements that should have attribution
            factual_patterns = [
                r'\bthe\s+policy\s+(?:states?|requires?)\s+\w+',
                r'\byou\s+(?:must|need|should)\s+\w+',
                r'\bthe\s+(?:deadline|requirement|process)\s+is\s+\w+',
                r'\bcontact\s+\w+\s+at\s+\w+',
            ]
            
            # Check if factual statements have nearby attribution
            for pattern in factual_patterns:
                matches = re.finditer(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    statement = match.group(0)
                    
                    # Look for attribution within 100 characters before or after
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(response_text), match.end() + 100)
                    context = response_text[context_start:context_end]
                    
                    has_attribution = any(
                        re.search(attr_pattern, context, re.IGNORECASE) 
                        for attr_pattern in self.attribution_patterns
                    )
                    
                    if not has_attribution:
                        missing_attributions.append(statement)
            
            return missing_attributions
        
        return await loop.run_in_executor(self.executor, check_attributions)

    def _calculate_overall_confidence(self, fact_checks: List[FactCheck]) -> float:
        """Calculate overall confidence score from individual fact checks"""
        if not fact_checks:
            return 0.5  # Neutral confidence for responses with no extractable facts
        
        verified_count = sum(1 for check in fact_checks if check.is_verified)
        high_risk_count = sum(1 for check in fact_checks if check.risk_level == "high")
        
        # Base confidence from verification ratio
        verification_ratio = verified_count / len(fact_checks)
        
        # Penalty for high-risk unverified facts
        risk_penalty = (high_risk_count / len(fact_checks)) * 0.3
        
        # Average confidence from individual checks
        avg_confidence = sum(check.confidence for check in fact_checks) / len(fact_checks)
        
        # Combine scores
        overall_confidence = (verification_ratio * 0.4 + avg_confidence * 0.6) - risk_penalty
        
        return max(0.0, min(1.0, overall_confidence))

    def _assess_risk_level(self, fact_checks: List[FactCheck], unsupported_claims: List[str]) -> str:
        """Assess overall risk level of the response"""
        high_risk_facts = sum(1 for check in fact_checks if check.risk_level == "high" and not check.is_verified)
        total_unsupported = len(unsupported_claims)
        
        if high_risk_facts > 0 or total_unsupported > 2:
            return "HIGH"
        elif high_risk_facts == 0 and total_unsupported <= 1:
            return "LOW"
        else:
            return "MEDIUM"

    def _generate_recommendations(self, 
                                fact_checks: List[FactCheck], 
                                unsupported_claims: List[str],
                                missing_attributions: List[str]) -> List[str]:
        """Generate recommendations for improving response quality"""
        recommendations = []
        
        # Recommendations based on fact checks
        unverified_high_risk = [check for check in fact_checks if not check.is_verified and check.risk_level == "high"]
        if unverified_high_risk:
            recommendations.append("Remove or verify high-risk unverified facts")
        
        # Recommendations based on unsupported claims
        if unsupported_claims:
            recommendations.append("Remove uncertain language and unsupported claims")
        
        # Recommendations based on missing attributions
        if missing_attributions:
            recommendations.append("Add proper source attribution for factual statements")
        
        # Verification level specific recommendations
        if self.verification_level == VerificationLevel.STRICT:
            if any(not check.is_verified for check in fact_checks):
                recommendations.append("All facts must be verified for strict mode")
        
        # Default recommendation if no issues found
        if not recommendations:
            recommendations.append("Response appears well-verified and properly attributed")
        
        return recommendations

    def create_safe_fallback_response(self, query: str, available_info: List[str]) -> str:
        """Create a safe fallback response when verification fails"""
        base_response = "I don't have enough verified information to fully answer your question."
        
        if available_info:
            safe_info = "\n\nBased on our available documentation, here's what I can confirm:\n"
            for info in available_info[:3]:  # Limit to top 3 pieces of verified info
                safe_info += f"• {info}\n"
            
            base_response += safe_info
        
        base_response += "\n\nFor complete and accurate information, please:\n"
        base_response += "• Check the official HR documentation\n"
        base_response += "• Contact the HR department directly\n"
        base_response += "• Consult with your supervisor or department head"
        
        return base_response

    def get_verification_statistics(self) -> Dict[str, Any]:
        """Get statistics about verification performance"""
        return {
            'verification_level': self.verification_level.value,
            'confidence_threshold': self.confidence_thresholds[self.verification_level],
            'supported_fact_types': [ft.value for ft in FactType],
            'hallucination_patterns': len(self.hallucination_indicators),
            'attribution_patterns': len(self.attribution_patterns)
        }
