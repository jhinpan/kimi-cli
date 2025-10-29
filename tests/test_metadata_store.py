"""Tests for MetadataStore functionality."""

import json
from pathlib import Path

import pytest

from kimi_cli.soul.metadata_store import MetadataStore, PinRecord, TodoTaskMap


@pytest.fixture
def temp_meta_file(tmp_path: Path) -> Path:
    """Create a temporary metadata file path."""
    return tmp_path / "test.meta.jsonl"


@pytest.fixture
def meta_store(temp_meta_file: Path) -> MetadataStore:
    """Create a MetadataStore instance."""
    return MetadataStore(temp_meta_file)


@pytest.mark.asyncio
async def test_metadata_store_initialization(temp_meta_file: Path):
    """Test MetadataStore initialization."""
    store = MetadataStore(temp_meta_file)
    assert store._path == temp_meta_file
    assert store.current_step == 0


@pytest.mark.asyncio
async def test_tag_creates_record(meta_store: MetadataStore, temp_meta_file: Path):
    """Test that tagging creates a proper record in the metadata file."""
    await meta_store.tag(
        task_id="task_abc123",
        message_ids=["msg1", "msg2"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=3,
        notes="Test tag",
    )

    # Verify file exists and contains the record
    assert temp_meta_file.exists()

    with open(temp_meta_file) as f:
        line = f.readline()
        record = json.loads(line)

    assert record["type"] == "tag"
    assert record["task_id"] == "task_abc123"
    assert record["message_ids"] == ["msg1", "msg2"]
    assert record["policy"] == "pin_outcome"
    assert record["ttl_steps"] == 100
    assert record["importance"] == 3
    assert record["notes"] == "Test tag"
    assert record["created_at_step"] == 0


@pytest.mark.asyncio
async def test_map_todo_task(meta_store: MetadataStore, temp_meta_file: Path):
    """Test creating a todo-task mapping."""
    await meta_store.map_todo_task("todo_xyz", "task_abc")

    assert temp_meta_file.exists()

    with open(temp_meta_file) as f:
        line = f.readline()
        record = json.loads(line)

    assert record["type"] == "map"
    assert record["todo_id"] == "todo_xyz"
    assert record["task_id"] == "task_abc"


@pytest.mark.asyncio
async def test_record_artifact(meta_store: MetadataStore, temp_meta_file: Path):
    """Test recording an artifact."""
    await meta_store.record_artifact(
        task_id="task_abc", kind="diff", path="/path/to/file.py", bytes_size=1024
    )

    assert temp_meta_file.exists()

    with open(temp_meta_file) as f:
        line = f.readline()
        record = json.loads(line)

    assert record["type"] == "artifact"
    assert record["task_id"] == "task_abc"
    assert record["kind"] == "diff"
    assert record["path"] == "/path/to/file.py"
    assert record["bytes"] == 1024


@pytest.mark.asyncio
async def test_list_active_pins_empty(meta_store: MetadataStore):
    """Test listing active pins when metadata file doesn't exist."""
    pins = await meta_store.list_active_pins()
    assert pins == []


@pytest.mark.asyncio
async def test_list_active_pins_with_records(meta_store: MetadataStore):
    """Test listing active pins with multiple records."""
    # Add several pins with different importance levels
    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg1"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=3,
    )
    await meta_store.tag(
        task_id="task_2",
        message_ids=["msg2"],
        policy="pin_process",
        ttl_steps=50,
        importance=5,
    )
    await meta_store.tag(
        task_id="task_3",
        message_ids=["msg3"],
        policy="pin_outcome",
        ttl_steps=200,
        importance=1,
    )

    pins = await meta_store.list_active_pins(current_step=0)

    # Should have all 3 pins
    assert len(pins) == 3

    # Should be sorted by importance (descending)
    assert pins[0].importance == 5
    assert pins[1].importance == 3
    assert pins[2].importance == 1

    # Verify pin details
    assert pins[0].task_id == "task_2"
    assert pins[0].policy == "pin_process"
    assert pins[0].ttl_steps == 50


