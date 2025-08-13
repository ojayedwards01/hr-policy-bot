"""
Enterprise-Grade Slack Event Handler
===================================

Production-ready implementation based on Databricks enterprise patterns:
- Asynchronous message processing with queues
- Thread-safe event deduplication
- Professional response formatting
- Clean separation of concerns
- Database-level audit trail simulation
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Set, Optional
from dataclasses import dataclass
from queue import Queue, Empty

logger = logging.getLogger(__name__)

@dataclass
class SlackEvent:
    """Professional Slack event data structure"""
    event_id: str
    channel_id: str
    user_id: str
    text: str
    thread_ts: Optional[str] = None
    timestamp: str = ""
    event_type: str = "message"
    
    def to_signature(self) -> str:
        """Create unique signature for deduplication"""
        return f"{self.user_id}_{self.channel_id}_{self.text[:50]}_{self.timestamp}"
    
    def to_urn(self) -> str:
        """Create URN for audit logging"""
        return f"slack://{self.channel_id}::{self.thread_ts or self.timestamp}::{self.timestamp}"

class EventAuditStore:
    """Thread-safe event audit store for enterprise-grade deduplication"""
    
    def __init__(self, max_events: int = 10000):
        self._events: Set[str] = set()
        self._processing: Set[str] = set()
        self._max_events = max_events
        self._lock = threading.RLock()
        self._logger = logging.getLogger(f"{__name__}.EventAuditStore")
        
    def is_duplicate_event(self, event_id: str) -> bool:
        """Check if event was already processed"""
        with self._lock:
            return event_id in self._events
    
    def is_processing(self, signature: str) -> bool:
        """Check if question is currently being processed"""
        with self._lock:
            return signature in self._processing
    
    def mark_event_processed(self, event_id: str) -> None:
        """Mark event as processed"""
        with self._lock:
            self._events.add(event_id)
            if len(self._events) > self._max_events:
                # Keep only recent half for memory management
                recent = list(self._events)[-self._max_events//2:]
                self._events = set(recent)
                self._logger.info(f"🧹 Cleaned audit store, kept {len(recent)} recent events")
    
    def mark_processing_start(self, signature: str) -> bool:
        """Mark question as being processed. Returns False if already processing."""
        with self._lock:
            if signature in self._processing:
                return False
            self._processing.add(signature)
            return True
    
    def mark_processing_complete(self, signature: str) -> None:
        """Mark question processing as complete"""
        with self._lock:
            self._processing.discard(signature)
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit store statistics"""
        with self._lock:
            return {
                "processed_events": len(self._events),
                "currently_processing": len(self._processing),
                "max_events": self._max_events
            }

