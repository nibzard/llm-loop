# LLM Loop

**An autonomous task execution plugin for the LLM CLI tool**

`llm loop` is a powerful plugin for the [LLM CLI tool](https://github.com/simonw/llm) that enables autonomous, goal-oriented task execution. Unlike traditional single-turn LLM interactions, `llm loop` allows the AI to work persistently towards a goal by making multiple tool calls, analyzing results, and iterating until the task is complete.

## 🚀 Features

- **Goal-Oriented Execution**: Define a task and let the AI work autonomously to complete it
- **Tool Integration**: Seamlessly use LLM tools and functions to interact with your environment
- **Iterative Problem Solving**: The AI can chain multiple tool calls and adapt based on results
- **Interactive Control**: Configure turn limits, approve tool calls, and guide the process
- **Comprehensive Logging**: Track all interactions and tool calls for debugging and analysis
- **Safety Features**: Built-in approval mechanisms for potentially dangerous operations

## 📦 Installation

### Prerequisites

1. **Install LLM CLI globally** (recommended using `uv`):
   ```bash
   uv tool install llm
   ```

   Or using `pipx`:
   ```bash
   pipx install llm
   ```

2. **Configure an LLM model** (you'll need an API key):
   ```bash
   # For OpenAI
   llm keys set openai
   llm models default gpt-4.1-mini

   # For Anthropic
   llm keys set anthropic
   llm models default claude-3-5-sonnet-20241022
   ```

### Install the Plugin

1. **Clone this repository**:
   ```bash
   git clone https://github.com/nibzard/llm-loop
   cd llm-loop
   ```

2. **Install the plugin**:
   ```bash
   # For regular use
   llm install -e .

   # For development (includes dev dependencies like pytest, ruff, mypy)
   pip install -e ".[dev]"
   ```

3. **Verify installation**:
   ```bash
   llm loop --help
   ```

## 🎯 Quick Start

### Basic Usage

```bash
# Simple example with default prompt
llm loop

# Custom task
llm loop "Create a Python script that analyzes a CSV file"

# With specific model
llm loop "Build a simple web server" -m gpt-4o

# Limit iterations
llm loop "Write unit tests for my code" --max-turns 5
```

### Using Tools

Tools are what make `llm loop` powerful. You can use existing LLM tools or create custom functions:

```bash
# Using built-in or installed tools
llm loop "Analyze the current directory structure" -T filesystem

# Using custom Python functions
llm loop "Create a Flask app" --functions dev_tools.py

# Multiple tools
llm loop "Set up a git repository and make initial commit" \
  -T filesystem -T shell --tools-approve
```

## 🛠️ Command Options

| Option | Description |
|--------|-------------|
| `-m, --model` | Specify the LLM model to use |
| `-s, --system` | Override the default system prompt |
| `-T, --tool` | Enable specific tools (can be used multiple times) |
| `--functions` | Python file containing custom tool functions |
| `--max-turns` | Maximum conversation turns (default: 25) |
| `--td, --tools-debug` | Show detailed tool execution information |
| `--ta, --tools-approve` | Manually approve each tool call |
| `--internal-cl` | Chain limit for tool calls within a single turn |
| `--no-log` | Disable logging to database |
| `--log` | Force logging even if globally disabled |

## 📚 Examples

### Example 1: Create a Flask Web Application

Create a simple tool file first. Note: With the refactoring, `dev_tools.py` has been moved to `llm_loop/plugins/dev_tools.py`. The plugin will automatically discover tools from this location if you are running from the project root or have installed the package. For custom tool files outside the package, you still use the `--functions` flag.

The example `dev_tools.py` content remains relevant:
```python
# llm_loop/plugins/dev_tools.py
import os
import pathlib

def write_file(file_path: str, content: str) -> str:
    """Write content to a file, creating directories if needed."""
    try:
        p = pathlib.Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {file_path}"
    except Exception as e:
        return f"Error writing {file_path}: {e}"

def read_file(file_path: str) -> str:
    """Read and return file contents."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def list_directory(path: str = ".") -> str:
    """List directory contents."""
    try:
        items = os.listdir(path)
        return "\n".join(items) if items else f"Directory {path} is empty"
    except Exception as e:
        return f"Error listing {path}: {e}"
```

Now run the loop:

```bash
mkdir my_flask_app && cd my_flask_app

llm loop "Create a Flask web application with a homepage and about page" \
  --functions ../dev_tools.py \
  --tools-debug \
  --max-turns 10
```

Make sure to adjust the path to `dev_tools.py` if you are not in `my_flask_app` directory and `dev_tools.py` is not in the parent directory.
If you've installed the package in development mode (`pip install -e ".[dev]"`), `llm-loop` will attempt to load tools from `llm_loop/plugins/dev_tools.py` automatically if no `--functions` flag is provided and the built-in tools are not sufficient.

The AI will:
1. Create `app.py` with Flask routes
2. Create HTML templates
3. Generate a `requirements.txt`
4. Provide instructions for running the app

### Example 2: Code Analysis and Documentation

```bash
llm loop "Analyze all Python files in this project and generate comprehensive documentation" \
  --functions llm_loop/plugins/dev_tools.py \
  -T filesystem \
  --max-turns 15
```
This assumes you are running the command from the root of the `llm-loop` project. If running from elsewhere after installation, and `dev_tools.py` is part of the installed package, you might not need `--functions` if those tools are made available by default.

### Example 3: Git Repository Setup (with approval)

```bash
llm loop "Initialize a git repository, create .gitignore, and make initial commit" \
  --functions llm_loop/plugins/dev_tools.py \
  --tools-approve \
  --max-turns 5
```
Similar to the above, adjust paths or rely on automatic discovery if applicable.

## 🔧 Advanced Usage

### Custom System Prompts

You can override the default system prompt to customize the AI's behavior:

```bash
llm loop "Build a REST API" \
  --system "You are a senior backend developer. Focus on best practices, error handling, and clean code architecture." \
  --functions dev_tools.py
```

### Tool Debugging

Use `--tools-debug` to see exactly what tools are being called:

```bash
llm loop "Create a Python package structure" \
  --functions llm_loop/plugins/dev_tools.py \
  --tools-debug
```

### Safety with Tool Approval

For potentially dangerous operations, use `--tools-approve`:

```bash
llm loop "Clean up old files and optimize the project structure" \
  --functions llm_loop/plugins/dev_tools.py \
  --tools-approve
```

## 🏗️ Project Structure

The `llm-loop` project has been refactored into a modular Python package:

```
llm_loop/
├── __init__.py                 # Package entry point
├── cli.py                      # Click command interface
├── core/
│   ├── __init__.py
│   ├── conversation.py         # ConversationManager class
│   ├── tools.py               # Tool provider system
│   └── prompts.py             # System prompt templates
├── config/
│   ├── __init__.py
│   └── settings.py            # Configuration management
├── utils/
│   ├── __init__.py
│   ├── logging.py             # Database logging utilities
│   ├── validation.py          # Input validation and sanitization
│   ├── exceptions.py          # Custom exception classes
│   └── types.py               # Type definitions
└── plugins/
    ├── __init__.py
    └── dev_tools.py           # Default development tools (can be extended)
```
This structure promotes separation of concerns, maintainability, and scalability.

## 🎛️ Configuration

### Environment Variables

- `LLM_MODEL`: Default model to use
- `LLM_TOOLS_DEBUG`: Enable tools debugging by default
- `LLM_LOGS_OFF`: Disable logging by default

### Logging

All interactions are logged to an SQLite database by default:
- Location: `~/.config/io.datasette.llm/logs.db`
- Disable with `--no-log`
- Force enable with `--log`

## 🚨 Safety Considerations

1. **Tool Approval**: Always use `--tools-approve` for tools that can modify your system
2. **Limited Scope**: Run in dedicated directories for file operations
3. **Review Tools**: Understand what each tool function does before using it
4. **Backup Important Data**: Especially when using file manipulation tools

## 🐛 Troubleshooting

### Common Issues

**Plugin not found after installation:**
```bash
# Reinstall the plugin
llm install -e .

# Check if it's loaded
llm --help | grep loop
```

**Tool import errors:**
- Ensure your tool functions have proper error handling
- Check that file paths in `--functions` are correct
- Verify Python syntax in your tool files

**Model errors:**
```bash
# Check available models
llm models list

# Set a working default
llm models default gpt-4.1-mini
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

- Built on the excellent [LLM CLI tool](https://github.com/simonw/llm) by Simon Willison
- Inspired by autonomous AI agent frameworks
- Thanks to the LLM tool ecosystem contributors

---

**Note**: This plugin enables powerful autonomous AI behavior. Always review and understand the tools you're providing to the AI, especially those that can modify files or execute system commands.