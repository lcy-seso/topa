"""The TileFoundry a round reads: a commit, what it needs staged, and a checkout.

The source is read-only for a round -- it reads and runs TileFoundry and reports what
blocks it as one issue. The checkout is still a real one, because `tilefoundry
tutorial`, `spec` and `tests/fixtures/schedule/` read from it and are not in a wheel.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import shutil
import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from topa import sh
from topa.config import Config
from topa.container import proxy_env


@dataclass(frozen=True)
class Prepared:
    commit: str
    stage: Path  # wheels/, build-tools/<project>/, report.json from kit/stage.py

    @property
    def report(self) -> dict:
        return json.loads((self.stage / "report.json").read_text())


def _stage(config: Config, commit: str, tileops_pyproject: str) -> Path:
    """Run kit/stage.py in the agent image, once per image and declared requirements."""
    pyproject = sh.run(["git", "-C", config.tilefoundry_repo, "show", f"{commit}:pyproject.toml"])
    data, tileops = tomllib.loads(pyproject), tomllib.loads(tileops_pyproject)
    image = sh.docker(config, "image", "inspect", config.agent_image, "--format", "{{.Id}}")
    key = hashlib.sha256(json.dumps([image, data["project"].get("dependencies", []),
                                     data["build-system"]["requires"],
                                     tileops["build-system"]["requires"]]).encode()).hexdigest()[:16]
    stage = config.cache / "stage" / key
    if (stage / "report.json").exists():
        return stage
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    (stage / "tilefoundry.toml").write_text(pyproject + "\n")
    (stage / "tileops.toml").write_text(tileops_pyproject)
    script = Path(str(files("topa") / "kit" / "stage.py"))
    sh.note(f"staging round dependencies in {stage}")
    sh.docker(config, "run", "--rm", "--entrypoint", "", *proxy_env(config),
              "--volume", f"{stage}:/stage", "--volume", f"{script}:/stage.py:ro",
              config.agent_image, "python", "/stage.py", "/stage/tilefoundry.toml", "/stage/tileops.toml", "/stage")
    return stage


def prepare(config: Config, tileops_pyproject: str) -> Prepared:
    """The TileFoundry commit a new round reads: `tilefoundry_commit`, or the newest main."""
    root = config.cache / "stage"
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        repo = config.tilefoundry_repo
        if config.tilefoundry_commit:
            ref = config.tilefoundry_commit
        else:
            remotes = sh.run(["git", "-C", repo, "remote"]).split()
            remote = "upstream" if "upstream" in remotes else "origin"
            sh.run(["git", "-C", repo, "fetch", "--quiet", remote, "main"])
            ref = f"{remote}/main"
        commit = sh.run(["git", "-C", repo, "rev-parse", f"{ref}^{{commit}}"])
        stage = _stage(config, commit, tileops_pyproject)
    return Prepared(commit=commit, stage=stage)


def source(config: Config, slug: str, base: str) -> tuple[Path, Path]:
    """A detached checkout of *base* for this round, and the git dir it shares."""
    path = config.checkouts / slug
    repo = config.tilefoundry_repo
    if not (path / ".git").exists():
        shutil.rmtree(path, ignore_errors=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        sh.run(["git", "-C", repo, "worktree", "prune"])
        sh.run(["git", "-C", repo, "worktree", "add", "--detach", path, base])
    git_dir = Path(sh.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"]))
    return path, git_dir


def remove_source(config: Config, path: Path) -> None:
    if not path.exists():
        return
    if not sh.ok(["git", "-C", config.tilefoundry_repo, "worktree", "remove", "--force", path]):
        shutil.rmtree(path, ignore_errors=True)
    sh.run(["git", "-C", config.tilefoundry_repo, "worktree", "prune"], check=False)
