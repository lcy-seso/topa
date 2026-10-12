---
name: topa-hunt
description: Find TileOPs ops that are behind on the nightly benchmark, let the user pick some, file or claim one issue per op, and start a TileFoundry round on each. Use when the user asks what to optimize next, to hunt for work, or to dispatch rounds.
---

# topa hunt

The loop: the nightly says which ops are behind; each picked op gets one issue
assigned to the user; each issue gets one round. One issue is one round's scope,
so never start a round on an issue that covers several ops unless the user says so.

`topa` is `~/topa/.venv/bin/topa`. Run it by that path.

## Steps

1. **Show the table.** Run `topa hunt` and show its table to the user exactly. It lists
   every op graded `behind` with the site's rules, its rival, the geometric-mean ratio,
   rows behind, the open issue that names the op, its assignee, and any round on it.
   `topa hunt --all` also lists ops that are level or ahead.
2. **Let the user pick.** Ask which rows to work: one or more numbers. Do not pick for
   them. Point out rows that need a decision:
   - the issue is assigned to someone else: it is theirs; skip it unless the user says;
   - a round is already on the issue: do not start another;
   - the issue names several ops: a round on it works all of them;
   - more rows than `max_rounds` (`topa config`): the extra ones wait.
3. **File or claim the issues.** Run `topa issue new <Op> [<Op> ...]` with the picked op
   names. For an op with no open issue it files one (`[Perf][<Family>] <Op> is behind
   <rival>`, the per-workload table, `perf` label), assigns it to the user and links it
   under the tracker issue. For an op that already has an unassigned issue it assigns
   that issue to the user. `--dry-run` prints the issues without filing them.
4. **Start the rounds.** For each issue: `topa round start <issue>`. It prints the round
   slug, its pane and how to watch it. Start them one after another, not in parallel:
   each start prepares shared caches under a lock.
5. **Report.** One line per round: slug, issue link, branch, GPU, pane. Say that
   `topa round status` follows them.

## Finish

The skill is done when every picked op has an issue assigned to the user and a running
round, or the user was told why one did not start (with the error, unchanged).
