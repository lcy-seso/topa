"""`topa hook pre-tool-use`: run a round's shell commands inside its container.

The agent runs on the host, where its own credentials work and where the round,
the TileOPs worktree and the TileFoundry source already live. Only execution
needs the container: the CUDA stack, the GPU and the installed `tilefoundry`.
Those directories are mounted into the container at the paths they have here, so
a command carries over unchanged -- only its interpreter moves.

Reads one PreToolUse event on stdin and answers on stdout. `topa round start`
installs it in the round's `.claude/settings.json`.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import TextIO

# These act on files, on GitHub, or on the round itself, not on the compute stack.
# git and gh use the host credentials; topa drives the host.
HOST_COMMANDS = frozenset({"cd", "gh", "git", "ls", "cat", "pwd", "mkdir", "rm", "cp", "mv", "topa"})


def ssh_alias(round_dir: Path) -> str | None:
    """The round container's SSH alias, as `topa round start` recorded it."""
    try:
        return json.loads((round_dir / "round.json").read_text()).get("alias")
    except (OSError, json.JSONDecodeError):
        return None


def runs_on_the_host(command: str) -> bool:
    """Whether every program *command* invokes is a host-side one.

    `cd work && pytest` names a host command first and a container command
    second, so the whole line belongs in the container: one stray segment is
    enough to move it. A program is named by its basename, so the absolute
    `/.../.venv/bin/topa` the brief writes counts as `topa`.
    """
    for segment in re.split(r"&&|\|\||[;|\n]", command):
        try:
            words = shlex.split(segment)
        except ValueError:  # unbalanced quotes: let the container decide
            return False
        if words and Path(words[0]).name not in HOST_COMMANDS:
            return False
    return True


def decide(event: dict, round_dir: Path) -> dict | None:
    """The hook's answer to *event*, or None to let the command run as written."""
    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None
    alias = ssh_alias(round_dir)
    if alias is None or runs_on_the_host(command):
        return None
    cwd = event.get("cwd") or str(round_dir)
    remote = f"cd {shlex.quote(cwd)} && {command}"
    updated = dict(tool_input)
    updated["command"] = f"ssh -T {shlex.quote(alias)} {shlex.quote(remote)}"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated,
        }
    }


def pre_tool_use(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    event = json.load(stdin)
    round_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    answer = decide(event, round_dir)
    if answer is not None:
        json.dump(answer, stdout)
    return 0
