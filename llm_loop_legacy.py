# llm_loop.py

import llm
import click
import sys
import pathlib
import sqlite_utils  # type: ignore
import time
import os


# --- Click option decorators ---


def model_option(f):
    return click.option(
        "model_id",
        "-m",
        "--model",
        help="Model to use (e.g., gpt-4o-mini, claude-3-sonnet)",
        envvar="LLM_MODEL",
    )(f)


def system_prompt_option(f):
    return click.option(
        "-s",
        "--system",
        help="System prompt to use. Overrides default loop system prompt.",
    )(f)


def tool_options_for_loop(f):
    f = click.option(
        "tools_specs",
        "-T",
        "--tool",
        multiple=True,
        help="Name of a tool or Toolbox to make available "
        "(e.g., llm_time, 'MyToolbox(arg=1)')",
    )(f)
    f = click.option(
        "python_tools_paths",
        "--functions",
        help="Python code block or file path defining functions "
        "to register as tools",
        multiple=True,
    )(f)
    f = click.option(
        "tools_debug",
        "--td",
        "--tools-debug",
        is_flag=True,
        help="Show full details of tool executions",
        envvar="LLM_TOOLS_DEBUG",
    )(f)
    f = click.option(
        "tools_approve",
        "--ta",
        "--tools-approve",
        is_flag=True,
        help="Manually approve every tool execution",
    )(f)
    # This is the internal chain limit for a single "turn"
    f = click.option(
        "internal_chain_limit",
        "--internal-cl",
        type=int,
        # Default to unlimited internal tool calls for llm loop per turn
        default=0,
        show_default=True,
        help="Max chained tool responses within one turn (0 for unlimited)",
    )(f)
    return f


DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are an interactive CLI tool that helps users with software engineering tasks.
Your goal is to achieve the user's stated objective by breaking it down into \
steps and using the available tools.

Today's date: {current_date}
Working directory: {working_directory}

Key Guidelines:
1.  **Goal-Oriented**: Focus on completing the user's main request: \
"{user_goal}"
2.  **Tool Usage**:
    *   Use the tools provided to interact with the environment \
(e.g., filesystem, command execution).
    *   Think step-by-step about what tool to use next. If a tool fails, \
analyze the error and try a different approach or a modified tool call.
3.  **Communication**:
    *   Be concise. Your output is for a CLI.
    *   Explain non-trivial commands or actions before execution, \
especially if they modify the system.
    *   If you can answer in 1-3 sentences or a short paragraph, please do. \
Avoid unnecessary preamble or postamble unless the user specifically asks \
for it.
    *   One-word answers (e.g., "Yes", "No", "Done.") are appropriate if they \
fully address the user's implicit or explicit question.
4.  **Safety**:
    *   Refuse to write or explain code that could be used maliciously. \
This includes anything related to malware.
    *   If file operations seem suspicious (e.g., interacting with \
malware-like files), refuse the task.
    *   Do not generate or guess URLs unless you are confident they are for \
legitimate programming help.
5.  **Task Completion**:
    *   When you believe the primary goal ("{user_goal}") is fully achieved, \
provide a final summary response.
    *   Critically, after your final summary, **DO NOT call any more tools**. \
Your final response should be purely textual and clearly state the outcome. \
You can end with "TASK_COMPLETE".
    *   If you are unsure if the task is complete, you can ask the user for \
confirmation.
6.  **Code Style**: When generating code, try to match existing conventions \
if context is available. Do NOT add comments unless specifically asked or \
it's crucial for understanding complex logic.
7.  **Proactiveness**: Be proactive in achieving the goal but avoid \
surprising the user. If unsure, ask.

