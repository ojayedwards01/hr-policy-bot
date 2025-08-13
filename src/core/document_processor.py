import logging
from typing import (
    Dict,
    List,
    Optional,
)
import csv
import os
from pathlib import Path

import fitz
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.schema import Document
# Removed unused imports to reduce dependencies
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from src.core.store_manager import VectorStoreManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# __________________________________________________________________________

sources_file = "./src/utils/sources.txt"
store_path = "./src/store"


class DocumentProcessor:
    """
    High-Performance Document Processor for RAG Systems
    ==================================================
    
    Optimized for:
    - Fast ingestion and processing of multi-format documents
    - Efficient chunking for semantic retrieval 
    - High-performance vector storage and retrieval
    - Scalable to 10k+ documents with sub-300ms query time
    - Smart content categorization and metadata enrichment
    """

    def __init__(self, chunk_size=None, chunk_overlap=None):
        # Load chunk settings from environment or use defaults
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", 200))
        
        self.supported_types = ["url", "file"]
        self.supported_extensions = [".pdf", ".txt", ".csv", ".html"]
        
        # Content categorization keywords
        self.content_categories = {
            "Policy": ["policy", "regulation", "rule", "guideline", "procedure", "compliance", "governance"],
            "HR": ["employee", "staff", "hiring", "recruitment", "onboarding", "offboarding", "benefits", "leave", "vacation"],
            "Academic": ["faculty", "research", "teaching", "tenure", "academic", "course", "semester", "grade"],
            "Administrative": ["administration", "budget", "finance", "procurement", "travel", "expense", "approval"],
            "Data": ["profile", "contact", "directory", "list", "database", "record", "information"],
            "General": []  # Default fallback
        }
        
        # Optimized chunking for fast retrieval
        # Environment-configured chunk size and overlap for better context
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]  # Hierarchical splitting
        )
        
        # DOCKER SIZE OPTIMIZATION: Use only FastEmbed to minimize image size
        # This must match what's used in bot.py for dimension compatibility
        from langchain_community.embeddings import FastEmbedEmbeddings
        self.embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-base-en-v1.5",  # 768 dimensions, matches bot.py
            cache_dir=os.getenv("MODEL_CACHE_DIR", "/tmp/model_cache")  # Use environment variable or default to /tmp
        )
        logger.info("✅ Using FastEmbedEmbeddings for document processing (Docker optimized)")

        self.vectorstore_manager = VectorStoreManager(self.embeddings)

    def categorize_content(self, text: str, filename: str = "") -> str:
        """Categorize content based on keywords and filename"""
        text_lower = (text + " " + filename).lower()
        
        for category, keywords in self.content_categories.items():
            if category == "General":
                continue
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "General"

    def extract_text_from_url(self, url: str) -> str:
        """Extract text from a URL with enhanced error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Try to find main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup
            text = main_content.get_text(separator="\n", strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return ""

    def extract_documents_from_csv(self, file_path: str) -> List[Dict[str, str]]:
        """Extract each row as a separate document entity"""
        try:
            documents = []
            filename = Path(file_path).name
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding, newline="") as csvfile:
                        # Try different delimiters in order of preference
                        delimiters = [',', ';', '\t', '|']
                        
                        # Read first few lines to detect delimiter
                        sample = csvfile.read(2048)
                        csvfile.seek(0)
                        
                        detected_delimiter = ','  # Default
                        max_fields = 0
                        
                        for delimiter in delimiters:
                            try:
                                test_reader = csv.DictReader(sample.splitlines(), delimiter=delimiter)
                                first_row = next(test_reader, None)
                                if first_row and len(first_row) > max_fields:
                                    max_fields = len(first_row)
                                    detected_delimiter = delimiter
                            except:
                                continue
                        
                        # Now process with the detected delimiter
                        csvfile.seek(0)
                        reader = csv.DictReader(csvfile, delimiter=detected_delimiter)
                        
                        # Process each row as a separate document
                        for i, row in enumerate(reader):
                            if i >= 500:  # Reasonable limit for performance
                                logger.info(f"Reached limit of 500 rows for {filename}")
                                break
                            
                            # Create a readable text representation of the row
                            row_content = []
                            primary_key = None
                            
                            # Try to identify the primary field (name, title, document name, etc.)
                            for key in ['name', 'title', 'document name', 'document_name', 'filename']:
                                if key.lower() in [k.lower() for k in row.keys()]:
                                    actual_key = next(k for k in row.keys() if k.lower() == key.lower())
                                    primary_key = actual_key
                                    break
                            
                            # If no obvious primary key, use the first column
                            if not primary_key and row:
                                primary_key = list(row.keys())[0]
                            
                            # Build the document content
                            for key, value in row.items():
                                if value and str(value).strip():
                                    clean_value = str(value).strip()
                                    # Limit very long values for readability
                                    if len(clean_value) > 500:
                                        clean_value = clean_value[:500] + "..."
                                    row_content.append(f"{key}: {clean_value}")
                            
                            if row_content:
                                # Create a title for this entity
                                entity_title = row.get(primary_key, f"Entity {i+1}") if primary_key else f"Entity {i+1}"
                                
                                # Build the full text content
                                text_content = f"Entity: {entity_title}\n"
                                text_content += f"Source: {filename}\n"
                                text_content += "\n".join(row_content)
                                
                                documents.append({
                                    "text": text_content,
                                    "entity_id": i,
                                    "entity_title": entity_title,
                                    "source_file": filename,
                                    "primary_key": primary_key,
                                    "row_data": row
                                })
                        
                        return documents
                        
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to process CSV with encoding {encoding}: {e}")
                    continue
            
            logger.error(f"Could not process CSV file {file_path} with any encoding/delimiter combination")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting documents from CSV {file_path}: {e}")
            return []

    def extract_text_from_csv(self, file_path: str) -> str:
        """Legacy method - maintained for compatibility"""
        try:
            text_content = []
            filename = Path(file_path).name
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding, newline="") as csvfile:
                        # Auto-detect delimiter
                        sample = csvfile.read(1024)
                        csvfile.seek(0)
                        delimiter = csv.Sniffer().sniff(sample).delimiter
                        
                        reader = csv.DictReader(csvfile, delimiter=delimiter)
                        
                        # Add header information
                        text_content.append(f"Dataset: {filename}")
                        text_content.append(f"Columns: {', '.join(reader.fieldnames)}")
                        text_content.append("")
                        
                        # Process rows with better formatting
                        for i, row in enumerate(reader):
                            if i >= 100:  # Limit for performance
                                text_content.append(f"... (showing first 100 rows of {filename})")
                                break
                                
                            row_text = []
                            for key, value in row.items():
                                if value and str(value).strip():
                                    row_text.append(f"{key}: {value}")
                            
                            if row_text:
                                text_content.append(f"Record {i+1}: " + " | ".join(row_text))
                        
                        return "\n".join(text_content)
                        
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Could not decode CSV file {file_path} with any encoding")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from CSV {file_path}: {e}")
            return ""

    def extract_text_from_txt(self, file_path: str) -> str:
        """Enhanced TXT extraction with encoding detection"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read()
                        # Clean up the content
                        lines = [line.strip() for line in content.split('\n')]
                        return '\n'.join(line for line in lines if line)
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Could not decode TXT file {file_path} with any encoding")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {e}")
            return ""

    def extract_text_from_html(self, file_path: str) -> str:
        """Enhanced HTML extraction with better content parsing"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read()
                    
                    soup = BeautifulSoup(content, "html.parser")
                    
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        element.decompose()
                    
                    # Extract title if available
                    title = soup.find('title')
                    title_text = title.get_text(strip=True) if title else ""
                    
                    # Try to find main content
                    main_content = (soup.find('main') or 
                                  soup.find('article') or 
                                  soup.find('div', class_='content') or 
                                  soup.find('div', id='content') or 
                                  soup.body or 
                                  soup)
                    
                    text = main_content.get_text(separator="\n", strip=True)
                    
                    # Clean up and format
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    formatted_content = []
                    
                    if title_text:
                        formatted_content.append(f"Title: {title_text}")
                        formatted_content.append("")
                    
                    formatted_content.extend(lines)
                    return '\n'.join(formatted_content)
                    
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Could not decode HTML file {file_path} with any encoding")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from HTML {file_path}: {e}")
            return ""

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Enhanced PDF extraction with better text processing"""
        try:
            text_content = []
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    # Clean up the text
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    cleaned_text = '\n'.join(lines)
                    text_content.append(cleaned_text)
            
            doc.close()
            
            if text_content:
                return '\n\n'.join(text_content)
            else:
                logger.warning(f"No text extracted from PDF {file_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""

    def load_sources_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """Load sources from configuration file"""
        sources = []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith(
                        "#"
                    ):  # Skip empty lines and comments
                        continue

                    parts = line.split(", ")
                    if len(parts) >= 2:
                        source_type = parts[0].strip()
                        path = ", ".join(parts[1:]).strip()  # Handle paths with commas

                        if source_type in self.supported_types:
                            sources.append({"type": source_type, "path": path})
                        else:
                            logger.info(
                                f"Warning: Unsupported source type '{source_type}' on line {line_num}"
                            )
                    else:
                        logger.info(
                            f"Warning: Invalid format on line {line_num}: {line}"
                        )
        except Exception as e:
            logger.error(f"Error loading sources from {file_path}: {e}")

        return sources

    def process_document(self, source: Dict[str, str]) -> List[Document]:
        """Process a single document source and return chunked documents"""
        try:
            source_type = source["type"]
            path = source["path"]
            filename = path.split("/")[-1] if "/" in path else path.split("\\")[-1]
            file_ext = filename.split(".")[-1].lower() if "." in filename else "unknown"

            # Special handling for CSV files - treat each row as a separate document
            if source_type == "file" and path.endswith(".csv"):
                csv_documents = self.extract_documents_from_csv(path)
                
                if not csv_documents:
                    logger.info(f"No data extracted from CSV {path}")
                    return []
                
                documents = []
                for csv_doc in csv_documents:
                    metadata = {
                        # Core identifiers
                        "source": path,
                        "filename": filename,
                        "source_type": source_type,
                        "file_type": file_ext,
                        
                        # CSV-specific metadata
                        "entity_id": csv_doc["entity_id"],
                        "entity_title": csv_doc["entity_title"],
                        "primary_key": csv_doc["primary_key"],
                        "row_data": csv_doc["row_data"],
                        
                        # Content classification
                        "content_category": self.categorize_content(csv_doc["text"], filename),
                        "document_type": "csv_entity",
                        
                        # Performance optimization
                        "embedding_ready": True
                    }
                    
                    doc = Document(page_content=csv_doc["text"], metadata=metadata)
                    documents.append(doc)
                
                logger.info(f"✅ {filename}: {len(documents)} entities extracted")
                return documents

            # Regular processing for non-CSV files
            text = ""
            if source_type == "url":
                text = self.extract_text_from_url(path)
            elif source_type == "file":
                if path.endswith(".pdf"):
                    text = self.extract_text_from_pdf(path)
                elif path.endswith(".txt"):
                    text = self.extract_text_from_txt(path)
                elif path.endswith(".html"):
                    text = self.extract_text_from_html(path)
                else:
                    logger.info(f"Unsupported file extension: {path}")
                    return []

            if text.strip():
                # Split text into optimal chunks for retrieval
                chunks = self.text_splitter.split_text(text)
                
                # Create document objects with enhanced metadata for filtering
                documents = []
                for i, chunk in enumerate(chunks):
                    metadata = {
                        # Core identifiers
                        "source": path,
                        "filename": filename,
                        "source_type": source_type,
                        "file_type": file_ext,
                        
                        # Chunking info
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                        
                        # Content classification for filtering
                        "content_category": self.categorize_content(chunk, filename),
                        "document_type": "chunked_text",
                        
                        # Performance optimization
                        "embedding_ready": True
                    }
                    
                    doc = Document(page_content=chunk, metadata=metadata)
                    documents.append(doc)
                
                logger.info(f"✅ {filename}: {len(chunks)} chunks (avg {len(text)//len(chunks) if chunks else 0} chars/chunk)")
                return documents
            else:
                logger.info(f"No text extracted from {path}")
                return []

        except Exception as e:
            logger.error(f"Error processing document {source}: {e}")
            return []

    def load_documents(self, sources: List[Dict[str, str]]) -> List[Document]:
        """Load and process documents from multiple sources with chunking"""
        documents = []

        # Use tqdm to show progress
        for source in tqdm(sources, desc="Processing sources", unit="source"):
            doc_chunks = self.process_document(source)  # Now returns List[Document]
            if doc_chunks:
                documents.extend(doc_chunks)  # Add all chunks to documents list

        logger.info(f"Total documents after chunking: {len(documents)}")
        return documents

    def ingest_and_save_sources(self, sources_file: str, store_path: str) -> bool:
        """
        Load documents from sources file, embed them into FAISS, and save the index to disk.
        Returns True on success.
        """
        try:
            sources = self.load_sources_from_file(sources_file)
            if not sources:
                logger.info("No sources found!")
                return False

            docs = self.load_documents(sources)
            if not docs:
                logger.info("No documents processed!")
                return False

            if not self.vectorstore_manager.create_vectorstore(docs):
                logger.info("Failed to build vectorstore!")
                return False

            self.vectorstore_manager.save_vectorstore(store_path)
            return True

        except Exception as e:
            logger.error(f"Error ingesting sources: {e}")
            return False


# initialize the DocumentProcessor
document_processor = DocumentProcessor()

# load sources from a configuration file and save content to the vector store
document_processor.ingest_and_save_sources(sources_file, store_path)
