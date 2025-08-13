import os
import re
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from html import unescape
import html2text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackIntegration:
    """Slack integration for the HR Policy Bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        
        if self.slack_token:
            try:
                self.client = WebClient(token=self.slack_token)
                logger.info("✅ Slack client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Slack client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ SLACK_BOT_TOKEN not found in environment variables")
            self.client = None
        
    def html_to_slack_text(self, html_content: str) -> str:
        """Convert HTML content to clean Slack-compatible text"""
        try:
            # Initialize html2text converter
            h = html2text.HTML2Text()
            h.ignore_links = False  # Keep links but format them for Slack
            h.body_width = 0  # Don't wrap lines
            h.ignore_images = True
            h.ignore_emphasis = False
            
            # Convert HTML to markdown first
            markdown_text = h.handle(html_content)
            
            # Clean up the markdown for Slack formatting
            # Remove extra newlines and clean up formatting
            cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_text)
            
            # Convert markdown headers to Slack format
            cleaned_text = re.sub(r'^### (.*?)$', r'*\1*', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^## (.*?)$', r'*\1*', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^# (.*?)$', r'*\1*', cleaned_text, flags=re.MULTILINE)
            
            # Convert markdown links to Slack format
            cleaned_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', cleaned_text)
            
            # Clean up bullet points for Slack
            cleaned_text = re.sub(r'^\* ', '• ', cleaned_text, flags=re.MULTILINE)
            
            # Remove any remaining HTML tags that might have been missed
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
            
            # Unescape HTML entities
            cleaned_text = unescape(cleaned_text)
            
            # Clean up extra whitespace
            cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error converting HTML to Slack text: {e}")
            # Fallback: strip HTML tags manually
            return self.strip_html_fallback(html_content)
    
    def strip_html_fallback(self, html_content: str) -> str:
        """Fallback method to strip HTML tags if html2text fails"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Unescape HTML entities
        text = unescape(text)
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()
    
    def format_for_slack(self, text: str) -> str:
        """Simple fallback - main formatting happens in bot.py with LLM"""
        # The bot now uses LLM for formatting, this is just a fallback
        return text.strip()
    
    def remove_duplicates(self, text: str) -> str:
        """Remove duplicate content from the response"""
        # Split the text into sections by double newlines
        sections = text.split('\n\n')
        
        # Remove duplicate sections
        seen_sections = set()
        unique_sections = []
        
        for section in sections:
            # Normalize the section for comparison (remove extra whitespace)
            normalized = ' '.join(section.split())
            
            # Skip very short sections (likely formatting artifacts)
            if len(normalized) < 10:
                continue
                
            # Skip if we've seen this content before
            if normalized not in seen_sections:
                seen_sections.add(normalized)
                unique_sections.append(section)
        
        return '\n\n'.join(unique_sections)
    
    def send_message(self, channel: str, text: str, thread_ts: str = None) -> bool:
        """Send a message to Slack"""
        try:
            if not self.client:
                logger.error("Slack client not initialized")
                return False
            
            # Remove duplicates first
            deduplicated_text = self.remove_duplicates(text)
            
            # Format the text for Slack
            formatted_text = self.format_for_slack(deduplicated_text)
            
            # Truncate very long messages for Slack (4000 char limit)
            if len(formatted_text) > 3800:
                formatted_text = formatted_text[:3700] + "\n\n... (response truncated for Slack)"
            
            response = self.client.chat_postMessage(
                channel=channel,
                text=formatted_text,
                thread_ts=thread_ts
            )
            
            logger.info(f"✅ Message sent to Slack channel {channel}")
            return True
            
        except SlackApiError as e:
            logger.error(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending Slack message: {e}")
            return False
    
    async def process_question(self, question: str, channel: str, thread_ts: str = None) -> bool:
        """Process a question and send response to Slack - now uses sync method to prevent duplicates"""
        try:
            # Use the synchronous method to prevent multiple responses
            result = self.process_question_sync(question, channel, thread_ts)
            return result.get("success", False)
                
        except Exception as e:
            logger.error(f"Error processing Slack question: {e}")
            error_msg = "Sorry, I encountered an error while processing your request. Please try again later."
            return self.send_message(channel, error_msg, thread_ts)

    def process_question_sync(self, question: str, channel: str, thread_ts: str = None) -> dict:
        """Synchronous version of process_question with detailed result reporting"""
        try:
            # Use the synchronous fast_answer method directly for better reliability
            if hasattr(self.bot, 'fast_answer'):
                result = self.bot.fast_answer(question, platform="slack")
            else:
                logger.error("Bot does not have fast_answer method")
                fallback_msg = "I apologize, but the bot is not properly configured. Please contact support."
                return self.send_message_safe(channel, fallback_msg, thread_ts)
            
            if result and "answer" in result:
                answer = result["answer"]
                return self.send_message_safe(channel, answer, thread_ts)
            else:
                fallback_msg = "I apologize, but I couldn't find information to answer your question. Please contact HR directly for assistance."
                return self.send_message_safe(channel, fallback_msg, thread_ts)
                
        except Exception as e:
            logger.error(f"Error processing Slack question: {e}")
            error_msg = "Sorry, I encountered an error while processing your request. Please try again later."
            return self.send_message_safe(channel, error_msg, thread_ts)
    
    def is_configured(self) -> bool:
        """Check if Slack integration is properly configured"""
        return bool(self.slack_token and self.client)
    
    def test_connection(self) -> bool:
        """Test Slack connection"""
        try:
            if not self.client:
                return False
                
            response = self.client.auth_test()
            logger.info(f"✅ Slack connection successful: {response['user']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Slack connection test failed: {e}")
            return False
    
    def validate_permissions(self) -> dict:
        """Validate Slack bot permissions and provide guidance"""
        validation_result = {
            "valid": False,
            "missing_scopes": [],
            "available_scopes": [],
            "guidance": []
        }
        
        try:
            if not self.client:
                validation_result["guidance"].append("❌ Slack client not initialized - check SLACK_BOT_TOKEN")
                return validation_result
            
            # Test basic auth
            auth_response = self.client.auth_test()
            if not auth_response["ok"]:
                validation_result["guidance"].append("❌ Slack authentication failed")
                return validation_result
            
            validation_result["available_scopes"] = auth_response.get("scopes", [])
            logger.info(f"Available scopes: {validation_result['available_scopes']}")
            
            # Test required scopes
            required_scopes = ["chat:write"]
            optional_scopes = ["channels:read", "app_mentions:read", "im:read", "im:write"]
            
            for scope in required_scopes:
                if scope not in validation_result["available_scopes"]:
                    validation_result["missing_scopes"].append(scope)
                    validation_result["guidance"].append(f"❌ Missing required scope: {scope}")
            
            for scope in optional_scopes:
                if scope not in validation_result["available_scopes"]:
                    validation_result["missing_scopes"].append(scope)
                    validation_result["guidance"].append(f"⚠️  Missing optional scope: {scope}")
            
            # Test message sending capability
            try:
                # Try to send to a test channel (will fail gracefully if no access)
                test_response = self.client.chat_postMessage(
                    channel="C000000000",  # Invalid channel ID for testing
                    text="test"
                )
                # We expect this to fail, but if we get a permissions error, that's good
            except SlackApiError as e:
                if "missing_scope" in str(e):
                    validation_result["guidance"].append(f"❌ Scope issue detected: {e}")
                elif "channel_not_found" in str(e):
                    validation_result["guidance"].append("✅ Message sending capability confirmed")
            
            # Provide guidance based on results
            if not validation_result["missing_scopes"]:
                validation_result["valid"] = True
                validation_result["guidance"].append("✅ All permissions configured correctly")
            else:
                validation_result["guidance"].append("\n📋 To fix permission issues:")
                validation_result["guidance"].append("1. Go to https://api.slack.com/apps")
                validation_result["guidance"].append("2. Select your 'cmu-hr-chatbot' app")
                validation_result["guidance"].append("3. Go to 'OAuth & Permissions'")
                validation_result["guidance"].append("4. Add missing scopes:")
                for scope in validation_result["missing_scopes"]:
                    validation_result["guidance"].append(f"   - {scope}")
                validation_result["guidance"].append("5. Reinstall app to workspace")
                
        except Exception as e:
            validation_result["guidance"].append(f"❌ Permission validation failed: {e}")
            
        return validation_result
    
    def send_message_safe(self, channel: str, text: str, thread_ts: str = None) -> dict:
        """Safe message sending with detailed error reporting"""
        result = {
            "success": False,
            "message": "",
            "error": None,
            "guidance": []
        }
        
        try:
            if not self.client:
                result["error"] = "Slack client not initialized"
                result["guidance"].append("Check SLACK_BOT_TOKEN environment variable")
                return result
            
            # Remove duplicates first
            deduplicated_text = self.remove_duplicates(text)
            
            # Format and truncate text
            formatted_text = self.format_for_slack(deduplicated_text)
            if len(formatted_text) > 3800:
                formatted_text = formatted_text[:3700] + "\n\n... (response truncated for Slack)"
            
            response = self.client.chat_postMessage(
                channel=channel,
                text=formatted_text,
                thread_ts=thread_ts
            )
            
            if response["ok"]:
                result["success"] = True
                result["message"] = "Message sent successfully"
                logger.info(f"✅ Message sent to Slack channel {channel}")
            else:
                result["error"] = response.get("error", "Unknown error")
                result["guidance"].append(f"Slack API error: {result['error']}")
                
        except SlackApiError as e:
            result["error"] = e.response.get("error", str(e))
            
            # Provide specific guidance based on error type
            if "missing_scope" in result["error"]:
                result["guidance"].append("❌ Missing required Slack permissions")
                result["guidance"].append("Run validation: python -c \"from src.integrations.slack_integration import SlackIntegration; SlackIntegration(None).validate_permissions()\"")
            elif "channel_not_found" in result["error"]:
                result["guidance"].append("❌ Channel not found or bot not invited")
                result["guidance"].append("Make sure bot is invited to the channel")
            elif "not_in_channel" in result["error"]:
                result["guidance"].append("❌ Bot not in channel")
                result["guidance"].append("Invite the bot to the channel first")
            else:
                result["guidance"].append(f"❌ Slack API error: {result['error']}")
                
        except Exception as e:
            result["error"] = str(e)
            result["guidance"].append(f"❌ Unexpected error: {e}")
            
        return result