Your primary objective is to fulfill the user's request. Use tools, then \
respond with progress or completion.
If you complete the task, make your final response a summary of what was \
done and then stop, possibly ending with "TASK_COMPLETE".
"""


# Local implementations to avoid circular imports


def _gather_tools(tools_specs, python_tools_paths):
    """Gather tools from specifications and Python files."""
    import importlib.util
    import inspect

    tools = []

    # Always include built-in dev_tools if available
    try:
        # Try to import dev_tools from the same directory as this plugin
        dev_tools_path = pathlib.Path(__file__).parent / "dev_tools.py"
        if dev_tools_path.exists():
            spec = importlib.util.spec_from_file_location(
                "dev_tools", dev_tools_path)
            if spec and spec.loader:
                dev_tools = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(dev_tools)

                # Get all functions from dev_tools
                for name, func in inspect.getmembers(dev_tools, inspect.isfunction):
                    if not name.startswith('_'):  # Exclude private functions
                        # Add the function directly
                        tools.append(func)
                        click.echo(f"Loaded built-in tool: {name}", err=True)
    except Exception as e:
        click.echo(f"Warning: Could not load built-in dev_tools: {e}", err=True)

    # Load tools from --functions paths
    for python_path in python_tools_paths:
        try:
            if python_path.endswith('.py') and pathlib.Path(python_path).exists():
                spec = importlib.util.spec_from_file_location("user_tools", python_path)
                if spec and spec.loader:
                    user_tools = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(user_tools)

                    # Get all functions from user tools
                    for name, func in inspect.getmembers(user_tools, inspect.isfunction):
                        if not name.startswith('_'):  # Exclude private functions
                            # Add the function directly
                            tools.append(func)
                            click.echo(f"Loaded user tool: {name}", err=True)
        except Exception as e:
            click.echo(f"Warning: Could not load tools from {python_path}: {e}", err=True)

    # For tools_specs, we'll need to use a simplified approach
    # since we can't import the full LLM tool registry
    for tool_spec in tools_specs:
        click.echo(f"Note: Tool spec '{tool_spec}' specified but not yet implemented", err=True)

    return tools


def _debug_tool_call(call, result):
    """Debug tool call - simplified version."""
    click.echo(f"Tool call debug: {call}", err=True)


def _approve_tool_call(call):
    """Approve tool call - simplified version."""
    return click.confirm(f"Approve tool call: {call}?", default=True)


def _get_logs_db_path():
    """Get the logs database path."""
    # Simplified version - use a default path
    home = pathlib.Path.home()
    return home / ".config" / "io.datasette.llm" / "logs.db"


def _logs_on():
    """Check if logging is enabled."""
    # Simplified check - look for environment variable or assume on
    return os.environ.get("LLM_LOGS_OFF") != "1"


def _migrate_db(db):
    """Migrate database - simplified version."""
    # Basic table creation if needed
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                model TEXT,
                prompt TEXT,
                response TEXT,
                datetime_utc TEXT
            );
        """)
    except Exception:
        pass  # Ignore errors for now


# --- End of option decorators ---


