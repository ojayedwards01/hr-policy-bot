import os
import smtplib
import logging
import imaplib
import email
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import List, Dict, Optional
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailIntegration:
    """Email integration for the HR Policy Bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.monitoring = False
        self.monitor_thread = None
        self.startup_time = None
        self.processed_emails = set()
        
        # Check if email credentials are configured
        if not self.username or not self.password:
            logger.warning("⚠️ Email credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
        else:
            logger.info("✅ Email integration initialized")
        
        # Email settings
        self.response_subject_prefix = "[CMU HR Bot]"
        self.bot_signature = """

---
🎓 CMU Africa HR Policy Assistant
This is an automated response from the Carnegie Mellon University Africa HR Policy Bot.
For urgent matters, please contact HR directly.
"""
        
        # Ensure bot is properly set up
        self._ensure_bot_setup()
    
    def send_email(self, to_email: str, subject: str, body: str, reply_to: Optional[str] = None) -> bool:
        """Send an email response"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = f"{self.response_subject_prefix} {subject}"
            
            if reply_to:
                msg['In-Reply-To'] = reply_to
                msg['References'] = reply_to
            
            # Add body with signature
            full_body = body + self.bot_signature
            msg.attach(MIMEText(full_body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {e}")
            return False
    
    def process_question_email(self, question: str, sender_email: str, original_subject: str, message_id: Optional[str] = None):
        """Process a question and send email response"""
        try:
            # Get answer from the bot using proper async handling
            result = self._get_bot_response(question)
            
            if result and result.get("answer") and result["answer"] != "No QA chain available. Please run setup first.":
                answer = result["answer"]
                source_docs = result.get("source_documents", [])
                
                # Format the response for email
                formatted_response = self._format_email_response(question, answer, source_docs)
                
                # Send response
                response_subject = f"Re: {original_subject}" if original_subject else "HR Policy Information"
                self.send_email(sender_email, response_subject, formatted_response, message_id)
                
            else:
                # Send fallback response
                fallback_response = self._create_fallback_response(question)
                response_subject = f"Re: {original_subject}" if original_subject else "HR Policy Information"
                self.send_email(sender_email, response_subject, fallback_response, message_id)
                
        except Exception as e:
            logger.error(f"Error processing question email: {e}")
            # Send error response
            error_response = self._create_error_response(question)
            response_subject = f"Re: {original_subject}" if original_subject else "HR Policy Information"
            self.send_email(sender_email, response_subject, error_response, message_id)
    
    def _get_bot_response(self, question: str) -> dict:
        """Get response from bot using synchronous approach"""
        try:
            # Use the synchronous fast_answer method directly for better reliability
            if hasattr(self.bot, 'fast_answer'):
                result = self.bot.fast_answer(question, platform="email")
                return result
            else:
                logger.error("Bot does not have fast_answer method")
                return None
            
        except Exception as e:
            logger.error(f"Error getting bot response: {e}")
            return None
    
    def _format_email_response(self, question: str, answer: str, source_docs: list) -> str:
        """Format the response for email using markdown"""
        response = f"""Hello,

Thank you for your HR policy question: **"{question}"**

{answer}
"""
        
        # Add source documents if available
        if source_docs:
            response += "\n\n## Sources and Additional Resources\n"
            for i, doc in enumerate(source_docs, 1):
                source = doc.metadata.get('source', 'Unknown')
                if source.startswith('http'):
                    response += f"{i}. [{source}]({source})\n"
                else:
                    response += f"{i}. {source}\n"
        
        response += "\nIf you need further assistance, please feel free to contact the HR department directly."
        
        return response
    
    def _create_fallback_response(self, question: str) -> str:
        """Create a fallback response when the bot can't answer"""
        return f"""Hello,

Thank you for your question: "{question}"

I apologize, but I couldn't find specific information in our HR policy documents to answer your question. 

For assistance with this matter, please contact the CMU Africa HR department directly:
- Email: hr-africa@cmu.edu
- Phone: +250 788 381 032
- Website: www.cmu.edu/africa

They will be able to provide you with accurate and up-to-date information.
"""
    
    def _create_error_response(self, question: str) -> str:
        """Create an error response"""
        return f"""Hello,

Thank you for your question: "{question}"

I encountered a technical issue while processing your request. Please try again later or contact the HR department directly:
- Email: hr-africa@cmu.edu
- Phone: +250 788 381 032
- Website: www.cmu.edu/africa

We apologize for any inconvenience.
"""
    
    def start_email_monitoring(self, check_interval: int = 60):
        """Start monitoring for new emails (basic implementation)"""
        if self.monitoring:
            logger.info("Email monitoring is already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_emails, args=(check_interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"📧 Started email monitoring (checking every {check_interval} seconds)")
    
    def stop_email_monitoring(self):
        """Stop email monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("📧 Stopped email monitoring")
    
    def _monitor_emails(self, check_interval: int):
        """Monitor for new emails (basic implementation)"""
        logger.info("Email monitoring started...")
        
        while self.monitoring:
            try:
                # Connect to IMAP server
                with imaplib.IMAP4_SSL(self.imap_server) as imap:
                    imap.login(self.username, self.password)
                    imap.select('INBOX')
                    
                    # Search for unread emails
                    status, messages = imap.search(None, 'UNSEEN')
                    
                    if status == 'OK' and messages[0]:
                        email_ids = messages[0].split()
                        
                        for email_id in email_ids:
                            try:
                                # Fetch email
                                status, msg_data = imap.fetch(email_id, '(RFC822)')
                                
                                if status == 'OK':
                                    email_body = msg_data[0][1]
                                    email_message = email.message_from_bytes(email_body)
                                    
                                    # Process the email
                                    self._process_incoming_email(email_message)
                                    
                                    # Mark as read
                                    imap.store(email_id, '+FLAGS', '\\Seen')
                                    
                            except Exception as e:
                                logger.error(f"Error processing email {email_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error in email monitoring: {e}")
            
            # Wait before next check
            time.sleep(check_interval)
    
    def _process_incoming_email(self, email_message):
        """Process an incoming email"""
        try:
            # Extract email details
            sender = email_message.get('From', '')
            subject = email_message.get('Subject', '')
            message_id = email_message.get('Message-ID', '')
            
            # Decode subject if needed
            if subject:
                decoded_subject = decode_header(subject)[0]
                if isinstance(decoded_subject[0], bytes):
                    subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
            
            # Extract email body
            body = self._extract_email_body(email_message)
            
            # Check if this is a potential HR question
            if self._is_hr_question(subject, body):
                logger.info(f"Processing HR question from {sender}: {subject}")
                self.process_question_email(body, sender, subject, message_id)
            
        except Exception as e:
            logger.error(f"Error processing incoming email: {e}")
    
    def _extract_email_body(self, email_message) -> str:
        """Extract the body text from an email message and clean it of signatures"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Clean the email body to extract only the actual question
        cleaned_body = self._extract_question_from_email(body.strip())
        return cleaned_body
    
    def _extract_question_from_email(self, email_body: str) -> str:
        """Extract only the actual question from email, removing signatures and metadata"""
        import re
        
        # Signature markers that clearly indicate start of signature
        definite_signature_markers = [
            r'^\*?Best Regards\*?$',
            r'^\*?Regards\*?$', 
            r'^\*?Sincerely\*?$',
            r'^\*?Best regards\*?$',
            r'^\*?Kind regards\*?$',
            r'^--$',
            r'^___+$',
            r'Sent from',
            r'Tel:',
            r'Phone:',
            r'LinkedIn:',
            r'Plot No',
            r'Building',
            r'Rwanda$',
        ]
        
        # Contact info patterns (emails, phones)
        contact_patterns = [
            r'@\w+\.\w+',  # Email addresses
            r'\+\d{1,4}[\s\-\(\)]*\d{6,}',  # Phone numbers
            r'www\.',
            r'https?://',
        ]
        
        lines = email_body.split('\n')
        question_lines = []
        signature_started = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line is definitely a signature marker
            is_definite_signature = any(re.search(marker, line, re.IGNORECASE) for marker in definite_signature_markers)
            
            # Check if this line contains contact info
            is_contact_info = any(re.search(pattern, line) for pattern in contact_patterns)
            
            # Stop processing if we hit a definite signature marker
            if is_definite_signature:
                signature_started = True
                break
            
            # If we find contact info, this might be start of signature
            if is_contact_info:
                signature_started = True
                break
            
            # Skip lines that look like email headers or formatting
            if (line.startswith('>') or 
                line.startswith('On ') or 
                'wrote:' in line.lower() or
                line.startswith('From:') or
                line.startswith('To:') or
                line.startswith('Subject:') or
                line.startswith('Date:')):
                continue
            
            # Skip lines that are just name/title formatting (like "*Edward Ajayi | MSEAI 26'*")
            if re.match(r'^\*.*\|.*\*$', line) or re.match(r'^\*.*\*$', line):
                signature_started = True
                break
            
            question_lines.append(line)
        
        # Join the question lines and clean up
        question = ' '.join(question_lines).strip()
        
        # Remove any remaining artifacts
        question = re.sub(r'\s+', ' ', question)  # Multiple spaces to single space
        question = re.sub(r'^(Hello,?|Hi,?)\s*', '', question, flags=re.IGNORECASE)  # Remove greetings
        question = re.sub(r'\s*(Thanks?|Thank you)\s*$', '', question, flags=re.IGNORECASE)  # Remove trailing thanks
        
        return question.strip()
    
    def _is_hr_question(self, subject: str, body: str) -> bool:
        """Determine if an email is an HR question"""
        # Simple keyword-based detection
        hr_keywords = [
            'hr', 'human resources', 'policy', 'leave', 'vacation', 'pto',
            'benefits', 'salary', 'hiring', 'onboarding', 'offboarding',
            'travel', 'expense', 'handbook', 'guidelines', 'faculty',
            'staff', 'employee', 'cmu africa', 'carnegie mellon'
        ]
        
        text_to_check = f"{subject} {body}".lower()
        return any(keyword in text_to_check for keyword in hr_keywords)
    
    def _ensure_bot_setup(self):
        """Ensure the bot is properly set up with vectorstore"""
        try:
            # Check if bot already has a current_chain
            if hasattr(self.bot, 'current_chain') and self.bot.current_chain is not None:
                logger.info("✅ Bot already set up with QA chain")
                return True
            
            # Try to set up the bot
            logger.info("🔧 Setting up bot with vectorstore...")
            if self.bot.setup_from_vectorstore():
                logger.info("✅ Bot setup successful for email integration")
                return True
            else:
                logger.error("❌ Bot setup failed for email integration")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up bot for email integration: {e}")
            return False
    
    def start_email_monitoring(self, check_interval: int = 60):
        """Start monitoring for new emails (only emails received after startup)"""
        if self.monitoring:
            logger.info("Email monitoring is already running")
            return
        
        # Mark startup time and get current email state
        import datetime
        self.startup_time = datetime.datetime.now()
        self._mark_existing_emails_as_processed()
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_emails, args=(check_interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"📧 Started email monitoring (checking every {check_interval} seconds)")
        logger.info(f"📧 Will only process emails received after {self.startup_time}")
    
    def _mark_existing_emails_as_processed(self):
        """Mark all existing emails as processed so we only handle new ones"""
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as imap:
                imap.login(self.username, self.password)
                imap.select('INBOX')
                
                # Get all email IDs to mark as processed
                status, messages = imap.search(None, 'ALL')
                
                if status == 'OK' and messages[0]:
                    email_ids = messages[0].split()
                    self.processed_emails.update(email_ids)
                    logger.info(f"📧 Marked {len(email_ids)} existing emails as processed")
                
        except Exception as e:
            logger.error(f"Error marking existing emails: {e}")
    
    def _monitor_emails(self, check_interval: int):
        """Monitor for new emails (only process emails received after startup)"""
        logger.info("Email monitoring started...")
        
        while self.monitoring:
            try:
                # Connect to IMAP server
                with imaplib.IMAP4_SSL(self.imap_server) as imap:
                    imap.login(self.username, self.password)
                    imap.select('INBOX')
                    
                    # Search for all emails (we'll filter by processed status)
                    status, messages = imap.search(None, 'ALL')
                    
                    if status == 'OK' and messages[0]:
                        email_ids = messages[0].split()
                        
                        # Process only new emails (not in processed set)
                        new_email_ids = [eid for eid in email_ids if eid not in self.processed_emails]
                        
                        if new_email_ids:
                            logger.info(f"📧 Found {len(new_email_ids)} new emails to process")
                        
                        for email_id in new_email_ids:
                            try:
                                # Fetch email
                                status, msg_data = imap.fetch(email_id, '(RFC822)')
                                
                                if status == 'OK':
                                    email_body = msg_data[0][1]
                                    email_message = email.message_from_bytes(email_body)
                                    
                                    # Process the email
                                    self._process_incoming_email(email_message)
                                    
                                    # Mark as processed
                                    self.processed_emails.add(email_id)
                                    
                            except Exception as e:
                                logger.error(f"Error processing email {email_id}: {e}")
                                # Still mark as processed to avoid reprocessing
                                self.processed_emails.add(email_id)
                    
            except Exception as e:
                logger.error(f"Error in email monitoring: {e}")
            
            # Wait before next check
            time.sleep(check_interval)
    
    def is_configured(self) -> bool:
        """Check if email integration is properly configured"""
        return bool(self.username and self.password)
    
    def test_connection(self) -> bool:
        """Test email connection"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            logger.info("✅ Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Email connection test failed: {e}")
            return False
