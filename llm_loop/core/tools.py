"""Tool management system for LLM Loop."""

import importlib.util
import inspect
import pathlib
from abc import ABC, abstractmethod
from typing import List, Optional

import click

from ..utils.types import ToolFunction
from ..utils.exceptions import ToolExecutionError


class ToolProvider(ABC):
    """Abstract base class for tool providers."""

    @abstractmethod
    def get_tools(self) -> List[ToolFunction]:
        """Return list of tool functions."""
        pass


class BuiltinToolProvider(ToolProvider):
    """Provider for built-in development tools."""

    def get_tools(self) -> List[ToolFunction]:
        """Load built-in tools from plugins directory."""
        tools = []

        try:
            # Try to import dev_tools from the plugins directory
            from ..plugins.dev_tools import SecureFileOperations

            # Get all methods from SecureFileOperations
            for name, method in inspect.getmembers(
                SecureFileOperations, inspect.isfunction
            ):
                if not name.startswith("_"):  # Exclude private methods
                    tools.append(method)
                    click.echo(f"Loaded built-in tool: {name}", err=True)

        except ImportError as e:
            click.echo(f"Warning: Could not load built-in tools: {e}", err=True)

        return tools


class FileSystemToolProvider(ToolProvider):
    """Provider for tools loaded from Python files."""

    def __init__(self, file_paths: List[str]):
        """Initialize with list of Python file paths."""
        self.file_paths = file_paths

    def get_tools(self) -> List[ToolFunction]:
        """Load tools from Python files."""
        tools = []

        for file_path in self.file_paths:
            tools.extend(self._load_tools_from_file(file_path))

        return tools

    def _load_tools_from_file(self, file_path: str) -> List[ToolFunction]:
        """Load tools from a single Python file."""
        tools = []

        try:
            if not file_path.endswith(".py") or not pathlib.Path(file_path).exists():
                click.echo(
                    f"Warning: Tool file not found or invalid: {file_path}", err=True
                )
                return tools

            spec = importlib.util.spec_from_file_location("user_tools", file_path)
            if spec and spec.loader:
                user_tools = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_tools)

                # Get all functions from the module
                for name, func in inspect.getmembers(user_tools, inspect.isfunction):
                    if not name.startswith("_"):  # Exclude private functions
                        tools.append(func)
                        click.echo(f"Loaded tool from {file_path}: {name}", err=True)

        except Exception as e:
            click.echo(f"Warning: Could not load tools from {file_path}: {e}", err=True)

        return tools


class LegacyToolProvider(ToolProvider):
    """Provider for legacy tool specifications (compatibility layer)."""

    def __init__(self, tool_specs: List[str]):
        """Initialize with list of tool specifications."""
        self.tool_specs = tool_specs

    def get_tools(self) -> List[ToolFunction]:
        """Load tools from specifications."""
        tools = []

        # For now, just log that these are not yet implemented
        for tool_spec in self.tool_specs:
            click.echo(
                f"Note: Tool spec '{tool_spec}' specified but not yet implemented",
                err=True,
            )

        return tools


class ToolManager:
    """Manages multiple tool providers and consolidates tools."""

    def __init__(self):
        """Initialize tool manager."""
        self.providers: List[ToolProvider] = []

    def add_provider(self, provider: ToolProvider) -> None:
        """Add a tool provider."""
        self.providers.append(provider)

    def get_all_tools(self) -> List[ToolFunction]:
        """Get all tools from all providers."""
        all_tools = []

        for provider in self.providers:
            try:
                tools = provider.get_tools()
                all_tools.extend(tools)
            except Exception as e:
                click.echo(
                    f"Warning: Error loading tools from provider {provider.__class__.__name__}: {e}",
                    err=True,
                )

        return all_tools

    @classmethod
    def create_from_specs(
        cls,
        tool_specs: Optional[List[str]] = None,
        python_tool_paths: Optional[List[str]] = None,
        include_builtin: bool = True,
    ) -> "ToolManager":
        """Create tool manager from specifications.

        Args:
            tool_specs: List of tool specifications
            python_tool_paths: List of Python file paths containing tools
            include_builtin: Whether to include built-in tools

        Returns:
            Configured ToolManager instance
        """
        manager = cls()

        # Always include built-in tools if requested
        if include_builtin:
            manager.add_provider(BuiltinToolProvider())

        # Add file-based tools
        if python_tool_paths:
            manager.add_provider(FileSystemToolProvider(python_tool_paths))

        # Add legacy tool specs
        if tool_specs:
            manager.add_provider(LegacyToolProvider(tool_specs))

        return manager
