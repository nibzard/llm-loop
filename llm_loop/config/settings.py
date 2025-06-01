"""Configuration settings for LLM Loop."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LoopSettings:
    """Configuration settings for LLM Loop."""
    
    default_model: Optional[str] = None
    default_max_turns: int = 25
    default_system_prompt: Optional[str] = None
    log_database_path: Optional[Path] = None
    tools_debug: bool = False
    tools_approve: bool = False
    
    @classmethod
    def from_env(cls) -> 'LoopSettings':
        """Create settings from environment variables."""
        return cls(
            default_model=os.getenv("LLM_MODEL"),
            default_max_turns=int(os.getenv("LLM_LOOP_MAX_TURNS", "25")),
            default_system_prompt=os.getenv("LLM_LOOP_SYSTEM_PROMPT"),
            log_database_path=Path(p) if (p := os.getenv("LLM_LOOP_LOG_DB_PATH")) else None,
            tools_debug=os.getenv("LLM_TOOLS_DEBUG", "").lower() in ("1", "true", "yes"),
            tools_approve=os.getenv("LLM_LOOP_TOOLS_APPROVE", "").lower() in ("1", "true", "yes"),
        )
    
    def merge_with_args(
        self,
        model_id: Optional[str] = None,
        max_turns: Optional[int] = None,
        system_prompt: Optional[str] = None,
        log_db_path: Optional[str] = None,
        tools_debug: Optional[bool] = None,
        tools_approve: Optional[bool] = None,
    ) -> 'LoopSettings':
        """Merge settings with command line arguments."""
        return LoopSettings(
            default_model=model_id or self.default_model,
            default_max_turns=max_turns if max_turns is not None else self.default_max_turns,
            default_system_prompt=system_prompt or self.default_system_prompt,
            log_database_path=Path(log_db_path) if log_db_path else self.log_database_path,
            tools_debug=tools_debug if tools_debug is not None else self.tools_debug,
            tools_approve=tools_approve if tools_approve is not None else self.tools_approve,
        )