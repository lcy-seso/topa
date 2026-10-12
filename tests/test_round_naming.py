from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from topa import ledger
from topa.issue import Issue, area, branch_name, branch_type, round_slug
from topa.round import kit, render

BRANCH = re.compile(r"^(bench|chore|design|doc|feat|fix|maintain|perf|refactor|style|test)/[a-z0-9._-]+/[a-z0-9._-]+$")


def issue(title: str, labels: tuple[str, ...] = ()) -> Issue:
    return Issue(2282, title, "open", labels, (), "https://github.com/tile-ai/TileOPs/issues/2282", 1)


class NamingTests(unittest.TestCase):
    def test_branch_follows_tileops_pattern(self) -> None:
        for title, labels in (
            ("[Perf][Attention] DSA decode is behind FlashMLA", ("perf",)),
            ("[Kernel][GEMM] FP8 1D2D", ()),
            ("Something without tags", ()),
            ("[Perf][Linear Attention] GLA", ()),
        ):
            name = branch_name(issue(title, labels), "i2282-r1")
            self.assertRegex(name, BRANCH)

    def test_family_fills_a_missing_area(self) -> None:
        self.assertEqual(branch_name(issue("[Kernel] GemmFp8FwdOp: x"), "i1-r1", "gemm"), "feat/gemm/i1-r1")
        self.assertEqual(branch_name(issue("[Perf][Attention] x"), "i1-r1", "gemm"), "perf/attention/i1-r1")

    def test_type_and_area(self) -> None:
        self.assertEqual(branch_type("[Kernel][GEMM] x", ()), "feat")
        self.assertEqual(branch_type("[Perf][GEMM] x", ("bug",)), "fix")
        self.assertEqual(area("[Perf][Linear Attention] x"), "linear-attention")
        self.assertEqual(area("no tags"), "ops")

    def test_slug_counts_earlier_rounds(self) -> None:
        self.assertEqual(round_slug(7, []), "i7-r1")
        self.assertEqual(round_slug(7, [{"round": "i7-r1", "issue": 7}, {"round": "i8-r1", "issue": 8}]), "i7-r2")
        self.assertRegex(round_slug(123456, []), r"^[a-z][a-z0-9_-]{0,31}$")


class BriefTests(unittest.TestCase):
    def test_every_placeholder_is_known(self) -> None:
        names = set(re.findall(r"\{\{([A-Z_]+)\}\}", (kit() / "brief.md").read_text()))
        values = {name: f"<{name}>" for name in names}
        text = render((kit() / "brief.md").read_text(), values)
        self.assertNotIn("{{", text)
        self.assertIn("<TOPA> pr --reviewed", text)

    def test_missing_value_is_an_error(self) -> None:
        with self.assertRaises(SystemExit):
            render("a {{ISSUE}} b {{BRANCH}}", {"ISSUE": 1})


class LedgerTests(unittest.TestCase):
    def test_fold(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.jsonl"
            ledger.append("create", path, round="i1-r1", issue=1)
            ledger.append("worktree", path, round="i1-r1", pane="w1:p1")
            ledger.append("start", path, round="i1-r1", gpu=3)
            ledger.append("say", path, round="i1-r1", text="hello")
            ledger.append("create", path, round="i2-r1", issue=2)
            ledger.append("fail", path, round="i2-r1", error="boom")
            views = ledger.rounds(path)
            self.assertEqual(views["i1-r1"]["state"], "running")
            self.assertEqual(views["i1-r1"]["pane"], "w1:p1")
            self.assertNotIn("text", views["i1-r1"])
            self.assertEqual(views["i1-r1"]["history"], ["create", "worktree", "start", "say"])
            self.assertEqual(views["i2-r1"]["state"], "failed")


if __name__ == "__main__":
    unittest.main()
