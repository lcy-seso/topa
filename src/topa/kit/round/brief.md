# {{SLUG}}: bring {{OP}} to its fastest comparator

Make `{{OP}}` of [tile-ai/TileOPs](https://github.com/tile-ai/TileOPs) at least as fast as
its fastest comparator, using [TileFoundry](https://github.com/tile-ai/TileFoundry), and
open a PR from the fork. The code, the PR and any TileFoundry issue are public.

## Requirement

The rows of `{{OP}}` behind in the [Perf Tracker of {{NIGHTLY_DATE}}]({{WIKI_URL}}) (nightly
run [{{NIGHTLY_RUN}}]({{NIGHTLY_RUN_URL}}), commit `{{NIGHTLY_COMMIT}}`, benchmark
`{{BENCHMARK}}`; CUPTI `device_busy_ms` in microseconds; ratio = comparator / TileOPs):

{{ROWS}}

- Take these rows and the op's manifest entry, Op, workloads, reference, tests and
  benchmark as the whole requirement.
- Hold every row of the op to the bar, not only the rows above.
- Write production code only in the worktree; keep everything else in the current
  directory, the round directory.

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
| `bar met` | Every row of the op beats its fastest comparable comparator in the median and in every repeat, or ties it within one timer step or at the DRAM floor; no row of any op is slower than main. | Open the PR. |
| `below bar` | The bar is not met, the candidate beats main on a row behind, and no row of any op is slower than main. | Open the PR; list the unmet rows in Result And Limitations. |
| none | Neither, or a person must decide. | Follow [Ending without a PR](#ending-without-a-pr). |

"Any op" includes every op that shares a kernel the round changes.

## Rules

- Keep main's cache hints and launch policy exactly (`evict_first`, `evict_last`, cache
  modifiers, L2 persistence, PDL).
- Do not defer writes, add GPU sleeps, or take a win only the L2 flush state gives.
- Do not branch on a shape; derive each dispatch rule from hardware and call facts, sweep it
  over the workloads, and cover it with a test.
- Do not change the benchmark, its timing, the comparators, tolerances, workloads, the
  manifest or the public Op.
- Add no op and no compatibility shim; migrate every caller in the same PR.
- Fix shared code with one rule for every op, never a list of ops or shapes.
- Fix a bug in main found on the way in this PR, with a test.
- Prove each new test by mutation in a snapshot no timing run compiles from. Why: TileLang
  re-reads kernel source at compile time.
- Follow `docs/design/` and `docs/code-style.md` of TileOPs.
- Never change the TileFoundry source or open a PR on `tile-ai/TileFoundry`.

## Where commands run

- Lines that run only `git`, `gh`, `codex`, `topa`, file commands or text tools run on the
  host; every other line runs in the round container, at the same paths.
- Do not write `ssh` or `docker` commands.

## Stages

Read every page of `tilefoundry tutorial` before stage 1, and `{{KNOWLEDGE}}` before
stage 3. Ask TileFoundry usage from `tilefoundry tutorial`, `spec` and `--help`. Cite
`tilefoundry --version` and the target name with every analysis number.

### 1. Requirement and comparators

1. Locate the gap: kernel body, tuning pick, launch count or host idle time, with CUPTI
   per-kernel times and `ncu`.
2. Run each comparator through the repository benchmark with its recommended settings.
3. Classify each (workload, comparator) pair:

| Class | Timed | Counts toward the fastest comparator |
| --- | --- | --- |
| comparable (passes the shared case reference) | yes | yes |
| not semantically comparable; reason recorded | yes | no |
| cannot express the case; reason recorded | no | no |

4. List the last two classes in Result And Limitations.

Exit: every pair is classified, and the comparator each row names is comparable. Otherwise
follow [Ending without a PR](#ending-without-a-pr).

### 2. HIR reference

1. Write the op's math in HIR, one module per workload or with `--dim`.
2. Save the repository reference's outputs on the same inputs as `.pt`.
3. Run `tilefoundry check <hir>.py:<Module> --inputs files:<in> --expected <out> --json <report>`
   with a two-sided `--fn` and `nan_inf` per output; add `--weights ckpt:<dir>` for
   `ConstTensor` weights.
4. Derive each tolerance from the dtype and the serial roundings, and record it. Never
   loosen one for a single workload.

Exit: the check passes on every output of every workload.

### 3. Floor and placement

1. Run `tilefoundry analyze <hir>.py:<Module> <report> --compute-cost --memory --roofline --json`
   per workload; `ideal-ns` and `bound-by` are its floor.
2. Check the flops and traffic by hand (each input read once, each output written once);
   fix the HIR if they disagree.
3. List placements, including the incumbent's and the fastest comparator's (from `ncu` and
   its generated source). Run `analyze ... --memory --performance --json` on each and choose
   one by waves, storage use and predicted time.

Exit: a floor table and a placement table exist.

### 4. Implementation rounds

Run each round in this order and add it to `iterations` in `provenance.json`:

1. Change the HIR's placement or schedule and run `analyze`. Continue only with a better
   prediction or a written basis.
2. Run `tilefoundry schedule candidates`, `schedule facts --target <target> <instruction>`,
   write the choices into `tf.schedule`, and run `schedule finalize` to get TIR.
3. Write the TileLang kernel from that TIR.
4. Re-run the stage 2 check if the math, outputs or shapes changed. Run
   `tilefoundry check <twin>.py:<Twin> --json <report>` on the runtime twin, which calls the
   production kernel, and the TileOPs tests.
5. Measure, and record measured / floor, measured / predicted and comparator / measured.

Measure this way:

- Make detached snapshots under `work/` of the base and of each candidate commit with
  `git -C {{TILEOPS_WORKTREE}} worktree add --detach`, and time each with its `src` first on
  `PYTHONPATH`.
- Alternate main, candidate and comparators on the round's GPU, with the L2 flush, and take
  the median of at least three runs of `device_busy_ms`.
- Skip re-timing when the generated CUDA is identical.

Stop optimizing when all three hold:

| Record | Holds when |
| --- | --- |
| (1) Gap attribution | Each workload's measured / floor is listed, and each gap is tied to a bottleneck with `ncu` or `analyze` data. |
| (2) Directions exhausted | Each feasible change against each bottleneck was measured or shown infeasible. |
| (3) TileFoundry consulted | Alternative placements were analyzed and `tutorial optimize` and `spec` were read, without a new direction. |

Exit: the bar is met, or all three records hold.

### 5. Review

1. Run Codex on the diff (`git -C {{TILEOPS_WORKTREE}} diff {{TILEOPS_BASE}}`), the rows and
   the paths of TileOPs `docs/design/` and `docs/code-style.md`, without your conclusions:

   ```bash
   codex exec -C {{TILEOPS_WORKTREE}} --sandbox read-only "<prompt>" < /dev/null > evidence/review-<n>.md 2>&1
   ```

2. Ask for correctness (edge shapes, dtypes, tails), the real call path, branch coverage by
   tests, a trustworthy benchmark, and hotfixes: a loosened tolerance, check or skipped
   case, logic only tests reach, or a shape branch without a stated rule and a test.
3. Fix each finding you agree with; answer the rest with a test, a measurement or a rule.
4. Rerun until no finding is blocking or major. Rerun a review that ends in an error.

Exit: no blocking or major finding is left. A disagreement that survives two reviews ends
the round: follow [Ending without a PR](#ending-without-a-pr).

### 6. Cleanup

1. Inline single-caller helpers, merge repeated logic, and delete process comments and
   tests of intermediate steps.
2. Pass `pre-commit run --all-files`.
3. Rerun the affected tests on the GPU, `scripts/validate_manifest.py`, the benchmark and
   the stage 3 analyses on the final commit.
4. Repeat stage 5 if the cleanup changed kernel logic, dispatch, tests or a performance
   number.

Exit: every rerun passes and matches the numbers before the cleanup.

### 7. PR

1. Rebase onto the newest `{{UPSTREAM}}` main, verify again, and check
   `git merge-tree --write-tree <upstream remote>/main HEAD`.
2. Title the commit and the PR `[Perf][foundry][<Family>] <imperative description>`, with
   no authorship trailer.
3. Fill in both files in place; replace every `<...>` and keep every heading and column:

| File | Becomes | Holds |
| --- | --- | --- |
| `pr-template.md` | the title (line 1) and the body | Summary, Test plan, Test node delta (`scripts/test_node_delta.py` output and the path each new case guards), Benchmark |
| `pr-comments.md` | one comment per `## ` section | TileFoundry Description with `work/final_hir.py` verbatim, Performance with every workload and a `main (us)` column, Result And Limitations opening with the result, TileFoundry Findings |

4. Leave out derivations, trial and error, reproducer commands, internal file names, logs
   and local paths.
5. Run `{{TOPA}} pr`, re-read the final HIR, the evidence and the diff, then run
   `{{TOPA}} pr --reviewed`. Never use `gh pr create`, `gh pr edit` or merge.
6. Report the PR link and stay in this session for CI and review. After a base move,
   rebase, verify, push with `--force-with-lease` and run `{{TOPA}} pr --reviewed` again.

Exit: the PR is open and its link is reported.

## Ending without a PR

1. Write `## Stop records` in `report.md`: the three records of stage 4, the rows still
   behind with final numbers, and both sides' evidence for a decision.
2. Close any PR this round opened, with a comment saying why.
3. Report the stop and stay in this session.

## TileFoundry findings

- Record a TileFoundry bug that blocks you as a finding, and continue with what still runs.
- Keep its reproducer as it fails, with the command and raw output, in
  `work/blocked/<finding-id>/`.
- Before the PR, open one issue on `tile-ai/TileFoundry` for all findings, in the form
  `{{TILEFOUNDRY_SOURCE}}/CONTRIBUTING.md` sets, one section per finding with its command,
  minimal HIR or TIR and raw output. Open none without a finding.

## Records

`{{TOPA}} gate` checks these. Paths are relative to the round directory; each `command` is
the exact command that wrote its non-empty `report`.

```json
{
  "tileops_base": "<40-hex>", "tilefoundry_base": "<40-hex>", "result": "bar met | below bar",
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

- Give `floor` one entry per workload and `placements` at least two, one chosen.
- Write `findings.json` as `{"findings": [], "issue": null}`, or with the issue URL and per
  finding `id`, `classification`, `command`, `expected`, `actual`, `workaround_cost`,
  `public_surface`, `affected_workloads` and `reproducer`.
- Expect the gate to reject a Performance table that lacks a row behind or a ratio column,
  shows a candidate slower than main, or claims `bar met` with a ratio below 0.99.

## Report

Write `report.md`. Under `## TileLang knowledge`, record each TileLang or ptxas fact the
next round would otherwise rediscover: what you did, the result, the build. Do not edit
`{{KNOWLEDGE}}`.
