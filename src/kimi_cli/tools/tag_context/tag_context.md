Tag messages for retention during context compaction.

This tool marks specific messages as important for retention when context compaction occurs.
It supports KV-cache-native context management by allowing you to specify which messages
should be preserved across compaction cycles.

## When to Use

- After completing a task that produced important results
- When generating code, diffs, or other artifacts that should persist
- For marking critical debugging information or command outputs
- To ensure key findings from research or analysis are retained

## Retention Policies

- **pin_outcome**: Keeps concise, factual results (diffs, final code, command outputs). Default and recommended.
- **pin_process**: Keeps detailed process logs, reasoning traces. Use sparingly as it consumes more tokens.
- **auto**: System automatically decides based on content type.

## Importance Levels

- **1-2**: Low priority, may be dropped first during aggressive compaction
- **3**: Normal priority (default)
- **4-5**: High priority, strongly retained

## TTL (Time-to-Live)

Messages are retained for the specified number of agent steps before the tag expires.
Default is 100 steps, which is suitable for most use cases.

## Examples

Tag recent task results for outcome retention:
```
TagContext(task_id="task_abc123", policy="pin_outcome", importance=4)
```

Tag specific messages with custom TTL:
```
TagContext(
    task_id="task_xyz789",
    message_ids=["msg-uuid-1", "msg-uuid-2"],
    policy="pin_process",
    ttl_steps=50,
    importance=3,
    notes="Debug trace for authentication bug"
)
```
