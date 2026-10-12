"""Grading the nightly benchmark the way the TileOPs benchmark site does.

The rules are those of `scripts/gen_bench_pages.py` in tile-ai/TileOPs.github.io:
per workload the fastest rival in the library and torch tiers; the op's rival is
the one named most often; its geometric-mean ratio (rival time / TileOPs time)
against that rival is ahead at >= 1.05, level at >= 0.95, behind below. An op
with only reference rivals is unrated. Keep this file in step with that script.
"""

from __future__ import annotations

import json
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from topa import sh
from topa.config import HOME

NIGHTLY = "tile-ai/TileOPs-nightly"
SNAPSHOT_BRANCH = "snapshots"
CACHE = HOME / "cache" / "nightly"

AHEAD, PAR, BEHIND, UNRATED = "ahead", "par", "behind", "unrated"
PAR_BAND = (0.95, 1.05)
TIER_LIB, TIER_TORCH, TIER_REF = "lib", "torch", "ref"
TORCH_NATIVE = {"torch", "torch-autograd", "torch-dequantized-matmul"}
LEGACY_TAG = "baseline"
METRIC_SUFFIXES = (
    "device_busy_p10_ms", "device_busy_p90_ms", "device_busy_ms",
    "latency_p10_ms", "latency_p90_ms", "latency_ms", "gap_ms",
    "uncounted_copy_ms", "bandwidth_tbs", "tflops", "ratio", "n_kernels",
    "n_samples", "flops", "bytes", "roof_key", "dtype", "timing", "variant",
)
NUMERIC = {
    "device_busy_ms", "device_busy_p10_ms", "device_busy_p90_ms",
    "latency_ms", "latency_p10_ms", "latency_p90_ms", "gap_ms",
    "uncounted_copy_ms", "tflops", "bandwidth_tbs", "ratio", "flops",
    "bytes", "n_kernels", "n_samples",
}


def tier_of(tag: str) -> str:
    if tag.endswith("-ref") or tag.endswith("_ref"):
        return TIER_REF
    if tag in TORCH_NATIVE:
        return TIER_TORCH
    return TIER_LIB


def status_of(ratio: float) -> str:
    lo, hi = PAR_BAND
    return AHEAD if ratio >= hi else PAR if ratio >= lo else BEHIND


# --- the snapshot -------------------------------------------------------------------


@dataclass(frozen=True)
class Snapshot:
    meta: dict[str, Any]
    bench: Path

    @property
    def label(self) -> str:
        env = self.meta.get("environment", {})
        image = str(env.get("image", "")).rsplit("/", 1)[-1]
        return (f"Nightly {self.meta.get('date')}, TileOPs `{str(self.meta.get('commit', ''))[:8]}`, "
                f"{self.meta.get('gpu', '').replace('NVIDIA ', '')}, `{image}`, CUPTI device-busy, "
                f"`{SNAPSHOT_BRANCH}/bench_results.xml` in {NIGHTLY}")


def _blob(sha: str, target: Path) -> None:
    # raw.githubusercontent is slow from here; the blob API serves the same bytes.
    data = sh.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                   f"repos/{NIGHTLY}/git/blobs/{sha}"])
    tmp = target.with_suffix(".part")
    tmp.write_text(data + "\n")
    tmp.replace(target)


def fetch(refresh: bool = True) -> Snapshot:
    """The newest nightly snapshot, cached under `~/.topa/cache/nightly/<commit>/`."""
    latest = CACHE / "latest"
    if refresh or not latest.is_symlink():
        tree = sh.gh_json("api", f"repos/{NIGHTLY}/git/trees/{SNAPSHOT_BRANCH}")
        blobs = {entry["path"]: entry["sha"] for entry in tree["tree"]}
        folder = CACHE / blobs["bench_results.xml"]
        folder.mkdir(parents=True, exist_ok=True)
        for name in ("meta.json", "bench_results.xml"):
            if not (folder / name).is_file():
                _blob(blobs[name], folder / name)
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(folder.name)
    folder = latest.resolve()
    return Snapshot(json.loads((folder / "meta.json").read_text()), folder / "bench_results.xml")


# --- grading ------------------------------------------------------------------------