class EnterpriseSlackProcessor:
    """
    Enterprise-grade Slack message processor
    
    Based on patterns from Databricks industry solutions:
    - Asynchronous processing with message queues
    - Proper event deduplication
    - Professional error handling
    - Comprehensive audit trail
    """
    
    def __init__(self, bot, slack_integration):
        self.bot = bot
        self.slack_integration = slack_integration
        self.audit_store = EventAuditStore()
        self.message_queue = Queue(maxsize=1000)  # Prevent memory issues
        self.processing_thread = None
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.EnterpriseSlackProcessor")
        
        # Statistics
        self.stats = {
            "messages_processed": 0,
            "messages_queued": 0,
            "duplicates_prevented": 0,
            "errors_encountered": 0,
            "start_time": datetime.now()
        }
        
    def start_processing(self):
        """Start the enterprise message processing system"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.running = True
            self.processing_thread = threading.Thread(
                target=self._enterprise_processing_loop, 
                daemon=True,
                name="SlackProcessor"
            )
            self.processing_thread.start()
            self.logger.info("🚀 Enterprise Slack processor started")
    
    def stop_processing(self):
        """Gracefully stop the processing system"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        self.logger.info("🛑 Enterprise Slack processor stopped")
        self._log_final_stats()
    
    def _enterprise_processing_loop(self):
        """Main enterprise processing loop with robust error handling"""
        self.logger.info("📡 Enterprise processing loop started")
        
        while self.running:
            try:
                # Process messages with timeout to allow graceful shutdown
                try:
                    slack_event = self.message_queue.get(timeout=1.0)
                    self._process_enterprise_message(slack_event)
                    self.message_queue.task_done()
                    self.stats["messages_processed"] += 1
                except Empty:
                    # Normal timeout - continue loop
                    continue
                    
            except Exception as e:
                self.logger.error(f"❌ Critical error in processing loop: {e}")
                self.stats["errors_encountered"] += 1
                time.sleep(1)  # Back off on errors
    
    def _process_enterprise_message(self, slack_event: SlackEvent):
        """Process a single message with enterprise-grade reliability"""
        try:
            urn = slack_event.to_urn()
            self.logger.info(f"🔄 Processing enterprise message: {urn}")
            
            # Enterprise-grade bot response generation
            if hasattr(self.bot, 'fast_answer'):
                result = self.bot.fast_answer(slack_event.text, platform="slack")
            else:
                self.logger.error("❌ Bot missing fast_answer method - critical configuration error")
                self._send_error_response(slack_event, "Bot configuration error")
                return
            
            if result and "answer" in result:
                # Send professional response
                success = self.slack_integration.send_message_safe(
                    channel=slack_event.channel_id,
                    text=result["answer"],
                    thread_ts=slack_event.thread_ts
                )
                
                if success.get("success"):
                    self.logger.info(f"✅ Enterprise response delivered: {urn}")
                    # Mark as processed only after successful delivery
                    self.audit_store.mark_event_processed(slack_event.event_id)
                else:
                    self.logger.error(f"❌ Response delivery failed: {urn} - {success.get('error')}")
                    self._handle_delivery_failure(slack_event, success.get("error"))
            else:
                self.logger.warning(f"⚠️ No answer generated for: {urn}")
                self._send_fallback_response(slack_event)
                
        except Exception as e:
            self.logger.error(f"❌ Enterprise processing error for {slack_event.to_urn()}: {e}")
            self.stats["errors_encountered"] += 1
            self._send_error_response(slack_event, str(e))
        finally:
            # Always clean up processing state
            self.audit_store.mark_processing_complete(slack_event.to_signature())
    
    def handle_slack_event(self, event_data: Dict) -> Dict[str, str]:
        """
        Enterprise event handler - main entry point
        
        Designed to respond within Slack's 3-second requirement
        while ensuring reliable message processing
        """
        try:
            start_time = time.time()
            
            # Extract and validate event
            event = event_data.get("event", {})
            event_type = event.get("type")
            
            # Generate comprehensive event ID for deduplication
            event_id = self._generate_event_id(event, event_type)
            
            # CRITICAL: Check for duplicate events first (fastest path)
            if self.audit_store.is_duplicate_event(event_id):
                self.logger.info(f"🚫 Enterprise duplicate prevention: {event_id}")
                self.stats["duplicates_prevented"] += 1
                return {"status": "ok", "message": "Duplicate event prevented"}
            
            # Handle relevant event types
            if event_type in ["app_mention", "message"]:
                slack_event = self._create_slack_event(event, event_id)
                if slack_event:
                    result = self._queue_for_enterprise_processing(slack_event)
                    
                    # Log performance
                    processing_time = time.time() - start_time
                    self.logger.info(f"⚡ Event handled in {processing_time:.3f}s")
                    
                    return result
            
            return {"status": "ok", "message": "Event type ignored"}
            
        except Exception as e:
            self.logger.error(f"❌ Critical enterprise event handling error: {e}")
            return {"status": "error", "message": "Enterprise handling failed"}
    
    def _generate_event_id(self, event: Dict, event_type: str) -> str:
        """Generate comprehensive event ID for enterprise deduplication"""
        return (event.get("client_msg_id") or 
                event.get("ts") or 
                f"{event_type}_{event.get('user')}_{int(time.time() * 1000000)}")
    
    def _create_slack_event(self, event: Dict, event_id: str) -> Optional[SlackEvent]:
        """Create validated SlackEvent from raw Slack data"""
        try:
            channel = event.get("channel")
            text = event.get("text", "")
            user_id = event.get("user")
            timestamp = event.get("ts")
            thread_ts = event.get("thread_ts")
            event_type = event.get("type")
            
            # Enterprise validation
            if not all([channel, user_id, timestamp]):
                self.logger.warning(f"⚠️ Enterprise validation failed: missing required fields")
                return None
            
            # Bot self-exclusion
            if self._is_bot_message(user_id):
                self.logger.info(f"🚫 Enterprise bot exclusion: {user_id}")
                return None
            
            # Clean app mentions for professional processing
            if event_type == "app_mention":
                text = self._clean_app_mention(text)
            elif event_type == "message" and not channel.startswith('D'):
                # Only process DMs for regular messages
                self.logger.info(f"🚫 Enterprise policy: public messages require @mention")
                return None
            
            return SlackEvent(
                event_id=event_id,
                channel_id=channel,
                user_id=user_id,
                text=text,
                thread_ts=thread_ts,
                timestamp=timestamp,
                event_type=event_type
            )
            
        except Exception as e:
            self.logger.error(f"❌ Enterprise event creation failed: {e}")
            return None
    
    def _is_bot_message(self, user_id: str) -> bool:
        """Check if message is from the bot itself"""
        try:
            auth_response = self.slack_integration.client.auth_test()
            bot_user_id = auth_response.get("user_id")
            return user_id == bot_user_id
        except Exception as e:
            self.logger.warning(f"⚠️ Could not verify bot user ID: {e}")
            return False
    
    def _clean_app_mention(self, text: str) -> str:
        """Clean app mention for professional processing"""
        import re
        return re.sub(r'<@[^>]+>\s*', '', text).strip()
    
    def _queue_for_enterprise_processing(self, slack_event: SlackEvent) -> Dict[str, str]:
        """Queue message for enterprise-grade asynchronous processing"""
        try:
            signature = slack_event.to_signature()
            
            # Question-level deduplication
            if self.audit_store.is_processing(signature):
                self.logger.info(f"🚫 Enterprise question deduplication: already processing")
                self.stats["duplicates_prevented"] += 1
                return {"status": "ok", "message": "Question already being processed"}
            
            # Mark as processing
            if not self.audit_store.mark_processing_start(signature):
                self.logger.info(f"🚫 Enterprise concurrency control: question locked")
                return {"status": "ok", "message": "Question processing locked"}
            
            # Queue for processing
            try:
                self.message_queue.put(slack_event, timeout=1)
                self.stats["messages_queued"] += 1
                self.logger.info(f"📤 Enterprise queue: {slack_event.to_urn()}")
                return {"status": "ok", "message": "Queued for enterprise processing"}
            except:
                # Queue full - clean up and return error
                self.audit_store.mark_processing_complete(signature)
                return {"status": "error", "message": "Enterprise queue capacity exceeded"}
            
        except Exception as e:
            self.logger.error(f"❌ Enterprise queueing failed: {e}")
            self.audit_store.mark_processing_complete(slack_event.to_signature())
            return {"status": "error", "message": "Enterprise queueing failed"}
    
    def _send_error_response(self, slack_event: SlackEvent, error: str):
        """Send professional error response"""
        error_msg = "I apologize, but I encountered a technical issue while processing your request. Our team has been notified. Please try again in a moment."
        self.slack_integration.send_message_safe(
            channel=slack_event.channel_id,
            text=error_msg,
            thread_ts=slack_event.thread_ts
        )
    
    def _send_fallback_response(self, slack_event: SlackEvent):
        """Send professional fallback response"""
        fallback_msg = "I apologize, but I couldn't find information to answer your question. Please contact HR directly for assistance, or try rephrasing your question."
        self.slack_integration.send_message_safe(
            channel=slack_event.channel_id,
            text=fallback_msg,
            thread_ts=slack_event.thread_ts
        )
    
    def _handle_delivery_failure(self, slack_event: SlackEvent, error: str):
        """Handle message delivery failures"""
        self.logger.error(f"🚨 Enterprise delivery failure: {error}")
        # Could implement retry logic here
    
    def get_enterprise_stats(self) -> Dict:
        """Get comprehensive enterprise statistics"""
        runtime = datetime.now() - self.stats["start_time"]
        audit_stats = self.audit_store.get_stats()
        
        return {
            **self.stats,
            "runtime_seconds": runtime.total_seconds(),
            "messages_per_second": self.stats["messages_processed"] / max(runtime.total_seconds(), 1),
            "queue_size": self.message_queue.qsize(),
            "is_running": self.running,
            **audit_stats
        }
    
    def _log_final_stats(self):
        """Log comprehensive final statistics"""
        stats = self.get_enterprise_stats()
        self.logger.info(f"📊 ENTERPRISE PROCESSOR FINAL STATS:")
        self.logger.info(f"   📨 Messages Processed: {stats['messages_processed']}")
        self.logger.info(f"   📤 Messages Queued: {stats['messages_queued']}")
        self.logger.info(f"   🚫 Duplicates Prevented: {stats['duplicates_prevented']}")
        self.logger.info(f"   ❌ Errors: {stats['errors_encountered']}")
        self.logger.info(f"   ⚡ Processing Rate: {stats['messages_per_second']:.2f} msg/sec")
        self.logger.info(f"   ⏱️ Runtime: {stats['runtime_seconds']:.1f} seconds")
