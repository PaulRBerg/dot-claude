#!/usr/bin/env python3
"""Enable Claude Code's built-in computer-use MCP server for every project.

The CLI keeps `computer-use` off until a project lists it in
`~/.claude.json` -> `projects[<path>].enabledMcpServers`, which `/mcp` writes
one project at a time. No settings.json key enables it globally. This
SessionStart hook adds the entry for the session's project; the CLI watches
`~/.claude.json` and picks up the change. Run with `--all` to backfill every
known project.

The project key mirrors the CLI: the nearest ancestor containing `.git`, else
the resolved cwd. The write is skipped when the server is already listed or the
CLI has not created the project entry yet.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

SERVER = "computer-use"


def config_path() -> Path:
    return Path.home() / ".claude.json"


def project_key(cwd: str) -> str:
    path = Path(cwd).resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return str(path)


def enable(project: dict) -> bool:
    servers = project.get("enabledMcpServers")
    if not isinstance(servers, list):
        servers = []
    if SERVER in servers:
        return False
    project["enabledMcpServers"] = [*servers, SERVER]
    return True


def write_atomic(path: Path, config: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main() -> int:
    path = config_path()
    if not path.exists():
        return 0
    config = json.loads(path.read_text())
    projects = config.setdefault("projects", {})

    if "--all" in sys.argv[1:]:
        changed = [enable(project) for project in projects.values()].count(True)
    else:
        # A partial entry would shadow the CLI's project defaults, so only patch existing ones
        project = projects.get(project_key(json.load(sys.stdin).get("cwd") or os.getcwd()))
        changed = int(project is not None and enable(project))

    if changed:
        write_atomic(path, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
