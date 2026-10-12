"""`topa gate` and `topa pr`: check a round's evidence, then open or update its PR.

The PR comes from the fork: the branch is pushed to the remote of `fork_owner`
(the gh login by default), and the PR's head is `<fork_owner>:<branch>`.
"""

from __future__ import annotations

from pathlib import Path

from topa import ledger, sh
from topa.config import Config
from topa.gate import GateError, validate_round
from topa.round import Round, find

CHECKLIST = """
Artifact checks passed. Re-open the actual files before creating the PR:

1. Was final_hir.py actually analyzed and measured, rather than reconstructed after tuning?
2. Do raw analyze and measurement results justify the kept and rejected placements?
3. Does the production diff implement that HIR decision beyond config/tile/launch tuning?

If any answer is no or uncertain, continue the round instead of opening a PR.
"""


def gate(config: Config, slug: str | None = None) -> Round:
    current = find(config, slug)
    try:
        validate_round(current.dir, Path(current.meta["worktree"]), "HEAD")
    except GateError as error:
        raise SystemExit(f"TileFoundry artifact gate: FAIL: {error}") from error
    print("TileFoundry artifact gate: PASS")
    return current


def open_pr(config: Config, slug: str | None = None, *, reviewed: bool = False, watch: bool = True) -> str | None:
    current = gate(config, slug)
    sh.note(CHECKLIST)
    if not reviewed:
        sh.note("PR not opened. Inspect those files, then rerun: topa pr --reviewed")
        raise SystemExit(2)

    worktree = Path(current.meta["worktree"])
    branch = sh.run(["git", "-C", worktree, "branch", "--show-current"])
    if not branch:
        raise SystemExit("the TileOPs worktree is not on a branch")
    owner = config.fork_owner or sh.gh_login()
    repo_name = config.upstream.split("/", 1)[1]
    fork = sh.github_remote(worktree, f"{owner}/{repo_name}")
    title = (current.dir / "pr-title.txt").read_text().strip()
    body = str(current.dir / "pr-body.md")
    repo = ["--repo", config.upstream]

    sh.run(["git", "-C", worktree, "push", "--force-with-lease", "-u", fork, branch], capture=False)
    rows = sh.gh_json("pr", "list", *repo, "--head", branch, "--state", "all",
                      "--limit", "1", "--json", "number,state,url")
    existing = rows[0] if rows else None
    if existing and existing["state"] == "OPEN":
        sh.run(["gh", "pr", "edit", str(existing["number"]), *repo, "--title", title, "--body-file", body])
        url = existing["url"]
    elif existing and existing["state"] == "CLOSED":
        sh.run(["gh", "pr", "reopen", str(existing["number"]), *repo])
        sh.run(["gh", "pr", "edit", str(existing["number"]), *repo, "--title", title, "--body-file", body])
        url = existing["url"]
    else:
        url = sh.run(["gh", "pr", "create", *repo, "--base", "main", "--head", f"{owner}:{branch}",
                      "--title", title, "--body-file", body])
    print(url)
    ledger.append("pr", round=current.slug, pr=url)
    if watch:
        sh.run(["gh", "pr", "checks", url, *repo, "--watch", "--interval", "300"], check=False, capture=False)
    return url
