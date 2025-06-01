# AGENT.md - Development Guidelines for llm-loop

## Build/Test/Lint Commands
- Install: `llm install -e .` (installs as LLM plugin)
- Test: No test framework configured yet
- Lint: No linting configured (consider adding flake8/black/ruff)
- Type check: No type checking configured (consider adding mypy)

## Project Structure
- Main plugin: `llm_loop.py` - LLM CLI plugin entry point
- Dev tools: `dev_tools.py` - Built-in tools for file/shell operations
- Package config: `pyproject.toml` - Python packaging configuration

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local imports
- **Formatting**: No formatter configured (follows basic PEP 8)
- **Type hints**: Partial type annotations present, use `# type: ignore` for complex cases
- **Naming**: snake_case for variables/functions, follow Python conventions
- **Error handling**: Use try/except with specific error messages, return error strings from tools
- **Comments**: Minimal - only use when explaining complex logic (avoid over-commenting)
- **Tool functions**: Return descriptive strings with emojis for user feedback
- **Docstrings**: Required for tool functions, brief and descriptive

## Tool Development Patterns
- Tools return strings (not raise exceptions)
- Use pathlib.Path for file operations
- Include error handling in all tools
- Use emoji prefixes for user-friendly output (✅❌📁💻)
