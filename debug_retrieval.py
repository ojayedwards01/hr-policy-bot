#!/usr/bin/env python3
"""
Debug script for HR Bot Docker container retrieval issues
This script tests the retrieval functionality directly and provides detailed diagnostics

Usage:
- Inside Docker container: python debug_retrieval.py
- Or using the helper scripts: debug-retrieval-docker.bat (Windows) or debug-retrieval-docker.sh (Linux/Mac)
"""

import os
import sys
import time
import logging
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fastembed():
    """Test if FastEmbed is working properly"""
    try:
        from fastembed import TextEmbedding
        logger.info("✅ FastEmbed imported successfully")
        
        # List available models
        models = TextEmbedding.list_supported_models()
        logger.info(f"📋 Available models: {models}")
        
        # Test the model we're using
        logger.info("🔄 Testing BAAI/bge-small-en-v1.5...")
        model = TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir="/app/model_cache")
        
        # Test embedding generation
        test_text = "This is a test embedding"
        embeddings = model.embed([test_text])
        logger.info(f"✅ Generated embedding with shape: {embeddings[0].shape}")
        
        return True
    except Exception as e:
        logger.error(f"❌ FastEmbed error: {e}")
        return False

def test_langchain_embeddings():
    """Test if LangChain embeddings are working"""
    try:
        from langchain_community.embeddings import FastEmbedEmbeddings
        logger.info("✅ LangChain FastEmbedEmbeddings imported successfully")
        
        # Initialize embeddings
        embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir="/app/model_cache"
        )
        
        # Test embedding generation
        test_text = "This is a test embedding"
        result = embeddings.embed_query(test_text)
        logger.info(f"✅ Generated LangChain embedding with length: {len(result)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ LangChain FastEmbedEmbeddings error: {e}")
        
        # Try HuggingFaceEmbeddings as fallback
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.info("🔄 Testing HuggingFaceEmbeddings fallback...")
            
            hf_embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            result = hf_embeddings.embed_query(test_text)
            logger.info(f"✅ Generated HuggingFace embedding with length: {len(result)}")
            
            return True
        except Exception as e2:
            logger.error(f"❌ HuggingFace embeddings error: {e2}")
            return False

def test_vectorstore():
    """Test loading the vector store"""
    try:
        from langchain_community.embeddings import FastEmbedEmbeddings
        from langchain_community.vectorstores import FAISS
        
        # Initialize embeddings
        embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir="/app/model_cache"
        )
        
        # Check if vectorstore exists
        store_path = "./vectorstore"
        
        if os.path.exists(store_path):
            logger.info(f"✅ Vector store directory exists: {store_path}")
            
            # Try loading the vectorstore
            try:
                logger.info("🔄 Loading vector store...")
                vectorstore = FAISS.load_local(store_path, embeddings)
                logger.info(f"✅ Vector store loaded successfully with {len(vectorstore.docstore._dict)} documents")
                
                # Try a simple similarity search
                query = "benefits"
                docs = vectorstore.similarity_search(query, k=3)
                logger.info(f"✅ Similarity search successful, found {len(docs)} documents")
                for i, doc in enumerate(docs):
                    logger.info(f"  Document {i+1}: {doc.page_content[:100]}...")
                
                return True
            except Exception as e:
                logger.error(f"❌ Vector store loading error: {e}")
                return False
        else:
            logger.error(f"❌ Vector store directory does not exist: {store_path}")
            return False
    except Exception as e:
        logger.error(f"❌ General error in test_vectorstore: {e}")
        return False

