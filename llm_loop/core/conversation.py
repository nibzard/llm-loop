"""Conversation management for LLM Loop."""

import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable

import click
import llm
from ..utils.types import ToolFunction, LoopResult
from ..utils.exceptions import ConversationError, ModelError


@dataclass
class LoopConfig:
    """Configuration for loop execution."""

    max_turns: int = 25
    internal_chain_limit: int = 0
    tools_debug: bool = False
    tools_approve: bool = False
    should_log: bool = True
    log_db_path: Optional[str] = None


class ConversationManager:
    """Manages LLM conversation loops with tool integration."""

    def __init__(self, model, config: LoopConfig):
        """Initialize conversation manager.

        Args:
            model: LLM model instance
            config: Loop configuration
        """
        self.model = model
        self.config = config
        self.conversation = model.conversation()
        self.turn_count = 0
        self.total_iterations = 0

    def execute_loop(
        self,
        goal: str,
        system_prompt: str,
        tools: List[ToolFunction],
        options: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
    ) -> LoopResult:
        """Execute the main conversation loop.

        Args:
            goal: The user's goal/prompt
            system_prompt: System prompt template
            tools: List of available tool functions
            options: Model options
            key: API key

        Returns:
            LoopResult with execution details
        """
        if options is None:
            options = {}

        current_user_directive = goal
        final_response = ""
        error = None

        try:
            while True:
                self.total_iterations += 1
                self.turn_count += 1

                self._log_iteration_start()

                # Execute conversation chain
                response_text, had_tool_calls = self._execute_chain(
                    current_user_directive, system_prompt, tools, options, key
                )

                final_response = response_text

                # Check exit conditions
                if self._should_exit(response_text, had_tool_calls):
                    break

                # Handle turn limits
                if self._check_turn_limit():
                    break

                # Prepare next iteration
                current_user_directive = self._get_next_directive(goal, had_tool_calls)

        except Exception as e:
            error = str(e)
            click.echo(f"Error in conversation loop: {e}", err=True)

        return LoopResult(
            completed="TASK_COMPLETE" in final_response.upper(),
            iterations=self.total_iterations,
            final_response=final_response,
            error=error,
        )

    def _execute_chain(
        self,
        directive: str,
        system_prompt: str,
        tools: List[ToolFunction],
        options: Dict[str, Any],
        key: Optional[str],
    ) -> tuple[str, bool]:
        """Execute a single conversation chain."""
        chain_kwargs = {
            "system": system_prompt,
            "options": options,
            "tools": tools,
            "chain_limit": self.config.internal_chain_limit,
            "key": key,
        }

        # Add debug/approval callbacks if configured
        if self.config.tools_debug:
            chain_kwargs["after_call"] = self._debug_tool_call
        if self.config.tools_approve:
            chain_kwargs["before_call"] = self._approve_tool_call

        if not directive and not self.conversation.responses:
            raise ConversationError("No directive provided and no conversation history")

        response_chain = self.conversation.chain(directive, **chain_kwargs)

        # Stream response
        response_text = ""
        had_tool_calls = False

        try:
            click.echo(f"LLM (iteration {self.total_iterations}): ", nl=False, err=True)
            for chunk in response_chain:
                print(chunk, end="")
                response_text += chunk
                sys.stdout.flush()
            print()

            if hasattr(response_chain, "_responses") and response_chain._responses:
                last_response = response_chain._responses[-1]
                had_tool_calls = bool(getattr(last_response, "_tool_calls", None))

        except Exception as e:
            raise ConversationError(f"Error during response streaming: {e}")

        return response_text, had_tool_calls

    def _should_exit(self, response_text: str, had_tool_calls: bool) -> bool:
        """Check if loop should exit based on response."""
        if "TASK_COMPLETE" in response_text.upper():
            click.echo("LLM indicated TASK_COMPLETE.", err=True)
            return True

        if not had_tool_calls:
            click.echo(
                "LLM provided a textual response without requesting more tools.",
                err=True,
            )
            return not click.confirm(
                "Loop iteration complete. Task might be finished. Continue working towards the goal?",
                default=False,
            )

        return False

    def _check_turn_limit(self) -> bool:
        """Check if turn limit reached and handle continuation."""
        if self.config.max_turns > 0 and self.turn_count >= self.config.max_turns:
            if not click.confirm(
                f"Reached {self.config.max_turns} turns in this segment. Continue loop?",
                default=True,
            ):
                return True
            self.turn_count = 0
        return False

    def _get_next_directive(self, original_goal: str, had_tool_calls: bool) -> str:
        """Get the next directive for the conversation."""
        if had_tool_calls:
            return ""  # Continue with tool results

        # Prompt user for next instruction
        directive = click.prompt(
            "Next instruction for the loop (or type 'exit' to stop, or press Enter to let LLM decide based on history)",
            default="",
            prompt_suffix="> ",
            show_default=False,
        )

        if directive.lower() == "exit":
            raise ConversationError("User requested exit")

        if not directive.strip():
            return f"Continue working on the goal: {original_goal}"

        return directive

    def _log_iteration_start(self) -> None:
        """Log the start of an iteration."""
        max_turns_display = (
            "unlimited" if self.config.max_turns == 0 else self.config.max_turns
        )
        click.echo(
            f"\n--- Loop Iteration {self.total_iterations} (Turn {self.turn_count}/{max_turns_display}) ---",
            err=True,
        )

    def _debug_tool_call(self, call, result) -> None:
        """Debug tool call callback."""
        click.echo(f"Tool call debug: {call}", err=True)

    def _approve_tool_call(self, call) -> bool:
        """Tool approval callback."""
        return click.confirm(f"Approve tool call: {call}?", default=True)
