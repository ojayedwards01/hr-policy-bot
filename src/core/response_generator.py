"""
Enterprise Response Generator
============================

Advanced response generation system with platform-specific formatting,
attribution management, and quality assurance.

Author: Enterprise HR Bot Team
Version: 2.0.0
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

from langchain.schema import Document
from langchain_groq import ChatGroq

from .query_processor import QueryContext, QueryType
from .retrieval_engine import RetrievalResult
from .hallucination_guard import HallucinationGuard, VerificationResult

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Supported response formats"""
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    SLACK = "slack"
    EMAIL = "email"


class ResponseQuality(Enum):
    """Response quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class ResponseMetadata:
    """Comprehensive response metadata"""
    query_context: QueryContext
    retrieval_results: List[RetrievalResult]
    verification_result: VerificationResult
    generation_time: float
    quality_score: float
    platform: str
    format_type: ResponseFormat
    attribution_count: int
    source_count: int
    confidence_level: str


@dataclass
class GeneratedResponse:
    """Complete response with metadata and quality metrics"""
    content: str
    metadata: ResponseMetadata
    sources: List[Document]
    quality_level: ResponseQuality
    is_safe: bool
    recommendations: List[str]


class EnterpriseResponseGenerator:
    """
    Enterprise-grade response generator with comprehensive quality assurance,
    platform-specific formatting, and anti-hallucination protection.
    """
    
    def __init__(self, llm: ChatGroq, hallucination_guard: HallucinationGuard):
        self.llm = llm
        self.guard = hallucination_guard
        
        # Platform-specific prompts
        self.platform_prompts = {
            "web": self._get_web_prompt(),
            "slack": self._get_slack_prompt(),
            "email": self._get_email_prompt(),
            "universal": self._get_universal_prompt()
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            ResponseQuality.EXCELLENT: 0.9,
            ResponseQuality.GOOD: 0.75,
            ResponseQuality.ACCEPTABLE: 0.6,
            ResponseQuality.POOR: 0.0
        }
        
        # Response templates for different scenarios
        self.templates = {
            'insufficient_info': self._get_insufficient_info_template(),
            'verification_failed': self._get_verification_failed_template(),
            'greeting': self._get_greeting_template(),
            'person_not_found': self._get_person_not_found_template()
        }
        
        logger.info("Enterprise Response Generator initialized")

    async def generate_response(self, 
                              query_context: QueryContext,
                              retrieval_results: List[RetrievalResult],
                              platform: str = "web") -> GeneratedResponse:
        """
        Generate enterprise-grade response with comprehensive quality assurance
        
        Args:
            query_context: Processed query context
            retrieval_results: Retrieved and ranked documents
            platform: Target platform (web, slack, email)
            
        Returns:
            GeneratedResponse: Complete response with quality metrics
        """
        start_time = time.time()
        
        # Handle special cases
        if query_context.query_type == QueryType.GREETING:
            return self._generate_greeting_response(query_context, platform, start_time)
        
        if not retrieval_results or len(retrieval_results) == 0:
            return self._generate_insufficient_info_response(query_context, platform, start_time)
        
        # Generate initial response
        initial_response = await self._generate_initial_response(
            query_context, retrieval_results, platform
        )
        
        # Verify response against sources
        source_documents = [result.document for result in retrieval_results]
        verification_result = await self.guard.verify_response(
            initial_response, source_documents, query_context
        )
        
        # Handle verification failure
        if not verification_result.overall_verified:
            return self._generate_verification_failed_response(
                query_context, verification_result, platform, start_time
            )
        
        # Format response for platform
        formatted_response = await self._format_for_platform(
            initial_response, platform, source_documents
        )
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(
            query_context, retrieval_results, verification_result
        )
        quality_level = self._determine_quality_level(quality_score)
        
        # Generate metadata
        generation_time = time.time() - start_time
        metadata = ResponseMetadata(
            query_context=query_context,
            retrieval_results=retrieval_results,
            verification_result=verification_result,
            generation_time=generation_time,
            quality_score=quality_score,
            platform=platform,
            format_type=self._get_format_type(platform),
            attribution_count=len(source_documents),
            source_count=len(retrieval_results),
            confidence_level=self._get_confidence_level(verification_result.confidence_score)
        )
        
        response = GeneratedResponse(
            content=formatted_response,
            metadata=metadata,
            sources=source_documents[:3],  # Top 3 sources for display
            quality_level=quality_level,
            is_safe=verification_result.overall_verified,
            recommendations=verification_result.recommendations
        )
        
        logger.info(f"🎯 Response generated: {quality_level.value} quality (time: {generation_time:.3f}s)")
        
        return response

    async def _generate_initial_response(self, 
                                       query_context: QueryContext,
                                       retrieval_results: List[RetrievalResult],
                                       platform: str) -> str:
        """Generate initial response using LLM"""
        # Prepare context from retrieval results
        context_parts = []
        for i, result in enumerate(retrieval_results[:5]):  # Top 5 results
            doc = result.document
            filename = doc.metadata.get('filename', 'unknown')
            content = doc.page_content[:800]  # Limit content length
            
            context_parts.append(f"Source {i+1} ({filename}): {content}")
        
        context = "\n\n".join(context_parts)
        
        # Get platform-specific prompt
        prompt_template = self.platform_prompts.get(platform, self.platform_prompts["universal"])
        
        # Fill in the prompt
        prompt = prompt_template.format(
            context=context,
            question=query_context.original_query,
            query_type=query_context.query_type.value,
            platform=platform
        )
        
        # Generate response with rate limit retry logic
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(self.llm.invoke, prompt)
                return response.content.strip()
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for rate limit errors
                if any(rate_limit_indicator in error_str for rate_limit_indicator in [
                    'rate limit', '429', 'too many requests', 'quota exceeded', 'rate exceeded'
                ]):
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"⚠️ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Rate limit exceeded after {max_retries} retries")
                        return "I'm experiencing high demand right now. Please wait a moment and try again."
                
                # For other errors, log and return generic message
                logger.error(f"❌ LLM generation failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return "I apologize, but I encountered an error generating a response. Please try again or contact HR directly."

    async def _format_for_platform(self, 
                                  response: str, 
                                  platform: str, 
                                  sources: List[Document]) -> str:
        """Format response for specific platform"""
        if platform == "slack":
            return await self._format_for_slack(response, sources)
        elif platform == "email":
            return await self._format_for_email(response, sources)
        elif platform == "web":
            return await self._format_for_web(response, sources)
        else:
            return await self._format_universal(response, sources)

    async def _format_for_slack(self, response: str, sources: List[Document]) -> str:
        """Format response for Slack with appropriate formatting"""
        # Remove HTML tags if present
        import re
        response = re.sub(r'<[^>]+>', '', response)
        
        # Add source references
        if sources:
            response += "\n\n📚 *Sources:*"
            for i, doc in enumerate(sources[:3]):
                filename = doc.metadata.get('filename', 'Document')
                response += f"\n• {filename}"
        
        return response

    async def _format_for_email(self, response: str, sources: List[Document]) -> str:
        """Format response for email with HTML formatting"""
        # Ensure proper HTML structure
        if not response.startswith('<'):
            response = f"<p>{response}</p>"
        
        # Add source references
        if sources:
            response += "\n\n<h3>Reference Documents:</h3>\n<ul>"
            for doc in sources[:3]:
                filename = doc.metadata.get('filename', 'Document')
                response += f"\n<li>{filename}</li>"
            response += "\n</ul>"
        
        return response

    async def _format_for_web(self, response: str, sources: List[Document]) -> str:
        """Format response for web interface with rich HTML"""
        # Add source references with proper HTML
        if sources:
            response += "\n\n<h3>Reference Documents:</h3>\n<ul>"
            for doc in sources[:3]:
                filename = doc.metadata.get('filename', 'Document')
                # Try to get URL from document metadata
                url = doc.metadata.get('url', '#')
                if url and url != '#':
                    response += f'\n<li><a href="{url}" target="_blank">{filename}</a></li>'
                else:
                    response += f"\n<li>{filename}</li>"
            response += "\n</ul>"
        
        return response

    async def _format_universal(self, response: str, sources: List[Document]) -> str:
        """Format response for universal/plain text"""
        # Add source references
        if sources:
            response += "\n\n**Sources:**"
            for i, doc in enumerate(sources[:3]):
                filename = doc.metadata.get('filename', 'Document')
                response += f"\n{i+1}. {filename}"
        
        return response

    def _generate_greeting_response(self, 
                                  query_context: QueryContext, 
                                  platform: str, 
                                  start_time: float) -> GeneratedResponse:
        """Generate response for greeting queries"""
        template = self.templates['greeting']
        content = template.format(platform=platform)
        
        metadata = ResponseMetadata(
            query_context=query_context,
            retrieval_results=[],
            verification_result=None,
            generation_time=time.time() - start_time,
            quality_score=0.9,
            platform=platform,
            format_type=self._get_format_type(platform),
            attribution_count=0,
            source_count=0,
            confidence_level="high"
        )
        
        return GeneratedResponse(
            content=content,
            metadata=metadata,
            sources=[],
            quality_level=ResponseQuality.GOOD,
            is_safe=True,
            recommendations=[]
        )

    def _generate_insufficient_info_response(self, 
                                           query_context: QueryContext, 
                                           platform: str, 
                                           start_time: float) -> GeneratedResponse:
        """Generate response when insufficient information is available"""
        template = self.templates['insufficient_info']
        content = template.format(question=query_context.original_query)
        
        metadata = ResponseMetadata(
            query_context=query_context,
            retrieval_results=[],
            verification_result=None,
            generation_time=time.time() - start_time,
            quality_score=0.6,
            platform=platform,
            format_type=self._get_format_type(platform),
            attribution_count=0,
            source_count=0,
            confidence_level="low"
        )
        
        return GeneratedResponse(
            content=content,
            metadata=metadata,
            sources=[],
            quality_level=ResponseQuality.ACCEPTABLE,
            is_safe=True,
            recommendations=["Query could be more specific", "Try alternative keywords"]
        )

    def _generate_verification_failed_response(self, 
                                             query_context: QueryContext,
                                             verification_result: VerificationResult,
                                             platform: str,
                                             start_time: float) -> GeneratedResponse:
        """Generate safe response when verification fails"""
        template = self.templates['verification_failed']
        content = template.format(question=query_context.original_query)
        
        metadata = ResponseMetadata(
            query_context=query_context,
            retrieval_results=[],
            verification_result=verification_result,
            generation_time=time.time() - start_time,
            quality_score=0.3,
            platform=platform,
            format_type=self._get_format_type(platform),
            attribution_count=0,
            source_count=0,
            confidence_level="low"
        )
        
        return GeneratedResponse(
            content=content,
            metadata=metadata,
            sources=[],
            quality_level=ResponseQuality.POOR,
            is_safe=True,
            recommendations=verification_result.recommendations
        )

    def _calculate_quality_score(self, 
                               query_context: QueryContext,
                               retrieval_results: List[RetrievalResult],
                               verification_result: VerificationResult) -> float:
        """Calculate comprehensive quality score"""
        score = 0.0
        
        # Query processing quality (25%)
        score += query_context.confidence_score * 0.25
        
        # Retrieval quality (25%)
        if retrieval_results:
            avg_retrieval_confidence = sum(r.confidence_score for r in retrieval_results) / len(retrieval_results)
            score += avg_retrieval_confidence * 0.25
        
        # Verification quality (50%)
        if verification_result:
            score += verification_result.confidence_score * 0.5
        else:
            score += 0.5 * 0.5  # Neutral score if no verification
        
        return min(score, 1.0)

    def _determine_quality_level(self, quality_score: float) -> ResponseQuality:
        """Determine quality level from score"""
        for level, threshold in self.quality_thresholds.items():
            if quality_score >= threshold:
                return level
        return ResponseQuality.POOR

    def _get_format_type(self, platform: str) -> ResponseFormat:
        """Get format type for platform"""
        format_map = {
            "web": ResponseFormat.HTML,
            "slack": ResponseFormat.SLACK,
            "email": ResponseFormat.EMAIL,
            "universal": ResponseFormat.PLAIN_TEXT
        }
        return format_map.get(platform, ResponseFormat.PLAIN_TEXT)

    def _get_confidence_level(self, confidence_score: float) -> str:
        """Get confidence level description"""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        else:
            return "low"

    # Platform-specific prompt templates
    def _get_web_prompt(self) -> str:
        return """You are the official CMU-Africa HR assistant. Provide comprehensive, well-organized information for faculty and staff.

