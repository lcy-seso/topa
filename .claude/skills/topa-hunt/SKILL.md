---
name: topa-hunt
description: Show the TileOPs Perf Tracker queue, let the user pick ops, and start a TileFoundry round on each. Use when the user asks what to optimize next, to hunt for work, or to dispatch rounds.
---

# topa hunt

The nightly writes the queue of ops behind to the TileOPs wiki. Each picked op gets one
round.

Run `topa` from `PATH`.

## Steps

1. **Show the table.** Run `topa hunt` and show its output to the user exactly. It lists
   every op of the newest Perf Tracker queue in the page's order, with its label, worst
   ratio, rows behind, nightlies behind and rounds, then each op's rows.
2. **Let the user pick.** Ask which rows to work: one or more numbers. Do not pick for
   them. Point out rows that need a decision:
   - the op already has a running round: do not start another;
   - more rows than `max_rounds` (`topa config`) allows: the extra ones wait.
3. **Start the rounds.** For each picked op: `topa round start <Op>`. It prints the round
   slug, its pane and how to watch it. Start them one after another, not in parallel:
   each start prepares shared caches under a lock.
4. **Report.** One line per round: slug, op, branch, GPU, pane. Say that
   `topa round status` follows them.

## Finish

The skill is done when every picked op has a running round, or the user was told why one
did not start (with the error, unchanged).
