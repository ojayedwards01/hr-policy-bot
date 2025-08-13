"""
Configuration Management
=======================

Centralized configuration system for the enterprise HR Bot.
Handles environment variables, settings validation, and runtime configuration.

Author: Enterprise HR Bot Team
Version: 2.0.0
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "groq"
    model_name: str = "llama-3.1-70b-versatile"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_day: int = 1000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class EmbeddingsConfig:
    """Embeddings configuration"""
    provider: str = "huggingface"
    # OPTIMIZED: Using lighter embedding model for Docker size reduction
    # ORIGINAL: model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"  # Still using same model but optimized
    device: str = "cpu"
    batch_size: int = 32
    max_length: int = 512
    
    # Caching
    cache_embeddings: bool = True
    cache_directory: Optional[str] = None


@dataclass
class VectorStoreConfig:
    """Vector store configuration"""
    provider: str = "faiss"
    index_type: str = "flat"
    similarity_metric: str = "cosine"
    
    # FAISS specific
    faiss_index_path: str = "vectorstore/faiss_index"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Performance
    search_top_k: int = 10
    rerank_top_k: int = 5
    similarity_threshold: float = 0.7


@dataclass
class SecurityConfig:
    """Security configuration"""
    # API Security
    require_api_key: bool = False
    api_keys: List[str] = field(default_factory=list)
    
    # Rate limiting
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Content filtering
    enable_content_filter: bool = True
    blocked_keywords: List[str] = field(default_factory=list)
    
    # Data privacy
    log_user_queries: bool = False
    anonymize_logs: bool = True
    data_retention_days: int = 30


@dataclass
class WebConfig:
    """Web interface configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_credentials: bool = True
    
    # SSL
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    
    # Static files
    static_directory: str = "static"
    template_directory: str = "templates"


@dataclass
class SlackConfig:
    """Slack integration configuration"""
    enabled: bool = False
    bot_token: Optional[str] = None
    signing_secret: Optional[str] = None
    app_token: Optional[str] = None
    
    # Features
    enable_dm: bool = True
    enable_mentions: bool = True
    use_threads: bool = True
    
    # Formatting
    max_message_length: int = 3000
    show_sources: bool = True
    include_metadata: bool = False


@dataclass
class EmailConfig:
    """Email integration configuration"""
    enabled: bool = False
    
    # SMTP settings
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # Email settings
    from_address: Optional[str] = None
    from_name: str = "HR Assistant"
    
    # Features
    auto_reply_enabled: bool = False
    include_sources: bool = True
    max_response_length: int = 5000


@dataclass
class DatabaseConfig:
    """Database configuration"""
    provider: str = "sqlite"
    url: Optional[str] = None
    
    # Connection settings
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    
    # SQLite specific
    sqlite_path: str = "data/hrbot.db"
    
    # Session storage
    session_table: str = "user_sessions"
    conversation_table: str = "conversations"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File logging
    log_to_file: bool = True
    log_file: str = "logs/hrbot.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    
    # Component-specific levels
    component_levels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    enabled: bool = True
    
    # Metrics collection
    collect_metrics: bool = True
    metrics_interval: int = 60  # seconds
    
    # Health checks
    health_check_interval: int = 30  # seconds
    
    # Performance tracking
    track_response_times: bool = True
    track_token_usage: bool = True
    track_error_rates: bool = True
    
    # Alerting
    enable_alerts: bool = False
    alert_threshold_error_rate: float = 0.1
    alert_threshold_response_time: float = 10.0  # seconds


@dataclass
class EnterpriseConfig:
    """Main enterprise configuration"""
    # Environment
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    debug: bool = False
    
    # Component configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    vectorstore: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    web: WebConfig = field(default_factory=WebConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Data paths
    documents_directory: str = "documents"
    vectorstore_directory: str = "vectorstore"
    logs_directory: str = "logs"
    cache_directory: str = "cache"
    
    # System settings
    max_concurrent_requests: int = 10
    request_timeout: int = 60
    
    # Feature flags
    enable_memory_management: bool = True
    enable_hallucination_guard: bool = True
    enable_response_caching: bool = True
    enable_usage_analytics: bool = True


