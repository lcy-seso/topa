"""`topa gate`: the facts a program can check before a round opens its PR.

It does not judge the optimization. It checks that the records the brief asks for
exist, agree with each other, and match the TileOPs diff and the PR text.
"""

from __future__ import annotations

import json
import math
import re
import shlex
import subprocess
from pathlib import Path


class GateError(ValueError):
    """The round is missing mechanically verifiable PR evidence."""


# What the round is measured against, and the repository's own tooling.
FORBIDDEN_ROOTS = ("benchmarks/", "workloads/", "src/tileops/manifest/", "scripts/", ".github/")
# The round's PR: `kit/round/pr-template.md` is the title and body, `pr-comments.md`
# one comment per section, both filled in.
PR_FILE = "pr-template.md"
COMMENTS_FILE = "pr-comments.md"
BODY_SECTIONS = ("Summary", "Test plan", "Test node delta", "Benchmark")
COMMENT_SECTIONS = ("TileFoundry Description", "Performance", "Result And Limitations", "TileFoundry Findings")
RESULTS = ("bar met", "below bar")
# How far a stated ratio may sit from the one its rounded times give.
RATIO_ROUNDING = 0.01
ENVIRONMENT_ROWS = ("image", "digest", "gpu", "timer", "timer step (us)")
# A template placeholder: `<...>` outside code, except the HTML tags a PR may use; or a
# code block whose only line is one.
PLACEHOLDER = re.compile(r"<(?!/?(?:br|b|i|em|strong|code|sub|sup|details|summary)\b)[^<>\n]+>")
EMPTY_BLOCK = re.compile(r"^```\w*\n<[^\n]*>\n```", re.MULTILINE)
LOCAL_PATH = re.compile(r"(?:/home/|/mnt/|/tmp/|/workspace/|/Users/|file://|[A-Za-z]:\\)")


def _real_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.strip().startswith("<")


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise GateError(f"expected a JSON object: {path}")
    return value


def _required_file(root: Path, relative: object) -> Path:
    if not _real_text(relative):
        raise GateError("required artifact path is empty")
    path = (root / str(relative)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise GateError(f"artifact escapes the round directory: {relative}") from error
    if not path.is_file() or path.stat().st_size == 0:
        raise GateError(f"required artifact is missing or empty: {relative}")
    return path


def _record(root: Path, record: object, section: str, *words: str, flags: tuple[str, ...] = ()) -> Path:
    """The report of a `{command, report}` record whose command runs `tilefoundry <words>` with *flags*."""
    if not isinstance(record, dict):
        raise GateError(f"{section} must be an object with a command and a report")
    command = record.get("command")
    if not _real_text(command) or "..." in command:
        raise GateError(f"{section} must record the exact command")
    try:
        argv = shlex.split(command)
    except ValueError as error:
        raise GateError(f"{section} command cannot be parsed: {error}") from error
    if words and not any(Path(arg).name == "tilefoundry" and argv[i + 1:i + 1 + len(words)] == list(words)
                         for i, arg in enumerate(argv)):
        raise GateError(f"{section} must run tilefoundry {' '.join(words)}")
    missing = [flag for flag in flags if flag not in argv]
    if missing:
        raise GateError(f"{section} must pass {', '.join(missing)}")
    return _required_file(root, record.get("report"))


def _passed(report: Path, section: str) -> None:
    if _load_json(report).get("passed") is not True:
        raise GateError(f"{section} report must say passed=true")


def _analysis(report: Path, section: str) -> None:
    if not _load_json(report):
        raise GateError(f"{section} report is empty")


def _git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    process = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=text)
    if process.returncode != 0:
        detail = process.stderr.strip() if text else process.stderr.decode(errors="replace").strip()
        raise GateError(detail or f"git {' '.join(args)} failed")
    return process


def _validate_production_diff(repo: Path, base: str, head: str, declaration: str) -> None:
    process = _git(repo, "diff", "--name-only", "-z", base, head, text=False)
    changed = [part.decode(errors="replace") for part in process.stdout.split(b"\0") if part]
    if not changed:
        raise GateError("base-to-head production diff is empty")
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_ROOTS)]
    if forbidden:
        raise GateError("production diff changes forbidden paths: " + ", ".join(forbidden))
    path, _, symbol = declaration.rpartition(":")
    if not path.startswith("src/tileops/") or not path.endswith(".py") or not _real_text(symbol):
        raise GateError("production_kernel must be src/tileops/<path>.py:<Symbol>")
    if path not in changed:
        raise GateError("the declared production kernel file is unchanged")
    messages = _git(repo, "log", "--format=%B", f"{base}..{head}").stdout
    if re.search(r"^(Co-authored-by|Signed-off-by):", messages, flags=re.MULTILINE | re.IGNORECASE):
        raise GateError("commit messages contain an extra authorship trailer")


