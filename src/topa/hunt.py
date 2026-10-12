"""`topa hunt` and `topa issue new`: find the ops that are behind, and file one issue each.

A round is started from an issue, and one issue is one round's scope, so an op
gets its own issue: the hunt lists every behind op with the open issue that names
it, if any, and any round already working that issue.
"""

from __future__ import annotations

import re
from typing import Any

from topa import ledger, sh
from topa.config import Config
from topa.grade import BEHIND, PAR_BAND, Grade, Snapshot, fetch, grade

FAMILY_TITLE = {
    "attention": "Attention", "linear_attention": "Linear Attention", "ssm": "SSM",
    "scan": "Scan", "normalization": "Normalization", "moe": "MoE", "linear_algebra": "GEMM",
    "gemm": "GEMM", "reduction": "Reduction", "elementwise": "Elementwise",
    "convolution": "Convolution", "pool": "Pooling", "quantization": "Quantization",
    "sampling": "Sampling", "positional": "RoPE", "fft": "FFT", "mhc": "mHC",
    "engram": "Engram", "topk": "Top-k",
}


def _open_issues(config: Config) -> list[dict[str, Any]]:
    return sh.gh_json("issue", "list", "--repo", config.upstream, "--state", "open", "--limit", "1000",
                      "--json", "number,title,body,assignees,url") or []


def issues_naming(op: str, issues: list[dict[str, Any]], tracker: int) -> list[dict[str, Any]]:
    """Open issues that name *op*, those naming it in the title first. The tracker is not one."""
    word = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(op)}(?![A-Za-z0-9_])")
    hits = [i for i in issues if i["number"] != tracker and (word.search(i["title"]) or word.search(i.get("body") or ""))]
    return sorted(hits, key=lambda i: (not word.search(i["title"]), i["number"]))


def hunt(config: Config, *, every: bool = False, refresh: bool = True) -> tuple[Snapshot, list[dict[str, Any]]]:
    snapshot = fetch(refresh)
    grades = [g for g in grade(snapshot) if every or g.status == BEHIND]
    issues = _open_issues(config)
    by_issue: dict[int, list[str]] = {}
    for view in ledger.rounds().values():
        if view.get("issue") and view["state"] in ledger.LIVE | {"stopped"}:
            by_issue.setdefault(view["issue"], []).append(f"{view['round']}:{view['state']}")
    rows = []
    for g in grades:
        named = issues_naming(g.op, issues, config.tracker)
        first = named[0] if named else None
        rows.append({
            **g.as_dict(),
            "issue": first["number"] if first else None,
            "issue_title": first["title"] if first else None,
            "assignees": [a["login"] for a in first["assignees"]] if first else [],
            "other_issues": [i["number"] for i in named[1:]],
            "rounds": by_issue.get(first["number"], []) if first else [],
        })
    return snapshot, rows


def table(rows: list[dict[str, Any]]) -> str:
    head = ("#", "op", "rival", "ratio", "behind", "issue", "assignee", "rounds")
    body = []
    for index, row in enumerate(rows, 1):
        issue = f"#{row['issue']}" if row["issue"] else "-"
        if row["other_issues"]:
            issue += " (+" + ",".join(f"#{n}" for n in row["other_issues"]) + ")"
        body.append((
            str(index), row["op"], row["rival"] or "-",
            f"{row['speedup']:.3f}x" if row["speedup"] else "-",
            f"{row['behind_rows']}/{row['rated_rows']}", issue,
            ",".join(row["assignees"]) or "-", ",".join(row["rounds"]) or "-",
        ))
    widths = [max(len(r[i]) for r in (head, *body)) for i in range(len(head))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)).rstrip() for r in (head, *body)]
    lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)


# --- issue new ----------------------------------------------------------------------


