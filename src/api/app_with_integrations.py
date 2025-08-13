import os
import sys
import json
import logging
import asyncio
import concurrent.futures
from pathlib import Path
from threading import Thread
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Enable Flask request logging
app.logger.setLevel(logging.INFO)

# Add health endpoint for Docker container health checks
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for Docker healthchecks"""
    return jsonify({
        "status": "ok", 
        "message": "HR Bot server is running"
    }), 200

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"🌐 {request.method} {request.path} - User Agent: {request.headers.get('User-Agent', 'Unknown')}")
    if request.is_json:
        logger.info(f"📄 Request body: {request.get_json()}")

@app.after_request  
def log_response_info(response):
    logger.info(f"📤 Response: {response.status_code} - {response.status}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"💥 UNHANDLED EXCEPTION: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Global variables for integrations
faq_bot = None
slack_integration = None
email_integration = None
slack_processor = None  # Enterprise-grade message processor
initialization_status = {"status": "initializing", "message": "Starting up..."}

def initialize_bot():
    """Initialize the bot and integrations with enterprise-grade architecture"""
    global faq_bot, slack_integration, email_integration, slack_processor, initialization_status
    
    try:
        logger.info("🚀 Starting enterprise bot initialization...")
        initialization_status = {"status": "initializing", "message": "Initializing enterprise bot..."}
        
        # Import here to avoid circular imports
        from src.core.bot import Bot
        from src.integrations.slack_integration import SlackIntegration
        from src.integrations.email_integration import EmailIntegration
        from src.integrations.enterprise_slack_processor import EnterpriseSlackProcessor
        
        # Initialize bot
        faq_bot = Bot()
        faq_bot.setup_from_vectorstore()
        
        # Initialize Slack integration
        try:
            slack_integration = SlackIntegration(faq_bot)
            logger.info("🔍 DEBUG: Slack integration created, testing connection...")
            if slack_integration.test_connection():
                logger.info("🔍 DEBUG: Slack connection successful, creating enterprise processor...")
                # Initialize enterprise processor
                slack_processor = EnterpriseSlackProcessor(faq_bot, slack_integration)
                logger.info("🔍 DEBUG: Enterprise processor created, starting processing...")
                slack_processor.start_processing()
                logger.info("✅ Enterprise Slack integration initialized successfully!")
            else:
                logger.warning("⚠️ Slack integration available but not connected")
                slack_processor = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Slack integration: {e}")
            logger.error(f"🔍 DEBUG: Full error traceback:", exc_info=True)
            slack_integration = None
            slack_processor = None
        
        # Initialize Email integration
        try:
            email_integration = EmailIntegration(faq_bot)
            email_integration.start_email_monitoring()
            logger.info("✅ Email integration initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Email integration: {e}")
            email_integration = None
        
        initialization_status = {"status": "ready", "message": "Bot ready!"}
        logger.info("🎓 HR Policy Bot initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        initialization_status = {"status": "error", "message": f"Initialization failed: {str(e)}"}

@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests to prevent 404 errors"""
    return "", 204  # No Content response

@app.route("/api/status")
def get_status():
    """Get the current status of the enterprise bot and integrations"""
    status_data = {
        "bot": initialization_status,
        "integrations": {
            "slack": slack_integration is not None and slack_integration.is_configured(),
            "email": email_integration is not None
        }
    }
    
    # Add enterprise processor stats if available
    if slack_processor:
        status_data["slack_processor"] = slack_processor.get_enterprise_stats()
    
    return jsonify(status_data)

@app.route("/api/ask", methods=["POST"])
def ask_question():
    """Handle questions from the web interface"""
    import time
    start_time = time.time()
    
    # FORCE logging to work
    print("🔥 DEBUG: ask_question endpoint called!")
    logger.error("🔥 DEBUG: ask_question endpoint called!")
    
    if initialization_status["status"] != "ready":
        logger.error("🔥 DEBUG: Bot not ready!")
        return jsonify({"error": "Bot is not ready yet"}), 503

    data = request.get_json()
    question = data.get("question", "").strip()
    format_type = data.get("format", "web")  # Get format from request
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    try:
        # Use fast_answer with the requested format
        result = faq_bot.fast_answer(question, platform=format_type)
        
        if result and "answer" in result:
            return jsonify({
                "answer": result["answer"],
                "sources": [doc.metadata.get('source', 'Unknown') for doc in result.get("source_documents", [])],
                "performance": result.get("performance", {}),
                "status": "success"
            })
        else:
            return jsonify({
                "answer": "I apologize, but I couldn't find a suitable answer to your question. Please try rephrasing or contact HR directly.",
                "sources": [],
                "status": "no_answer"
            })
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return jsonify({
            "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
            "sources": [],
            "status": "error"
        }), 500


