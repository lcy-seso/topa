from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from topa.grade import AHEAD, BEHIND, PAR, UNRATED, grade_op, parse, tier_of
from topa.hunt import issues_naming


def case(op: str, config: str, props: dict[str, float]) -> str:
    rows = "".join(f'<property name="{k}" value="{v}" />' for k, v in props.items())
    return (f'<testcase classname="benchmarks.ops.bench_x" name="test_x[{config}]">'
            f'<properties><property name="op" value="{op}" /><property name="op_module" '
            f'value="tileops.ops.attention.x" />{rows}</properties></testcase>')


def workloads(*cases: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "bench.xml"
        path.write_text("<testsuites><testsuite>" + "".join(cases) + "</testsuite></testsuites>")
        return parse(path)


class GradeTests(unittest.TestCase):
    def test_tiers(self) -> None:
        self.assertEqual(tier_of("torch-ref"), "ref")
        self.assertEqual(tier_of("torch_fp32_ref"), "ref")
        self.assertEqual(tier_of("torch-autograd"), "torch")
        self.assertEqual(tier_of("fla"), "lib")

    def test_rival_named_most_often_and_its_geomean(self) -> None:
        items = workloads(
            case("A", "w1", {"tileops_device_busy_ms": 1.0, "fla_device_busy_ms": 0.5, "torch_device_busy_ms": 2.0}),
            case("A", "w2", {"tileops_device_busy_ms": 1.0, "fla_device_busy_ms": 0.8}),
            case("A", "w3", {"tileops_device_busy_ms": 1.0, "torch_device_busy_ms": 0.9}),
        )
        g = grade_op("A", items)
        self.assertEqual(g.rival, "fla")
        self.assertAlmostEqual(g.speedup, (0.5 * 0.8) ** 0.5)
        self.assertEqual(g.status, BEHIND)
        self.assertEqual(g.behind_rows, 3)

    def test_recorded_ratio_wins_and_legacy_tag_is_dropped(self) -> None:
        items = workloads(case("A", "w", {"tileops_device_busy_ms": 1.0, "fla_device_busy_ms": 1.0,
                                          "fla_ratio": 1.2, "baseline_device_busy_ms": 0.1}))
        g = grade_op("A", items)
        self.assertEqual((g.rival, g.speedup, g.status), ("fla", 1.2, AHEAD))

    def test_par_band_and_reference_only(self) -> None:
        par = grade_op("A", workloads(case("A", "w", {"tileops_device_busy_ms": 1.0, "fla_device_busy_ms": 0.96})))
        self.assertEqual(par.status, PAR)
        ref = grade_op("B", workloads(case("B", "w", {"tileops_device_busy_ms": 1.0, "torch-ref_device_busy_ms": 0.1})))
        self.assertEqual(ref.status, UNRATED)

    def test_issue_matching_is_by_whole_name(self) -> None:
        issues = [
            {"number": 1, "title": "[Perf] GQABwdOp is slow", "body": ""},
            {"number": 2, "title": "tracker", "body": "GQABwdOp"},
            {"number": 3, "title": "other", "body": "mentions GQABwdOpX only"},
            {"number": 4, "title": "body only", "body": "see `GQABwdOp`"},
        ]
        self.assertEqual([i["number"] for i in issues_naming("GQABwdOp", issues, tracker=2)], [1, 4])


if __name__ == "__main__":
    unittest.main()
