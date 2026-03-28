PROVIDER_MODEL_MAP = {
    "openai": [
        "gpt-4.1-mini",
        "gpt-4o",
    ],
    "anthropic": [
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    ],
}

MODEL_TO_PROVIDER = {
    model: provider
    for provider, models in PROVIDER_MODEL_MAP.items()
    for model in models
}

MODEL_CHOICES = [model for models in PROVIDER_MODEL_MAP.values() for model in models]
