# How a round works

One round is one agent making one [TileOPs](https://github.com/tile-ai/TileOPs) op reach
its fastest comparator:

1. The TileOPs nightly writes a Perf Tracker page to the TileOPs wiki: the ops behind, in
   the order to work them, with each op's rows. `topa hunt` reads the newest page and shows
   what already works each op.
2. `topa round start <Op>` creates a TileOPs worktree and branch, a TileFoundry checkout,
   a container with one GPU, and a round directory with the brief. The brief carries the
   op's rows. Then it starts Claude Code in a herdr pane and tells it to read the brief.
3. The agent runs on the host. A PreToolUse hook sends each shell line that runs anything
   but `git`, `gh`, `codex`, `topa`, a file operation or a text tool into the round's
   container over SSH.
4. The agent follows the brief's seven stages: classify the comparators; check an HIR
   reference against authoritative outputs; take the floor and choose a placement with
   TileFoundry; implement in rounds whose schedule TileFoundry derives, measuring main
   and the candidate alternately; have Codex review the diff; clean up and verify
   again; open the PR with `topa pr`. That command checks the evidence, opens the PR from
   your fork, and posts the evidence as four comments. TileFoundry problems the agent hits
   go into one TileFoundry issue.
5. A round that misses the bar on some rows still opens its PR when it beats main and
   slows no row; the unmet rows go under Result And Limitations. Otherwise it opens no PR
   and writes its stop records in `report.md`.
6. `topa round stop <slug> [--rm]` stops the agent, archives its transcripts, and with
   `--rm` releases the container, the worktree and the checkout.

```mermaid
flowchart LR
    N["nightly benchmark"] -- "Perf Tracker page" --> Q["wiki queue"]
    Q -- "topa round start" --> A["agent + GPU container"]
    A -- "topa pr" --> P["TileOPs PR"]
    A -- "findings" --> F["TileFoundry issue"]
    P --> N
    F -- "TileFoundry fix" --> A
```

A merged PR moves the nightly. A TileFoundry fix reaches the next round.