def _num(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pos(value: Any) -> float | None:
    return value if isinstance(value, (int, float)) and value > 0 else None


def _busy(impl: dict[str, Any]) -> float | None:
    return _pos(impl.get("device_busy_ms")) or _pos(impl.get("latency_ms"))


def parse(path: Path) -> list[dict[str, Any]]:
    """The benchmarked workloads in a JUnit XML; skipped and failed cases are left out."""
    workloads = []
    for case in ET.parse(path).iter("testcase"):
        if case.find("skipped") is not None or case.find("failure") is not None or case.find("error") is not None:
            continue
        props = {p.attrib["name"]: p.attrib.get("value", "") for p in case.iter("property")}
        if "op" not in props:
            continue
        impls: dict[str, dict[str, Any]] = defaultdict(dict)
        for key, value in props.items():
            if key in ("op", "op_module"):
                continue
            for suffix in METRIC_SUFFIXES:
                if key.endswith("_" + suffix):
                    tag = key[: -len(suffix) - 1]
                    if tag != LEGACY_TAG:
                        impls[tag][suffix] = _num(value) if suffix in NUMERIC else value
                    break
        name = case.attrib.get("name", "")
        workloads.append({
            "name": name,
            "config": name.split("[")[-1].rstrip("]") if "[" in name else name,
            "op": props["op"],
            "op_module": props.get("op_module"),
            "bench": case.attrib.get("classname"),
            "impls": dict(impls),
        })
    return workloads


def rivals(workload: dict[str, Any]) -> tuple[float | None, dict[str, dict[str, Any]]]:
    busy = _busy(workload["impls"].get("tileops", {}))
    found = {}
    for tag, impl in workload["impls"].items():
        if tag.startswith("tileops"):
            continue
        rival_busy = _busy(impl)
        if not rival_busy:
            continue
        # The recorded ratio was computed before the times were rounded for the XML.
        speedup = _pos(impl.get("ratio")) or (rival_busy / busy if busy else None)
        found[tag] = {"tier": tier_of(tag), "busy_ms": rival_busy, "speedup": speedup}
    return busy, found


@dataclass
class Row:
    config: str
    tileops_ms: float | None
    rival: str | None
    rival_ms: float | None
    speedup: float | None


@dataclass
class Grade:
    op: str
    op_module: str | None
    bench: str | None
    status: str
    rival: str | None
    speedup: float | None
    rows: list[Row] = field(default_factory=list)

    @property
    def behind_rows(self) -> int:
        return sum(1 for row in self.rows if row.speedup is not None and row.speedup < PAR_BAND[0])

    @property
    def rated_rows(self) -> int:
        return sum(1 for row in self.rows if row.speedup is not None)

    def as_dict(self) -> dict[str, Any]:
        return {"op": self.op, "status": self.status, "rival": self.rival, "speedup": self.speedup,
                "behind_rows": self.behind_rows, "rated_rows": self.rated_rows,
                "op_module": self.op_module, "bench": self.bench}


def _best(per_workload: list[tuple[str, float]]) -> tuple[str | None, float | None]:
    if not per_workload:
        return None, None
    tag = Counter(t for t, _ in per_workload).most_common(1)[0][0]
    return tag, statistics.geometric_mean([s for t, s in per_workload if t == tag])


def grade_op(op: str, workloads: list[dict[str, Any]]) -> Grade:
    rows, real, ref = [], [], []
    for workload in workloads:
        busy, found = rivals(workload)
        best_row = None
        for tiers, sink in (((TIER_LIB, TIER_TORCH), real), ((TIER_REF,), ref)):
            candidates = {t: r for t, r in found.items() if r["tier"] in tiers and r["speedup"]}
            if candidates:
                tag = min(candidates, key=lambda t: candidates[t]["busy_ms"])
                sink.append((tag, candidates[tag]["speedup"]))
                if tiers != (TIER_REF,):
                    best_row = (tag, candidates[tag])
        rows.append(Row(workload["config"], busy, best_row[0] if best_row else None,
                        best_row[1]["busy_ms"] if best_row else None,
                        best_row[1]["speedup"] if best_row else None))
    tag, ratio = _best(real)
    status = status_of(ratio) if ratio is not None else UNRATED
    if tag is None:
        tag, ratio = _best(ref)
    first = workloads[0]
    return Grade(op, first.get("op_module"), first.get("bench"), status, tag, ratio, rows)


def grade(snapshot: Snapshot) -> list[Grade]:
    by_op: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for workload in parse(snapshot.bench):
        by_op[workload["op"]].append(workload)
    return sorted((grade_op(op, items) for op, items in by_op.items()),
                  key=lambda g: (g.speedup is None, g.speedup or 0.0, g.op))