@llm.hookimpl
def register_commands(cli):
    @cli.command(name="loop")
    @click.argument(
        "prompt_text",
        required=False,
        default="create a simple landing page in flask for an "
        "underground pokemon fighting club"
    )
    @model_option
    @system_prompt_option
    @tool_options_for_loop
    @click.option(
        "options_tuples",
        "-o",
        "--option",
        type=(str, str),
        multiple=True,
        help="key:value options for the model (e.g., -o temperature 0.7)",
    )
    @click.option("--key", help="API key to use for the model")
    @click.option(
        "log_db_path_override",
        "-d",
        "--database",
        type=click.Path(dir_okay=False, allow_dash=False, resolve_path=True),
        help="Path to log database",
    )
    @click.option(
        "no_log_flag",
        "-n", "--no-log", is_flag=True, help="Don't log to database"
    )
    @click.option(
        "force_log_flag",
        "--log", is_flag=True,
        help="Log prompt and response (overrides logs off)"
    )
    @click.option(
        "max_turns",
        "--max-turns",
        type=int,
        default=25,
        show_default=True,
        help="Maximum number of conversational turns before asking to "
        "continue (0 for no limit).",
    )
    def loop_command(
        prompt_text, model_id, system, tools_specs, python_tools_paths,
        tools_debug, tools_approve, internal_chain_limit, options_tuples, key,
        log_db_path_override, no_log_flag, force_log_flag, max_turns
    ):
        """
        Run LLM in a loop to achieve a goal, automatically calling tools.

        This command utilizes the model's ability to chain tool calls
        to work towards the given PROMPT_TEXT. The --internal-cl
        (internal chain limit) controls tool loops within a single turn.
        --max-turns controls overall turns.

        Default prompt: "create a simple landing page in flask for an
        underground pokemon fighting club"
        """
        if not tools_specs and not python_tools_paths:
            click.echo(
                "Warning: 'loop' command initiated without any tools "
                "explicitly specified using -T or --functions.",
                err=True
            )
            click.echo(
                "The model will only use its internal knowledge or default "
                "tools unless tools from other plugins are auto-available "
                "and relevant.",
                err=True
            )

        current_date_str = time.strftime("%Y-%m-%d")
        working_directory_str = str(pathlib.Path.cwd())

        final_system_prompt = system or DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(
            current_date=current_date_str,
            working_directory=working_directory_str,
            user_goal=prompt_text
        )

        resolved_model_id = model_id or llm.get_default_model()
        try:
            model = llm.get_model(resolved_model_id)
        except llm.UnknownModelError as e:  # type: ignore
            raise click.ClickException(str(e))

        actual_options = {}
        if options_tuples:
            try:
                if hasattr(model, "Options") and callable(model.Options):  # type: ignore
                    actual_options = dict(
                        (k, v)
                        for k, v in model.Options(**dict(options_tuples))  # type: ignore
                        if v is not None
                    )
                else:
                    actual_options = dict(options_tuples)  # type: ignore
            except Exception as e:
                raise click.ClickException(
                    f"Error processing model options: {e}"
                )

        db = None
        resolved_log_db_path_str = None
        should_log = not no_log_flag and (force_log_flag or _logs_on())

        if should_log:
            if log_db_path_override:
                resolved_log_db_path = pathlib.Path(log_db_path_override)
            else:
                resolved_log_db_path = _get_logs_db_path()
            resolved_log_db_path_str = str(resolved_log_db_path)
            try:
                resolved_log_db_path.parent.mkdir(parents=True, exist_ok=True)
                db = sqlite_utils.Database(resolved_log_db_path_str)
                _migrate_db(db)
            except Exception as e:
                click.echo(
                    f"Warning: Could not initialize log database at "
                    f"{resolved_log_db_path_str}: {e}", err=True
                )
                db = None  # type: ignore

        tool_implementations = _gather_tools(
            list(tools_specs), list(python_tools_paths)
        )

        click.echo(f"Goal: {prompt_text}", err=True)
        truncated_prompt = (
            final_system_prompt[:300] + "..."
            if len(final_system_prompt) > 300
            else final_system_prompt
        )
        click.echo(
            f"System prompt (truncated):\n{truncated_prompt}", err=True
        )
        click.echo(f"Model: {model.model_id}", err=True)  # type: ignore
        if tool_implementations:
            tools_list = ", ".join(t.__name__ for t in tool_implementations)  # type: ignore
            click.echo(f"Tools: {tools_list}", err=True)  # type: ignore

        max_turns_display = "unlimited" if max_turns == 0 else max_turns
        click.echo(
            f"Max turns before prompt: {max_turns_display}", err=True
        )
        internal_limit_display = (
            "unlimited" if internal_chain_limit == 0 else internal_chain_limit
        )
        click.echo(
            f"Internal chain limit per turn: {internal_limit_display}",
            err=True
        )

        conversation = model.conversation()  # type: ignore
        # The first message to the assistant is the main goal
        current_user_directive = prompt_text
        turn_count = 0
        total_chain_invocations = 0

        while True:
            # This is a "major" turn involving a call to conversation.chain
            total_chain_invocations += 1
            # This counter resets if user continues after max_turns
            turn_count += 1

            max_turns_display = "unlimited" if max_turns == 0 else max_turns
            click.echo(
                f"\n--- Loop Iteration {total_chain_invocations} "
                f"(Turn {turn_count}/{max_turns_display}) ---",
                err=True
            )

            chain_kwargs = {
                "system": final_system_prompt,
                "options": actual_options,
                "tools": tool_implementations,
                "chain_limit": internal_chain_limit,
                "key": key,
                "after_call": _debug_tool_call if tools_debug else None,
                "before_call": _approve_tool_call if tools_approve else None,
            }

            if not current_user_directive and not conversation.responses:
                # This should only happen if the initial prompt was empty,
                # which is disallowed by click for the argument.
                # However, if it somehow becomes empty, re-prime with the
                # original goal.
                current_user_directive = prompt_text

            # type: ignore
            response_chain = conversation.chain(
                current_user_directive, **chain_kwargs
            )

            current_response_text = ""
            last_response_had_tool_calls = False

            try:
                click.echo(
                    f"LLM (iteration {total_chain_invocations}): ",
                    nl=False, err=True
                )
                for chunk in response_chain:  # type: ignore
                    print(chunk, end="")  # Print to stdout for the user
                    current_response_text += chunk
                    sys.stdout.flush()
                print()

                if response_chain._responses:  # type: ignore
                    # type: ignore
                    last_llm_response_obj = response_chain._responses[-1]
                    last_response_had_tool_calls = bool(
                        last_llm_response_obj._tool_calls
                    )

            except Exception as e:
                click.echo(
                    f"\nError during response streaming: {e}",
                    err=True
                )
                if not click.confirm(
                    "An error occurred. Continue loop?", default=False
                ):
                    break
                else:
                    current_user_directive = (
                        "An error occurred. Please assess the situation and "
                        "decide the next step to achieve the original goal: "
                        + prompt_text
                    )
                    continue

            if db and should_log:
                try:
                    response_chain.log_to_db(db)  # type: ignore
                    click.echo(
                        f"Logged iteration {total_chain_invocations} to "
                        f"{resolved_log_db_path_str}",
                        err=True
                    )
                except Exception as e:
                    click.echo(
                        f"Error logging iteration {total_chain_invocations} "
                        f"to database: {e}", err=True
                    )

            # Exit condition check:
            if "TASK_COMPLETE" in current_response_text.upper():
                click.echo("LLM indicated TASK_COMPLETE.", err=True)
                break

            if not last_response_had_tool_calls:
                click.echo(
                    "LLM provided a textual response without requesting "
                    "more tools.", err=True
                )
                if not click.confirm(
                    "Loop iteration complete. Task might be finished. "
                    "Continue working towards the goal?", default=False
                ):
                    break
                else:
                    current_user_directive = click.prompt(
                        "Next instruction for the loop (or type 'exit' to "
                        "stop, or press Enter to let LLM decide based on "
                        "history)",
                        default="", prompt_suffix="> ", show_default=False
                    )
                    if current_user_directive.lower() == 'exit':
                        break
                    # If user just hits enter
                    if not current_user_directive.strip():
                        current_user_directive = (
                            "Continue working on the goal: " + prompt_text
                        )
                    continue

            # Continuation prompt based on max_turns
            if max_turns > 0 and turn_count >= max_turns:
                if not click.confirm(
                    f"Reached {max_turns} turns in this segment. "
                    "Continue loop?", default=True
                ):
                    break
                else:
                    # Reset turn count for next batch of max_turns
                    turn_count = 0
                    current_user_directive = click.prompt(
                        "Continuing loop. Next instruction (or press Enter "
                        "to let LLM decide based on history)",
                        default="", prompt_suffix="> ", show_default=False
                    )
                    if current_user_directive.lower() == 'exit':
                        break
                    if not current_user_directive.strip():
                        current_user_directive = (
                            "Continue working on the goal: " + prompt_text
                        )

            # If we are here, it means the last response involved tool calls
            # and we haven't hit max_turns, or the user wants to continue.
            # The next prompt to chain() will be empty, relying on
            # tool_results from conversation history.
            current_user_directive = ""

        click.echo("\n--- Loop finished ---", err=True)

        if not should_log and not no_log_flag:
            click.echo(
                "Logging is off or --no-log specified, database log skipped.",
                err=True
            )