"""`topa hunt`: the wiki's perf queue, with each op's rows and the rounds working it."""

from __future__ import annotations

from typing import Any

from topa import ledger, wiki
from topa.config import Config


def hunt(config: Config, *, refresh: bool = True) -> tuple[wiki.Page, list[dict[str, Any]]]:
    page = wiki.fetch(config, refresh=refresh)
    working: dict[str, list[str]] = {}
    for view in ledger.rounds().values():
        if view["state"] != "removed" and view.get("op"):
            working.setdefault(view["op"], []).append(f"{view['round']}:{view['state']}")
    rows = [{"op": op.name, "category": op.category, "label": op.label, "worst": op.worst,
             "behind": len(op.rows), "measured": op.measured, "nightlies": op.nightlies,
             "rounds": working.get(op.name, []), "rows": [vars(row) for row in op.rows]}
            for op in page.queue]
    return page, rows


def table(rows: list[dict[str, Any]]) -> str:
    head = ("#", "op", "label", "worst", "behind", "nightlies", "rounds")
    body = [(str(i), row["op"], row["label"], f"{row['worst']:.4f}", f"{row['behind']}/{row['measured']}",
             str(row["nightlies"]), ",".join(row["rounds"]) or "-")
            for i, row in enumerate(rows, 1)]
    widths = [max(len(r[i]) for r in (head, *body)) for i in range(len(head))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)).rstrip() for r in (head, *body)]
    lines.insert(1, "  ".join("-" * w for w in widths))
    for row in rows:
        lines += ["", f"{row['op']}: workload, TileOPs us, fastest comparator, its us, ratio"]
        lines += [f"  {r['workload']}  {r['tileops_us']:.3f}  {r['comparator']}  {r['comparator_us']:.3f}  "
                  f"{r['ratio']:.4f}" for r in row["rows"]]
    return "\n".join(lines)
