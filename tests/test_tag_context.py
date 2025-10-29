"""Tests for TagContext tool."""

from pathlib import Path

import pytest
import pytest_asyncio
from kosong.base.message import Message
from kosong.tooling import ToolOk

from kimi_cli.soul.context import Context
from kimi_cli.soul.toolset import current_context
from kimi_cli.tools.tag_context import Params, TagContext


@pytest.fixture
def temp_history_file(tmp_path: Path) -> Path:
    """Create a temporary history file path."""
    return tmp_path / "history.jsonl"


@pytest_asyncio.fixture
async def context_with_messages(temp_history_file: Path) -> Context:
    """Create a Context instance with some test messages."""
    context = Context(temp_history_file)

    # Add some test messages
    await context.append_message(
        [
            Message(role="user", content="Test user message"),
            Message(role="assistant", content="Test assistant response"),
            Message(role="tool", content="Test tool result"),
        ]
    )

    return context


@pytest_asyncio.fixture
async def tag_context_tool(context_with_messages: Context) -> TagContext:
    """Create a TagContext tool instance with context set."""
    # Set the context variable so the tool can access it
    token = current_context.set(context_with_messages)
    try:
        yield TagContext()
    finally:
        current_context.reset(token)


@pytest.mark.asyncio
async def test_tag_context_with_explicit_message_ids(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext with explicitly provided message IDs."""
    params = Params(
        task_id="task_abc123",
        message_ids=["msg1", "msg2"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=4,
        notes="Test tag",
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)
    assert "task_abc123" in result.output
    assert "2 message(s)" in result.output
    assert "outcome retention" in result.output
    assert "4/5" in result.output
    assert "100 steps" in result.output
    assert "Test tag" in result.output

    # Verify the tag was stored in metadata
    pins = await context_with_messages.meta.list_active_pins(current_step=0)
    assert len(pins) == 1
    assert pins[0].task_id == "task_abc123"
    assert pins[0].message_ids == ["msg1", "msg2"]
    assert pins[0].policy == "pin_outcome"
    assert pins[0].importance == 4


@pytest.mark.asyncio
async def test_tag_context_with_inferred_message_ids(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext with message IDs inferred from recent messages."""
    params = Params(
        task_id="task_xyz789",
        policy="pin_process",
        ttl_steps=50,
        importance=3,
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)
    assert "task_xyz789" in result.output
    # Should have inferred message IDs from recent assistant/tool messages
    assert "message(s)" in result.output
    assert "process retention" in result.output

    # Verify the tag was stored
    pins = await context_with_messages.meta.list_active_pins(current_step=0)
    assert len(pins) == 1
    assert pins[0].task_id == "task_xyz789"
    assert len(pins[0].message_ids) > 0  # Should have inferred some IDs


@pytest.mark.asyncio
async def test_tag_context_with_auto_policy(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext with auto policy."""
    params = Params(
        task_id="task_auto",
        message_ids=["msg1"],
        policy="auto",
        importance=2,
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)
    assert "task_auto" in result.output
    assert "automatic policy" in result.output


@pytest.mark.asyncio
async def test_tag_context_without_notes(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext without optional notes."""
    params = Params(
        task_id="task_no_notes",
        message_ids=["msg1"],
        policy="pin_outcome",
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)
    # Should not contain "Notes:" in output
    assert "Notes:" not in result.output


@pytest.mark.asyncio
async def test_tag_context_with_notes(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext with notes."""
    params = Params(
        task_id="task_with_notes",
        message_ids=["msg1"],
        policy="pin_outcome",
        notes="Important fix for bug #123",
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)
    assert "Notes: Important fix for bug #123" in result.output


@pytest.mark.asyncio
async def test_tag_context_empty_context(tmp_path: Path):
    """Test TagContext when context has no recent messages."""
    temp_file = tmp_path / "test_empty_context.jsonl"
    context = Context(temp_file)

    # Set the context variable
    token = current_context.set(context)
    try:
        tool = TagContext()

        params = Params(
            task_id="task_empty",
            policy="pin_outcome",
        )

        result = await tool(params)

        assert isinstance(result, ToolOk)
        assert "No recent messages found" in result.output
    finally:
        current_context.reset(token)


@pytest.mark.asyncio
async def test_tag_context_default_values(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test TagContext with default parameter values."""
    params = Params(
        task_id="task_defaults",
        message_ids=["msg1"],
    )

    result = await tag_context_tool(params)

    assert isinstance(result, ToolOk)

    # Verify defaults were used
    pins = await context_with_messages.meta.list_active_pins(current_step=0)
    pin = pins[-1]  # Get the most recently added pin
    assert pin.policy == "pin_outcome"  # Default policy
    assert pin.ttl_steps == 100  # Default TTL
    assert pin.importance == 3  # Default importance


@pytest.mark.asyncio
async def test_tag_context_multiple_tags(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test creating multiple tags for different tasks."""
    # Create first tag
    params1 = Params(
        task_id="task_1",
        message_ids=["msg1"],
        importance=5,
    )
    await tag_context_tool(params1)

    # Create second tag
    params2 = Params(
        task_id="task_2",
        message_ids=["msg2"],
        importance=2,
    )
    await tag_context_tool(params2)

    # Verify both tags exist
    pins = await context_with_messages.meta.list_active_pins(current_step=0)
    assert len(pins) == 2

    # Verify sorting by importance
    assert pins[0].importance == 5
    assert pins[1].importance == 2


@pytest.mark.asyncio
async def test_tag_context_importance_validation():
    """Test that importance parameter validation works."""
    # Test with invalid importance (too low)
    with pytest.raises(Exception):  # Pydantic will raise validation error
        Params(
            task_id="task_invalid",
            message_ids=["msg1"],
            importance=0,  # Invalid: must be >= 1
        )

    # Test with invalid importance (too high)
    with pytest.raises(Exception):  # Pydantic will raise validation error
        Params(
            task_id="task_invalid",
            message_ids=["msg1"],
            importance=6,  # Invalid: must be <= 5
        )


@pytest.mark.asyncio
async def test_tag_context_ttl_validation():
    """Test that ttl_steps parameter validation works."""
    # Test with invalid TTL (too low)
    with pytest.raises(Exception):  # Pydantic will raise validation error
        Params(
            task_id="task_invalid",
            message_ids=["msg1"],
            ttl_steps=0,  # Invalid: must be >= 1
        )


@pytest.mark.asyncio
async def test_tag_context_policy_values(
    tag_context_tool: TagContext, context_with_messages: Context
):
    """Test all valid policy values."""
    policies = ["pin_outcome", "pin_process", "auto"]

    for policy in policies:
        params = Params(
            task_id=f"task_{policy}",
            message_ids=["msg1"],
            policy=policy,
        )

        result = await tag_context_tool(params)
        assert isinstance(result, ToolOk)

    # Verify all tags were created
    pins = await context_with_messages.meta.list_active_pins(current_step=0)
    assert len(pins) == 3
