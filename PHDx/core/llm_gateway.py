"""
LLM Gateway - Triad Strategy Model Routing

Strictly typed model routing system implementing the Triad Strategy for optimal
task-based LLM selection. Each tier is purpose-built for specific use cases.

Tiers:
    - TIER_LOGIC (Red Thread): Claude-3.5-Sonnet - High reasoning, argument analysis
    - TIER_CREATIVE (DNA/Style): GPT-4o - Tone mimicry, style editing, creative tasks
    - TIER_SPEED (Airlock/Sanitize): Claude-3-Haiku or GPT-4o-mini - Fast, cheap, PII handling

All responses are parsed into Pydantic models for type safety and frontend stability.
"""

import json
import logging
import os
import toml
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, ValidationError

# Set up logging
logger = logging.getLogger(__name__)

# Optional Langchain imports for backward compatibility
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    _langchain_available = True
except ImportError:
    _langchain_available = False

# Native SDK imports
try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False

try:
    import openai
    _openai_available = True
except ImportError:
    _openai_available = False


# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent / 'config'
STREAMLIT_DIR = Path(__file__).parent.parent / '.streamlit'
SECRETS_PATH = CONFIG_DIR / 'secrets.toml'
STREAMLIT_SECRETS_PATH = STREAMLIT_DIR / 'secrets.toml'

# Token threshold for context considerations
HEAVY_LIFT_THRESHOLD = 30000


# =============================================================================
# Tier Definitions
# =============================================================================

class ModelTier(str, Enum):
    """
    Model tiers for the Triad Strategy routing system.

    Each tier is optimized for specific task types:
        - LOGIC: Deep reasoning, argument construction (Red Thread Engine)
        - CREATIVE: Tone mimicry, style editing (DNA/Style Engine)
        - SPEED: Fast sanitization, PII handling (Airlock Engine)
    """
    LOGIC = "logic"
    CREATIVE = "creative"
    SPEED = "speed"


class EngineType(str, Enum):
    """
    Engine types that map to model tiers.

    Used for strict routing based on the requesting engine.
    """
    RED_THREAD = "red_thread"
    DNA = "dna"
    STYLE = "style"
    AIRLOCK = "airlock"
    SANITIZE = "sanitize"
    AUDIT = "audit"
    GENERIC = "generic"


# Engine to Tier mapping
ENGINE_TIER_MAP: dict[EngineType, ModelTier] = {
    EngineType.RED_THREAD: ModelTier.LOGIC,
    EngineType.DNA: ModelTier.CREATIVE,
    EngineType.STYLE: ModelTier.CREATIVE,
    EngineType.AIRLOCK: ModelTier.SPEED,
    EngineType.SANITIZE: ModelTier.SPEED,
    EngineType.AUDIT: ModelTier.LOGIC,
    EngineType.GENERIC: ModelTier.LOGIC,
}


# =============================================================================
# Pydantic Response Models
# =============================================================================

class LLMResponse(BaseModel):
    """Base response model for all LLM responses."""
    content: str = Field(..., description="The generated text content")
    model_used: str = Field(..., description="The model that generated the response")
    tier: str = Field(..., description="The tier used for generation")
    tokens_estimated: int = Field(default=0, description="Estimated input tokens")
    fallback_used: bool = Field(default=False, description="Whether a fallback model was used")

    class Config:
        extra = "forbid"


class StructuredResponse(BaseModel):
    """Response model for structured/JSON outputs."""
    content: str = Field(..., description="The generated text content")
    model_used: str = Field(..., description="The model that generated the response")
    tier: str = Field(..., description="The tier used for generation")
    tokens_estimated: int = Field(default=0, description="Estimated input tokens")
    fallback_used: bool = Field(default=False, description="Whether a fallback model was used")
    parsed_data: Optional[dict[str, Any]] = Field(default=None, description="Parsed JSON data if applicable")

    class Config:
        extra = "forbid"


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    model_attempted: str = Field(..., description="Model that was attempted")
    tier: str = Field(..., description="Tier that was requested")
    fallback_attempted: bool = Field(default=False, description="Whether fallback was attempted")

    class Config:
        extra = "forbid"


# =============================================================================
# Model Configuration
# =============================================================================

class TierModelConfig(BaseModel):
    """Configuration for a specific model within a tier."""
    provider: str = Field(..., description="Model provider (anthropic, openai)")
    model_id: str = Field(..., description="Full model identifier")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: int = Field(default=4096, description="Maximum output tokens")