def test_query_performance():
    """Test query performance with different parameters"""
    try:
        from langchain_community.embeddings import FastEmbedEmbeddings
        from langchain_community.vectorstores import FAISS
        
        # Initialize embeddings
        embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir="/app/model_cache"
        )
        
        # Load vectorstore
        store_path = "./vectorstore"
        vectorstore = FAISS.load_local(store_path, embeddings)
        
        # Test queries
        test_queries = [
            "What are the benefits for employees?",
            "How do I change my name in the system?",
            "What is the onboarding process?",
            "How do I request leave?",
            "What documents are required for new employees?"
        ]
        
        logger.info("Running performance tests with different k values...")
        for k in [5, 10, 15, 20]:
            total_time = 0
            total_docs = 0
            
            logger.info(f"\nTesting with k={k}:")
            for query in test_queries:
                start_time = time.time()
                try:
                    docs = vectorstore.similarity_search(query, k=k)
                    duration = time.time() - start_time
                    total_time += duration
                    total_docs += len(docs)
                    
                    logger.info(f"  Query: '{query}' - Found {len(docs)} docs in {duration:.2f}s")
                    
                    # Show first result preview
                    if docs:
                        source = docs[0].metadata.get('source', 'unknown')
                        preview = docs[0].page_content[:100].replace('\n', ' ')
                        logger.info(f"    First result: {source} - '{preview}...'")
                except Exception as e:
                    logger.error(f"  Query '{query}' failed: {e}")
            
            avg_time = total_time / len(test_queries)
            logger.info(f"Average for k={k}: {avg_time:.2f}s per query, {total_docs/len(test_queries):.1f} docs per query")
        
        return True
    except Exception as e:
        logger.error(f"❌ Performance test error: {e}")
        logger.error(traceback.format_exc())
        return False

def check_environment():
    """Check the environment for potential issues"""
    try:
        # Check if we're running in Docker
        in_docker = os.path.exists('/.dockerenv')
        logger.info(f"Running in Docker: {in_docker}")
        
        # Check Python version
        logger.info(f"Python version: {sys.version}")
        
        # Check for key directories
        dirs_to_check = ['./vectorstore', './documents', './src', './model_cache']
        for dir_path in dirs_to_check:
            exists = os.path.exists(dir_path)
            if exists:
                file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                logger.info(f"Directory '{dir_path}': ✅ Exists with {file_count} files")
            else:
                logger.warning(f"Directory '{dir_path}': ❌ Does not exist")
        
        # Check memory usage
        try:
            import psutil
            vm = psutil.virtual_memory()
            logger.info(f"Memory: {vm.available/1024/1024:.1f}MB available out of {vm.total/1024/1024:.1f}MB total")
        except ImportError:
            logger.info("psutil not available, skipping memory check")
        
        return True
    except Exception as e:
        logger.error(f"❌ Environment check error: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== HR Bot Retrieval Debugging Tool ===")
    
    # First check the environment
    logger.info("\n=== Environment Check ===")
    env_ok = check_environment()
    
    logger.info("\n=== Embedding Tests ===")
    logger.info("\n1. Testing FastEmbed...")
    fastembed_ok = test_fastembed()
    
    logger.info("\n2. Testing LangChain embeddings...")
    langchain_ok = test_langchain_embeddings()
    
    logger.info("\n=== Vector Store Tests ===")
    logger.info("\n3. Testing vector store...")
    vectorstore_ok = test_vectorstore()
    
    # Performance testing if vector store is available
    if vectorstore_ok:
        logger.info("\n=== Performance Tests ===")
        logger.info("\n4. Testing query performance...")
        performance_ok = test_query_performance()
    else:
        performance_ok = False
    
    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Environment: {'✅ OK' if env_ok else '⚠️ WARNINGS'}")
    logger.info(f"FastEmbed: {'✅ OK' if fastembed_ok else '❌ FAILED'}")
    logger.info(f"LangChain: {'✅ OK' if langchain_ok else '❌ FAILED'}")
    logger.info(f"VectorStore: {'✅ OK' if vectorstore_ok else '❌ FAILED'}")
    logger.info(f"Performance: {'✅ OK' if performance_ok else '❌ FAILED' if vectorstore_ok else '⚠️ SKIPPED'}")
    
    if fastembed_ok and langchain_ok and vectorstore_ok:
        logger.info("\n✅ All tests passed! Retrieval system should be working.")
    else:
        logger.info("\n❌ Some tests failed. See logs above for details.")
