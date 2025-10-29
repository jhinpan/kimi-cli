# ruff: noqa

from inline_snapshot import snapshot
from kosong.base.tool import Tool
import pytest

from kimi_cli.agentspec import DEFAULT_AGENT_FILE
from kimi_cli.soul.agent import load_agent
from kimi_cli.soul.runtime import Runtime


@pytest.mark.asyncio
async def test_default_agent(runtime: Runtime):
    agent = await load_agent(DEFAULT_AGENT_FILE, runtime, mcp_configs=[])
    assert agent.system_prompt.replace(
        f"{runtime.builtin_args.KIMI_WORK_DIR}", "/path/to/work/dir"
    ) == snapshot(
        """\
You are Kimi CLI. You are an interactive CLI agent specializing in software engineering tasks. Your primary goal is to help users safely and efficiently, adhering strictly to the following instructions and utilizing your available tools.



# Prompt and Tool Use

The user's requests are provided in natural language within `user` messages, which may contain code snippets, logs, file paths, or specific requirements. ALWAYS follow the user's requests, always stay on track. Do not do anything that is not asked.

When handling the user's request, you can call available tools to accomplish the task. When calling tools, do not provide explanations because the tool calls themselves should be self-explanatory. You MUST follow the description of each tool and its parameters when calling tools.

You have the capability to output any number of tool calls in a single response. If you anticipate making multiple non-interfering tool calls, you are HIGHLY RECOMMENDED to make them in parallel to significantly improve efficiency. This is very important to your performance.

The results of the tool calls will be returned to you in a `tool` message. In some cases, non-plain-text content might be sent as a `user` message following the `tool` message. You must decide on your next action based on the tool call results, which could be one of the following: 1. Continue working on the task, 2. Inform the user that the task is completed or has failed, or 3. Ask the user for more information.

The system may, where appropriate, insert hints or information wrapped in `<system>` and `</system>` tags within `user` or `tool` messages. This information is relevant to the current task or tool calls, may or may not be important to you. Take this info into consideration when determining your next action.

When responding to the user, you MUST use the SAME language as the user, unless explicitly instructed to do otherwise.

# General Coding Guidelines

Always think carefully. Be patient and thorough. Do not give up too early.

ALWAYS, keep it stupidly simple. Do not overcomplicate things.

When building something from scratch, you should:

- Understand the user's requirements.
- Design the architecture and make a plan for the implementation.
- Write the code in a modular and maintainable way.

When working on existing codebase, you should:

- Understand the codebase and the user's requirements. Identify the ultimate goal and the most important criteria to achieve the goal.
- For a bug fix, you typically need to check error logs or failed tests, scan over the codebase to find the root cause, and figure out a fix. If user mentioned any failed tests, you should make sure they pass after the changes.
- For a feature, you typically need to design the architecture, and write the code in a modular and maintainable way, with minimal intrusions to existing code. Add new tests if the project already has tests.
- For a code refactoring, you typically need to update all the places that call the code you are refactoring if the interface changes. DO NOT change any existing logic especially in tests, focus only on fixing any errors caused by the interface changes.
- Make MINIMAL changes to achieve the goal. This is very important to your performance.
- Follow the coding style of existing code in the project.

# Working Environment

## Operating System

The operating environment is not in a sandbox. Any action especially mutation you do will immediately affect the user's system. So you MUST be extremely cautious. Unless being explicitly instructed to do so, you should never access (read/write/execute) files outside of the working directory.

## Working Directory

The current working directory is `/path/to/work/dir`. This should be considered as the project root if you are instructed to perform tasks on the project. Every file system operation will be relative to the working directory if you do not explicitly specify the absolute path. Tools may require absolute paths for some parameters, if so, you should strictly follow the requirements.

The directory listing of current working directory is:

```
Test ls content
```

Use this as your basic understanding of the project structure.

## Date and Time

The current date and time in ISO format is `1970-01-01T00:00:00+00:00`. This is only a reference for you when searching the web, or checking file modification time, etc. If you need the exact time, use Bash tool with proper command.

# Project Information

Markdown files named `AGENTS.md` usually contain the background, structure, coding styles, user preferences and other relevant information about the project. You should use this information to understand the project and the user's preferences. `AGENTS.md` files may exist at different locations in the project, but typically there is one in the project root. The following content between two `---`s is the content of the root-level `AGENTS.md` file.

`/path/to/work/dir/AGENTS.md`:

---

Test agents content

---\
"""
    )
    assert agent.toolset.tools == snapshot(
        [
            Tool(
                name="Task",
                description="""\
Spawn a subagent to perform a specific task. Subagent will be spawned with a fresh context without any history of yours.

**Context Isolation**

Context isolation is one of the key benefits of using subagents. By delegating tasks to subagents, you can keep your main context clean and focused on the main goal requested by the user.

Here are some scenarios you may want this tool for context isolation:

- You wrote some code and it did not work as expected. In this case you can spawn a subagent to fix the code, asking the subagent to return how it is fixed. This can potentially benefit because the detailed process of fixing the code may not be relevant to your main goal, and may clutter your context.
- When you need some latest knowledge of a specific library, framework or technology to proceed with your task, you can spawn a subagent to search on the internet for the needed information and return to you the gathered relevant information, for example code examples, API references, etc. This can avoid ton of irrelevant search results in your own context.

DO NOT directly forward the user prompt to Task tool. DO NOT simply spawn Task tool for each todo item. This will cause the user confused because the user cannot see what the subagent do. Only you can see the response from the subagent. So, only spawn subagents for very specific and narrow tasks like fixing a compilation error, or searching for a specific solution.

**Parallel Multi-Tasking**

Parallel multi-tasking is another key benefit of this tool. When the user request involves multiple subtasks that are independent of each other, you can use Task tool multiple times in a single response to let subagents work in parallel for you.

Examples:

- User requests to code, refactor or fix multiple modules/files in a project, and they can be tested independently. In this case you can spawn multiple subagents each working on a different module/file.
- When you need to analyze a huge codebase (> hundreds of thousands of lines), you can spawn multiple subagents each exploring on a different part of the codebase and gather the summarized results.
- When you need to search the web for multiple queries, you can spawn multiple subagents for better efficiency.

**Available Subagents:**

- `coder`: Good at general software engineering tasks.
""",
                parameters={
                    "properties": {
                        "description": {
                            "description": "A short (3-5 word) description of the task",
                            "type": "string",
                        },
                        "subagent_name": {
                            "description": "The name of the specialized subagent to use for this task",
                            "type": "string",
                        },
                        "prompt": {
                            "description": "The task for the subagent to perform. You must provide a detailed prompt with all necessary background information because the subagent cannot see anything in your context.",
                            "type": "string",
                        },
                        "task_id": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "description": "Optional stable task ID (e.g., task_ab12cd34)",
                        },
                    },
                    "required": ["description", "subagent_name", "prompt"],
                    "type": "object",
                },
            ),
            Tool(
                name="Think",
                description="Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.\n",
                parameters={
                    "properties": {
                        "thought": {
                            "description": "A thought to think about.",
                            "type": "string",
                        }
                    },
                    "required": ["thought"],
                    "type": "object",
                },
            ),
            Tool(
                name="SetTodoList",
                description="""\
Update the whole todo list.

Todo list is a simple yet powerful tool to help you get things done. You typically want to use this tool when the given task involves multiple subtasks/milestones, or, multiple tasks are given in a single request. This tool can help you to break down the task and track the progress.

This is the only todo list tool available to you. That said, each time you want to operate on the todo list, you need to update the whole. Make sure to maintain the todo items and their statuses properly.

Once you finished a subtask/milestone, remember to update the todo list to reflect the progress. Also, you can give yourself a self-encouragement to keep you motivated.

Abusing this tool to track too small steps will just waste your time and make your context messy. For example, here are some cases you should not use this tool:

- When the user just simply ask you a question. E.g. "What language and framework is used in the project?", "What is the best practice for x?"
- When it only takes a few steps/tool calls to complete the task. E.g. "Fix the unit test function 'test_xxx'", "Refactor the function 'xxx' to make it more solid."
- When the user prompt is very specific and the only thing you need to do is brainlessly following the instructions. E.g. "Replace xxx to yyy in the file zzz", "Create a file xxx with content yyy."

However, do not get stuck in a rut. Be flexible. Sometimes, you may try to use todo list at first, then realize the task is too simple and you can simply stop using it; or, sometimes, you may realize the task is complex after a few steps and then you can start using todo list to break it down.
""",
                parameters={
                    "$defs": {
                        "Todo": {
                            "properties": {
                                "title": {
                                    "description": "The title of the todo",
                                    "minLength": 1,
                                    "type": "string",
                                },
                                "status": {
                                    "description": "The status of the todo",
                                    "enum": ["Pending", "In Progress", "Done"],
                                    "type": "string",
                                },
                                "id": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "default": None,
                                    "description": "Stable todo id (e.g., todo_ab12cd34)",
                                },
                                "tags": {
                                    "description": "Free-form tags for categorization",
                                    "items": {"type": "string"},
                                    "type": "array",
                                },
                                "related_task_ids": {
                                    "description": "Linked task IDs",
                                    "items": {"type": "string"},
                                    "type": "array",
                                },
                            },
                            "required": ["title", "status"],
                            "type": "object",
                        }
                    },
                    "properties": {
                        "todos": {
                            "description": "The updated todo list",
                            "items": {"$ref": "#/$defs/Todo"},
                            "type": "array",
                        }
                    },
                    "required": ["todos"],
                    "type": "object",
                },
            ),
            Tool(
                name="TagContext",
                description="""\
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
""",
                parameters={
                    "properties": {
                        "task_id": {
                            "description": "The task ID these messages belong to",
                            "type": "string",
                        },
                        "policy": {
                            "default": "pin_outcome",
                            "description": "Retention policy: 'pin_outcome' keeps concise results, 'pin_process' keeps detailed process logs, 'auto' decides automatically",
                            "enum": ["pin_outcome", "pin_process", "auto"],
                            "type": "string",
                        },
                        "message_ids": {
                            "anyOf": [
                                {"items": {"type": "string"}, "type": "array"},
                                {"type": "null"},
                            ],
                            "default": None,
                            "description": "List of message IDs to tag. If None, will infer from recent assistant and tool messages related to this task.",
                        },
                        "ttl_steps": {
                            "default": 100,
                            "description": "Time-to-live in agent steps before this tag expires",
                            "minimum": 1,
                            "type": "integer",
                        },
                        "importance": {
                            "default": 3,
                            "description": "Priority level (1-5, where 5 is most important)",
                            "maximum": 5,
                            "minimum": 1,
                            "type": "integer",
                        },
                        "notes": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "description": "Optional human-readable notes about this tag",
                        },
                    },
                    "required": ["task_id"],
                    "type": "object",
                },
            ),
            Tool(
                name="Bash",
                description="""\
Execute a shell command. Use this tool to explore the filesystem, edit files, run scripts, get system information, etc.

**Output:**
The stdout and stderr will be combined and returned as a string. The output may be truncated if it is too long. If the command failed, the exit code will be provided in a system tag.

**Guidelines for safety and security:**
- Each shell tool call will be executed in a fresh shell environment. The shell variables, current working directory changes, and the shell history is not preserved between calls.
- The tool call will return after the command is finished. You shall not use this tool to execute an interactive command or a command that may run forever. For possibly long-running commands, you shall set `timeout` argument to a reasonable value.
- Avoid using `..` to access files or directories outside of the working directory.
- Avoid modifying files outside of the working directory unless explicitly instructed to do so.
- Never run commands that require superuser privileges unless explicitly instructed to do so.

**Guidelines for efficiency:**
- For multiple related commands, use `&&` to chain them in a single call, e.g. `cd /path && ls -la`
- Use `;` to run commands sequentially regardless of success/failure
- Use `||` for conditional execution (run second command only if first fails)
- Use pipe operations (`|`) and redirections (`>`, `>>`) to chain input and output between commands
- Always quote file paths containing spaces with double quotes (e.g., cd "/path with spaces/")
- Use `if`, `case`, `for`, `while` control flows to execute complex logic in a single call.
- Verify directory structure before create/edit/delete files or directories to reduce the risk of failure.

**Commands available:**
- Shell environment: cd, pwd, export, unset, env
- File system operations: ls, find, mkdir, rm, cp, mv, touch, chmod, chown
- File viewing/editing: cat, grep, head, tail, diff, patch
- Text processing: awk, sed, sort, uniq, wc
- System information/operations: ps, kill, top, df, free, uname, whoami, id, date
- Package management: pip, uv, npm, yarn, bun, cargo
- Network operations: curl, wget, ping, telnet, ssh
- Archive operations: tar, zip, unzip
- Other: Other commands available in the shell environment. Check the existence of a command by running `which <command>` before using it.
""",
                parameters={
                    "properties": {
                        "command": {
                            "description": "The bash command to execute.",
                            "type": "string",
                        },
                        "timeout": {
                            "default": 60,
                            "description": "The timeout in seconds for the command to execute. If the command takes longer than this, it will be killed.",
                            "maximum": 300,
                            "minimum": 1,
                            "type": "integer",
                        },
                    },
                    "required": ["command"],
                    "type": "object",
                },
            ),
            Tool(
                name="ReadFile",
                description="""\
Read content from a file.

**Tips:**
- Make sure you follow the description of each tool parameter.
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- Use `line_offset` and `n_lines` parameters when you only need to read a part of the file.
- The maximum number of lines that can be read at once is 1000.
- Any lines longer than 2000 characters will be truncated, ending with "...".
- The system will notify you when there is any limitation hit when reading the file.
- This tool is a tool that you typically want to use in parallel. Always read multiple files in one response when possible.
- This tool can only read text files. To list directories, you must use the Glob tool or `ls` command via the Bash tool. To read other file types, use appropriate commands via the Bash tool.
- If the file doesn't exist or path is invalid, an error will be returned.
- If you want to search for a certain content/pattern, prefer Grep tool over ReadFile.
""",
                parameters={
                    "properties": {
                        "path": {
                            "description": "The absolute path to the file to read",
                            "type": "string",
                        },
                        "line_offset": {
                            "default": 1,
                            "description": "The line number to start reading from. By default read from the beginning of the file. Set this when the file is too large to read at once.",
                            "minimum": 1,
                            "type": "integer",
                        },
                        "n_lines": {
                            "default": 1000,
                            "description": "The number of lines to read. By default read up to 1000 lines, which is the max allowed value. Set this value when the file is too large to read at once.",
                            "minimum": 1,
                            "type": "integer",
                        },
                    },
                    "required": ["path"],
                    "type": "object",
                },
            ),
            Tool(
                name="Glob",
                description="""\
Find files and directories using glob patterns. This tool supports standard glob syntax like `*`, `?`, and `**` for recursive searches.

**When to use:**
- Find files matching specific patterns (e.g., all Python files: `*.py`)
- Search for files recursively in subdirectories (e.g., `src/**/*.js`)
- Locate configuration files (e.g., `*.config.*`, `*.json`)
- Find test files (e.g., `test_*.py`, `*_test.go`)

**Example patterns:**
- `*.py` - All Python files in current directory
- `src/**/*.js` - All JavaScript files in src directory recursively
- `test_*.py` - Python test files starting with "test_"
- `*.config.{js,ts}` - Config files with .js or .ts extension

**Bad example patterns:**
- `**`, `**/*.py` - Any pattern starting with '**' will be rejected. Because it would recursively search all directories and subdirectories, which is very likely to yield large result that exceeds your context size. Always use more specific patterns like `src/**/*.py` instead.
- `node_modules/**/*.js` - Although this does not start with '**', it would still highly possible to yield large result because `node_modules` is well-known to contain too many directories and files. Avoid recursively searching in such directories, other examples include `venv`, `.venv`, `__pycache__`, `target`. If you really need to search in a dependency, use more specific patterns like `node_modules/react/src/*` instead.
""",
                parameters={
                    "properties": {
                        "pattern": {
                            "description": "Glob pattern to match files/directories.",
                            "type": "string",
                        },
                        "directory": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "description": "Absolute path to the directory to search in (defaults to working directory).",
                        },
                        "include_dirs": {
                            "default": True,
                            "description": "Whether to include directories in results.",
                            "type": "boolean",
                        },
                    },
                    "required": ["pattern"],
                    "type": "object",
                },
            ),
            Tool(
                name="Grep",
                description="""\
A powerful search tool based-on ripgrep.

**Tips:**
- ALWAYS use Grep tool instead of running `grep` or `rg` command with Bash tool.
- Use the ripgrep pattern syntax, not grep syntax. E.g. you need to escape braces like `\\\\{` to search for `{`.
""",
                parameters={
                    "properties": {
                        "pattern": {
                            "description": "The regular expression pattern to search for in file contents",
                            "type": "string",
                        },
                        "path": {
                            "default": ".",
                            "description": "File or directory to search in. Defaults to current working directory. If specified, it must be an absolute path.",
                            "type": "string",
                        },
                        "glob": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "description": "Glob pattern to filter files (e.g. `*.js`, `*.{ts,tsx}`). No filter by default.",
                        },
                        "output_mode": {
                            "default": "files_with_matches",
                            "description": "`content`: Show matching lines (supports `-B`, `-A`, `-C`, `-n`, `head_limit`); `files_with_matches`: Show file paths (supports `head_limit`); `count_matches`: Show total number of matches. Defaults to `files_with_matches`.",
                            "type": "string",
                        },
                        "-B": {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                            "default": None,
                            "description": "Number of lines to show before each match (the `-B` option). Requires `output_mode` to be `content`.",
                        },
                        "-A": {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                            "default": None,
                            "description": "Number of lines to show after each match (the `-A` option). Requires `output_mode` to be `content`.",
                        },
                        "-C": {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                            "default": None,
                            "description": "Number of lines to show before and after each match (the `-C` option). Requires `output_mode` to be `content`.",
                        },
                        "-n": {
                            "default": False,
                            "description": "Show line numbers in output (the `-n` option). Requires `output_mode` to be `content`.",
                            "type": "boolean",
                        },
                        "-i": {
                            "default": False,
                            "description": "Case insensitive search (the `-i` option).",
                            "type": "boolean",
                        },
                        "type": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "description": "File type to search. Examples: py, rust, js, ts, go, java, etc. More efficient than `glob` for standard file types.",
                        },
                        "head_limit": {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                            "default": None,
                            "description": "Limit output to first N lines, equivalent to `| head -N`. Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count_matches (limits count entries). By default, no limit is applied.",
                        },
                        "multiline": {
                            "default": False,
                            "description": "Enable multiline mode where `.` matches newlines and patterns can span lines (the `-U` and `--multiline-dotall` options). By default, multiline mode is disabled.",
                            "type": "boolean",
                        },
                    },
                    "required": ["pattern"],
                    "type": "object",
                },
            ),
            Tool(
                name="WriteFile",
                description="""\
Write content to a file.

**Tips:**
- When `mode` is not specified, it defaults to `overwrite`. Always write with caution.
- When the content to write is too long (e.g. > 100 lines), use this tool multiple times instead of a single call. Use `overwrite` mode at the first time, then use `append` mode after the first write.
""",
                parameters={
                    "properties": {
                        "path": {
                            "description": "The absolute path to the file to write",
                            "type": "string",
                        },
                        "content": {
                            "description": "The content to write to the file",
                            "type": "string",
                        },
                        "mode": {
                            "default": "overwrite",
                            "description": "The mode to use to write to the file. Two modes are supported: `overwrite` for overwriting the whole file and `append` for appending to the end of an existing file.",
                            "enum": ["overwrite", "append"],
                            "type": "string",
                        },
                    },
                    "required": ["path", "content"],
                    "type": "object",
                },
            ),
            Tool(
                name="StrReplaceFile",
                description="""\
Replace specific strings within a specified file.

**Tips:**
- Only use this tool on text files.
- Multi-line strings are supported.
- Can specify a single edit or a list of edits in one call.
- You should prefer this tool over WriteFile tool and Bash `sed` command.
""",
                parameters={
                    "$defs": {
                        "Edit": {
                            "properties": {
                                "old": {
                                    "description": "The old string to replace. Can be multi-line.",
                                    "type": "string",
                                },
                                "new": {
                                    "description": "The new string to replace with. Can be multi-line.",
                                    "type": "string",
                                },
                                "replace_all": {
                                    "default": False,
                                    "description": "Whether to replace all occurrences.",
                                    "type": "boolean",
                                },
                            },
                            "required": ["old", "new"],
                            "type": "object",
                        }
                    },
                    "properties": {
                        "path": {
                            "description": "The absolute path to the file to edit.",
                            "type": "string",
                        },
                        "edit": {
                            "anyOf": [
                                {"$ref": "#/$defs/Edit"},
                                {"items": {"$ref": "#/$defs/Edit"}, "type": "array"},
                            ],
                            "description": "The edit(s) to apply to the file. You can provide a single edit or a list of edits here.",
                        },
                    },
                    "required": ["path", "edit"],
                    "type": "object",
                },
            ),
            Tool(
                name="SearchWeb",
                description="WebSearch tool allows you to search on the internet to get latest information, including news, documents, release notes, blog posts, papers, etc.\n",
                parameters={
                    "properties": {
                        "query": {
                            "description": "The query text to search for.",
                            "type": "string",
                        },
                        "limit": {
                            "default": 5,
                            "description": "The number of results to return. Typically you do not need to set this value. When the results do not contain what you need, you probably want to give a more concrete query.",
                            "maximum": 20,
                            "minimum": 1,
                            "type": "integer",
                        },
                        "include_content": {
                            "default": False,
                            "description": "Whether to include the content of the web pages in the results. It can consume a large amount of tokens when this is set to True. You should avoid enabling this when `limit` is set to a large value.",
                            "type": "boolean",
                        },
                    },
                    "required": ["query"],
                    "type": "object",
                },
            ),
            Tool(
                name="FetchURL",
                description="Fetch a web page from a URL and extract main text content from it.\n",
                parameters={
                    "properties": {
                        "url": {
                            "description": "The URL to fetch content from.",
                            "type": "string",
                        }
                    },
                    "required": ["url"],
                    "type": "object",
                },
            ),
        ]
    )