# Default model configurations for each tier
DEFAULT_TIER_CONFIGS: dict[ModelTier, TierModelConfig] = {
    ModelTier.LOGIC: TierModelConfig(
        provider="anthropic",
        model_id="claude-3-5-sonnet-20240620",
        temperature=0.5,
        max_tokens=8192,
    ),
    ModelTier.CREATIVE: TierModelConfig(
        provider="openai",
        model_id="gpt-4o",
        temperature=0.7,
        max_tokens=4096,
    ),
    ModelTier.SPEED: TierModelConfig(
        provider="anthropic",
        model_id="claude-3-haiku-20240307",
        temperature=0.3,
        max_tokens=2048,
    ),
}

# Fallback configurations
FALLBACK_CONFIGS: dict[ModelTier, TierModelConfig] = {
    ModelTier.LOGIC: TierModelConfig(
        provider="openai",
        model_id="gpt-4o",
        temperature=0.5,
        max_tokens=8192,
    ),
    ModelTier.CREATIVE: TierModelConfig(
        provider="anthropic",
        model_id="claude-3-5-sonnet-20240620",
        temperature=0.7,
        max_tokens=4096,
    ),
    ModelTier.SPEED: TierModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        temperature=0.3,
        max_tokens=2048,
    ),
}


# =============================================================================
# Secrets Management
# =============================================================================

def _find_secrets_file() -> Path:
    """Find the secrets file from supported locations."""
    if SECRETS_PATH.exists():
        return SECRETS_PATH
    if STREAMLIT_SECRETS_PATH.exists():
        return STREAMLIT_SECRETS_PATH
    return SECRETS_PATH


def _load_api_keys() -> dict[str, str]:
    """
    Load API keys from secrets file or environment variables.

    Returns:
        Dictionary with 'anthropic' and 'openai' API keys.
    """
    keys = {
        'anthropic': os.environ.get('ANTHROPIC_API_KEY', ''),
        'openai': os.environ.get('OPENAI_API_KEY', ''),
    }

    secrets_file = _find_secrets_file()
    if secrets_file.exists():
        try:
            config = toml.load(secrets_file)
            if 'anthropic' in config:
                keys['anthropic'] = config['anthropic'].get('api_key', keys['anthropic'])
            if 'openai' in config:
                keys['openai'] = config['openai'].get('api_key', keys['openai'])
        except Exception as e:
            logger.warning(f"Failed to load secrets file: {e}")

    return keys


# =============================================================================
# Model Router Class
# =============================================================================

