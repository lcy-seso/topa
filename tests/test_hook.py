from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from topa.hook import decide, pre_tool_use, runs_on_the_host


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.round = Path(self.temporary.name)
        (self.round / "round.json").write_text(json.dumps({"round": "i1-r1", "alias": "topa-i1-r1"}))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def event(self, command: str) -> dict:
        return {"tool_input": {"command": command, "description": "x"}, "cwd": str(self.round / "work")}

    def test_host_commands_stay_on_the_host(self) -> None:
        for command in ("git status", "gh pr view 1 && ls", "cat a | cat", "/abs/.venv/bin/topa pr --reviewed"):
            self.assertTrue(runs_on_the_host(command), command)
            self.assertIsNone(decide(self.event(command), self.round))

    def test_one_container_segment_moves_the_line(self) -> None:
        answer = decide(self.event("cd work && pytest -x"), self.round)
        assert answer is not None
        updated = answer["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["description"], "x")
        self.assertTrue(updated["command"].startswith("ssh -T topa-i1-r1 "))
        self.assertIn("cd ", updated["command"])
        self.assertIn("pytest -x", updated["command"])

    def test_unbalanced_quotes_go_to_the_container(self) -> None:
        self.assertFalse(runs_on_the_host("git commit -m 'oops"))

    def test_no_round_json_leaves_the_command(self) -> None:
        (self.round / "round.json").unlink()
        self.assertIsNone(decide(self.event("python x.py"), self.round))

    def test_stdin_to_stdout(self) -> None:
        out = io.StringIO()
        event = {**self.event("nvidia-smi"), "cwd": str(self.round)}
        pre_tool_use(io.StringIO(json.dumps(event)), out)
        self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "allow")


if __name__ == "__main__":
    unittest.main()
