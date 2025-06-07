# llm-loop Usage Examples

This document collects additional examples for using the **llm-loop** plugin.
These build upon the basics covered in the README and provide more
context for common development scenarios.

## 1. Generate Documentation for a Project

Use the built-in development tools to analyze your project and create
Markdown documentation files for each module:

```bash
llm loop "Generate documentation for this project" \
  --functions llm_loop/plugins/dev_tools.py \
  -T filesystem \
  --max-turns 20
```

The AI will read your source files and produce new `.md` documents
summarizing the code.

## 2. Build and Test a Flask Application

Create a new Flask application with routes and unit tests. The AI will
write the application code, a `requirements.txt`, and corresponding
pytest files:

```bash
llm loop "Create a Flask app with unit tests" \
  --functions llm_loop/plugins/dev_tools.py \
  -T filesystem \
  --max-turns 15
```

Run the generated tests using `pytest` once the loop completes.

## 3. Initialize a New Repository

Use the `--tools-approve` flag when you want the AI to run potentially
unsafe commands such as initializing a git repository:

```bash
llm loop "Initialize git and make the first commit" \
  --functions llm_loop/plugins/dev_tools.py \
  --tools-approve \
  --max-turns 5
```

The AI will call the git-related tools and pause for approval before
executing each command.

## 4. Apply a Custom System Prompt

You can steer the AI by providing your own system prompt. This works
well for style or architectural guidance:

```bash
llm loop "Create a simple REST API" \
  --system "You are an experienced backend engineer. Use FastAPI." \
  --functions llm_loop/plugins/dev_tools.py
```

The loop will use the given system prompt instead of the default.
