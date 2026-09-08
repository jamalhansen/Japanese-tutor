class JapaneseTutorError(Exception):
    """Base typed error for japanese-tutor."""


class ProviderSetupError(JapaneseTutorError):
    """Raised when the LLM provider cannot be initialized."""
