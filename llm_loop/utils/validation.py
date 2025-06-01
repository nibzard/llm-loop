"""Input validation utilities for LLM Loop."""

import re
import shlex
from pathlib import Path
from typing import Union

from .exceptions import ValidationError


def validate_path(file_path: Union[str, Path]) -> Path:
    """Validate and normalize a file path.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid or unsafe
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Check for path traversal attempts
    if ".." in file_path.parts:
        raise ValidationError("Path traversal detected")
    
    # Check for absolute paths outside user directory
    if file_path.is_absolute():
        home = Path.home()
        try:
            file_path.relative_to(home)
        except ValueError:
            raise ValidationError("Absolute path outside user directory")
    
    return file_path


def sanitize_command(command: str) -> str:
    """Sanitize a shell command for safer execution.
    
    Args:
        command: Command to sanitize
        
    Returns:
        Sanitized command
        
    Raises:
        ValidationError: If command contains unsafe patterns
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'sudo\s+',       # sudo commands
        r'curl.*\|\s*sh', # curl | sh patterns
        r'wget.*\|\s*sh', # wget | sh patterns
        r'>\s*/dev/',     # redirecting to devices
        r'&\s*$',         # background processes
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            raise ValidationError(f"Potentially dangerous command pattern detected: {pattern}")
    
    # Basic validation that command can be parsed
    try:
        shlex.split(command)
    except ValueError as e:
        raise ValidationError(f"Invalid command syntax: {e}")
    
    return command.strip()