def sections(text: str) -> list[tuple[str, str]]:
    """Each `## ` section of *text* outside code blocks: its heading and its text, heading line included."""
    found: list[tuple[str, str]] = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            found.append((line[3:].strip(), ""))
        if found:
            found[-1] = (found[-1][0], found[-1][1] + line)
    return found


def read_pr(round_dir: Path) -> tuple[str, str]:
    """The title and the body of the round's PR, from its filled-in template."""
    text = _required_file(round_dir, PR_FILE).read_text(encoding="utf-8").lstrip()
    first, _, body = text.partition("\n")
    if not first.startswith("# "):
        raise GateError(f"{PR_FILE} must start with the PR title as a `# ` line")
    return first[2:].strip(), body.strip() + "\n"


def read_comments(round_dir: Path) -> list[tuple[str, str]]:
    """The PR's comments: one per section of the filled-in comments file, in order."""
    found = sections(_required_file(round_dir, COMMENTS_FILE).read_text(encoding="utf-8"))
    if tuple(name for name, _ in found) != COMMENT_SECTIONS:
        raise GateError(f"{COMMENTS_FILE} must have exactly the sections {', '.join(COMMENT_SECTIONS)}, in order")
    return [(name, text.strip() + "\n") for name, text in found]


def _table(lines: list[str], header: str) -> list[list[str]]:
    """The cells of the Markdown table whose header line starts with *header*, header first."""
    start = next((i for i, line in enumerate(lines) if line.startswith(header)), None)
    if start is None:
        return []
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return [row for row in rows if not all(set(cell) <= set("-: ") for cell in row)]


