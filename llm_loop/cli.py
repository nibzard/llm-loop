"""CLI interface for LLM Loop."""

import time
import pathlib
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

import click
import llm

from .core import (
    ConversationManager,
    LoopConfig,
    ToolManager,
    DEFAULT_SYSTEM_PROMPT_TEMPLATE,
)
from .config import LoopSettings
from .utils.logging import setup_logging
from .utils.exceptions import ConversationError
from .utils.types import ToolFunction, LoopResult


def model_option(f):
    """Click decorator for model selection."""
    return click.option(
        "model_id",
        "-m",
        "--model",
        help="Model to use (e.g., gpt-4o-mini, claude-3-sonnet)",
        envvar="LLM_MODEL",
    )(f)


def system_prompt_option(f):
    """Click decorator for system prompt override."""
    return click.option(
        "-s",
        "--system",
        help="System prompt to use. Overrides default loop system prompt.",
    )(f)


def tool_options_for_loop(f):
    """Click decorator for tool-related options."""
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
    f = click.option(
        "internal_chain_limit",
        "--internal-cl",
        type=int,
        default=0,
        show_default=True,
        help="Max chained tool responses within one turn (0 for unlimited)",
    )(f)
    return f


@llm.hookimpl
def register_commands(cli):
    """Register the loop command with LLM CLI."""

    @cli.command(name="loop")
    @click.argument(
        "prompt_text",
        required=False,
        default=(
            "create a simple landing page in flask for an "
            "underground pokemon fighting club"
        ),
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
        "no_log_flag", "-n", "--no-log", is_flag=True, help="Don't log to database"
    )
    @click.option(
        "force_log_flag",
        "--log",
        is_flag=True,
        help="Log prompt and response (overrides logs off)",
    )
    @click.option(
        "max_turns",
        "--max-turns",
        type=int,
        default=25,
        show_default=True,
        help=(
            "Maximum number of conversational turns before asking to "
            "continue (0 for no limit)."
        ),
    )
    def loop_command(
        prompt_text: str,
        model_id: Optional[str],
        system: Optional[str],
        tools_specs: Tuple[str, ...],
        python_tools_paths: Tuple[str, ...],
        tools_debug: bool,
        tools_approve: bool,
        internal_chain_limit: int,
        options_tuples: Tuple[Tuple[str, str], ...],
        key: Optional[str],
        log_db_path_override: Optional[str],
        no_log_flag: bool,
        force_log_flag: bool,
        max_turns: int,
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
        # Load settings from environment and merge with CLI args
        settings = LoopSettings.from_env().merge_with_args(
            model_id=model_id,
            max_turns=max_turns,
            system_prompt=system,
            log_db_path=log_db_path_override,
            tools_debug=tools_debug,
            tools_approve=tools_approve,
        )

        # Warn if no tools specified
        if not tools_specs and not python_tools_paths:
            click.echo(
                "Warning: 'loop' command initiated without any tools "
                "explicitly specified using -T or --functions.",
                err=True,
            )
            click.echo(
                "The model will only use its internal knowledge or default "
                "tools unless tools from other plugins are auto-available "
                "and relevant.",
                err=True,
            )

        # Prepare system prompt
        current_date_str = time.strftime("%Y-%m-%d")
        working_directory_str = str(pathlib.Path.cwd())
        user_goal_str = prompt_text  # For clarity in format string

        final_system_prompt = (
            settings.default_system_prompt
            or DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(
                current_date=current_date_str,
                working_directory=working_directory_str,
                user_goal=user_goal_str,
            )
        )

        # Get model
        try:
            resolved_model_id = settings.default_model or llm.get_default_model()
            model = llm.get_model(resolved_model_id)
        except llm.UnknownModelError as e:
            raise click.ClickException(str(e))

        # Process model options
        actual_options = _process_model_options(model, options_tuples)

        # Set up logging
        should_log = not no_log_flag and (force_log_flag or settings.log_database_path)
        db_path = settings.log_database_path
        if log_db_path_override:
            db_path = log_db_path_override

        db = (
            setup_logging(pathlib.Path(db_path) if db_path else None)
            if should_log
            else None
        )

        # Set up tools
        tool_manager = ToolManager.create_from_specs(
            tool_specs=list(tools_specs),
            python_tool_paths=list(python_tools_paths),
            include_builtin=True,
        )
        tool_implementations: List[ToolFunction] = tool_manager.get_all_tools()

        # Display configuration
        _display_configuration(
            prompt_text,
            final_system_prompt,
            model,
            tool_implementations,
            settings.default_max_turns,
            internal_chain_limit,
        )

        # Set up loop configuration
        loop_config = LoopConfig(
            max_turns=settings.default_max_turns,
            internal_chain_limit=internal_chain_limit,
            tools_debug=settings.tools_debug,
            tools_approve=settings.tools_approve,
            should_log=should_log,
            log_db_path=str(db.path) if db and hasattr(db, "path") else None,
        )

        # Execute the loop
        try:
            conversation_manager = ConversationManager(model, loop_config)
            result: LoopResult = conversation_manager.execute_loop(
                prompt_text,
                final_system_prompt,
                tool_implementations,
                actual_options,
                key,
            )

            click.echo("\n--- Loop finished ---", err=True)

            if result["error"]:
                click.echo(f"Loop completed with error: {result['error']}", err=True)
            elif result["completed"]:
                click.echo("Task completed successfully!", err=True)
            else:
                click.echo("Loop finished without explicit completion.", err=True)

        except ConversationError as e:
            if "User requested exit" not in str(e):
                click.echo(f"Conversation error: {e}", err=True)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            raise


def _process_model_options(
    model: Any, options_tuples: Tuple[Tuple[str, str], ...]
) -> Dict[str, Any]:
    """Process model options from CLI arguments."""
    actual_options: Dict[str, Any] = {}
    if options_tuples:
        try:
            if hasattr(model, "Options") and callable(model.Options):
                # Ensure model.Options returns a Pydantic model or dict
                options_obj = model.Options(**dict(options_tuples))
                if hasattr(options_obj, "model_dump"):  # Pydantic v2
                    processed_options = options_obj.model_dump(exclude_none=True)
                elif hasattr(options_obj, "dict"):  # Pydantic v1 or similar
                    processed_options = {
                        k: v for k, v in options_obj.dict().items() if v is not None
                    }
                else:  # Fallback for plain dicts
                    processed_options = (
                        {k: v for k, v in options_obj.items() if v is not None}
                        if isinstance(options_obj, dict)
                        else {}
                    )
                actual_options = processed_options
            else:
                actual_options = dict(options_tuples)
        except Exception as e:
            raise click.ClickException(f"Error processing model options: {e}")
    return actual_options


def _display_configuration(
    prompt_text: str,
    system_prompt: str,
    model: Any,
    tools: List[ToolFunction],
    max_turns: int,
    internal_chain_limit: int,
) -> None:
    """Display current configuration to user."""
    click.echo(f"Goal: {prompt_text}", err=True)
    truncated_prompt = (
        system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt
    )
    click.echo(f"System prompt (truncated):\n{truncated_prompt}", err=True)
    click.echo(f"Model: {model.model_id}", err=True)
    if tools:
        tools_list = ", ".join(getattr(t, "__name__", str(t)) for t in tools)
        click.echo(f"Tools: {tools_list}", err=True)

    max_turns_display = "unlimited" if max_turns == 0 else max_turns
    click.echo(f"Max turns before prompt: {max_turns_display}", err=True)
    internal_limit_display = (
        "unlimited" if internal_chain_limit == 0 else internal_chain_limit
    )
    click.echo(f"Internal chain limit per turn: {internal_limit_display}", err=True)
