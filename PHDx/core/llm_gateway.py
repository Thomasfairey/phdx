"""
LLM Gateway - Intelligence Layer

Multi-model routing system for the PhD writing assistant. Automatically
selects the optimal LLM based on task type and context size to maximize
quality while avoiding token limit issues.

Models:
    - Writer (Claude): Best prose style for drafting and synthesis
    - Auditor (GPT): Strict logic checking for audits and critiques
    - Context (Gemini): Large context window for heavy lifting tasks
"""

import toml
from pathlib import Path
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Optional Gemini support - try Google GenAI first, fall back gracefully
_gemini_available = False
_ChatGoogleGenerativeAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    _ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
    _gemini_available = True
except ImportError:
    pass


# Configuration paths (check multiple locations)
CONFIG_DIR = Path(__file__).parent.parent / 'config'
STREAMLIT_DIR = Path(__file__).parent.parent / '.streamlit'
SECRETS_PATH = CONFIG_DIR / 'secrets.toml'
STREAMLIT_SECRETS_PATH = STREAMLIT_DIR / 'secrets.toml'


def _find_secrets_file() -> Path:
    """Find the secrets file from supported locations."""
    if SECRETS_PATH.exists():
        return SECRETS_PATH
    if STREAMLIT_SECRETS_PATH.exists():
        return STREAMLIT_SECRETS_PATH
    return SECRETS_PATH  # Return default for error messages

# Token threshold for forcing context model
HEAVY_LIFT_THRESHOLD = 30000

# Cached models
_models_cache: Optional[dict] = None


def init_models() -> dict:
    """
    Initialize LLM models from configuration.

    Loads API keys and model names from config/secrets.toml and creates
    three distinct model instances for different task types.

    Returns:
        Dictionary containing:
            - 'writer': ChatAnthropic (Claude) for drafting
            - 'auditor': ChatOpenAI (GPT) for auditing
            - 'context': ChatGoogleGenerativeAI (Gemini) for large context tasks

    Raises:
        FileNotFoundError: If secrets.toml is not found.
    """
    global _models_cache

    if _models_cache is not None:
        return _models_cache

    secrets_file = _find_secrets_file()
    if not secrets_file.exists():
        raise FileNotFoundError(
            f"Secrets file not found. Checked:\n"
            f"  - {SECRETS_PATH}\n"
            f"  - {STREAMLIT_SECRETS_PATH}\n"
            "Please create config/secrets.toml with your API keys."
        )

    # Load configuration
    config = toml.load(secrets_file)

    # Extract API keys and model names
    anthropic_config = config.get('anthropic', {})
    openai_config = config.get('openai', {})
    google_config = config.get('google', {})

    # Initialize Writer Model (Claude)
    writer_model = ChatAnthropic(
        api_key=anthropic_config.get('api_key'),
        model=anthropic_config.get('model', 'claude-sonnet-4-20250514'),
        temperature=0.7,
        max_tokens=4096,
    )

    # Initialize Auditor Model (GPT)
    auditor_model = ChatOpenAI(
        api_key=openai_config.get('api_key'),
        model=openai_config.get('model', 'gpt-4o'),
        temperature=0.3,
        max_tokens=4096,
    )

    # Initialize Context Model (Gemini) - optional
    context_model = None
    if _gemini_available and google_config.get('api_key'):
        context_model = _ChatGoogleGenerativeAI(
            google_api_key=google_config.get('api_key'),
            model=google_config.get('model', 'gemini-1.5-pro'),
            temperature=0.5,
            max_tokens=8192,
        )

    _models_cache = {
        'writer': writer_model,
        'auditor': auditor_model,
        'context': context_model,
    }

    return _models_cache


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.

    Uses a rough approximation of 4 characters per token.

    Args:
        text: Input text to estimate.

    Returns:
        Estimated token count.
    """
    return len(text) // 4


def generate_content(
    prompt: str,
    task_type: str,
    context_text: str = "",
    system_prompt: Optional[str] = None,
) -> dict:
    """
    Generate content using smart model routing.

    Automatically selects the optimal model based on task type and context size:
        - Heavy Lift (>30k tokens): Forces Gemini regardless of task
        - Drafting/Synthesis: Uses Claude for best prose style
        - Audit/Critique: Uses GPT for strict logic checking

    Args:
        prompt: The main prompt/question to send.
        task_type: Type of task ('drafting', 'synthesis', 'audit', 'critique').
        context_text: Optional context to include (e.g., document content).
        system_prompt: Optional system message to set model behavior.

    Returns:
        Dictionary with:
            - 'content': Generated text response
            - 'model_used': Name of the model that was used
            - 'tokens_estimated': Estimated input token count
    """
    models = init_models()

    # Estimate total tokens
    total_text = prompt + context_text
    token_estimate = estimate_tokens(total_text)

    # Smart routing logic
    model_key = _route_task(task_type, token_estimate, models)
    model = models[model_key]

    # Build messages
    messages = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    # Combine prompt and context
    if context_text:
        full_prompt = f"{prompt}\n\n---\n\nContext:\n{context_text}"
    else:
        full_prompt = prompt

    messages.append(HumanMessage(content=full_prompt))

    # Generate response
    try:
        response = model.invoke(messages)
        content = response.content
    except Exception as e:
        # Fallback error handling
        content = f"Error generating content: {str(e)}"

    # Map model keys to friendly names
    model_names = {
        'writer': 'Claude (Writer)',
        'auditor': 'GPT (Auditor)',
        'context': 'Gemini (Context)',
    }

    return {
        'content': content,
        'model_used': model_names.get(model_key, model_key),
        'tokens_estimated': token_estimate,
    }


def _route_task(task_type: str, token_count: int, models: dict = None) -> str:
    """
    Determine which model to use based on routing rules.

    Rules (in priority order):
        A. Heavy Lift: If tokens > 30,000, force context model
        B. Drafting: If task is drafting/synthesis, use writer model
        C. Auditing: If task is audit/critique, use auditor model

    Args:
        task_type: The type of task being performed.
        token_count: Estimated token count for the request.
        models: Optional models dict to check availability.

    Returns:
        Model key: 'writer', 'auditor', or 'context'.
    """
    task_type_lower = task_type.lower().strip()

    # Check if context model is available
    context_available = models is not None and models.get('context') is not None

    # Rule A: Heavy Lift - force context model for large inputs
    if token_count > HEAVY_LIFT_THRESHOLD:
        if context_available:
            return 'context'
        # Fall back to writer if Gemini not available
        return 'writer'

    # Rule B: Drafting tasks - use writer model
    if task_type_lower in ('drafting', 'synthesis', 'writing', 'draft'):
        return 'writer'

    # Rule C: Auditing tasks - use auditor model
    if task_type_lower in ('audit', 'critique', 'review', 'check'):
        return 'auditor'

    # Default to writer for unrecognized task types
    return 'writer'


# Utility functions for direct model access
def get_writer_model():
    """Get the Claude writer model directly."""
    return init_models()['writer']


def get_auditor_model():
    """Get the GPT auditor model directly."""
    return init_models()['auditor']


def get_context_model():
    """Get the Gemini context model directly (may be None if not configured)."""
    return init_models()['context']


def clear_model_cache():
    """Clear the cached model instances."""
    global _models_cache
    _models_cache = None


def get_available_models() -> list[str]:
    """Return list of available model keys."""
    models = init_models()
    return [k for k, v in models.items() if v is not None]
