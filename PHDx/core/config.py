"""
PHDx Configuration Management

Provides environment-aware configuration with validation.
Supports development, staging, and production environments.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


class Environment(Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class CORSConfig:
    """CORS configuration."""
    allowed_origins: List[str] = field(default_factory=list)
    allow_credentials: bool = True
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    allowed_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_minute: int = 60
    burst_size: int = 10


@dataclass
class DatabaseConfig:
    """Vector database configuration."""
    use_pinecone: bool = False
    pinecone_api_key: Optional[str] = None
    pinecone_index: str = "phdx-thesis"
    chroma_persist_dir: str = "data/chroma_db"


@dataclass
class LLMConfig:
    """LLM service configuration."""
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    google_api_key: Optional[str] = None
    google_model: str = "gemini-1.5-pro"
    heavy_lift_threshold: int = 30000


@dataclass
class GoogleConfig:
    """Google API configuration."""
    client_secret_path: str = "config/client_secret.json"
    token_path: str = "config/token.json"
    credentials_path: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Feature flags
    enable_google_auth: bool = True
    enable_spacy_ner: bool = True
    enable_usage_logging: bool = True
    mock_mode: bool = False

    # Sub-configs
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    google: GoogleConfig = field(default_factory=GoogleConfig)

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        env_name = os.getenv("PHDX_ENV", "development").lower()
        environment = Environment(env_name) if env_name in [e.value for e in Environment] else Environment.DEVELOPMENT

        # Determine CORS origins based on environment
        if environment == Environment.PRODUCTION:
            cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
            cors_origins = [o.strip() for o in cors_origins if o.strip()]
            if not cors_origins:
                cors_origins = ["https://phdx.ai", "https://www.phdx.ai"]
        elif environment == Environment.STAGING:
            cors_origins = ["https://staging.phdx.ai", "http://localhost:3000"]
        else:
            cors_origins = ["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:3000"]

        return cls(
            environment=environment,
            debug=environment != Environment.PRODUCTION,
            log_level=os.getenv("LOG_LEVEL", "INFO" if environment == Environment.PRODUCTION else "DEBUG"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            enable_google_auth=os.getenv("ENABLE_GOOGLE_AUTH", "true").lower() == "true",
            enable_spacy_ner=os.getenv("ENABLE_SPACY_NER", "true").lower() == "true",
            enable_usage_logging=os.getenv("ENABLE_USAGE_LOGGING", "true").lower() == "true",
            mock_mode=os.getenv("MOCK_MODE", "false").lower() == "true",
            cors=CORSConfig(
                allowed_origins=cors_origins,
                allow_credentials=True,
            ),
            rate_limit=RateLimitConfig(
                enabled=environment == Environment.PRODUCTION,
                requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
            ),
            database=DatabaseConfig(
                use_pinecone=bool(os.getenv("PINECONE_API_KEY")),
                pinecone_api_key=os.getenv("PINECONE_API_KEY"),
                pinecone_index=os.getenv("PINECONE_INDEX", "phdx-thesis"),
            ),
            llm=LLMConfig(
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                google_model=os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
            ),
            google=GoogleConfig(
                client_secret_path=os.getenv("GOOGLE_CLIENT_SECRET_PATH", "config/client_secret.json"),
                token_path=os.getenv("GOOGLE_TOKEN_PATH", "config/token.json"),
                credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH"),
            ),
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if self.environment == Environment.PRODUCTION:
            if not self.llm.anthropic_api_key:
                issues.append("ANTHROPIC_API_KEY is required in production")
            if not self.cors.allowed_origins:
                issues.append("CORS_ORIGINS must be set in production")
            if self.debug:
                issues.append("DEBUG should be False in production")

        return issues

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig.from_environment()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment."""
    global _config
    _config = AppConfig.from_environment()
    return _config