@pytest.mark.asyncio
async def test_list_active_pins_with_ttl_expiration(meta_store: MetadataStore):
    """Test that expired pins are not returned."""
    # Add a pin with TTL of 50 steps
    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg1"],
        policy="pin_outcome",
        ttl_steps=50,
        importance=3,
    )

    # At step 0, pin should be active
    pins = await meta_store.list_active_pins(current_step=0)
    assert len(pins) == 1

    # At step 49, pin should still be active
    pins = await meta_store.list_active_pins(current_step=49)
    assert len(pins) == 1

    # At step 50, pin should be expired
    pins = await meta_store.list_active_pins(current_step=50)
    assert len(pins) == 0

    # At step 100, pin should definitely be expired
    pins = await meta_store.list_active_pins(current_step=100)
    assert len(pins) == 0


@pytest.mark.asyncio
async def test_list_active_pins_ignores_non_tag_records(meta_store: MetadataStore):
    """Test that list_active_pins only returns tag records."""
    # Add different types of records
    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg1"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=3,
    )
    await meta_store.map_todo_task("todo_1", "task_1")
    await meta_store.record_artifact("task_1", "diff")

    pins = await meta_store.list_active_pins(current_step=0)

    # Should only return the tag record
    assert len(pins) == 1
    assert pins[0].task_id == "task_1"


@pytest.mark.asyncio
async def test_list_todo_task_maps_empty(meta_store: MetadataStore):
    """Test listing todo-task maps when metadata file doesn't exist."""
    maps = await meta_store.list_todo_task_maps()
    assert maps == []


@pytest.mark.asyncio
async def test_list_todo_task_maps(meta_store: MetadataStore):
    """Test listing todo-task mappings."""
    await meta_store.map_todo_task("todo_1", "task_abc")
    await meta_store.map_todo_task("todo_2", "task_xyz")
    await meta_store.map_todo_task("todo_3", "task_def")

    maps = await meta_store.list_todo_task_maps()

    assert len(maps) == 3
    assert maps[0].todo_id == "todo_1"
    assert maps[0].task_id == "task_abc"
    assert maps[1].todo_id == "todo_2"
    assert maps[1].task_id == "task_xyz"


@pytest.mark.asyncio
async def test_list_todo_task_maps_ignores_non_map_records(meta_store: MetadataStore):
    """Test that list_todo_task_maps only returns map records."""
    # Add different types of records
    await meta_store.map_todo_task("todo_1", "task_1")
    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg1"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=3,
    )
    await meta_store.record_artifact("task_1", "diff")

    maps = await meta_store.list_todo_task_maps()

    # Should only return the map record
    assert len(maps) == 1
    assert maps[0].todo_id == "todo_1"


@pytest.mark.asyncio
async def test_increment_step(meta_store: MetadataStore):
    """Test step counter increment."""
    assert meta_store.current_step == 0

    meta_store.increment_step()
    assert meta_store.current_step == 1

    meta_store.increment_step()
    assert meta_store.current_step == 2


@pytest.mark.asyncio
async def test_multiple_tags_for_same_task(meta_store: MetadataStore):
    """Test that multiple tags can be created for the same task."""
    # Add multiple tags for the same task
    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg1", "msg2"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=3,
    )

    meta_store.increment_step()

    await meta_store.tag(
        task_id="task_1",
        message_ids=["msg3", "msg4"],
        policy="pin_process",
        ttl_steps=50,
        importance=4,
    )

    pins = await meta_store.list_active_pins(current_step=1)

    # Should have both tags
    assert len(pins) == 2
    assert all(p.task_id == "task_1" for p in pins)


@pytest.mark.asyncio
async def test_pin_record_dataclass():
    """Test PinRecord dataclass creation."""
    pin = PinRecord(
        task_id="task_abc",
        message_ids=["msg1", "msg2"],
        policy="pin_outcome",
        ttl_steps=100,
        importance=4,
        notes="Test pin",
        created_at_step=5,
    )

    assert pin.task_id == "task_abc"
    assert pin.message_ids == ["msg1", "msg2"]
    assert pin.policy == "pin_outcome"
    assert pin.ttl_steps == 100
    assert pin.importance == 4
    assert pin.notes == "Test pin"
    assert pin.created_at_step == 5


@pytest.mark.asyncio
async def test_todo_task_map_dataclass():
    """Test TodoTaskMap dataclass creation."""
    todo_map = TodoTaskMap(todo_id="todo_xyz", task_id="task_abc")

    assert todo_map.todo_id == "todo_xyz"
    assert todo_map.task_id == "task_abc"