STRICT ANTI-HALLUCINATION RULES:
✅ DO:
- ONLY use information explicitly provided in the context below
- Quote specific details directly from the context documents
- Provide step-by-step guidance ONLY when explicitly outlined in the context
- Reference specific policies and procedures ONLY if they appear in the context

❌ DON'T:
- NEVER invent, assume, or fabricate any information not explicitly stated in the context
- NEVER make up contact information, deadlines, amounts, or dates not in the documents
- NEVER create fictional policies or procedures

MANDATORY INFORMATION VALIDATION:
- If specific details aren't in the context, say "I don't have the specific information. Please check with the relevant department"
- If procedures aren't fully described, say "I don't have complete information about this process. Please consult the official documentation"
- If you cannot find relevant information, say "I don't have enough information to answer that question based on our current documentation"

Context: {context}
Question: {question}

Generate a comprehensive, professionally formatted HTML response. DO NOT include source references - they will be added automatically."""

    def _get_slack_prompt(self) -> str:
        return """You are the official CMU-Africa HR assistant. Provide clear, helpful information for faculty and staff.

STRICT ANTI-HALLUCINATION RULES:
- ONLY use information explicitly provided in the context
- NEVER invent contact details, deadlines, or amounts not in the context
- If information is missing, say "I don't have that specific information"

