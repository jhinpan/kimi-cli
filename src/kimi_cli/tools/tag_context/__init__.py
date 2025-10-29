"""
TagContext tool - Tag messages for retention during context compaction.

This tool allows the agent to mark specific messages as important for retention
during context compaction, supporting KV-cache-native context management.
"""

from pathlib import Path
from typing import Literal, override

from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel, Field

from kimi_cli.soul.toolset import get_current_context_or_none


class Params(BaseModel):
    task_id: str = Field(description="The task ID these messages belong to")
    policy: Literal["pin_outcome", "pin_process", "auto"] = Field(
        default="pin_outcome",
        description=(
            "Retention policy: 'pin_outcome' keeps concise results, "
            "'pin_process' keeps detailed process logs, "
            "'auto' decides automatically"
        ),
    )
    message_ids: list[str] | None = Field(
        default=None,
        description=(
            "List of message IDs to tag. If None, will infer from recent "
            "assistant and tool messages related to this task."
        ),
    )
    ttl_steps: int = Field(
        default=100,
        description="Time-to-live in agent steps before this tag expires",
        ge=1,
    )
    importance: int = Field(
        default=3,
        description="Priority level (1-5, where 5 is most important)",
        ge=1,
        le=5,
    )
    notes: str | None = Field(
        default=None, description="Optional human-readable notes about this tag"
    )


class TagContext(CallableTool2[Params]):
    name: str = "TagContext"
    description: str = (Path(__file__).parent / "tag_context.md").read_text(encoding="utf-8")
    params: type[Params] = Params

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        # Get the current context
        context = get_current_context_or_none()
        if context is None:
            return ToolError(
                message="Context not available. This tool must be run within an active soul session.",
                brief="Context not available",
            )

        # Infer message_ids if not provided
        if params.message_ids is None:
            # Get recent assistant and tool messages
            message_ids = await context.get_recent_message_ids(n=5, roles={"assistant", "tool"})
            if not message_ids:
                return ToolOk(
                    output=(
                        f"No recent messages found to tag for task_id={params.task_id}. "
                        "Please specify message_ids explicitly."
                    )
                )
        else:
            message_ids = params.message_ids

        # Tag the messages in the metadata store
        await context.meta.tag(
            task_id=params.task_id,
            message_ids=message_ids,
            policy=params.policy,
            ttl_steps=params.ttl_steps,
            importance=params.importance,
            notes=params.notes,
        )

        # Build output summary
        policy_desc = {
            "pin_outcome": "outcome retention (concise results)",
            "pin_process": "process retention (detailed logs)",
            "auto": "automatic policy selection",
        }

        output = (
            f"Tagged {len(message_ids)} message(s) for task_id={params.task_id}\n"
            f"- Policy: {policy_desc[params.policy]}\n"
            f"- Importance: {params.importance}/5\n"
            f"- TTL: {params.ttl_steps} steps"
        )

        if params.notes:
            output += f"\n- Notes: {params.notes}"

        return ToolOk(output=output)
