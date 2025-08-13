"""
Enterprise Retrieval Engine
==========================

Advanced retrieval system with hybrid search, reranking,
and confidence scoring for enterprise-grade accuracy.

Author: Enterprise HR Bot Team
Version: 2.0.0
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .query_processor import QueryContext, QueryType

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with confidence and relevance metrics"""
    document: Document
    relevance_score: float
    confidence_score: float
    retrieval_method: str
    chunk_quality: float
    source_reliability: float
    context_match: float


class RetrievalStrategy(Enum):
    """Different retrieval strategies for various query types"""
    SEMANTIC_ONLY = "semantic"
    KEYWORD_ONLY = "keyword"
    HYBRID = "hybrid"
    PERSON_FOCUSED = "person_focused"
    POLICY_FOCUSED = "policy_focused"
    AFRICA_FOCUSED = "africa_focused"


class EnterpriseRetrievalEngine:
    """
    Enterprise-grade retrieval engine with multiple strategies,
    reranking, and confidence scoring.
    """
    
    def __init__(self, embeddings_model: HuggingFaceEmbeddings):
        self.embeddings = embeddings_model
        self.vectorstore = None
        self.bm25_retriever = None
        self.ensemble_retriever = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Retrieval configuration
        self.default_k = 8
        self.max_k = 12
        self.min_relevance_threshold = 0.3
        self.rerank_top_k = 20
        
        # Source reliability weights
        self.source_weights = {
            'hiring-process-2024': 1.0,
            'cmu-africa': 0.95,
            'africa': 0.9,
            'kigali': 0.9,
            'rwanda': 0.9,
            'travel': 0.85,
            'benefits': 0.8,
            'general': 0.7
        }
        
        # Query-specific retrieval parameters
        self.query_configs = {
            QueryType.PERSON_LOOKUP: {
                'strategy': RetrievalStrategy.PERSON_FOCUSED,
                'k': 6,
                'semantic_weight': 0.3,
                'keyword_weight': 0.7
            },
            QueryType.POLICY_INQUIRY: {
                'strategy': RetrievalStrategy.POLICY_FOCUSED,
                'k': 8,
                'semantic_weight': 0.6,
                'keyword_weight': 0.4
            },
            QueryType.PROCEDURE_INQUIRY: {
                'strategy': RetrievalStrategy.HYBRID,
                'k': 10,
                'semantic_weight': 0.5,
                'keyword_weight': 0.5
            },
            QueryType.TRAVEL_RELATED: {
                'strategy': RetrievalStrategy.HYBRID,
                'k': 8,
                'semantic_weight': 0.6,
                'keyword_weight': 0.4
            },
            QueryType.BENEFITS_RELATED: {
                'strategy': RetrievalStrategy.SEMANTIC_ONLY,
                'k': 8,
                'semantic_weight': 0.8,
                'keyword_weight': 0.2
            },
            QueryType.GENERAL_INFO: {
                'strategy': RetrievalStrategy.HYBRID,
                'k': 8,
                'semantic_weight': 0.5,
                'keyword_weight': 0.5
            }
        }
        
        logger.info("Enterprise Retrieval Engine initialized")

    def setup_retrievers(self, vectorstore_path: str, documents: Optional[List[Document]] = None) -> bool:
        """Initialize all retrieval systems"""
        try:
            # Load semantic retriever
            if not self._load_vectorstore(vectorstore_path):
                return False
            
            # Initialize keyword retriever if documents provided
            if documents:
                self._setup_keyword_retriever(documents)
                self._setup_ensemble_retriever()
            
            logger.info("All retrievers initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup retrievers: {e}")
            return False

    def _load_vectorstore(self, store_path: str) -> bool:
        """Load FAISS vectorstore"""
        try:
            import os
            if not os.path.exists(store_path):
                logger.error(f"Vectorstore path does not exist: {store_path}")
                logger.info(f"Current directory: {os.getcwd()}")
                logger.info(f"Directory contents: {os.listdir('.')}")
                return False
                
            logger.info(f"Attempting to load vectorstore from {store_path}")
            
            # Check what files are in the vectorstore directory
            if os.path.isdir(store_path):
                files = os.listdir(store_path)
                logger.info(f"Vectorstore directory contains: {files}")
                if not files:
                    logger.error(f"Vectorstore directory is empty: {store_path}")
                    return False
            
            self.vectorstore = FAISS.load_local(
                store_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            
            # Check document count
            doc_count = len(self.vectorstore.docstore._dict)
            logger.info(f"Vectorstore loaded from {store_path} with {doc_count} documents")
            
            # Validate vectorstore with a simple test query
            try:
                test_docs = self.vectorstore.similarity_search("test query", k=1)
                logger.info(f"Vectorstore test query returned {len(test_docs)} documents")
            except Exception as test_err:
                logger.warning(f"Vectorstore test query failed: {test_err}")
            
            return True
        except Exception as e:
            import traceback
            logger.error(f"Failed to load vectorstore: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _setup_keyword_retriever(self, documents: List[Document]):
        """Setup BM25 keyword retriever"""
        try:
            # Extract text content for BM25
            texts = [doc.page_content for doc in documents]
            self.bm25_retriever = BM25Retriever.from_texts(texts)
            self.bm25_retriever.k = self.default_k
            logger.info("BM25 keyword retriever initialized")
        except Exception as e:
            logger.error(f"Failed to setup BM25 retriever: {e}")
            self.bm25_retriever = None

    def _setup_ensemble_retriever(self):
        """Setup ensemble retriever combining semantic and keyword search"""
        if self.vectorstore and self.bm25_retriever:
            try:
                semantic_retriever = self.vectorstore.as_retriever()
                
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=[semantic_retriever, self.bm25_retriever],
                    weights=[0.6, 0.4]  # Default weights
                )
                logger.info("Ensemble retriever initialized")
            except Exception as e:
                logger.error(f"❌ Failed to setup ensemble retriever: {e}")
                self.ensemble_retriever = None

    async def retrieve_documents(self, context: QueryContext) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using query-specific strategy
        
        Args:
            context: Processed query context
            
        Returns:
            List[RetrievalResult]: Ranked and scored retrieval results
        """
        start_time = time.time()
        
        # Get retrieval configuration for query type
        config = self.query_configs.get(context.query_type, self.query_configs[QueryType.GENERAL_INFO])
        
        # Execute retrieval strategy
        raw_documents = await self._execute_retrieval_strategy(context, config)
        
        # Rerank and score results
        results = await self._rerank_and_score(raw_documents, context, config)
        
        # Apply confidence threshold filtering
        filtered_results = [r for r in results if r.confidence_score >= self.min_relevance_threshold]
        
        # Limit to top k results
        final_results = filtered_results[:config['k']]
        
        retrieval_time = time.time() - start_time
        logger.info(f"🔍 Retrieved {len(final_results)} documents in {retrieval_time:.3f}s using {config['strategy'].value}")
        
        return final_results

    async def _execute_retrieval_strategy(self, 
                                        context: QueryContext, 
                                        config: Dict[str, Any]) -> List[Document]:
        """Execute the appropriate retrieval strategy"""
        strategy = config['strategy']
        query = context.processed_query
        
        if strategy == RetrievalStrategy.SEMANTIC_ONLY:
            return await self._semantic_retrieval(query, config['k'] * 2)
        
        elif strategy == RetrievalStrategy.KEYWORD_ONLY:
            return await self._keyword_retrieval(query, config['k'] * 2)
        
        elif strategy == RetrievalStrategy.HYBRID:
            return await self._hybrid_retrieval(query, config, config['k'] * 2)
        
        elif strategy == RetrievalStrategy.PERSON_FOCUSED:
            return await self._person_focused_retrieval(context, config['k'] * 2)
        
        elif strategy == RetrievalStrategy.POLICY_FOCUSED:
            return await self._policy_focused_retrieval(context, config['k'] * 2)
        
        elif strategy == RetrievalStrategy.AFRICA_FOCUSED:
            return await self._africa_focused_retrieval(context, config['k'] * 2)
        
        else:
            return await self._hybrid_retrieval(query, config, config['k'] * 2)

    async def _semantic_retrieval(self, query: str, k: int) -> List[Document]:
        """Semantic similarity retrieval using embeddings"""
        if not self.vectorstore:
            logger.warning(f"Cannot perform semantic retrieval - vectorstore not initialized")
            return []
        
        start_time = time.time()
        logger.info(f"Starting semantic retrieval for query: '{query}' with k={k}")
        
        try:
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(
                self.executor,
                lambda: self.vectorstore.similarity_search(query, k=k)
            )
            
            duration = time.time() - start_time
            logger.info(f"Semantic retrieval returned {len(documents)} documents in {duration:.2f}s")
            
            # Log some basic info about retrieved documents
            if documents:
                for i, doc in enumerate(documents[:3]):  # Log first 3 docs
                    source = doc.metadata.get('source', 'unknown')
                    preview = doc.page_content[:50].replace('\n', ' ')
                    logger.debug(f"Doc {i+1}: {source} - '{preview}...'")
            else:
                logger.warning(f"No documents retrieved for query: '{query}'")
                
            return documents
            
        except Exception as e:
            import traceback
            logger.error(f"Error during semantic retrieval: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def _keyword_retrieval(self, query: str, k: int) -> List[Document]:
        """Keyword-based retrieval using BM25"""
        if not self.bm25_retriever:
            return []
        
        loop = asyncio.get_event_loop()
        documents = await loop.run_in_executor(
            self.executor,
            lambda: self.bm25_retriever.get_relevant_documents(query)[:k]
        )
        return documents

    async def _hybrid_retrieval(self, query: str, config: Dict[str, Any], k: int) -> List[Document]:
        """Hybrid retrieval combining semantic and keyword approaches"""
        if not self.ensemble_retriever:
            # Fallback to semantic only
            return await self._semantic_retrieval(query, k)
        
        # Update ensemble weights based on query type
        semantic_weight = config.get('semantic_weight', 0.5)
        keyword_weight = config.get('keyword_weight', 0.5)
        
        self.ensemble_retriever.weights = [semantic_weight, keyword_weight]
        
        loop = asyncio.get_event_loop()
        documents = await loop.run_in_executor(
            self.executor,
            lambda: self.ensemble_retriever.get_relevant_documents(query)[:k]
        )
        return documents

    async def _person_focused_retrieval(self, context: QueryContext, k: int) -> List[Document]:
        """Specialized retrieval for person lookup queries"""
        # Extract person names from context
        people = context.extracted_entities.get('people', [])
        
        if people:
            # Create person-focused query
            person_query = f"{context.processed_query} {' '.join(people)} faculty staff professor"
            return await self._hybrid_retrieval(person_query, 
                                              {'semantic_weight': 0.3, 'keyword_weight': 0.7}, k)
        
        return await self._keyword_retrieval(context.processed_query, k)

    async def _policy_focused_retrieval(self, context: QueryContext, k: int) -> List[Document]:
        """Specialized retrieval for policy-related queries"""
        # Enhance query with policy-specific terms
        enhanced_query = f"{context.processed_query} policy procedure guideline handbook manual"
        return await self._semantic_retrieval(enhanced_query, k)

    async def _africa_focused_retrieval(self, context: QueryContext, k: int) -> List[Document]:
        """Specialized retrieval focusing on CMU-Africa specific content"""
        # Enhance with Africa-specific terms
        enhanced_query = f"{context.processed_query} CMU-Africa Kigali Rwanda africa campus"
        return await self._hybrid_retrieval(enhanced_query, 
                                          {'semantic_weight': 0.6, 'keyword_weight': 0.4}, k)

    async def _rerank_and_score(self, 
                               documents: List[Document], 
                               context: QueryContext, 
                               config: Dict[str, Any]) -> List[RetrievalResult]:
        """Rerank documents and assign comprehensive scores"""
        if not documents:
            return []
        
        results = []
        
        for i, doc in enumerate(documents):
            # Calculate component scores
            relevance_score = await self._calculate_relevance_score(doc, context)
            confidence_score = await self._calculate_confidence_score(doc, context)
            chunk_quality = self._assess_chunk_quality(doc)
            source_reliability = self._get_source_reliability(doc)
            context_match = self._calculate_context_match(doc, context)
            
            # Combine scores
            final_score = (
                relevance_score * 0.3 +
                confidence_score * 0.25 +
                chunk_quality * 0.15 +
                source_reliability * 0.15 +
                context_match * 0.15
            )
            
            result = RetrievalResult(
                document=doc,
                relevance_score=relevance_score,
                confidence_score=final_score,
                retrieval_method=config['strategy'].value,
                chunk_quality=chunk_quality,
                source_reliability=source_reliability,
                context_match=context_match
            )
            
            results.append(result)
        
        # Sort by confidence score
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return results

    async def _calculate_relevance_score(self, doc: Document, context: QueryContext) -> float:
        """Calculate semantic relevance score"""
        if not self.vectorstore:
            return 0.5
        
        try:
            # Get similarity score from vectorstore
            loop = asyncio.get_event_loop()
            similar_docs = await loop.run_in_executor(
                self.executor,
                lambda: self.vectorstore.similarity_search_with_score(context.processed_query, k=1)
            )
            
            if similar_docs and similar_docs[0][0].page_content == doc.page_content:
                # Normalize FAISS distance to 0-1 score
                distance = similar_docs[0][1]
                return max(0, 1 - (distance / 2))  # Approximate normalization
            
            return 0.5
            
        except Exception as e:
            logger.warning(f"Could not calculate relevance score: {e}")
            return 0.5

    async def _calculate_confidence_score(self, doc: Document, context: QueryContext) -> float:
        """Calculate confidence score based on content analysis"""
        content = doc.page_content.lower()
        query_lower = context.processed_query.lower()
        
        score = 0.0
        
        # Keyword matching boost
        query_words = set(query_lower.split())
        content_words = set(content.split())
        overlap = len(query_words.intersection(content_words))
        score += min(overlap / len(query_words), 0.3) if query_words else 0
        
        # Priority keyword boost
        priority_matches = sum(1 for keyword in context.priority_keywords if keyword.lower() in content)
        score += min(priority_matches * 0.1, 0.2)
        
        # Entity matching boost
        for entity_type, entities in context.extracted_entities.items():
            if entities:
                entity_matches = sum(1 for entity in entities if entity.lower() in content)
                score += min(entity_matches * 0.05, 0.15)
        
        # Content quality indicators
        if any(indicator in content for indicator in ['policy', 'procedure', 'guideline', 'requirement']):
            score += 0.1
        
        # CMU-Africa specific boost
        if any(term in content for term in ['cmu-africa', 'kigali', 'rwanda', 'africa campus']):
            score += 0.1
        
        return min(score, 1.0)

    def _assess_chunk_quality(self, doc: Document) -> float:
        """Assess the quality of the document chunk"""
        content = doc.page_content
        
        # Length quality (not too short, not too long)
        length = len(content)
        if 100 <= length <= 1000:
            length_score = 1.0
        elif length < 100:
            length_score = length / 100
        else:
            length_score = max(0.5, 1000 / length)
        
        # Completeness indicators
        completeness_score = 0.5
        if content.endswith('.') or content.endswith('!') or content.endswith('?'):
            completeness_score += 0.2
        if not content.startswith(content.lower()):  # Starts with capital
            completeness_score += 0.1
        if not content.startswith(' '):  # Not a fragment
            completeness_score += 0.1
        
        # Structure indicators
        structure_score = 0.5
        if ':' in content or '•' in content or '1.' in content:
            structure_score += 0.2
        if '\n' in content:
            structure_score += 0.1
        
        return (length_score + completeness_score + structure_score) / 3

    def _get_source_reliability(self, doc: Document) -> float:
        """Get reliability score based on document source"""
        filename = doc.metadata.get('filename', '').lower()
        
        for pattern, weight in self.source_weights.items():
            if pattern in filename:
                return weight
        
        return self.source_weights['general']

    def _calculate_context_match(self, doc: Document, context: QueryContext) -> float:
        """Calculate how well document matches conversation context"""
        if not context.conversation_history:
            return 0.5
        
        # Extract context from recent conversation
        recent_topics = []
        for entry in context.conversation_history[-2:]:
            if 'question' in entry:
                recent_topics.extend(entry['question'].lower().split())
        
        if not recent_topics:
            return 0.5
        
        content_lower = doc.page_content.lower()
        matches = sum(1 for topic in recent_topics if topic in content_lower)
        
        return min(matches / len(recent_topics), 1.0) if recent_topics else 0.5

    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """Get comprehensive retrieval statistics"""
        stats = {
            'vectorstore_loaded': self.vectorstore is not None,
            'bm25_available': self.bm25_retriever is not None,
            'ensemble_available': self.ensemble_retriever is not None,
            'supported_strategies': [strategy.value for strategy in RetrievalStrategy],
            'default_k': self.default_k,
            'min_threshold': self.min_relevance_threshold
        }
        
        if self.vectorstore:
            try:
                stats['vectorstore_size'] = self.vectorstore.index.ntotal
            except:
                stats['vectorstore_size'] = 'unknown'
        
        return stats
