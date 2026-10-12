"""Running the external programs topa drives: git, gh, docker, herdr, ssh, nvidia-smi."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from topa.config import Config


class CommandError(RuntimeError):
    def __init__(self, args: Sequence[str], code: int, output: str) -> None:
        super().__init__(f"{' '.join(map(str, args))} exited {code}\n{output.strip()}")
        self.code = code
        self.output = output


def run(
    args: Sequence[str | Path],
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture: bool = True,
    input: str | None = None,
    timeout: float | None = None,
) -> str:
    """Run *args* and return its stdout; stderr joins the error when it fails."""
    args = [str(arg) for arg in args]
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        input=input,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        timeout=timeout,
        check=False,
    )
    if check and completed.returncode != 0:
        raise CommandError(args, completed.returncode, (completed.stdout or "") + (completed.stderr or ""))
    return (completed.stdout or "").strip() if capture else ""


def ok(args: Sequence[str | Path], **kwargs: Any) -> bool:
    try:
        run(args, **kwargs)
    except CommandError:
        return False
    return True


def note(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def require(*commands: str) -> None:
    missing = [command for command in commands if shutil.which(command) is None]
    if missing:
        raise SystemExit(f"required commands are missing: {', '.join(missing)}")


# --- docker -------------------------------------------------------------------


def docker_env(config: Config) -> dict[str, str]:
    env = dict(os.environ)
    if config.docker_host:
        env["DOCKER_HOST"] = config.docker_host
    return env


def bootstrap_docker(config: Config) -> None:
    if config.docker_bootstrap:
        subprocess.run([config.docker_bootstrap], stdout=sys.stderr, check=True)


def docker(config: Config, *args: str | Path, **kwargs: Any) -> str:
    return run(["docker", *args], env=docker_env(config), **kwargs)


def docker_ok(config: Config, *args: str | Path) -> bool:
    return ok(["docker", *args], env=docker_env(config))


# --- herdr ----------------------------------------------------------------------


def herdr(*args: str, check: bool = True, timeout: float | None = None) -> dict[str, Any]:
    """Run a herdr command and return its `result` object."""
    out = run(["herdr", *args], check=check, timeout=timeout)
    if not out:
        return {}
    try:
        return json.loads(out).get("result", {})
    except json.JSONDecodeError:
        return {"text": out}


# --- gh ---------------------------------------------------------------------------


def gh_json(*args: str) -> Any:
    out = run(["gh", *args])
    return json.loads(out) if out else None


def gh_login() -> str:
    return run(["gh", "api", "user", "--jq", ".login"])


def github_remote(repo: Path, slug: str) -> str:
    """The name of the remote of *repo* that points at github.com/<slug>."""
    pattern = re.compile(rf"github\.com[:/]{re.escape(slug)}(?:\.git)?/?$", re.IGNORECASE)
    for line in run(["git", "-C", repo, "remote", "-v"]).splitlines():
        name, url, *_ = line.split()
        if pattern.search(url):
            return name
    raise SystemExit(f"{repo} has no remote for github.com/{slug}; add one with git remote add")