class ConfigurationManager:
    """
    Centralized configuration management system.
    
    Features:
    - Environment variable loading
    - Configuration validation
    - Runtime configuration updates
    - Default value management
    - Configuration export/import
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = EnterpriseConfig()
        
        # Load configuration
        self._load_from_environment()
        if config_file:
            self._load_from_file(config_file)
        
        # Validate configuration
        self._validate_configuration()
        
        # Setup directories
        self._create_directories()
        
        logger.info(f"Configuration loaded for {self.config.environment} environment")

    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Environment type
        env_type = os.getenv('HR_BOT_ENVIRONMENT', 'development').lower()
        try:
            self.config.environment = EnvironmentType(env_type)
        except ValueError:
            logger.warning(f"Invalid environment type: {env_type}, using development")
            self.config.environment = EnvironmentType.DEVELOPMENT
        
        # Debug mode
        self.config.debug = os.getenv('HR_BOT_DEBUG', 'false').lower() == 'true'
        
        # LLM Configuration
        if groq_key := os.getenv('GROQ_API_KEY'):
            self.config.llm.api_key = groq_key
        
        self.config.llm.model_name = os.getenv('LLM_MODEL_NAME', self.config.llm.model_name)
        self.config.llm.temperature = float(os.getenv('LLM_TEMPERATURE', self.config.llm.temperature))
        self.config.llm.max_tokens = int(os.getenv('LLM_MAX_TOKENS', self.config.llm.max_tokens))
        
        # Embeddings Configuration
        self.config.embeddings.model_name = os.getenv('EMBEDDINGS_MODEL', self.config.embeddings.model_name)
        self.config.embeddings.device = os.getenv('EMBEDDINGS_DEVICE', self.config.embeddings.device)
        
        # Vector Store Configuration
        self.config.vectorstore.faiss_index_path = os.getenv('VECTORSTORE_PATH', './src/store')
        self.config.vectorstore.chunk_size = int(os.getenv('CHUNK_SIZE', self.config.vectorstore.chunk_size))
        self.config.vectorstore.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', self.config.vectorstore.chunk_overlap))
        
        # Web Configuration
        self.config.web.host = os.getenv('WEB_HOST', self.config.web.host)
        self.config.web.port = int(os.getenv('WEB_PORT', self.config.web.port))
        self.config.web.debug = os.getenv('WEB_DEBUG', str(self.config.web.debug)).lower() == 'true'
        
        # Slack Configuration
        if slack_token := os.getenv('SLACK_BOT_TOKEN'):
            self.config.slack.enabled = True
            self.config.slack.bot_token = slack_token
        
        if slack_secret := os.getenv('SLACK_SIGNING_SECRET'):
            self.config.slack.signing_secret = slack_secret
        
        # Email Configuration
        if smtp_server := os.getenv('SMTP_SERVER'):
            self.config.email.enabled = True
            self.config.email.smtp_server = smtp_server
            self.config.email.smtp_username = os.getenv('SMTP_USERNAME')
            self.config.email.smtp_password = os.getenv('SMTP_PASSWORD')
            self.config.email.from_address = os.getenv('FROM_EMAIL_ADDRESS')
        
        # Security Configuration
        api_keys = os.getenv('API_KEYS', '').strip()
        if api_keys:
            self.config.security.api_keys = [key.strip() for key in api_keys.split(',')]
            self.config.security.require_api_key = True
        
        # Database Configuration
        if db_url := os.getenv('DATABASE_URL'):
            self.config.database.url = db_url
            if 'postgresql' in db_url:
                self.config.database.provider = 'postgresql'
            elif 'mysql' in db_url:
                self.config.database.provider = 'mysql'
        
        # Logging Configuration
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        try:
            self.config.logging.level = LogLevel(log_level)
        except ValueError:
            logger.warning(f"Invalid log level: {log_level}, using INFO")
            self.config.logging.level = LogLevel.INFO
        
        # Data directories
        self.config.documents_directory = os.getenv('DOCUMENTS_DIR', self.config.documents_directory)
        self.config.vectorstore_directory = os.getenv('VECTORSTORE_DIR', self.config.vectorstore_directory)
        self.config.logs_directory = os.getenv('LOGS_DIR', self.config.logs_directory)

    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration with file data
                self._update_config_from_dict(config_data)
                logger.info(f"📄 Configuration loaded from {config_file}")
            else:
                logger.warning(f"Configuration file not found: {config_file}")
                
        except Exception as e:
            logger.error(f"❌ Error loading configuration file: {e}")

    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in config_data.items():
            if hasattr(self.config, key):
                if isinstance(value, dict):
                    # Handle nested configuration objects
                    nested_config = getattr(self.config, key)
                    for nested_key, nested_value in value.items():
                        if hasattr(nested_config, nested_key):
                            setattr(nested_config, nested_key, nested_value)
                else:
                    setattr(self.config, key, value)

    def _validate_configuration(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate LLM configuration
        if not self.config.llm.api_key:
            errors.append("LLM API key is required (set GROQ_API_KEY)")
        
        if self.config.llm.temperature < 0 or self.config.llm.temperature > 2:
            errors.append("LLM temperature must be between 0 and 2")
        
        # Validate Slack configuration
        if self.config.slack.enabled:
            if not self.config.slack.bot_token:
                errors.append("Slack bot token is required when Slack is enabled")
            if not self.config.slack.signing_secret:
                errors.append("Slack signing secret is required when Slack is enabled")
        
        # Validate Email configuration
        if self.config.email.enabled:
            if not self.config.email.smtp_server:
                errors.append("SMTP server is required when email is enabled")
            if not self.config.email.from_address:
                errors.append("From email address is required when email is enabled")
        
        # Validate paths
        if not os.path.exists(self.config.documents_directory):
            logger.warning(f"Documents directory does not exist: {self.config.documents_directory}")
        
        if errors:
            error_msg = "Configuration validation errors:\n" + "\n".join(f"- {error}" for error in errors)
            if self.config.environment == EnvironmentType.PRODUCTION:
                raise ValueError(error_msg)
            else:
                logger.warning(f"⚠️ Configuration warnings:\n{error_msg}")

    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.config.vectorstore_directory,
            self.config.logs_directory,
            self.config.cache_directory
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def get_config(self) -> EnterpriseConfig:
        """Get the current configuration"""
        return self.config

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration at runtime"""
        try:
            self._update_config_from_dict(updates)
            self._validate_configuration()
            logger.info("🔄 Configuration updated successfully")
        except Exception as e:
            logger.error(f"❌ Failed to update configuration: {e}")
            raise

    def save_config(self, file_path: Optional[str] = None):
        """Save current configuration to file"""
        try:
            output_path = file_path or self.config_file or "config.json"
            
            # Convert configuration to dictionary
            config_dict = asdict(self.config)
            
            # Convert enums to strings
            config_dict['environment'] = config_dict['environment'].value
            config_dict['logging']['level'] = config_dict['logging']['level'].value
            
            with open(output_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"💾 Configuration saved to {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            raise

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            'environment': self.config.environment.value,
            'debug': self.config.debug,
            'python_version': os.sys.version,
            'platform': os.name,
            'working_directory': os.getcwd(),
            'config_file': self.config_file,
            'features_enabled': {
                'slack': self.config.slack.enabled,
                'email': self.config.email.enabled,
                'memory_management': self.config.enable_memory_management,
                'hallucination_guard': self.config.enable_hallucination_guard,
                'response_caching': self.config.enable_response_caching
            }
        }

    def get_component_config(self, component: str) -> Any:
        """Get configuration for specific component"""
        if hasattr(self.config, component):
            return getattr(self.config, component)
        else:
            raise ValueError(f"Unknown component: {component}")

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config.environment == EnvironmentType.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.config.environment == EnvironmentType.DEVELOPMENT


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigurationManager:
    """Get or create global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_file)
    return _config_manager


def get_config() -> EnterpriseConfig:
    """Get current configuration"""
    return get_config_manager().get_config()
