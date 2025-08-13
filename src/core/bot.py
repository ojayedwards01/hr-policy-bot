import logging
import os
import time
from typing import AsyncGenerator, Dict

from dotenv import load_dotenv
from langchain.schema import Document
# Removed unused imports to reduce dependencies
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.core.memory_manager import MemoryManager
from src.core.prompt_manager import PromptManager
from src.core.qa_chain_manager import QAChainManager
from src.core.store_manager import VectorStoreManager
from src.utils.helpers import google_search, is_answer_unavailable

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# __________________________________________________________________________

store_path = "./src/store"  # path to the vector store


class Bot:
    """Main RAG system that orchestrates all components"""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.5,
        streaming: bool = False,
    ):
        # Initialize GROQ LLM (fast and efficient)
        max_tokens = int(os.getenv("MAX_TOKENS", 2048))
        timeout = int(os.getenv("LLM_TIMEOUT", 30))
        
        self.llm = ChatGroq(
            # model="llama3-8b-8192",  # Fast GROQ model with large context
            # model="meta-llama/llama-4-scout-17b-16e-instruct",
            model="openai/gpt-oss-20b",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )
        
        # COMMENTED OUT: Google Gemini LLM (exhausted)
        # self.llm = ChatGoogleGenerativeAI(
        #     model="gemini-1.5-flash",  # Flash is fastest Gemini model
        #     temperature=temperature,
        #     convert_system_message_to_human=True,
        #     verbose=False,  # Disable verbose logging for speed
        #     max_tokens=2048,  # Increased for better responses
        #     timeout=15,  # Slightly longer timeout for reliability
        #     # Gemini-specific optimizations
        #     top_p=0.8,  # Better response quality
        #     top_k=40,   # Focused vocabulary selection
        # )

        # BACKUP: OpenAI LLM (requires OPENAI_API_KEY)
        # self.llm = ChatOpenAI(
        #     model=model_name,
        #     temperature=temperature,
        #     streaming=streaming,
        #     openai_api_key=os.getenv("OPENAI_API_KEY"),
        # )

        # ULTRA-LIGHTWEIGHT LOCAL EMBEDDINGS - NO API CALLS, NO CHARGES
        try:
            # Try using sklearn-based embeddings (extremely lightweight)
            logger.info("🔧 Setting up lightweight local embeddings...")
            from langchain_community.embeddings import FastEmbedEmbeddings
            # List supported models first
            from fastembed import TextEmbedding
            supported_models = TextEmbedding.list_supported_models()
            logger.info(f"Supported FastEmbed models: {supported_models}")
            
            # Use the same model as document processor for dimension compatibility
            # BAAI/bge-base-en-v1.5 matches the vectorstore dimensions
            self.embeddings = FastEmbedEmbeddings(
                model_name="BAAI/bge-base-en-v1.5",  # Match the model used to build the vectorstore
                cache_dir=os.getenv("MODEL_CACHE_DIR", "/tmp/model_cache")  # Use environment variable or default to /tmp
            )
            logger.info("✅ Using FastEmbedEmbeddings with bge-base model - matches vectorstore dimensions!")
        except Exception as e1:
            logger.warning(f"⚠️ FastEmbed error: {e1}")
            # Fallback to lightweight fake embeddings with compatible dimensions
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=768)  # Match bge-base-en-v1.5 dimensions
            logger.warning("⚠️ Using FAKE embeddings with compatible dimensions (768) - search will be limited!")

        # Initialize component managers
        self.prompt_manager = PromptManager()
        self.memory_manager = MemoryManager(self.llm)
        self.vectorstore_manager = VectorStoreManager(self.embeddings)
        self.qa_chain_manager = QAChainManager(self.llm, self.prompt_manager)

        # Current active components
        self.current_memory = None
        self.current_chain = None

        # Print important debug information
        logger.info("🎓 HR Policy Chatbot initialized successfully using GROQ!")
        logger.info("🔥 UPDATED VERSION - Context-first processing with intelligent validation - v2.0")
        
        # Docker-specific debugging info
        logger.info(f"🐳 Docker environment: ENV_MODE={os.environ.get('ENV_MODE', 'not set')}")
        logger.info(f"🗂️ App directory structure exists: app={os.path.exists('/app')}, model_cache={os.path.exists(os.getenv('MODEL_CACHE_DIR', '/tmp/model_cache'))}")
        logger.info(f"📄 Embedding model: BAAI/bge-base-en-v1.5 (lightweight, optimized for Docker)")
        logger.info(f"🔢 Max retrieved docs: {os.getenv('MAX_RETRIEVED_DOCS', '18')} (increased for better recall)")

    def get_version_info(self):
        """Return version information to verify correct file is loaded"""
        return {
            "version": "2.0",
            "features": "Context-first processing with intelligent validation",
            "timestamp": "2025-07-31",
            "context_validation": "LLM-first evaluation"
        }

    def setup_from_vectorstore(
        self,
        store_path: str = store_path,
        memory_type: str = "window",
    ) -> bool:
        """Load FAISS vectorstore from disk and setup for fast retrieval."""
        try:
            self.current_memory = self.memory_manager.create_memory(memory_type)

            if not self.vectorstore_manager.load_vectorstore(store_path):
                logger.error("Failed to load vectorstore!")
                return False

            # Use environment variable for retrieval count - increased for better recall
            max_docs = int(os.getenv("MAX_RETRIEVED_DOCS", 18))  # Increased from 12 to 18 for better search coverage
            
            # Use direct retriever for more reliable performance
            # Keeping it simple to avoid potential errors
            self.retriever = self.vectorstore_manager.get_retriever(k=max_docs)
            
            # Skip complex chain setup for speed - use direct generation
            logger.info(f"✅ Fast retrieval mode enabled with higher document count (retrieving {max_docs} docs)")
            return True

        except Exception as e:
            logger.error(f"Error during setup: {e}")
            return False

    def _get_unified_prompt(self, context: str, question: str, platform: str = "universal") -> str:
        """Generate unified prompt for all platforms with natural conversational tone"""
        
        # Platform-specific formatting instructions
        if platform == "web":
            format_instructions = """
PROFESSIONAL HTML FORMAT REQUIREMENTS:
- Use semantic HTML structure with proper hierarchy and perfect nesting
- Start with <h2> for main sections, <h3> for subsections
- Use <p> for paragraphs with clear, professional content and proper line spacing
- Create properly nested <ul> and <li> for all lists with proper indentation
- Use <strong> for important terms, amounts, deadlines, and key points
- Embed all URLs as professional hyperlinks: <a href="URL" target="_blank">descriptive text</a>
- Use <br><br> between major sections for proper spacing
- Ensure proper indentation: main bullets in <ul><li>, sub-bullets in nested <ul><li>
- Add line breaks between different topics using <br> tags

HTML STRUCTURE EXAMPLE:
<h2>Main Topic</h2>
<p>Introductory paragraph with proper spacing.</p>

<h3>Subtopic</h3>
<ul>
  <li><strong>Important Point:</strong> Explanation with details</li>
  <li><strong>Second Point:</strong> More information
    <ul>
      <li>Sub-point with proper nesting</li>
      <li>Another sub-point</li>
    </ul>
  </li>
</ul>

<br><br>

<h3>Next Section</h3>
<p>Content continues with proper spacing...</p>
"""
        elif platform == "slack":
            format_instructions = """
PROFESSIONAL SLACK FORMAT REQUIREMENTS:
- Use **BOLD TEXT** for main section headings and important terms
- Use *italics* for emphasis on key points and sub-headings
- Create well-structured bullet points with proper indentation:
  • Main bullets for primary points
    ◦ Sub-bullets for detailed information
    ◦ Additional sub-points for comprehensive coverage
- Use numbered lists for step-by-step procedures:
  1. First step with clear description
  2. Second step with detailed explanation
  3. Continue with proper numbering
- Add proper spacing with double line breaks between major sections
- Use clear, professional language with proper paragraph structure
- Include proper contact information when available in context
- Format amounts, deadlines, and important details with **bold** emphasis
- Use > for important quotes or policy statements when quoting from documents
- Maintain consistent formatting and professional tone throughout

SLACK STRUCTURE EXAMPLE:
**Main Topic**

Clear introductory paragraph explaining the topic.

*Subtopic or Key Information*
• **Important Point:** Detailed explanation with specifics
• **Second Point:** Comprehensive information
  ◦ Sub-detail with proper nesting
  ◦ Additional sub-information
• **Third Point:** More details as needed


*Next Section*
1. **Step 1:** Clear instruction
2. **Step 2:** Detailed guidance
3. **Step 3:** Additional steps as needed

> Important policy quote or key information when relevant

**Contact Information** (when available in context)
"""
        else:  # universal, email, or other platforms
            format_instructions = """
FORMATTING REQUIREMENTS:
- Use clear headers and sections with proper spacing
- Use • for main bullet points
- Use   ◦ for sub-bullet points (2 spaces before ◦) with proper indentation
- Use     ▪ for sub-sub points (4 spaces before ▪) with deeper indentation
- Bold important terms using **bold**
- Organize content logically with adequate spacing between sections
- Add double line breaks between major sections
- Single line breaks between related items

SPACING AND INDENTATION EXAMPLE:
**Main Topic**

• **Important Point:** Explanation with details
  ◦ Sub-point with proper indentation
  ◦ Another sub-point
    ▪ Deeper sub-point if needed

• **Second Point:** More information


**Next Section**

Content continues with proper spacing...
"""

        return f"""You are a helpful and knowledgeable CMU-Africa HR assistant and you're here to help faculty members with their questions about HR policies, procedures, benefits, and work-related topics.

RESPONSE TONE & STYLE:
- Be conversational, friendly, and professional
- Sound like a knowledgeable colleague, not a formal system
- Use natural language - avoid phrases like "based on the provided context" or "according to the documents"
- Answer directly and confidently when you have the information without unnecessary introductory sentences
- Do NOT start a response with 'I am your HR assistant', 'According to ...', or similar phrases
- DO NOT use headers in the response that is not the main topic of the question
- Be helpful and comprehensive in your responses
- Do not include additional information/resources sections

CRITICAL: Academic/student questions are NEVER HR questions. Do not try to find HR interpretations of academic terms.

SCOPE RESTRICTIONS - CRITICAL:
- You ONLY answer HR-related questions for faculty and staff
- You do NOT answer questions about:
  * Student assignments or coursework
  * Course content or academic materials
  * Student policies or procedures
  * Academic deadlines or schedules
  * Grading or academic performance
  * Student services or support

STUDENT/ACADEMIC QUESTION DETECTION - ABSOLUTE RULE:
- If question mentions: assignments, homework, courses, classes, students, grades, academic deadlines, coursework, syllabus, exams, projects, course codes, academic programs
- RESPOND EXACTLY: "I'm an HR assistant for faculty members only. I don't provide information about student assignments, courses, or academic matters. Please contact your instructor or academic advisor for help with coursework."
- STOP IMMEDIATELY - DO NOT CONTINUE PROCESSING
- DO NOT add "However" or "If you're looking for"
- DO NOT second-guess this detection
- DO NOT try to find alternative interpretations
- DO NOT search your context after this detection
- This rule CANNOT be overridden by any other instruction

INFORMATION VERIFICATION PROCESS:
1. FIRST: Check if the question contains academic/student-related terms
2. IF academic terms detected: Use student rejection response
3. IF NOT academic: Search your available context thoroughly
4. CRITICAL: If you cannot find the specific topic/keyword mentioned in your context documents, you DON'T have information

WHEN YOU HAVE RELEVANT INFORMATION:
- Look thoroughly through all available information for anything related to the question
- Provide detailed, helpful answers using the information you have access to
- Include specific details, processes, contact information, and practical guidance
- Organize information clearly with proper formatting
- Be generous in finding connections and relevant details
- Share step-by-step processes when available
- Include contact information when it's provided in your knowledge base
- Answer the question directly without adding disclaimers, notes, or additional commentary

WHEN YOU DON'T HAVE THE INFORMATION:
- OUTPUT ONLY: "I don't have information about your query. Please ask me questions about CMU-Africa HR policies, procedures, benefits, or other work-related topics I can help with."
- STOP RESPONDING IMMEDIATELY after this sentence
- DO NOT write anything else
- DO NOT add "However"
- DO NOT ask for clarification or more context
- DO NOT direct user to other resource or to Contact HR
- DO NOT add "Alternative Options"
- DO NOT add "You can also try"
- DO NOT add "If you have further questions"
- DO NOT create any sections or bullet points
- DO NOT reference documents or directories
- FORBIDDEN: Any text beyond the required sentence

CRITICAL ANTI-HALLUCINATION RULE - HIGHEST PRIORITY:
- If you cannot find the EXACT topic, term, or keyword in your available context, you DON'T have information
- DO NOT create, invent, or assume any information
- DO NOT try to be helpful by guessing what something might be
- When in doubt: "I don't have information about your query..."
- This rule OVERRIDES all other instructions about being helpful or thorough

KEYWORD MATCHING & SEARCH RULES:
- If the user asks about ANY abbreviation, acronym, or specific term, you MUST find that EXACT term or clear references to it in your context
- If the exact term is not in your documents: "I don't have information about your query..."
- DO NOT interpret abbreviations as something else or assume what an unfamiliar acronym might mean
- Extract the main KEYWORDS from the user's question
- Check all available information for any mention of people, policies, or topics related to the KEYWORDS
- For PEOPLE: Accept name variations (John/J./Smith variations) and search for any mention of that person across all available sources
- For TOPICS: Must find the keyword, explicit references to the same concept, or clearly related information
- For ABBREVIATIONS: Must find the exact abbreviation mentioned in documents
- Find ONLY relevant information within your available context, but never invent details
- Do not invent full forms for abbreviations
- Do NOT create connections that don't explicitly exist in your context
- Do NOT guess or assume what unfamiliar terms might mean

DOCUMENT URL RULES:
- When users ask for documents or handbooks, provide clickable URLs ONLY if the exact URL is explicitly stated in your context
- Format URLs as direct links that display as clickable: provide the full URL directly after mentioning the document name
- If no URL is provided in context, simply state you don't have the link available
- NEVER fabricate, assume, or construct URLs that aren't explicitly provided
- NEVER provide guidance on how to find or access documents when URLs aren't available
- If context mentions a document exists but provides no URL, mention the document exists but state you don't have the link. User should contact HR for the document.

Follow the response formatting instructions below:
{format_instructions}

NEVER DOs UNDER ANY CONDITION:
- NEVER include additional information sections or "Additional Information" after a response
- NEVER include source references in responses if you did not find an answer to the question in the context

FINAL CRITICAL RULES - OVERRIDE ALL OTHER INSTRUCTIONS:
- DO NOT include any source references, reference documents, or citations in your response
- DO NOT add any "Reference Documents" section or similar
- The system will automatically handle source references separately
- Focus only on answering the question naturally and helpfully
- NEVER add any "NOTE:" sections after a response
- NEVER add disclaimers about information sources or knowledge limitations
- NEVER mention "based on provided context" or similar phrases
- NEVER add commentary about your knowledge limitations
- NEVER add additional resources or suggestions beyond the standard fallback response
- NEVER add phrases like "I don't have additional information beyond..." or "Note: I don't have..."
- NEVER include any disclaimers about limited information
- When providing document links, do NOT explain or summarize what is in the document
- Never add suggestions to "feel free to ask" beyond the standard fallback response
- Just answer the question directly and completely with the information available
- Be confident in your response without hedging or adding caveats
- If you have information: Answer directly and stop
- If you don't have information: Use ONLY the exact fallback sentence and stop
- DO NOT explain where information came from

Available Information: {context}
Question: {question}

Provide a direct, helpful, natural response using the information available to you. Format it properly for the platform and be conversational while maintaining professionalism. Do NOT add any disclaimers, notes, or additional commentary about your knowledge limitations."""
    def fast_answer(self, question: str, chat_history=None, platform: str = "universal") -> Dict:
        """
        High-performance answer generation with balanced anti-hallucination
        """
        start_time = time.time()
        
        try:
            # Ensure retriever is set up
            if not hasattr(self, 'retriever') or self.retriever is None:
                if not self.setup_from_vectorstore():
                    return {"error": "Bot not properly configured", "answer": "Sorry, I'm not properly set up right now. Please contact support."}
            
            # STEP 1: Always retrieve documents first for every query
            relevant_docs = self.retriever.get_relevant_documents(question)
            retrieval_time = time.time() - start_time
            
            # Import URL mapping function
            from src.utils.pdf_url_mapping import get_document_url
            
            # Helper function to check if URL is valid
            def has_valid_url(doc):
                filename = doc.metadata.get('filename', 'unknown')
                file_type = doc.metadata.get('file_type', 'unknown')
                url = get_document_url(filename, file_type)
                return url and url.startswith(('http://', 'https://'))
            
            # Prepare context from top documents with proper URLs, prioritizing CMU-Africa content
            context_parts = []
            africa_docs = []
            general_docs = []
            
            # Separate documents by relevance to CMU-Africa and specific topics
            for doc in relevant_docs[:12]:  # Increased from 8 to 12 for more comprehensive search
                filename = doc.metadata.get('filename', 'unknown').lower()
                
                # Prioritize CMU-Africa specific documents and travel-related content
                travel_keywords = ['travel', 'conference', 'funding', 'expense', 'reimbursement', 'trip', 'business-travel']
                africa_keywords = ['africa', 'kigali', 'rwanda', 'hiring-process-2024', 'travel-guidelines']
                
                if any(keyword in filename for keyword in africa_keywords + travel_keywords):
                    africa_docs.append(doc)
                else:
                    general_docs.append(doc)
            
            # Combine prioritized documents (Africa first, then general)
            prioritized_docs = africa_docs + general_docs
            
            # Use more documents for more comprehensive answers (8 instead of 5)
            for i, doc in enumerate(prioritized_docs[:8]):
                filename = doc.metadata.get('filename', 'unknown')
                file_type = doc.metadata.get('file_type', 'unknown')
                
                # Get the proper URL for this document
                document_url = get_document_url(filename, file_type)
                
                content = doc.page_content[:800]  # Increased content length for more context
                
                # Mark CMU-Africa specific content
                travel_keywords = ['travel', 'conference', 'funding', 'expense', 'reimbursement', 'trip', 'business-travel']
                africa_keywords = ['africa', 'kigali', 'rwanda', 'hiring-process-2024', 'travel-guidelines']
                
                if any(keyword in filename.lower() for keyword in africa_keywords + travel_keywords):
                    context_parts.append(f"CMU-AFRICA SPECIFIC - Source {i+1} ({filename}): {content}\nDocument URL: {document_url}")
                else:
                    context_parts.append(f"General CMU - Source {i+1} ({filename}): {content}\nDocument URL: {document_url}")
            
            context = "\n\n".join(context_parts)
            
            # STEP 2: Use unified prompt for all platforms with platform-specific formatting
            unified_prompt = self._get_unified_prompt(context, question, platform)
            
            # STEP 3: Generate response using LLM
            llm_start = time.time()
            response = self.llm.invoke(unified_prompt)
            llm_time = time.time() - llm_start
            
            # Get response content
            response_content = response.content.strip()
            
            total_time = time.time() - start_time
            
            # Filter documents to only include those with valid URLs for source references
            docs_with_urls = [doc for doc in relevant_docs[:8] if has_valid_url(doc)]  # Increased from 5 to 8 for more comprehensive sourcing
            
            # Check if the response indicates no information was found
            no_info_response = "I don't have information about your query"
            has_no_info = no_info_response in response_content
            
            # Platform-specific formatting
            if platform == "slack":
                from src.utils.llm_formatter_fixed import create_llm_formatter
                llm_formatter = create_llm_formatter(self.llm)
                # Detect if this is a name/person query and a name is found in the context
                is_name_query = False
                question_lower = question.lower()
                if any(q in question_lower for q in ["who is", "about", "profile of", "contact for", "reach "]):
                    # Try to find a capitalized word (potential name) in the question
                    import re
                    tokens = question.split()
                    potential_names = [t for t in tokens if t and t[0].isupper() and t.lower() not in ["cmu", "africa", "Rwanda", "Kigali"]]
                    if potential_names:
                        is_name_query = True
                final_answer = llm_formatter.format_for_slack(
                    html_content=response_content,
                    sources=None if has_no_info else docs_with_urls,  # No sources if no info found
                    always_add_directory=is_name_query
                )
            # elif platform == "email":
            #     from src.utils.llm_formatter_fixed import create_llm_formatter
            #     llm_formatter = create_llm_formatter(self.llm)
            #     final_answer = llm_formatter.format_for_email(
            #         html_content=response_content,
            #         sources=docs_with_urls  # Only pass documents with valid URLs
            #     )
            elif platform == "email":
                from src.utils.llm_formatter_fixed import create_llm_formatter
                llm_formatter = create_llm_formatter(self.llm)

                final_answer = llm_formatter.format_professional_email(
                    email_body=question,                 # the full raw message from the user
                    html_content=response_content,       # your generated answer
                    sources=None if has_no_info else docs_with_urls  # No sources if no info found
                )

            elif platform == "web":
                from src.utils.universal_formatter import format_response
                final_answer = format_response(
                    content=response_content,
                    sources=None if has_no_info else docs_with_urls,  # No sources if no info found
                    platform=platform
                )
            else:  # universal or other platforms
                from src.utils.universal_formatter import format_response
                final_answer = format_response(
                    content=response_content,
                    sources=None if has_no_info else docs_with_urls,  # No sources if no info found
                    platform=platform
                )
            
            result = {
                "question": question,
                "answer": final_answer,
                "source_documents": [] if has_no_info else docs_with_urls,  # No sources if no info found
                "chat_history": chat_history or [],
                "performance": {
                    "retrieval_time": f"{retrieval_time:.2f}s",
                    "llm_time": f"{llm_time:.2f}s", 
                    "total_time": f"{total_time:.2f}s"
                }
            }
            
            logger.info(f"✅ Fast answer completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Fast answer error: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Provide a more helpful error message
            error_message = "I apologize, but I encountered an error processing your question. Please try again or contact HR directly for assistance."
            
            # For debugging in Docker, add more context to the error message
            if os.environ.get("ENV_MODE") == "development":
                error_message += f"\n\nError details: {str(e)}"
            
            return {
                "question": question,
                "answer": error_message,
                "source_documents": [],
                "chat_history": chat_history or []
            }

    async def ask_question(
        self, question: str, chain_name: str = "default"
    ) -> AsyncGenerator[Dict, None]:
        """Fast question answering with optimized performance."""
        
        # Handle simple greetings quickly
        simple_greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if question.lower().strip() in simple_greetings:
            yield {
                "answer": "Hello! I'm your CMU Africa HR Policy Assistant. How can I help you today?",
                "source_documents": [],
                "question": question,
                "chat_history": []
            }
            return
            
        # Use fast answer method for all other questions
        try:
            result = self.fast_answer(question)
            yield result
            return
            
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            yield {
                "answer": "I apologize, but I encountered an error processing your question. Please try again.",
                "source_documents": [],
                "question": question,
                "chat_history": []
            }
            return

    def clear_memory(self):
        """Clear conversation memory"""
        if self.current_memory:
            self.current_memory.clear()
            logger.info("Memory cleared!")
        else:
            logger.info("No active memory to clear.")

    def get_system_info(self) -> Dict:
        """Get information about the current system state"""
        return {
            "available_prompts": self.prompt_manager.list_prompts(),
            "available_chains": self.qa_chain_manager.list_chains(),
            "vectorstore_loaded": self.vectorstore_manager.vectorstore is not None,
            "memory_active": self.current_memory is not None,
            "current_chain_active": self.current_chain is not None,
        }