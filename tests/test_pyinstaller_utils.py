from pathlib import Path

from inline_snapshot import snapshot


def test_pyinstaller_datas():
    from kimi_cli.utils.pyinstaller import datas

    project_root = Path(__file__).parent.parent
    datas = [(str(Path(path).relative_to(project_root)), dst) for path, dst in datas]

    assert sorted(datas) == snapshot(
        [
            (
                ".venv/lib/python3.13/site-packages/dateparser/data/dateparser_tz_cache.pkl",
                "dateparser/data",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/INSTALLER",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/METADATA",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/RECORD",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/REQUESTED",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/WHEEL",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/entry_points.txt",
                "fastmcp/../fastmcp-2.12.5.dist-info",
            ),
            (
                ".venv/lib/python3.13/site-packages/fastmcp/../fastmcp-2.12.5.dist-info/licenses/LICENSE",
                "fastmcp/../fastmcp-2.12.5.dist-info/licenses",
            ),
            (
                "src/kimi_cli/CHANGELOG.md",
                "kimi_cli",
            ),
            ("src/kimi_cli/agents/default/agent.yaml", "kimi_cli/agents/default"),
            ("src/kimi_cli/agents/default/sub.yaml", "kimi_cli/agents/default"),
            ("src/kimi_cli/agents/default/system.md", "kimi_cli/agents/default"),
            ("src/kimi_cli/deps/bin/rg", "kimi_cli/deps/bin"),
            ("src/kimi_cli/prompts/compact.md", "kimi_cli/prompts"),
            ("src/kimi_cli/prompts/init.md", "kimi_cli/prompts"),
            (
                "src/kimi_cli/tools/bash/bash.md",
                "kimi_cli/tools/bash",
            ),
            (
                "src/kimi_cli/tools/dmail/dmail.md",
                "kimi_cli/tools/dmail",
            ),
            (
                "src/kimi_cli/tools/file/glob.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/file/grep.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/file/patch.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/file/read.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/file/replace.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/file/write.md",
                "kimi_cli/tools/file",
            ),
            (
                "src/kimi_cli/tools/tag_context/tag_context.md",
                "kimi_cli/tools/tag_context",
            ),
            (
                "src/kimi_cli/tools/task/task.md",
                "kimi_cli/tools/task",
            ),
            (
                "src/kimi_cli/tools/think/think.md",
                "kimi_cli/tools/think",
            ),
            (
                "src/kimi_cli/tools/todo/set_todo_list.md",
                "kimi_cli/tools/todo",
            ),
            (
                "src/kimi_cli/tools/web/fetch.md",
                "kimi_cli/tools/web",
            ),
            (
                "src/kimi_cli/tools/web/search.md",
                "kimi_cli/tools/web",
            ),
        ]
    )


def test_pyinstaller_hiddenimports():
    from kimi_cli.utils.pyinstaller import hiddenimports

    assert sorted(hiddenimports) == snapshot(
        [
            "kimi_cli.tools",
            "kimi_cli.tools.bash",
            "kimi_cli.tools.dmail",
            "kimi_cli.tools.file",
            "kimi_cli.tools.file.glob",
            "kimi_cli.tools.file.grep",
            "kimi_cli.tools.file.patch",
            "kimi_cli.tools.file.read",
            "kimi_cli.tools.file.replace",
            "kimi_cli.tools.file.write",
            "kimi_cli.tools.mcp",
            "kimi_cli.tools.tag_context",
            "kimi_cli.tools.task",
            "kimi_cli.tools.test",
            "kimi_cli.tools.think",
            "kimi_cli.tools.todo",
            "kimi_cli.tools.utils",
            "kimi_cli.tools.web",
            "kimi_cli.tools.web.fetch",
            "kimi_cli.tools.web.search",
        ]
    )
