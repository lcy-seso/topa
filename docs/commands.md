# Commands

| Command | Does |
| --- | --- |
| `topa setup` | check tools, build `topa:agent`, include the round SSH entries |
| `topa config [--default]` | print the settings in effect / print a default `config.toml` |
| `topa hunt [--cached]` | the newest Perf Tracker queue, with each op's rows and rounds |
| `topa round start <Op>` | start a round on an op of the queue |
| `topa round say <slug> "..."` | message the round's agent |
| `topa round status` | every round, its agent state and PR |
| `topa round log [<slug>]` | ledger events |
| `topa round stop <slug> [--rm]` | stop, archive, release |
| `topa gate` / `topa pr [--reviewed]` | check the evidence / open the PR (run by the agent) |
| `topa review prepare <PR>` | write the PR's review inputs and check out its head |
| `topa review post <PR>` | post the findings as one COMMENT review |
| `topa run <cmd>` | one command against a TileOPs worktree in a throwaway container |