def _get_bot_response_sync(question: str) -> dict:
    """Simplified synchronous wrapper for bot's async ask_question method"""
    import asyncio
    
    async def get_answer():
        try:
            logger.info(f"🔄 Starting async bot processing for: {question}")
            # Get the first (and typically only) result from the async generator
            async for result in faq_bot.ask_question(question):
                logger.info(f"✅ Got result from bot: {type(result)}")
                return result
            logger.warning("⚠️ No result returned from bot async generator")
            return None
        except Exception as e:
            logger.error(f"❌ Error in async bot processing: {e}", exc_info=True)
            return None
    
    try:
        logger.info(f"🚀 Starting sync wrapper for question: {question}")
        # Simple approach - just run the async function
        result = asyncio.run(get_answer())
        logger.info(f"🎯 Sync wrapper result: {result}")
        return result
    except Exception as e:
        logger.error(f"💥 Error in sync wrapper: {e}", exc_info=True)
        return None

@app.route("/api/chat", methods=["POST"])
def chat():
    """Streaming chat endpoint"""
    if initialization_status["status"] != "ready":
        return jsonify({"error": "Bot is not ready yet"}), 503

    data = request.get_json()
    # Handle both 'question' and 'message' field names for compatibility
    question = data.get("question", data.get("message", ""))

    if not question:
        return jsonify({"error": "No question provided"}), 400

    def generate():
        try:
            # Get response from bot using sync wrapper
            result = _get_bot_response_sync(question)
            
            if result:
                # Clean the result for JSON serialization
                clean_result = {
                    "answer": result.get("answer", ""),
                    "sources": [doc.metadata.get('source', 'Unknown') for doc in result.get("source_documents", [])],
                    "performance": result.get("performance", {}),
                    "status": "success"
                }
                yield f"data: {json.dumps(clean_result)}\n\n"
            else:
                yield f"data: {json.dumps({'error': 'No response generated'})}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/plain')

