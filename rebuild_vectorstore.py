#!/usr/bin/env python3
# rebuild_vectorstore.py
"""
Vector Database Rebuild Script
==============================

This script rebuilds the FAISS vector database from scratch using 
the configured document sources.
"""

import os
import sys
import shutil
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def rebuild_vectorstore():
    """Rebuild the vector database from scratch"""
    print("🔧 Starting vector database rebuild...")
    
    # Import after setting up path
    from src.core.document_processor import DocumentProcessor
    
    store_path = "./src/store"
    sources_file = "./src/utils/sources.txt"
    
    try:
        # 1. Backup existing store (if it exists)
        if os.path.exists(store_path):
            backup_path = f"{store_path}_backup"
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(store_path, backup_path)
            print(f"📦 Backed up existing store to {backup_path}")
            
            # Remove old store
            shutil.rmtree(store_path)
            print("🗑️  Removed old vector store")
        
        # 2. Create fresh vector store directory
        os.makedirs(store_path, exist_ok=True)
        print(f"📁 Created fresh store directory: {store_path}")
        
        # 3. Initialize document processor
        print("🤖 Initializing document processor...")
        processor = DocumentProcessor()
        print(f"📄 Supported file formats: {', '.join(processor.supported_extensions)} (PDF, Text, CSV, HTML)")
        print(f"📊 Supported source types: {', '.join(processor.supported_types)} (Files and URLs)")
        print("✨ Multi-format processing: PDFs, text files, CSV data, and HTML content")
        print("🔄 Text chunking: 1000 chars/chunk with 200 char overlap")
        print("🎯 Optimized for semantic search and retrieval accuracy")
        print()
        print(f"📋 Loading sources from {sources_file}")
        sources = processor.load_sources_from_file(sources_file)
        
        if not sources:
            print("❌ ERROR: No sources found in sources.txt!")
            return False
            
        print(f"✅ Found {len(sources)} sources to process:")
        for i, source in enumerate(sources, 1):
            print(f"   {i}. {source['type']}: {source['path']}")
        
        # 5. Process documents and build vector store
        print("\n🔄 Processing documents and building vector store...")
        success = processor.ingest_and_save_sources(sources_file, store_path)
        
        if success:
            print("\n🎉 SUCCESS! Vector database rebuilt successfully!")
            print(f"📍 New vector store saved to: {store_path}")
            
            # Verify the new store
            if os.path.exists(f"{store_path}/index.faiss") and os.path.exists(f"{store_path}/index.pkl"):
                print("✅ Vector store files created successfully:")
                print(f"   - {store_path}/index.faiss")
                print(f"   - {store_path}/index.pkl")
            else:
                print("⚠️  WARNING: Vector store files not found!")
                return False
                
        else:
            print("❌ ERROR: Failed to rebuild vector database!")
            return False
            
        return True
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR during rebuild: {e}")
        return False

def verify_sources():
    """Verify that source documents exist and are readable"""
    print("\n🔍 Verifying source documents...")
    
    sources_file = "./src/utils/sources.txt"
    documents_dir = "./documents"
    
    if not os.path.exists(sources_file):
        print(f"❌ ERROR: Sources file not found: {sources_file}")
        return False
        
    if not os.path.exists(documents_dir):
        print(f"❌ ERROR: Documents directory not found: {documents_dir}")
        return False
    
    # Check documents directory
    pdf_files = list(Path(documents_dir).glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDF files in documents/:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Check sources.txt content
    try:
        with open(sources_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Count non-comment lines
        lines = [line.strip() for line in content.split('\n')]
        source_lines = [line for line in lines if line and not line.startswith('#')]
        
        print(f"📋 Found {len(source_lines)} configured sources in sources.txt")
        
        return len(source_lines) > 0
        
    except Exception as e:
        print(f"❌ ERROR reading sources.txt: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Vector Database Rebuild Tool")
    print("=" * 50)
    
    # Step 1: Verify sources
    if not verify_sources():
        print("\n❌ Source verification failed! Please check your documents and sources.txt")
        sys.exit(1)
    
    # Step 2: Rebuild vector store
    print("\n" + "=" * 50)
    success = rebuild_vectorstore()
    
    if success:
        print("\n🎯 REBUILD COMPLETE!")
        print("Your vector database has been successfully rebuilt.")
        print("You can now restart your bot with: python run_app.py")
    else:
        print("\n💥 REBUILD FAILED!")
        print("Please check the error messages above and try again.")
        sys.exit(1)