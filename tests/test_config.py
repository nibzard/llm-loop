"""Tests for configuration management."""

import os
from pathlib import Path

from llm_loop.config.settings import LoopSettings


class TestLoopSettings:
    """Tests for LoopSettings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = LoopSettings()
        assert settings.default_model is None
        assert settings.default_max_turns == 25
        assert settings.default_system_prompt is None
        assert settings.log_database_path is None
        assert settings.tools_debug is False
        assert settings.tools_approve is False

    def test_from_env_with_values(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("LLM_MODEL", "gpt-4")
        monkeypatch.setenv("LLM_LOOP_MAX_TURNS", "50")
        monkeypatch.setenv("LLM_TOOLS_DEBUG", "true")
        monkeypatch.setenv("LLM_LOOP_TOOLS_APPROVE", "1")
        
        settings = LoopSettings.from_env()
        assert settings.default_model == "gpt-4"
        assert settings.default_max_turns == 50
        assert settings.tools_debug is True
        assert settings.tools_approve is True

    def test_from_env_with_defaults(self, monkeypatch):
        """Test that defaults are used when env vars not set."""
        # Clear any existing env vars
        for key in ["LLM_MODEL", "LLM_LOOP_MAX_TURNS", "LLM_TOOLS_DEBUG"]:
            monkeypatch.delenv(key, raising=False)
            
        settings = LoopSettings.from_env()
        assert settings.default_model is None
        assert settings.default_max_turns == 25
        assert settings.tools_debug is False

    def test_merge_with_args(self):
        """Test merging settings with command line arguments."""
        base_settings = LoopSettings(default_model="gpt-3.5-turbo")
        
        merged = base_settings.merge_with_args(
            model_id="gpt-4",
            max_turns=10,
            tools_debug=True
        )
        
        assert merged.default_model == "gpt-4"  # Overridden
        assert merged.default_max_turns == 10   # Overridden
        assert merged.tools_debug is True       # Overridden
        assert merged.tools_approve is False    # Unchanged