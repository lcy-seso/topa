"""A TileOPs issue, and the round names derived from it.

A round is started from an issue number alone. Its slug, its branch and the line
the brief opens with all follow from the issue, so one issue is one round's scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from topa import sh
from topa.config import Config

# TileOPs .claude/conventions/types.sh: BRANCH_PREFIXES.
BRANCH_TYPES = {"bench", "chore", "design", "doc", "feat", "fix", "maintain", "perf", "refactor", "style", "test"}
TYPE_BY_LABEL = {
    "perf": "perf",
    "feature": "feat",
    "enhancement": "feat",
    "fix": "fix",
    "bug": "fix",
    "bench": "bench",
    "refactor": "refactor",
    "test": "test",
    "chore": "chore",
    "docs": "doc",
}
# Title tags that name a kind of change or an origin rather than an area.
NOT_AN_AREA = {"perf", "kernel", "feat", "feature", "fix", "bugfix", "bench", "benchmark",
               "refactor", "test", "chore", "doc", "docs", "foundry", "tracker", "rfc", "meta"}


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    state: str
    labels: tuple[str, ...]
    assignees: tuple[str, ...]
    url: str
    node_id: int

    @classmethod
    def fetch(cls, config: Config, number: int) -> "Issue":
        data = sh.gh_json("api", f"repos/{config.upstream}/issues/{number}")
        if "pull_request" in data:
            raise SystemExit(f"#{number} is a pull request, not an issue")
        return cls(
            number=number,
            title=data["title"],
            state=data["state"],
            labels=tuple(label["name"] for label in data["labels"]),
            assignees=tuple(user["login"] for user in data["assignees"]),
            url=data["html_url"],
            node_id=data["id"],
        )

    @property
    def branch_type(self) -> str:
        return branch_type(self.title, self.labels)

    @property
    def area(self) -> str:
        return area(self.title)


def branch_type(title: str, labels: Iterable[str]) -> str:
    for label in labels:
        if label.lower() in TYPE_BY_LABEL:
            return TYPE_BY_LABEL[label.lower()]
    for tag in re.findall(r"\[([^\]]+)\]", title):
        tag = tag.lower()
        if tag in TYPE_BY_LABEL:
            return TYPE_BY_LABEL[tag]
        if tag in {"kernel", "feat"}:
            return "feat"
    return "perf"


def area(title: str) -> str:
    for tag in re.findall(r"\[([^\]]+)\]", title):
        if tag.lower() not in NOT_AN_AREA:
            return re.sub(r"[^a-z0-9._-]+", "-", tag.lower()).strip("-") or "ops"
    return "ops"


def round_slug(number: int, earlier: Iterable[dict[str, Any]]) -> str:
    """`i<issue>-r<k>`, k one past the rounds the ledger already holds for this issue.

    herdr names agents `[a-z][a-z0-9_-]{0,31}`, which this always satisfies.
    """
    taken = {view["round"] for view in earlier if view.get("issue") == number}
    k = 1
    while f"i{number}-r{k}" in taken:
        k += 1
    return f"i{number}-r{k}"


def op_family(repo: Path, ref: str, title: str) -> str | None:
    """The `src/tileops/ops/<family>/` directory of the first op the title names.

    Matching ignores case: titles write `GemmFp8FwdOp` for `GemmFP8FwdOp`.
    """
    for op in re.findall(r"\b([A-Z][A-Za-z0-9]*Op)\b", title):
        found = sh.run(["git", "-C", repo, "grep", "-l", "-i", "-E", rf"^class {op}\b", ref,
                        "--", "src/tileops/ops"], check=False)
        for line in found.splitlines():
            parts = line.split(":", 1)[-1].split("/")
            if len(parts) > 4:
                return parts[3].replace("_", "-")
    return None


def branch_name(issue: Issue, slug: str, family: str | None = None) -> str:
    """`<type>/<area>/<slug>`. The area is the first area tag of the title, else *family*."""
    kind = issue.branch_type
    assert kind in BRANCH_TYPES, kind
    where = issue.area
    if where == "ops" and family:
        where = family
    return f"{kind}/{where}/{slug}"
