import secrets
from pathlib import Path
from typing import Literal, override

from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from pydantic import BaseModel, Field


class Todo(BaseModel):
    title: str = Field(description="The title of the todo", min_length=1)
    status: Literal["Pending", "In Progress", "Done"] = Field(description="The status of the todo")
    id: str | None = Field(default=None, description="Stable todo id (e.g., todo_ab12cd34)")
    tags: list[str] = Field(default_factory=list, description="Free-form tags for categorization")
    related_task_ids: list[str] = Field(default_factory=list, description="Linked task IDs")


class Params(BaseModel):
    todos: list[Todo] = Field(description="The updated todo list")


class SetTodoList(CallableTool2[Params]):
    name: str = "SetTodoList"
    description: str = (Path(__file__).parent / "set_todo_list.md").read_text(encoding="utf-8")
    params: type[Params] = Params

    @override
    async def __call__(self, params: Params) -> ToolReturnType:
        rendered = ""
        for todo in params.todos:
            # Auto-generate todo ID if not provided
            if todo.id is None:
                todo.id = f"todo_{secrets.token_hex(4)}"

            rendered += f"- {todo.title} [{todo.status}]\n"

            # Add metadata footer if there are tags or related tasks
            metadata_parts = []
            if todo.tags:
                metadata_parts.append(f"tags={','.join(todo.tags)}")
            if todo.related_task_ids:
                metadata_parts.append(f"related_tasks={','.join(todo.related_task_ids)}")

            if metadata_parts or todo.id:
                metadata_parts.insert(0, f"todo_id={todo.id}")
                rendered += f"  [{'; '.join(metadata_parts)}]\n"

        return ToolOk(output=rendered)