Context: {context}
Question: {question}

Generate a clear, professional response formatted for Slack. Keep it concise but comprehensive."""

    def _get_email_prompt(self) -> str:
        return """You are the official CMU-Africa HR assistant responding via email. Provide professional, comprehensive information.

STRICT ANTI-HALLUCINATION RULES:
- ONLY use information explicitly provided in the context
- NEVER fabricate contact information, deadlines, or policy details
- Always acknowledge when information is incomplete

Context: {context}
Question: {question}

Generate a professional HTML email response with proper structure and formatting."""

    def _get_universal_prompt(self) -> str:
        return """You are the official CMU-Africa HR assistant. Provide accurate, helpful information.

STRICT ANTI-HALLUCINATION RULES:
- ONLY use information from the provided context
- NEVER invent details not explicitly stated
- Be transparent about information limitations

Context: {context}
Question: {question}

Generate a well-structured, professional response with clear formatting."""

    # Response templates
    def _get_insufficient_info_template(self) -> str:
        return """I don't have enough information in our current documentation to fully answer your question about "{question}".

For accurate and complete information, please:
• Check the official HR documentation
• Contact the HR department directly  
• Consult with your supervisor or department head

I apologize that I cannot provide a more complete answer at this time."""

    def _get_verification_failed_template(self) -> str:
        return """I want to ensure I provide you with accurate information about "{question}", but I'm unable to verify all the details from our available documentation.

For reliable and verified information, please:
• Consult the official HR policies and procedures
• Contact the HR department directly
• Speak with your department administrator

This ensures you receive the most accurate and up-to-date information."""

    def _get_greeting_template(self) -> str:
        return """Hello! I'm your CMU-Africa HR Assistant. I'm here to help you with questions about HR policies, procedures, benefits, faculty information, and work-related matters at CMU-Africa.

How can I assist you today?"""

    def _get_person_not_found_template(self) -> str:
        return """I couldn't find specific information about that person in our current documentation.

For faculty and staff directory information, please:
• Check the official CMU-Africa directory
• Contact the HR department
• Use the university's internal directory system

Is there anything else I can help you with regarding HR policies or procedures?"""