def family(op_module: str | None) -> str:
    parts = (op_module or "").split(".")
    if len(parts) > 2 and parts[:2] == ["tileops", "ops"]:
        return FAMILY_TITLE.get(parts[2], parts[2].replace("_", " ").title())
    return "Ops"


def _ms(value: float | None) -> str:
    return f"{value:.4f}" if value else "--"


def issue_body(g: Grade, snapshot: Snapshot) -> str:
    lines = [
        f"`{g.op}` reads **behind** on the benchmark site: {g.speedup:.3f}x against {g.rival}. "
        "Graded the way",
        "`scripts/gen_bench_pages.py` in TileOPs.github.io grades an op: per workload the fastest",
        "rival in the library and torch tiers, the op's rival is the one named most often, and its",
        "geometric-mean ratio against that rival is ahead at >= 1.05, level at >= 0.95, behind below.",
        "",
        snapshot.label + ".",
        "",
        "| workload | TileOPs ms | fastest rival | rival ms | rival / TileOPs |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for row in g.rows:
        if row.speedup is None:
            lines.append(f"| `{row.config}` | {_ms(row.tileops_ms)} | -- (reference only, unrated) | -- | -- |")
        else:
            lines.append(f"| `{row.config}` | {_ms(row.tileops_ms)} | {row.rival} | {_ms(row.rival_ms)} "
                         f"| {row.speedup:.3f}x |")
    lines += ["", "## Where it plugs in", ""]
    if g.op_module:
        lines.append(f"- Op: `src/{g.op_module.replace('.', '/')}.py`.")
    if g.bench:
        lines.append(f"- Bench: `{g.bench.replace('.', '/')}.py`.")
    lines += [
        "",
        "## Done when",
        "",
        f"`{g.op}` reads level or ahead on the site -- geometric mean against its named rival",
        f">= {PAR_BAND[0]} -- with correctness unchanged and no other row of the op regressing.",
    ]
    return "\n".join(lines) + "\n"


def new_issues(config: Config, ops: list[str], *, dry_run: bool = False) -> list[dict[str, Any]]:
    snapshot = fetch(refresh=False)
    grades = {g.op: g for g in grade(snapshot)}
    unknown = [op for op in ops if op not in grades]
    if unknown:
        raise SystemExit(f"not in the nightly: {', '.join(unknown)}")
    issues = _open_issues(config)
    me = sh.gh_login()
    done = []
    for op in ops:
        g = grades[op]
        named = issues_naming(op, issues, config.tracker)
        if named:
            found = named[0]
            assignees = [a["login"] for a in found["assignees"]]
            # An unassigned issue is free to take; one assigned to someone else is theirs.
            if not assignees and not dry_run:
                sh.run(["gh", "issue", "edit", str(found["number"]), "--repo", config.upstream,
                        "--add-assignee", me])
                assignees = [me]
            done.append({"op": op, "issue": found["number"], "url": found["url"], "created": False,
                         "assignees": assignees})
            continue
        if g.speedup is None or g.rival is None:
            raise SystemExit(f"{op} has no rated rival in the nightly; write its issue by hand")
        title = f"[Perf][{family(g.op_module)}] {op} is behind {g.rival}"
        body = issue_body(g, snapshot)
        if dry_run:
            done.append({"op": op, "title": title, "body": body, "created": False})
            continue
        url = sh.run(["gh", "issue", "create", "--repo", config.upstream, "--title", title,
                      "--body", body, "--label", "perf", "--assignee", me])
        number = int(url.rstrip("/").rsplit("/", 1)[1])
        node = sh.gh_json("api", f"repos/{config.upstream}/issues/{number}")["id"]
        sh.run(["gh", "api", "-X", "POST", f"repos/{config.upstream}/issues/{config.tracker}/sub_issues",
                "-F", f"sub_issue_id={node}"], check=False)
        ledger.append("issue", issue=number, op=op, url=url)
        done.append({"op": op, "issue": number, "url": url, "created": True, "assignees": [me]})
    return done
