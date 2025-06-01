"""Type definitions for LLM Loop."""

from typing import TypedDict, Union, Optional, Callable, List, Dict, Any
from pathlib import Path


class ToolResult(TypedDict):
    """Result of a tool execution."""
    success: bool
    output: str
    error: Optional[str]


class LoopResult(TypedDict):
    """Result of a complete loop execution."""
    completed: bool
    iterations: int
    final_response: str
    error: Optional[str]


ToolFunction = Callable[..., str]
ToolList = List[ToolFunction]
OptionsDict = Dict[str, Any]