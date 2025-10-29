from contextvars import ContextVar
from typing import TYPE_CHECKING, override

from kosong.base.message import ToolCall
from kosong.tooling import HandleResult, SimpleToolset

if TYPE_CHECKING:
    from kimi_cli.soul.context import Context

current_tool_call = ContextVar[ToolCall | None]("current_tool_call", default=None)
current_context = ContextVar["Context | None"]("current_context", default=None)


def get_current_tool_call_or_none() -> ToolCall | None:
    """
    Get the current tool call or None.
    Expect to be not None when called from a `__call__` method of a tool.
    """
    return current_tool_call.get()


def get_current_context_or_none() -> "Context | None":
    """
    Get the current context or None.
    Expect to be not None when called from a `__call__` method of a tool within a soul.
    """
    return current_context.get()


class CustomToolset(SimpleToolset):
    @override
    def handle(self, tool_call: ToolCall) -> HandleResult:
        token = current_tool_call.set(tool_call)
        try:
            return super().handle(tool_call)
        finally:
            current_tool_call.reset(token)