@app.route("/api/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events with enterprise-grade processing"""
    if not slack_integration:
        return jsonify({"error": "Slack integration not available"}), 503

    data = request.get_json()
    
    # Handle URL verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
    # Handle message events with enterprise processor
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        
        if (event.get("type") in ["message", "app_mention"]) and not event.get("bot_id"):
            # Use enterprise processor if available, otherwise fall back to direct processing
            if slack_processor:
                try:
                    slack_processor.handle_slack_event(data)
                except Exception as e:
                    logger.error(f"❌ Enterprise processor error: {e}")
                    # Fallback to direct processing
                    _fallback_slack_processing(event)
            else:
                _fallback_slack_processing(event)
    
    return jsonify({"status": "ok"})

def _fallback_slack_processing(event):
    """Fallback processing when enterprise processor is not available"""
    channel = event.get("channel")
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    
    try:
        slack_integration.process_question_sync(text, channel, thread_ts)
    except Exception as e:
        logger.error(f"Error processing Slack question: {e}")

@app.route("/")
def index():
    """Serve the main chat interface"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMU Africa HR Policy Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }
        
        /* Sidebar Styles */
        .sidebar {
            width: 300px;
            background: linear-gradient(180deg, #c41e3a 0%, #8b1538 100%);
            color: white;
            display: flex;
            flex-direction: column;
            box-shadow: 2px 0 20px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 30px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        
        .app-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .app-subtitle {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .quick-actions {
            padding: 20px;
            flex: 1;
        }
        
        .quick-actions h3 {
            font-size: 16px;
            margin-bottom: 15px;
            opacity: 0.9;
        }
        
        .action-button {
            width: 100%;
            padding: 12px 16px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: left;
            font-size: 14px;
        }
        
        .action-button:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }
        
        .status-indicator {
            padding: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4caf50;
        }
        
        .status-dot.offline {
            background: #f44336;
        }
        
        /* Main Chat Area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
        }
        
        .chat-header {
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .chat-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .chat-status {
            font-size: 14px;
            color: #666;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-badge {
            padding: 4px 12px;
            background: #e8f5e8;
            color: #2e7d2e;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .chat-messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }
        
        .user .message-avatar {
            background: #667eea;
            color: white;
        }
        
        .bot .message-avatar {
            background: #c41e3a;
            color: white;
        }
        
        .message-content {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 18px;
            line-height: 1.5;
            font-size: 14px;
        }
        
        .user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .chat-input-area {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-container {
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }
        
        .input-wrapper {
            flex: 1;
            position: relative;
        }
        
        #questionInput {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            resize: none;
            outline: none;
            transition: all 0.3s ease;
            min-height: 50px;
            max-height: 120px;
        }
        
        #questionInput:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-button {
            width: 50px;
            height: 50px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .send-button:hover {
            background: #5a6fd8;
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Loading Animation */
        .typing-indicator {
            display: none;
            padding: 15px 20px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            max-width: 70%;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.5s infinite;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                width: 250px;
            }
            
            .chat-messages {
                padding: 20px;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #a1a1a1;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <div class="logo-icon">🎓</div>
                    <div>
                        <div class="app-title">CMU Africa</div>
                        <div class="app-subtitle">HR Policy Assistant</div>
                    </div>
                </div>
            </div>
            
            <div class="quick-actions">
                <h3>Quick Questions</h3>
                <button class="action-button" onclick="askQuestion('How do I request PTO?')">
                    📅 Request PTO
                </button>
                <button class="action-button" onclick="askQuestion('What are the travel guidelines?')">
                    ✈️ Travel Guidelines
                </button>
                <button class="action-button" onclick="askQuestion('How do I access the staff handbook?')">
                    📖 Staff Handbook
                </button>
                <button class="action-button" onclick="askQuestion('What benefits are available?')">
                    💰 Benefits Information
                </button>
                <button class="action-button" onclick="askQuestion('What is the hiring process?')">
                    👥 Hiring Process
                </button>
                <button class="action-button" onclick="askQuestion('How do I submit expenses?')">
                    🧾 Expense Submission
                </button>
            </div>
            
            <div class="status-indicator">
                <div class="status-item">
                    <div class="status-dot" id="botStatus"></div>
                    <span id="botStatusText">Checking...</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" id="slackStatus"></div>
                    <span>Slack Integration</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" id="emailStatus"></div>
                    <span>Email Integration</span>
                </div>
            </div>
        </div>
        
        <!-- Main Chat Area -->
        <div class="chat-area">
            <div class="chat-header">
                <div class="chat-title">HR Policy Assistant</div>
                <div class="chat-status">
                    <span class="status-badge" id="statusBadge">Initializing...</span>
                    <span>Ask me about HR policies, procedures, and guidelines</span>
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-avatar">HR</div>
                    <div class="message-content">
                        <strong>Welcome to CMU Africa HR Policy Assistant! 🎓</strong><br><br>
                        I'm here to help you with HR policies, procedures, and guidelines. You can:
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Ask questions about travel policies</li>
                            <li>Learn about benefits and compensation</li>
                            <li>Get information about hiring processes</li>
                            <li>Find staff handbook details</li>
                            <li>Understand PTO and leave policies</li>
                        </ul>
                        Try clicking one of the quick questions in the sidebar, or type your own question below!
                    </div>
                </div>
            </div>
            
            <div class="chat-input-area">
                <div class="input-container">
                    <div class="input-wrapper">
                        <textarea id="questionInput" placeholder="Ask me about HR policies, procedures, or guidelines..." 
                                rows="1" onkeydown="handleKeyDown(event)"></textarea>
                    </div>
                    <button class="send-button" id="sendButton" onclick="sendMessage()">
                        →
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        
        // Auto-resize textarea
        const textarea = document.getElementById('questionInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Check status on page load
        window.onload = function() {
            checkStatus();
            // Check status every 5 seconds
            setInterval(checkStatus, 5000);
        };
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function askQuestion(question) {
            document.getElementById('questionInput').value = question;
            sendMessage();
        }
        
        async function checkStatus() {
            try {
                console.log('🔍 Checking status...');
                const response = await fetch('/api/status');
                const data = await response.json();
                console.log('📊 Status response:', data);
                
                // Safely update bot status elements
                const botStatusEl = document.getElementById('botStatus');
                const botStatusTextEl = document.getElementById('botStatusText');
                const statusBadgeEl = document.getElementById('statusBadge');
                
                if (data.bot && data.bot.status === 'ready') {
                    if (botStatusEl) botStatusEl.className = 'status-dot';
                    if (botStatusTextEl) botStatusTextEl.textContent = 'Bot Ready';
                    if (statusBadgeEl) {
                        statusBadgeEl.textContent = 'Ready';
                        statusBadgeEl.style.background = '#e8f5e8';
                        statusBadgeEl.style.color = '#2e7d2e';
                    }
                    console.log('✅ Bot status updated to Ready');
                } else {
                    if (botStatusEl) botStatusEl.className = 'status-dot offline';
                    if (botStatusTextEl) botStatusTextEl.textContent = 'Bot Initializing...';
                    if (statusBadgeEl) {
                        statusBadgeEl.textContent = 'Initializing...';
                        statusBadgeEl.style.background = '#fff3e0';
                        statusBadgeEl.style.color = '#f57c00';
                    }
                    console.log('⏳ Bot status updated to Initializing');
                }
                
                // Safely update integration status
                const slackStatusEl = document.getElementById('slackStatus');
                const emailStatusEl = document.getElementById('emailStatus');
                
                if (slackStatusEl && data.integrations) {
                    slackStatusEl.className = data.integrations.slack ? 'status-dot' : 'status-dot offline';
                }
                if (emailStatusEl && data.integrations) {
                    emailStatusEl.className = data.integrations.email ? 'status-dot' : 'status-dot offline';
                }
                
                console.log('🔄 Status check completed successfully');
                    
            } catch (error) {
                console.error('❌ Error checking status:', error);
                
                // Safely handle error states
                const botStatusEl = document.getElementById('botStatus');
                const botStatusTextEl = document.getElementById('botStatusText');
                const statusBadgeEl = document.getElementById('statusBadge');
                
                if (botStatusEl) botStatusEl.className = 'status-dot offline';
                if (botStatusTextEl) botStatusTextEl.textContent = 'Connection Error';
                if (statusBadgeEl) {
                    statusBadgeEl.textContent = 'Offline';
                    statusBadgeEl.style.background = '#ffebee';
                    statusBadgeEl.style.color = '#d32f2f';
                }
            }
        }
        
        async function sendMessage() {
            if (isLoading) return;
            
            const questionInput = document.getElementById('questionInput');
            const question = questionInput.value.trim();
            
            if (!question) return;
            
            // Add user message to chat
            addMessage(question, 'user');
            
            // Clear input and reset height
            questionInput.value = '';
            questionInput.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Disable send button
            isLoading = true;
            const sendButton = document.getElementById('sendButton');
            sendButton.disabled = true;
            sendButton.innerHTML = '⏳';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                // Hide typing indicator
                hideTypingIndicator();
                
                if (data.error) {
                    addMessage(`❌ Error: ${data.error}`, 'bot');
                } else {
                    addMessage(data.answer || 'Sorry, I could not generate a response.', 'bot');
                }
                
            } catch (error) {
                hideTypingIndicator();
                addMessage('❌ Sorry, I encountered an error while processing your question. Please try again.', 'bot');
                console.error('Error:', error);
            } finally {
                // Re-enable send button
                isLoading = false;
                sendButton.disabled = false;
                sendButton.innerHTML = '→';
            }
        }
        
        function addMessage(content, sender) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = sender === 'user' ? 'You' : 'HR';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            if (sender === 'bot') {
                // Content from web platform is already HTML, just set it directly
                messageContent.innerHTML = content;
            } else {
                messageContent.textContent = content;
            }
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function convertMarkdownToHtml(content) {
            // Content should already be HTML from the web platform
            // Just return it as-is to avoid regex issues
            return content;
        }
        
        function showTypingIndicator() {
            const chatMessages = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot';
            typingDiv.id = 'typingIndicator';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = 'HR';
            
            const typingContent = document.createElement('div');
            typingContent.className = 'typing-indicator';
            typingContent.style.display = 'block';
            typingContent.innerHTML = `
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            
            typingDiv.appendChild(avatar);
            typingDiv.appendChild(typingContent);
            chatMessages.appendChild(typingDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTypingIndicator() {
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Start bot initialization in background
    init_thread = Thread(target=initialize_bot)
    init_thread.daemon = True
    init_thread.start()
    
    # Start Flask app
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting HR Policy Bot server on port {port}")
    logger.info(f"📱 Web interface: http://localhost:{port}")
    logger.info(f"📊 API status: http://localhost:{port}/api/status")
    
    app.run(host="0.0.0.0", port=port, debug=False)