class ModelRouter:
    """
    Triad Strategy Model Router.

    Routes requests to the appropriate model tier based on the requesting engine.
    Implements automatic fallback when primary models fail.

    Usage:
        router = ModelRouter()
        response = router.generate(
            prompt="Analyze this argument...",
            engine=EngineType.RED_THREAD,  # Routes to TIER_LOGIC
        )
    """

    def __init__(self, custom_configs: Optional[dict[ModelTier, TierModelConfig]] = None):
        """
        Initialize the Model Router.

        Args:
            custom_configs: Optional custom tier configurations to override defaults.
        """
        self._api_keys = _load_api_keys()
        self._tier_configs = custom_configs or DEFAULT_TIER_CONFIGS.copy()
        self._clients: dict[str, Any] = {}
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize API clients for each provider."""
        if _anthropic_available and self._api_keys.get('anthropic'):
            self._clients['anthropic'] = anthropic.Anthropic(
                api_key=self._api_keys['anthropic']
            )

        if _openai_available and self._api_keys.get('openai'):
            self._clients['openai'] = openai.OpenAI(
                api_key=self._api_keys['openai']
            )

    def _get_tier_for_engine(self, engine: Union[EngineType, str]) -> ModelTier:
        """
        Map an engine type to its corresponding tier.

        Args:
            engine: The engine requesting generation.

        Returns:
            The appropriate ModelTier for the engine.
        """
        if isinstance(engine, str):
            engine = engine.lower().strip()
            # Map string to EngineType
            engine_map = {
                'red_thread': EngineType.RED_THREAD,
                'redthread': EngineType.RED_THREAD,
                'dna': EngineType.DNA,
                'style': EngineType.STYLE,
                'airlock': EngineType.AIRLOCK,
                'sanitize': EngineType.SANITIZE,
                'audit': EngineType.AUDIT,
                # Legacy task type mappings
                'drafting': EngineType.DNA,
                'synthesis': EngineType.RED_THREAD,
                'writing': EngineType.DNA,
                'critique': EngineType.AUDIT,
                'review': EngineType.AUDIT,
                'check': EngineType.AIRLOCK,
            }
            engine = engine_map.get(engine, EngineType.GENERIC)

        return ENGINE_TIER_MAP.get(engine, ModelTier.LOGIC)

    def _call_anthropic(
        self,
        config: TierModelConfig,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Call Anthropic API with the given configuration.

        Args:
            config: Model configuration.
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt.

        Returns:
            Generated content string.
        """
        client = self._clients.get('anthropic')
        if not client:
            raise RuntimeError("Anthropic client not initialized. Check API key.")

        kwargs = {
            'model': config.model_id,
            'max_tokens': config.max_tokens,
            'temperature': config.temperature,
            'messages': messages,
        }

        if system_prompt:
            kwargs['system'] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text

    def _call_openai(
        self,
        config: TierModelConfig,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Call OpenAI API with the given configuration.

        Args:
            config: Model configuration.
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt.

        Returns:
            Generated content string.
        """
        client = self._clients.get('openai')
        if not client:
            raise RuntimeError("OpenAI client not initialized. Check API key.")

        full_messages = []
        if system_prompt:
            full_messages.append({'role': 'system', 'content': system_prompt})
        full_messages.extend(messages)

        response = client.chat.completions.create(
            model=config.model_id,
            messages=full_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        return response.choices[0].message.content

    def _call_model(
        self,
        config: TierModelConfig,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Call the appropriate model based on configuration.

        Args:
            config: Model configuration specifying provider and model.
            messages: List of message dicts.
            system_prompt: Optional system prompt.

        Returns:
            Generated content string.
        """
        if config.provider == 'anthropic':
            return self._call_anthropic(config, messages, system_prompt)
        elif config.provider == 'openai':
            return self._call_openai(config, messages, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def generate(
        self,
        prompt: str,
        engine: Union[EngineType, str] = EngineType.GENERIC,
        context_text: str = "",
        system_prompt: Optional[str] = None,
        force_tier: Optional[ModelTier] = None,
        enable_fallback: bool = True,
    ) -> LLMResponse:
        """
        Generate content using the appropriate tier based on engine type.

        Args:
            prompt: The main prompt/question to send.
            engine: The engine requesting generation (determines tier).
            context_text: Optional context to include.
            system_prompt: Optional system message.
            force_tier: Optional tier to force (overrides engine-based routing).
            enable_fallback: Whether to attempt fallback on failure.

        Returns:
            LLMResponse with generated content and metadata.
        """
        # Determine tier
        tier = force_tier or self._get_tier_for_engine(engine)
        config = self._tier_configs.get(tier, DEFAULT_TIER_CONFIGS[ModelTier.LOGIC])

        # Build message content
        if context_text:
            full_content = f"{prompt}\n\n---\n\nContext:\n{context_text}"
        else:
            full_content = prompt

        messages = [{'role': 'user', 'content': full_content}]
        token_estimate = len(full_content) // 4

        # Primary attempt
        fallback_used = False
        model_used = f"{config.provider}:{config.model_id}"

        try:
            content = self._call_model(config, messages, system_prompt)
        except Exception as primary_error:
            logger.warning(f"Primary model failed ({model_used}): {primary_error}")

            if not enable_fallback:
                raise

            # Attempt fallback
            fallback_config = FALLBACK_CONFIGS.get(tier)
            if fallback_config:
                try:
                    logger.info(f"Attempting fallback to {fallback_config.provider}:{fallback_config.model_id}")
                    content = self._call_model(fallback_config, messages, system_prompt)
                    fallback_used = True
                    model_used = f"{fallback_config.provider}:{fallback_config.model_id}"
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise RuntimeError(
                        f"Both primary ({config.model_id}) and fallback ({fallback_config.model_id}) failed"
                    ) from fallback_error
            else:
                raise

        return LLMResponse(
            content=content,
            model_used=model_used,
            tier=tier.value,
            tokens_estimated=token_estimate,
            fallback_used=fallback_used,
        )

    def generate_structured(
        self,
        prompt: str,
        engine: Union[EngineType, str] = EngineType.GENERIC,
        context_text: str = "",
        system_prompt: Optional[str] = None,
        response_schema: Optional[type[BaseModel]] = None,
    ) -> StructuredResponse:
        """
        Generate structured JSON content with optional schema validation.

        Args:
            prompt: The main prompt.
            engine: The engine requesting generation.
            context_text: Optional context.
            system_prompt: Optional system message.
            response_schema: Optional Pydantic model for response validation.

        Returns:
            StructuredResponse with content and parsed data.
        """
        # Modify prompt to request JSON output
        json_instruction = "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no explanation."
        modified_prompt = prompt + json_instruction

        response = self.generate(
            prompt=modified_prompt,
            engine=engine,
            context_text=context_text,
            system_prompt=system_prompt,
        )

        # Attempt to parse JSON
        parsed_data = None
        try:
            # Clean potential markdown wrapper
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            parsed_data = json.loads(content)

            # Validate against schema if provided
            if response_schema:
                validated = response_schema.model_validate(parsed_data)
                parsed_data = validated.model_dump()

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse structured response: {e}")

        return StructuredResponse(
            content=response.content,
            model_used=response.model_used,
            tier=response.tier,
            tokens_estimated=response.tokens_estimated,
            fallback_used=response.fallback_used,
            parsed_data=parsed_data,
        )

    def get_available_tiers(self) -> list[str]:
        """Return list of tiers with configured API keys."""
        available = []
        for tier, config in self._tier_configs.items():
            if config.provider in self._clients:
                available.append(tier.value)
        return available


# =============================================================================
# Global Router Instance
# =============================================================================

_router_instance: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Get or create the global ModelRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance


def reset_router() -> None:
    """Reset the global router instance (useful for testing)."""
    global _router_instance
    _router_instance = None


# =============================================================================
# Backward Compatibility Layer
# =============================================================================

# Legacy cached models
_models_cache: Optional[dict] = None


def init_models() -> dict:
    """
    Initialize LLM models (backward compatibility).

    Returns:
        Dictionary with legacy model keys.
    """
    global _models_cache

    if _models_cache is not None:
        return _models_cache

    if not _langchain_available:
        raise ImportError("LangChain not available for legacy model initialization")

    api_keys = _load_api_keys()

    # Initialize models using LangChain for backward compatibility
    writer_model = ChatAnthropic(
        api_key=api_keys.get('anthropic'),
        model='claude-3-5-sonnet-20240620',
        temperature=0.7,
        max_tokens=4096,
    ) if api_keys.get('anthropic') else None

    auditor_model = ChatOpenAI(
        api_key=api_keys.get('openai'),
        model='gpt-4o',
        temperature=0.3,
        max_tokens=4096,
    ) if api_keys.get('openai') else None

    _models_cache = {
        'writer': writer_model,
        'auditor': auditor_model,
        'context': None,  # Deprecated - use TIER_LOGIC for large context
    }

    return _models_cache


def estimate_tokens(text: str) -> int:
    """Estimate token count (approximately 4 chars per token)."""
    return len(text) // 4


def generate_content(
    prompt: str,
    task_type: str,
    context_text: str = "",
    system_prompt: Optional[str] = None,
) -> dict:
    """
    Generate content using Triad Strategy routing (backward compatible).

    This function maintains backward compatibility while using the new
    ModelRouter under the hood.

    Args:
        prompt: The main prompt/question.
        task_type: Type of task (maps to engine type).
        context_text: Optional context.
        system_prompt: Optional system message.

    Returns:
        Dictionary with 'content', 'model_used', and 'tokens_estimated'.
    """
    router = get_router()

    try:
        response = router.generate(
            prompt=prompt,
            engine=task_type,  # Router handles string mapping
            context_text=context_text,
            system_prompt=system_prompt,
        )

        return {
            'content': response.content,
            'model_used': response.model_used,
            'tokens_estimated': response.tokens_estimated,
        }
    except Exception as e:
        return {
            'content': f"Error generating content: {str(e)}",
            'model_used': 'error',
            'tokens_estimated': estimate_tokens(prompt + context_text),
        }


def _route_task(task_type: str, token_count: int, models: dict = None) -> str:
    """
    Determine which model to use (backward compatibility).

    Now delegates to ModelRouter's tier mapping.
    """
    router = get_router()
    tier = router._get_tier_for_engine(task_type)

    # Map tier to legacy model keys
    tier_to_key = {
        ModelTier.LOGIC: 'writer',
        ModelTier.CREATIVE: 'auditor',
        ModelTier.SPEED: 'writer',
    }
    return tier_to_key.get(tier, 'writer')


def get_writer_model():
    """Get the Claude writer model (legacy)."""
    return init_models().get('writer')


def get_auditor_model():
    """Get the GPT auditor model (legacy)."""
    return init_models().get('auditor')


def get_context_model():
    """Get the context model (deprecated)."""
    return init_models().get('context')


def clear_model_cache():
    """Clear cached model instances."""
    global _models_cache
    _models_cache = None
    reset_router()


def get_available_models() -> list[str]:
    """Return list of available model keys."""
    models = init_models()
    return [k for k, v in models.items() if v is not None]
