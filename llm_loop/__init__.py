"""LLM Loop - Autonomous task execution plugin for LLM CLI."""

__version__ = "0.2.0"
__author__ = "nibzard"
__email__ = "wave@nibzard.com"

from .cli import register_commands

__all__ = ["register_commands"]