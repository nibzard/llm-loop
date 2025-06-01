"""Custom exceptions for LLM Loop."""


class LoopError(Exception):
    """Base exception for loop operations."""
    pass


class ToolExecutionError(LoopError):
    """Raised when tool execution fails."""
    pass


class ConversationError(LoopError):
    """Raised when conversation management fails."""
    pass


class ModelError(LoopError):
    """Raised when model-related operations fail."""
    pass


class ValidationError(LoopError):
    """Raised when input validation fails."""
    pass