def _time(value: object) -> float | None:
    """*value* as a measured time: a finite positive number, else None."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 and not isinstance(value, bool) else None


def _not_slower(table: list[list[str]], label: str) -> set[str]:
    """The rows of *table* faster than main; a row slower than main, or without times, fails."""
    main, candidate = table[0].index("main (us)"), table[0].index("candidate (us)")
    faster = set()
    for row in table[1:]:
        name = " ".join(cell.strip("`") for cell in row[:label]) if label else row[0].strip("`")
        times = [_time(row[i]) if i < len(row) else None for i in (main, candidate)]
        if None in times:
            raise GateError(f"Performance: row {name!r} needs positive times for main and candidate")
        if times[1] > times[0]:
            raise GateError(f"Performance: row {name!r} is slower than main")
        if times[1] < times[0]:
            faster.add(name)
    return faster


def _validate_performance(text: str, workloads: tuple[str, ...], measured: int, result: str) -> None:
    """The environment, the method, one row per workload of the op, and no row slower than main.

    The op's own table holds the bar: under `bar met` each row beats its comparator or ties
    it, or the DRAM floor, within one timer step; under `below bar` some row beats main. Other
    ops that share a changed kernel only must not be slower than main.
    """
    lines = text.splitlines()
    values = {row[0]: row[1].strip("`") for row in _table(lines, "| Environment |")[1:] if len(row) >= 2}
    missing = [row for row in ENVIRONMENT_ROWS if row not in values]
    if missing:
        raise GateError(f"Performance: the environment table lacks {', '.join(missing)}")
    if re.fullmatch(r"sha256:[0-9a-f]{64}", values["digest"]) is None:
        raise GateError("Performance: the digest must be the full sha256 of the image")
    step = _time(values["timer step (us)"])
    if step is None:
        raise GateError("Performance: the timer step must be a positive number of microseconds")
    if not any(line.startswith("Method: ") for line in lines):
        raise GateError("Performance: the Method line is missing")
    results = _table(lines, "| Workload |")
    if not results or not {"main (us)", "candidate (us)", "DRAM floor (us)", "ratio"} <= set(results[0]):
        raise GateError("Performance: the results table needs main (us), candidate (us), DRAM floor (us) and ratio columns")
    faster = _not_slower(results, 0)
    others = _table(lines, "| Op | Workload |")
    if others and not {"main (us)", "candidate (us)"} <= set(others[0]):
        raise GateError("Performance: the other-ops table needs main (us) and candidate (us) columns")
    if others:
        _not_slower(others, 2)
    names = [row[0].strip("`") for row in results[1:]] + [
        " ".join(cell.strip("`") for cell in row[:2]) for row in others[1:]]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise GateError(f"Performance: rows {', '.join(repeated)} appear more than once")
    seen = {row[0].strip("`") for row in results[1:]}
    if not seen or len(seen) < measured:
        raise GateError(f"Performance: the results table has {len(seen)} rows; the op has {measured} measured rows")
    absent = [name for name in workloads if name not in seen]
    if absent:
        raise GateError(f"Performance: the results table lacks the rows behind {', '.join(absent)}")
    # Each ratio column follows its comparator's time column.
    candidate, floor = results[0].index("candidate (us)"), results[0].index("DRAM floor (us)")
    ratios = [i for i, name in enumerate(results[0]) if name == "ratio"]
    for row in results[1:]:
        name = row[0].strip("`")
        ours, least = _time(row[candidate]), _time(row[floor]) if floor < len(row) else None
        if least is None:
            raise GateError(f"Performance: row {name!r} needs a positive DRAM floor")
        for i in ratios:
            comparator, stated = (_time(row[j]) if j < len(row) else None for j in (i - 1, i))
            if comparator is None or stated is None:
                raise GateError(f"Performance: row {name!r} needs a positive comparator time and ratio")
            if abs(stated - comparator / ours) > RATIO_ROUNDING:
                raise GateError(f"Performance: row {name!r} states ratio {stated}, "
                                f"its times give {comparator / ours:.4f}")
            # Rounded to the nanosecond, so a gap of exactly one step is a tie.
            if result == "bar met" and round(ours - max(comparator, least), 3) > step:
                raise GateError(f"Performance: row {name!r} is more than one timer step behind its "
                                "comparator and the floor, so the bar is not met")
    if result == "below bar" and not faster & seen:
        raise GateError("Performance: a below bar result must beat main on a row")


def _validate_pr(round_dir: Path, final_hir: Path, result: str, workloads: tuple[str, ...], measured: int) -> None:
    title, body = read_pr(round_dir)
    for name, text in ((PR_FILE, f"{title}\n{body}"),
                       (COMMENTS_FILE, _required_file(round_dir, COMMENTS_FILE).read_text(encoding="utf-8"))):
        left = PLACEHOLDER.search(re.sub(r"```.*?```", "", text, flags=re.DOTALL)) or EMPTY_BLOCK.search(text)
        if left:
            raise GateError(f"{name} still has the placeholder {left.group(0)}")
        if LOCAL_PATH.search(text):
            raise GateError(f"{name} exposes a local path")
    if not re.fullmatch(r"\[Perf\]\[foundry\]\[[A-Za-z0-9_-]+\] [A-Z`].+", title):
        raise GateError(f"the {PR_FILE} title does not follow [Perf][foundry][Family] Description")
    if tuple(name for name, _ in sections(body)) not in (BODY_SECTIONS, (*BODY_SECTIONS, "Regression")):
        raise GateError(f"{PR_FILE} must have exactly the sections {', '.join(BODY_SECTIONS)}, in order")
    comments = dict(read_comments(round_dir))
    match = re.search(r"```python\s*\n(.*?)\n```", comments["TileFoundry Description"], flags=re.DOTALL)
    if not match:
        raise GateError("TileFoundry Description must contain one Python HIR block")
    if match.group(1).strip() != final_hir.read_text(encoding="utf-8").strip():
        raise GateError("TileFoundry Description is not the exact final HIR")
    if "tf.schedule(" not in match.group(1):
        raise GateError("the final HIR must carry its tf.schedule instruction choices")
    _validate_performance(comments["Performance"], workloads, measured, result)
    stated = comments["Result And Limitations"].splitlines()[1:]
    if next((line.strip() for line in stated if line.strip()), None) != f"**{result}**":
        raise GateError(f"Result And Limitations must open with **{result}**, the result of provenance.json")


def _validate_findings(round_dir: Path) -> None:
    data = _load_json(_required_file(round_dir, "findings.json"))
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise GateError("findings.json must contain a findings list")
    # A round reports its findings to TileFoundry as one issue, so the link is one
    # field for the whole file rather than one per finding.
    issue = data.get("issue")
    if findings:
        if not isinstance(issue, str) or not re.fullmatch(r"https://github\.com/tile-ai/TileFoundry/issues/\d+", issue):
            raise GateError("findings.json issue must be the one tile-ai/TileFoundry issue URL "
                            "that holds every finding of this round")
    elif issue is not None:
        raise GateError("findings.json issue must be null when there is no finding")
    for finding in findings:
        if not isinstance(finding, dict) or not _real_text(finding.get("id")):
            raise GateError("every finding must have an id")
        for field in ("classification", "command", "expected", "actual", "workaround_cost", "public_surface"):
            if not _real_text(finding.get(field)):
                raise GateError(f"every finding must record {field}")
        if not isinstance(finding.get("affected_workloads"), list):
            raise GateError("every finding must record affected_workloads")
        _required_file(round_dir, finding.get("reproducer"))


def _list(provenance: dict, name: str) -> list:
    value = provenance.get(name)
    if not isinstance(value, list) or not value:
        raise GateError(f"provenance {name} must be a non-empty list")
    return value


def validate_round(round_dir: Path, tileops_repo: Path, head: str = "HEAD",
                   workloads: tuple[str, ...] = (), measured: int = 0) -> dict:
    """Validate only facts a program can decide without interpreting optimization quality.

    *workloads* are the op's rows behind and *measured* its count of measured rows; the
    Performance table must show each row behind and as many rows as were measured.
    """
    round_dir = round_dir.resolve()
    tileops_repo = tileops_repo.resolve()
    provenance = _load_json(_required_file(round_dir, "provenance.json"))
    base = provenance.get("tileops_base")
    if not isinstance(base, str) or re.fullmatch(r"[0-9a-f]{40}", base) is None:
        raise GateError("provenance tileops_base must be the full admitted commit")
    if _git(tileops_repo, "rev-parse", f"{base}^{{commit}}").stdout.strip() != base:
        raise GateError("provenance tileops_base is not available in the TileOPs repository")
    if _git(tileops_repo, "status", "--porcelain").stdout.strip():
        raise GateError("TileOPs worktree must be clean and committed before the PR gate")
    foundry_base = provenance.get("tilefoundry_base")
    if not isinstance(foundry_base, str) or re.fullmatch(r"[0-9a-f]{40}", foundry_base) is None:
        raise GateError("provenance tilefoundry_base must be the full TileFoundry commit")
    if provenance.get("candidate_commit") != _git(tileops_repo, "rev-parse", head).stdout.strip():
        raise GateError("provenance candidate_commit must be the commit the PR ships; measure it again")
    result = provenance.get("result")
    if result not in RESULTS:
        raise GateError(f"provenance result must be one of: {', '.join(RESULTS)}")

    final_hir = _required_file(round_dir, provenance.get("final_hir"))
    _required_file(round_dir, provenance.get("runtime_twin"))
    _passed(_record(round_dir, provenance.get("reference_check"), "reference_check", "check",
                    flags=("--expected", "--json")), "reference_check")
    floor = _list(provenance, "floor")
    absent = sorted(set(workloads) - {record.get("workload") for record in floor if isinstance(record, dict)})
    if absent:
        raise GateError(f"floor lacks the rows behind {', '.join(absent)}")
    for index, record in enumerate(floor):
        _analysis(_record(round_dir, record, f"floor[{index}]", "analyze", flags=("--roofline", "--json")),
                  f"floor[{index}]")
    placements = _list(provenance, "placements")
    if len(placements) < 2 or sum(isinstance(p, dict) and p.get("chosen") is True for p in placements) != 1:
        raise GateError("placements must compare at least two placements and choose exactly one")
    for index, record in enumerate(placements):
        if not isinstance(record, dict) or not _real_text(record.get("placement")):
            raise GateError(f"placements[{index}] must describe its placement")
        _analysis(_record(round_dir, record, f"placements[{index}]", "analyze", flags=("--performance", "--json")),
                  f"placements[{index}]")
    _record(round_dir, provenance.get("schedule"), "schedule", "schedule", "finalize")
    _passed(_record(round_dir, provenance.get("twin_check"), "twin_check", "check", flags=("--json",)), "twin_check")
    for index, iteration in enumerate(_list(provenance, "iterations")):
        if not isinstance(iteration, dict) or not all(_real_text(iteration.get(k)) for k in ("change", "basis")):
            raise GateError(f"iterations[{index}] must record its change and its basis")
        for key in ("predicted_us", "measured_us"):
            if not isinstance(iteration.get(key), (int, float)) or _time(iteration[key]) is None:
                raise GateError(f"iterations[{index}] must record a positive {key}")
    for section in ("tests", "benchmark"):
        _record(round_dir, provenance.get(section), section)
    for review in _list(provenance, "reviews"):
        _required_file(round_dir, review)

    _required_file(round_dir, "report.md")
    _validate_findings(round_dir)
    production_kernel = provenance.get("production_kernel")
    if not _real_text(production_kernel):
        raise GateError("provenance must declare production_kernel as src/tileops/<path>.py:<Symbol>")
    _validate_production_diff(tileops_repo, base, head, production_kernel)
    _validate_pr(round_dir, final_hir, result, workloads, measured)
    return provenance
