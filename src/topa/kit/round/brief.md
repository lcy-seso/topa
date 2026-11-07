# {{SLUG}}: bring {{OP}} to its fastest comparator

Make `{{OP}}` of [tile-ai/TileOPs](https://github.com/tile-ai/TileOPs) at least as fast as
its fastest comparator with [TileFoundry](https://github.com/tile-ai/TileFoundry). The
code, the PR and any TileFoundry issue are public.

## Requirement

The rows of `{{OP}}` behind in the [Perf Tracker of {{NIGHTLY_DATE}}]({{WIKI_URL}}) (nightly
run [{{NIGHTLY_RUN}}]({{NIGHTLY_RUN_URL}}), commit `{{NIGHTLY_COMMIT}}`, benchmark
`{{BENCHMARK}}`; CUPTI `device_busy_ms` in microseconds; ratio = comparator / TileOPs):

{{ROWS}}

- Take these rows and the op's manifest entry, Op, workloads, reference, tests and
  benchmark as the whole requirement.
- Write production code only in the worktree.
- Keep experiments, evidence and records in the round directory, `{{ROUND_DIR}}`.

| Environment | Value |
| --- | --- |
| branch | `{{BRANCH}}` |
| TileOPs base | `{{TILEOPS_BASE}}` |
| TileOPs worktree | `{{TILEOPS_WORKTREE}}` |
| TileFoundry base | `{{TILEFOUNDRY_BASE}}` |
| TileFoundry source (read-only) | `{{TILEFOUNDRY_SOURCE}}` |

## The bar

| Result | When | Do |
| --- | --- | --- |
| `bar met` | Every row of `{{OP}}`, behind or not, beats its fastest comparable comparator in the median and in every repeat, or ties it within one timer step or at the DRAM floor; no row of any op is slower than main. | Open the PR. |
| `below bar` | The bar is not met, the candidate beats main on a row behind, and no row of any op is slower than main. | Open the PR; list the unmet rows in Result And Limitations. |
| none | Neither, or a person must decide. | Follow [Ending without a PR](#ending-without-a-pr). |

- "Any op" includes every op that shares a kernel the round changes.
- `topa gate` rejects `bar met` with a ratio below 0.99; the review judges ties above it.

## Rules

- Keep main's cache hints and launch policy exactly (`evict_first`, `evict_last`, cache
  modifiers, L2 persistence, PDL).
- Do not defer writes, add GPU sleeps, or take a win only the L2 flush state gives.
- Do not branch on a shape.
- Derive each dispatch rule from hardware and call facts, sweep it over the workloads, and
  cover it with a test.
- Do not change the benchmark, its timing, the comparators, the repository's tolerances,
  the workloads, the manifest or the public Op.
- Add no op and no compatibility shim.
- Migrate every caller of a changed interface in the same PR.
- Fix shared code with one rule for every op, never a list of ops or shapes.
- Fix a bug in main that the changed call paths hit in this PR, with a test. Report other
  bugs in `report.md`.
- Prove each new test by mutation in a snapshot no timing run compiles from. Why: TileLang
  re-reads kernel source at compile time.
- Follow `docs/design/` and `docs/code-style.md` of TileOPs.
- Never change the TileFoundry source or open a PR on `tile-ai/TileFoundry`.

## Where commands run

- Lines that run only `git`, `gh`, `codex`, `topa`, file commands or text tools run on the
  host; every other line runs in the round container, at the same paths.
- Do not write `ssh` or `docker` commands.

## Stages

- Read every page of `tilefoundry tutorial` before stage 1.
- Read `{{KNOWLEDGE}}` before stage 3.
- Resolve TileFoundry usage questions with `tilefoundry tutorial`, `spec` and `--help`.
- Cite `tilefoundry --version` and the target name with every analysis number.

### 1. Requirement and comparators

1. Locate the gap (kernel body, tuning pick, launch count or host idle time) with CUPTI
   per-kernel times and `ncu`.
2. Run each comparator through the repository benchmark with the settings its
   documentation recommends. Record any setting the benchmark cannot apply.
3. Classify each (workload, comparator) pair:

| Class | Timed | Counts toward the fastest comparator |
| --- | --- | --- |
| comparable (passes the shared case reference) | yes | yes |
| not semantically comparable; reason recorded | yes | no |
| cannot express the case; reason recorded | no | no |

4. List the last two classes in Result And Limitations.

Exit: every pair is classified, and each row behind has a comparable comparator. If one has
none, follow [Ending without a PR](#ending-without-a-pr).

### 2. HIR reference

1. Write the op's math in HIR, one module per workload or with `--dim`.
2. Save the repository reference's outputs on the same inputs as `.pt`.
3. Run `tilefoundry check <hir>.py:<Module> --inputs files:<in> --expected <out> --json <report>`
   with a two-sided `--fn` and `nan_inf` per output.
4. Add `--weights ckpt:<dir>` for `ConstTensor` weights.
5. Derive each `check` tolerance from the dtype and the serial roundings.
6. Record each derivation; never loosen a tolerance for a single workload.

Exit: the check passes on every output of every workload.

### 3. Floor and placement

1. Run `tilefoundry analyze <hir>.py:<Module> <report> --compute-cost --memory --roofline --json`
   per workload; `ideal-ns` and `bound-by` are its floor.
2. Check the flops and traffic by hand: each input read once, each output written once.
3. Fix the HIR where the hand count and the report disagree.
4. List placements, including the incumbent's and the fastest comparator's, read from `ncu`
   and the comparator's generated source.
5. Run `analyze ... --memory --performance --json` on each placement.
6. Choose one by waves, storage use and predicted time, and record why.

Exit: every workload has a checked floor, and the chosen placement has a recorded reason.

### 4. Implementation rounds

Run each round in this order, and add it to `iterations` in `provenance.json`:

1. Change the HIR's placement or schedule.
2. Run `analyze`. Continue if it predicts less time than the current kernel's placement on
   the targeted rows. Otherwise continue only with a named effect HIR cannot express and
   the measurement that would show it.
3. Run `tilefoundry schedule candidates`.
4. Run `tilefoundry schedule facts --target <target> <instruction>` for each candidate you
   consider.
5. Write the choices into `tf.schedule`.
6. Run `tilefoundry schedule finalize` and write the TileLang kernel from its TIR.
7. Re-run the stage 2 check if the math, outputs or shapes changed.
8. Run `tilefoundry check <twin>.py:<Twin> --json <report>` on the runtime twin, which calls
   the production kernel.
9. Run the TileOPs tests.
10. Measure (rules below).
11. Record measured / floor, measured / predicted and comparator / measured.
12. Record the cause of a prediction error, or that it is unresolved, in TileFoundry
    Findings.

Measure this way:

- Snapshot the base and each candidate commit with
  `git -C {{TILEOPS_WORKTREE}} worktree add --detach {{ROUND_DIR}}/work/<name> <commit>`.
- Time each snapshot with its `src` first on `PYTHONPATH`.
- Alternate main, candidate and comparators on the round's GPU, with the L2 flush.
- Take the median of at least three runs of `device_busy_ms`.

Exit: the bar is met. Otherwise, exit when all three stop records hold:

| Record | Holds when |
| --- | --- |
| (1) Gap attribution | Each workload's measured / floor is listed, and each gap is tied to a bottleneck with `ncu` or `analyze` data. |
| (2) Directions exhausted | Each direction on the recorded list for each bottleneck was measured or shown infeasible. |
| (3) TileFoundry consulted | Alternative placements were analyzed, `tutorial optimize` and the `spec` pages of each bottleneck were read, and each direction they gave is on the list. |

### 5. Review

1. Run Codex read-only from the worktree:

   ```bash
   codex exec -C {{TILEOPS_WORKTREE}} --sandbox read-only "<prompt>" < /dev/null > evidence/review-<n>.md 2>&1
   ```

2. Give it the diff against the current `tileops_base`, this brief, the rows, the
   Performance table with its raw timings, the timer resolution and the floors, and the
   paths of TileOPs `docs/design/` and `docs/code-style.md`. Give it none of your
   conclusions.
3. Ask for correctness (edge shapes, dtypes, tails), the real call path, branch coverage by
   tests, the comparator classes, ties claimed under the bar, regressions against main,
   and hotfixes: a loosened tolerance or check, a skipped case, logic only tests reach, or
   a shape branch.
4. Fix each finding you agree with.
5. Answer each other finding with a test, a measurement or a rule.
6. Rerun Codex on the revised diff. Rerun a review that ends in an error.

Exit: no blocking or major finding is left. A blocking or major finding still disputed
after two reviews ends the round: follow [Ending without a PR](#ending-without-a-pr).

### 6. Cleanup

1. Inline single-caller helpers.
2. Merge repeated logic.
3. Delete process comments and tests that guard no shipped behavior.
4. Pass `pre-commit run --all-files`.
5. Run the verification on the candidate commit: the affected tests on the GPU,
   `scripts/validate_manifest.py`, the benchmark and the stage 3 analyses.
6. Repeat stage 5 if the cleanup changed kernel logic, dispatch, tests or a performance
   number.

Exit: the verification passes, and the result of the bar is unchanged.

### 7. PR

1. Rebase onto the newest `{{UPSTREAM}}` main.
2. Title the commit `[Perf][foundry][<Family>] <imperative description>`, with no
   authorship trailer.
3. Run the stage 6 verification.
4. Measure main and the candidate again, and set the result.
5. Set `tileops_base` to the new base and `candidate_commit` to HEAD in `provenance.json`.
6. Fill in `pr-template.md` and `pr-comments.md` where they are:

| File | Becomes | Holds |
| --- | --- | --- |
| `pr-template.md` | the title (line 1, same as the commit) and the body | Summary, Test plan, Test node delta (`scripts/test_node_delta.py` output and the path each new case guards), Benchmark |
| `pr-comments.md` | one comment per `## ` section | TileFoundry Description with `work/final_hir.py` verbatim; Performance with one row per measured workload of `{{OP}}`, and the other ops that share a changed kernel (delete that table when there are none); Result And Limitations opening with the result; TileFoundry Findings |

7. Replace every `<...>`.
8. Keep every `## ` heading and every column.
9. Leave out local paths, raw logs, and the order things were tried.
10. Run `{{TOPA}} pr`.
11. Re-read the final HIR, the evidence and the diff.
12. Run `{{TOPA}} pr --reviewed`. Never use `gh pr create`, `gh pr edit` or merge.
13. Report the PR link.
14. Fix each CI failure and answer each review comment in this session, then repeat steps
    3-12.
15. After a base move, repeat steps 1-12.

Exit: the PR is open and its link is reported.

## Ending without a PR

1. Write `## Stop records` in `report.md`: the stop records of stage 4 that apply and the
   rows still behind with their last measured numbers. Mark each record that does not
   apply, with the reason.
2. When a disputed finding or a missing comparator stopped the round, write the decision
   a person must make and the evidence on each side.
3. Close any PR this round opened, with a comment saying why.
4. Report the stop and the decision it waits for.

## TileFoundry findings

- Record a TileFoundry bug that blocks you as a finding.
- Continue with the part of the work that still runs.
- Keep its reproducer as it fails, with the command and raw output, in
  `work/blocked/<finding-id>/`.
- Before the PR or the stop report, open one issue on `tile-ai/TileFoundry` for all
  findings, in the form `{{TILEFOUNDRY_SOURCE}}/CONTRIBUTING.md` sets.
- Give each finding a section with its command, minimal HIR or TIR and raw output.
- Add a later finding to the same issue. Open no issue without a finding.

## Records

`{{TOPA}} gate` checks these. Paths are relative to the round directory; each `command` is
the exact command that wrote its non-empty `report`.

```json
{
  "tileops_base": "<40-hex>", "tilefoundry_base": "<40-hex>", "candidate_commit": "<40-hex HEAD>",
  "result": "bar met | below bar",
  "final_hir": "work/final_hir.py", "runtime_twin": "work/runtime_twin.py",
  "production_kernel": "src/tileops/<path>.py:<Symbol>",
  "reference_check": {"command": "tilefoundry check ... --expected ... --json <r>", "report": "<r>"},
  "floor": [{"workload": "<name>", "command": "tilefoundry analyze ... --roofline --json", "report": "<r>"}],
  "placements": [{"placement": "<tiling>", "chosen": true, "command": "tilefoundry analyze ... --performance --json", "report": "<r>"}],
  "schedule": {"command": "tilefoundry schedule finalize ...", "report": "<tir>"},
  "twin_check": {"command": "tilefoundry check work/runtime_twin.py:<Twin> ... --json <r>", "report": "<r>"},
  "iterations": [{"change": "<what>", "basis": "<fact>", "predicted_us": 0.0, "measured_us": 0.0}],
  "tests": {"command": "<pytest>", "report": "<r>"}, "benchmark": {"command": "<bench>", "report": "<r>"},
  "reviews": ["evidence/review-1.md"]
}
```

- Give `floor` one entry per workload.
- Give `placements` at least two entries, exactly one chosen.
- Write `findings.json` as `{"findings": [], "issue": null}`, or with the issue URL and per
  finding `id`, `classification`, `command`, `expected`, `actual`, `workaround_cost`,
  `public_surface`, `affected_workloads` and `reproducer`.

## Report

Write `report.md`. Under `## TileLang knowledge`, record each TileLang or ptxas fact the
next round would otherwise rediscover: what you did, the result, the build. Do not edit
`{{KNOWLEDGE}}`.
