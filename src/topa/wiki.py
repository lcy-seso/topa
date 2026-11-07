"""The perf work queue: the newest daily page of the TileOPs wiki's Perf Tracker.

The TileOPs nightly writes `Perf-Tracker-<YYYY-MM-DD>.md` to the wiki with
`scripts/perf_tracker.py`. Its `## Queue` table lists the ops behind their fastest
comparator, in the order they should be worked, and `## Rows behind` holds one
table per op. Change the parser here together with that script's `render()`.
"""

from __future__ import annotations

import fcntl
import re
from dataclasses import dataclass

from topa import sh
from topa.config import Config

PAGE = re.compile(r"Perf-Tracker-(\d{4}-\d{2}-\d{2})\.md")
NIGHTLY = re.compile(r"^Nightly run \[(\d+)\]\((\S+)\), commit \[`[0-9a-f]+`\]\(\S+/commit/([0-9a-f]{40})\)",
                     re.MULTILINE)
QUEUE_HEADER = "| # | Op | Category | Label | Worst ratio | Rows behind | Nightlies behind |"
QUEUE_SEPARATOR = "| ---: | --- | --- | --- | ---: | ---: | ---: |"
QUEUE_ROW = re.compile(r"\| (\d+) \| \[(\w+)\]\(#\w+\) \| (\w*) \| (P\d) \| (\d+\.\d+) \| (\d+) of (\d+) \| (\d+) \|")
ROWS_HEADER = "| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |"
ROWS_SEPARATOR = "| --- | ---: | --- | ---: | ---: |"
ROW = re.compile(r"\| `([^`]+)` \| (\d+\.\d+) \| ([^|]+?) \| (\d+\.\d+) \| (\d+\.\d+) \|")
BENCHMARK = re.compile(r"^Benchmark `([\w.]+)`\.$", re.MULTILINE)


class FormatError(SystemExit):
    """The page is not laid out the way this parser reads it."""


@dataclass(frozen=True)
class Row:
    workload: str
    tileops_us: float
    comparator: str
    comparator_us: float
    ratio: float


@dataclass(frozen=True)
class Op:
    name: str
    category: str
    label: str
    worst: float
    measured: int
    nightlies: int
    benchmark: str
    rows: tuple[Row, ...]

    def table(self) -> str:
        """The op's rows behind, as the page shows them."""
        lines = [ROWS_HEADER, ROWS_SEPARATOR]
        lines += [f"| `{r.workload}` | {r.tileops_us:.3f} | {r.comparator} | {r.comparator_us:.3f} | {r.ratio:.4f} |"
                  for r in self.rows]
        return "\n".join(lines)


@dataclass(frozen=True)
class Page:
    date: str
    url: str
    run_id: str
    run_url: str
    commit: str
    queue: tuple[Op, ...]

    def op(self, name: str) -> Op:
        for op in self.queue:
            if op.name == name:
                return op
        raise SystemExit(f"{name} is not in the queue of {self.url}")


def _table(lines: list[str], header: str, separator: str, row: re.Pattern, where: str) -> list[re.Match]:
    """The rows of the table in *lines* under *header*: each must match *row*, and a blank line ends it."""
    if header not in lines:
        raise FormatError(f"{where}: no table with the header {header!r}")
    start = lines.index(header) + 1
    if lines[start:start + 1] != [separator]:
        raise FormatError(f"{where}: the line under the header is not {separator!r}")
    matches = []
    for line in lines[start + 1:]:
        if not line.strip():
            break
        match = row.fullmatch(line)
        if match is None:
            raise FormatError(f"{where}: unexpected row {line!r}")
        matches.append(match)
    return matches


def _sections(text: str, marker: str) -> dict[str, list[str]]:
    """The lines under each `<marker> <name>` heading of *text*."""
    parts = re.split(rf"^{marker} (.+)$", text, flags=re.MULTILINE)
    return {name.strip(): body.splitlines() for name, body in zip(parts[1::2], parts[2::2])}


def parse(text: str, date: str, url: str) -> Page:
    where = url
    if not text.startswith(f"# Perf Tracker {date}\n"):
        raise FormatError(f"{where}: the first line is not '# Perf Tracker {date}'")
    nightly = NIGHTLY.search(text)
    if nightly is None:
        raise FormatError(f"{where}: no 'Nightly run [<id>](<url>), commit [...](.../commit/<sha>)' line")
    sections = _sections(text, "##")
    for name in ("Queue", "Rows behind"):
        if name not in sections:
            raise FormatError(f"{where}: no '## {name}' section")
    queue = _table(sections["Queue"], QUEUE_HEADER, QUEUE_SEPARATOR, QUEUE_ROW, f"{where} ## Queue")
    behind = _sections("\n".join(sections["Rows behind"]), "###")
    ops = []
    for rank, match in enumerate(queue, 1):
        number, name, category, label, worst, count, measured, nightlies = match.groups()
        if int(number) != rank:
            raise FormatError(f"{where} ## Queue: row {rank} is numbered {number}")
        if name not in behind:
            raise FormatError(f"{where}: no '### {name}' under '## Rows behind'")
        lines = behind[name]
        benchmark = BENCHMARK.search("\n".join(lines))
        if benchmark is None:
            raise FormatError(f"{where} ### {name}: no 'Benchmark `<module>`.' line")
        rows = tuple(Row(m[1], float(m[2]), m[3], float(m[4]), float(m[5]))
                     for m in _table(lines, ROWS_HEADER, ROWS_SEPARATOR, ROW, f"{where} ### {name}"))
        if len(rows) != int(count):
            raise FormatError(f"{where} ### {name}: {len(rows)} rows, the queue says {count}")
        ops.append(Op(name, category, label, float(worst), int(measured), int(nightlies), benchmark[1], rows))
    extra = sorted(set(behind) - {op.name for op in ops})
    if extra:
        raise FormatError(f"{where}: '## Rows behind' has ops the queue lacks: {', '.join(extra)}")
    return Page(date=date, url=url, run_id=nightly[1], run_url=nightly[2], commit=nightly[3], queue=tuple(ops))


def fetch(config: Config, *, refresh: bool = True) -> Page:
    """The newest daily page, from the cached wiki clone; *refresh* pulls the wiki first.

    The nightly rewrites the wiki as one commit, so the clone is reset, never merged.
    """
    path = config.cache / "wiki"
    remote = f"https://github.com/{config.upstream}.wiki.git"
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent / "wiki.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not (path / ".git").is_dir():
            sh.run(["git", "clone", "--quiet", "--depth", "1", remote, path])
        elif refresh:
            sh.run(["git", "-C", path, "fetch", "--quiet", "--depth", "1", remote, "HEAD"])
            sh.run(["git", "-C", path, "reset", "--quiet", "--hard", "FETCH_HEAD"])
        pages = sorted(p for p in path.iterdir() if PAGE.fullmatch(p.name))
        if not pages:
            raise FormatError(f"{remote} has no Perf-Tracker-<date>.md page")
        newest = pages[-1]
        text = newest.read_text(encoding="utf-8")
    url = f"https://github.com/{config.upstream}/wiki/{newest.stem}"
    return parse(text, PAGE.fullmatch(newest.name)[1], url)
