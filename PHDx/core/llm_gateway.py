"""
LLM Gateway - Intelligence Layer

Multi-model routing system for the PhD writing assistant. Automatically
selects the optimal LLM based on task type and context size to maximize
quality while avoiding token limit issues.

Models:
    - Opus (Claude Opus 4.5): Best for complex reasoning and prose
    - Writer (Claude Sonnet): Fast drafting and standard tasks
    - Quick (Claude Haiku): Fast, cost-effective for simple tasks
    - Auditor (GPT-4o): Strict logic checking for audits and critiques
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
CONFIG_DIR = Path(__file__).parent.parent / "config"
STREAMLIT_DIR = Path(__file__).parent.parent / ".streamlit"
SECRETS_PATH = CONFIG_DIR / "secrets.toml"
STREAMLIT_SECRETS_PATH = STREAMLIT_DIR / "secrets.toml"


def _find_secrets_file() -> Path:
    """Find the secrets file from supported locations."""
    if SECRETS_PATH.exists():
        return SECRETS_PATH
    if STREAMLIT_SECRETS_PATH.exists():
        return STREAMLIT_SECRETS_PATH
    return SECRETS_PATH  # Return default for error messages


# Token threshold for forcing context model
HEAVY_LIFT_THRESHOLD = 30000

# Task-to-model routing matrix
TASK_MODEL_MAP = {
    # Complex tasks -> Opus (best reasoning)
    "complex_reasoning": "opus",
    "literature_synthesis": "opus",
    "argument_analysis": "opus",
    "deep_analysis": "opus",
    "thesis_structure": "opus",
    # Standard drafting -> Writer (Sonnet - good balance)
    "drafting": "writer",
    "synthesis": "writer",
    "writing": "writer",
    "draft": "writer",
    "expansion": "writer",
    "rewrite": "writer",
    # Quick tasks -> Quick (Haiku - fast, cheap)
    "classification": "quick",
    "citation_match": "quick",
    "outline_generation": "quick",
    "summarization": "quick",
    # Audit tasks -> Auditor (GPT-4o - strict logic)
    "audit": "auditor",
    "critique": "auditor",
    "review": "auditor",
    "check": "auditor",
    "statistical_interpretation": "auditor",
    "logic_check": "auditor",
    # Large context -> Context (Gemini 1M tokens)
    "full_thesis_analysis": "context",
    "bulk_processing": "context",
}

# Cached models
_models_cache: Optional[dict] = None


def init_models() -> dict:
    """
    Initialize LLM models from configuration.

    Loads API keys and model names from config/secrets.toml and creates
    multiple model instances for different task types.

    Returns:
        Dictionary containing:
            - 'opus': ChatAnthropic (Claude Opus 4.5) for complex reasoning
            - 'writer': ChatAnthropic (Claude Sonnet) for drafting
            - 'quick': ChatAnthropic (Claude Haiku) for fast tasks
            - 'auditor': ChatOpenAI (GPT-4o) for auditing
            - 'context': ChatGoogleGenerativeAI (Gemini) for large context

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
    anthropic_config = config.get("anthropic", {})
    openai_config = config.get("openai", {})
    google_config = config.get("google", {})

    # Get Anthropic API key (shared across all Claude models)
    anthropic_api_key = anthropic_config.get("api_key")

    # Initialize Opus Model (Claude Opus 4.5) - Best reasoning & prose
    opus_model = ChatAnthropic(
        api_key=anthropic_api_key,
        model=anthropic_config.get("opus_model", "claude-opus-4-5-20250101"),
        temperature=0.7,
        max_tokens=8192,
    )

    # Initialize Writer Model (Claude Sonnet) - Standard drafting
    writer_model = ChatAnthropic(
        api_key=anthropic_api_key,
        model=anthropic_config.get("writer_model", "claude-sonnet-4-20250514"),
        temperature=0.7,
        max_tokens=4096,
    )

    # Initialize Quick Model (Claude Haiku) - Fast, cost-effective
    quick_model = None
    haiku_model_name = anthropic_config.get("quick_model", "claude-3-5-haiku-20241022")
    if haiku_model_name:
        try:
            quick_model = ChatAnthropic(
                api_key=anthropic_api_key,
                model=haiku_model_name,
                temperature=0.3,
                max_tokens=2048,
            )
        except Exception:
            # Fall back to sonnet if haiku not available
            quick_model = writer_model

    # Initialize Auditor Model (GPT-4o) - Strict logic checking
    auditor_model = ChatOpenAI(
        api_key=openai_config.get("api_key"),
        model=openai_config.get("model", "gpt-4o"),
        temperature=0.3,
        max_tokens=4096,
    )

    # Initialize Context Model (Gemini) - Large context window
    context_model = None
    if _gemini_available and google_config.get("api_key"):
        context_model = _ChatGoogleGenerativeAI(
            google_api_key=google_config.get("api_key"),
            model=google_config.get("model", "gemini-1.5-pro"),
            temperature=0.5,
            max_tokens=8192,
        )

    _models_cache = {
        "opus": opus_model,
        "writer": writer_model,
        "quick": quick_model,
        "auditor": auditor_model,
        "context": context_model,
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
    force_model: Optional[str] = None,
) -> dict:
    """
    Generate content using smart model routing.

    Automatically selects the optimal model based on task type and context size:
        - Heavy Lift (>30k tokens): Forces Gemini regardless of task
        - Complex/Synthesis: Uses Opus for best analytical depth
        - Drafting: Uses Sonnet for good balance of quality/speed
        - Quick tasks: Uses Haiku for fast, cost-effective responses
        - Audit/Critique: Uses GPT-4o for strict logic checking

    Args:
        prompt: The main prompt/question to send.
        task_type: Type of task (see TASK_MODEL_MAP for options).
        context_text: Optional context to include (e.g., document content).
        system_prompt: Optional system message to set model behavior.
        force_model: Optional model key to force specific model.

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

    # Smart routing logic (unless model is forced)
    if force_model and force_model in models:
        model_key = force_model
    else:
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
        "opus": "Claude Opus 4.5 (Complex)",
        "writer": "Claude Sonnet (Writer)",
        "quick": "Claude Haiku (Quick)",
        "auditor": "GPT-4o (Auditor)",
        "context": "Gemini 1.5 Pro (Context)",
    }

    return {
        "content": content,
        "model_used": model_names.get(model_key, model_key),
        "tokens_estimated": token_estimate,
    }


def _route_task(task_type: str, token_count: int, models: dict = None) -> str:
    """
    Determine which model to use based on enhanced routing rules.

    Rules (in priority order):
        A. Heavy Lift: If tokens > 30,000, force context model
        B. Task-specific: Use TASK_MODEL_MAP for explicit task routing
        C. Default: Fall back to writer model

    Args:
        task_type: The type of task being performed.
        token_count: Estimated token count for the request.
        models: Optional models dict to check availability.

    Returns:
        Model key: 'opus', 'writer', 'quick', 'auditor', or 'context'.
    """
    task_type_lower = task_type.lower().strip()

    # Check model availability
    context_available = models is not None and models.get("context") is not None
    opus_available = models is not None and models.get("opus") is not None
    quick_available = models is not None and models.get("quick") is not None

    # Rule A: Heavy Lift - force context model for large inputs
    if token_count > HEAVY_LIFT_THRESHOLD:
        if context_available:
            return "context"
        # Fall back to opus for large contexts if Gemini unavailable
        if opus_available:
            return "opus"
        return "writer"

    # Rule B: Task-specific routing from TASK_MODEL_MAP
    if task_type_lower in TASK_MODEL_MAP:
        preferred = TASK_MODEL_MAP[task_type_lower]

        # Check if preferred model is available
        if preferred == "opus" and opus_available:
            return "opus"
        elif preferred == "quick" and quick_available:
            return "quick"
        elif preferred == "context" and context_available:
            return "context"
        elif preferred in ("writer", "auditor"):
            return preferred

        # Fall back based on task category
        if preferred in ("opus", "writer", "quick"):
            return "writer"  # Fall back to writer for Claude tasks
        elif preferred == "context":
            return "opus" if opus_available else "writer"

    # Rule C: Default to writer for unrecognized task types
    return "writer"


# =============================================================================
# UTILITY FUNCTIONS FOR DIRECT MODEL ACCESS
# =============================================================================


def get_opus_model():
    """Get the Claude Opus 4.5 model directly (best for complex reasoning)."""
    return init_models()["opus"]


def get_writer_model():
    """Get the Claude Sonnet writer model directly."""
    return init_models()["writer"]


def get_quick_model():
    """Get the Claude Haiku quick model directly (may be None)."""
    return init_models()["quick"]


def get_auditor_model():
    """Get the GPT-4o auditor model directly."""
    return init_models()["auditor"]


def get_context_model():
    """Get the Gemini context model directly (may be None if not configured)."""
    return init_models()["context"]


def clear_model_cache():
    """Clear the cached model instances."""
    global _models_cache
    _models_cache = None


def get_available_models() -> list[str]:
    """Return list of available model keys."""
    models = init_models()
    return [k for k, v in models.items() if v is not None]


def get_model_info() -> dict:
    """Return information about configured models."""
    models = init_models()
    return {
        key: {
            "available": model is not None,
            "type": type(model).__name__ if model else None,
        }
        for key, model in models.items()
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx LLM Gateway - Model Routing Test")
    print("=" * 60)

    try:
        models = init_models()
        print("\nAvailable models:")
        for key, model in models.items():
            status = "OK" if model else "Not configured"
            print(f"  - {key}: {status}")

        print("\nTask routing examples:")
        test_tasks = [
            ("complex_reasoning", 5000),
            ("drafting", 5000),
            ("audit", 5000),
            ("classification", 5000),
            ("full_thesis_analysis", 50000),
        ]

        for task, tokens in test_tasks:
            route = _route_task(task, tokens, models)
            print(f"  - {task} ({tokens} tokens) -> {route}")

    except FileNotFoundError as e:
        print(f"\nError: {e}")

    print("\n" + "=" * 60)
