import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from typing import Any, NamedTuple, Protocol, runtime_checkable

from kosong.base.message import ContentPart

from kimi_cli.utils.logging import logger
from kimi_cli.wire import Wire, WireUISide
from kimi_cli.wire.message import WireMessage


class LLMNotSet(Exception):
    """Raised when the LLM is not set."""

    pass


class MaxStepsReached(Exception):
    """Raised when the maximum number of steps is reached."""

    n_steps: int
    """The number of steps that have been taken."""

    def __init__(self, n_steps: int):
        self.n_steps = n_steps


class StatusSnapshot(NamedTuple):
    context_usage: float
    """The usage of the context, in percentage."""


@runtime_checkable
class Soul(Protocol):
    @property
    def name(self) -> str:
        """The name of the soul."""
        ...

    @property
    def model(self) -> str:
        """The LLM model used by the soul. Empty string indicates no LLM configured."""
        ...

    @property
    def status(self) -> StatusSnapshot:
        """The current status of the soul. The returned value is immutable."""
        ...

    async def run(self, user_input: str | list[ContentPart]):
        """
        Run the agent with the given user input until the max steps or no more tool calls.

        Args:
            user_input (str | list[ContentPart]): The user input to the agent.

        Raises:
            LLMNotSet: When the LLM is not set.
            ChatProviderError: When the LLM provider returns an error.
            MaxStepsReached: When the maximum number of steps is reached.
            asyncio.CancelledError: When the run is cancelled by user.
        """
        ...


type UILoopFn = Callable[[WireUISide], Coroutine[Any, Any, None]]
"""A long-running async function to visualize the agent behavior."""


class RunCancelled(Exception):
    """The run was cancelled by the cancel event."""


async def run_soul(
    soul: "Soul",
    user_input: str | list[ContentPart],
    ui_loop_fn: UILoopFn,
    cancel_event: asyncio.Event,
) -> None:
    """
    Run the soul with the given user input, connecting it to the UI loop with a wire.

    `cancel_event` is a outside handle that can be used to cancel the run. When the
    event is set, the run will be gracefully stopped and a `RunCancelled` will be raised.

    Raises:
        LLMNotSet: When the LLM is not set.
        ChatProviderError: When the LLM provider returns an error.
        MaxStepsReached: When the maximum number of steps is reached.
        RunCancelled: When the run is cancelled by the cancel event.
    """
    wire = Wire()
    wire_token = _current_wire.set(wire)

    logger.debug("Starting UI loop with function: {ui_loop_fn}", ui_loop_fn=ui_loop_fn)
    ui_task = asyncio.create_task(ui_loop_fn(wire.ui_side))

    logger.debug("Starting soul run")
    soul_task = asyncio.create_task(soul.run(user_input))

    cancel_event_task = asyncio.create_task(cancel_event.wait())
    await asyncio.wait(
        [soul_task, cancel_event_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    try:
        if cancel_event.is_set():
            logger.debug("Cancelling the run task")
            soul_task.cancel()
            try:
                await soul_task
            except asyncio.CancelledError:
                raise RunCancelled from None
        else:
            assert soul_task.done()  # either stop event is set or the run task is done
            cancel_event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cancel_event_task
            soul_task.result()  # this will raise if any exception was raised in the run task
    finally:
        logger.debug("Shutting down the UI loop")
        # shutting down the wire should break the UI loop
        wire.shutdown()
        try:
            await asyncio.wait_for(ui_task, timeout=0.5)
        except asyncio.QueueShutDown:
            logger.debug("UI loop shut down")
            pass
        except TimeoutError:
            logger.warning("UI loop timed out")

        _current_wire.reset(wire_token)


_current_wire = ContextVar[Wire | None]("current_wire", default=None)


def get_wire_or_none() -> Wire | None:
    """
    Get the current wire or None.
    Expect to be not None when called from anywhere in the agent loop.
    """
    return _current_wire.get()


def wire_send(msg: WireMessage) -> None:
    """
    Send a wire message to the current wire.
    Take this as `print` and `input` for souls.
    Souls should always use this function to send wire messages.
    """
    wire = get_wire_or_none()
    assert wire is not None, "Wire is expected to be set when soul is running"
    wire.soul_side.send(msg)
