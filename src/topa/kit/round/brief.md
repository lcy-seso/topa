# {{SLUG}}: {{ISSUE_TITLE}}

This round contributes one GPU kernel to the open-source operator library
[tile-ai/TileOPs](https://github.com/tile-ai/TileOPs). You implement or optimize one
operator as a public issue describes it, verify its numbers against the reference in the
repository, compare its performance with public implementations, and open a PR that
follows the upstream rules. The code, the evidence and the PR all go into public
repositories. The tool is [tile-ai/TileFoundry](https://github.com/tile-ai/TileFoundry), an
open-source compiler front end that analyzes the cost of tensor programs, selects hardware
instructions and lowers to TIR.

**Use TileFoundry for the whole round. Write, analyze and measure several different
Sharded/Placed HIRs. Derive the structural change of the production kernel from the HIR
you keep, and put that HIR in the PR unchanged. Do not open a PR for a change that only
tunes config, launch, tile size or stages. When a TileFoundry limit blocks you, record a
finding and continue with the part of the workflow that still runs. Do not write an
implementation that goes around TileFoundry, and do not stop. Keep a blocking example as a
minimal reproducer exactly as it fails. Do not reduce it until it passes.**

The requirement of this round is [{{UPSTREAM}}#{{ISSUE}}]({{ISSUE_URL}}), and it is the only
source. Before you start, read its body and all comments with
`gh issue view {{ISSUE}} --repo {{UPSTREAM}} --comments`. The goal, the acceptance line, the
comparison implementations and the code locations are what the issue says.

| Environment | Value |
| --- | --- |
| issue | [#{{ISSUE}}]({{ISSUE_URL}}) |
| branch | `{{BRANCH}}` |
| TileOPs base | `{{TILEOPS_BASE}}` |
| TileFoundry base | `{{TILEFOUNDRY_BASE}}` |

## Workflow

1. Read every page that `tilefoundry tutorial` lists. Get the real contract from the
   manifest, the Op, the workloads, the reference, the tests and the benchmark. Do not read
   the incumbent kernel body until your first production runtime twin is correct. Before
   you write the production kernel, read `{{KNOWLEDGE}}`: it lists TileLang and ptxas
   problems that earlier rounds hit on named builds, with workarounds.
2. The runtime twin must call the production TileLang kernel you will submit, and it must
   pass `tilefoundry check`. Torch, an evaluator or a detached implementation does not
   count.
3. Measure at least 10 different Sharded/Placed HIRs. For each, keep the raw
   `tilefoundry analyze` JSON, the placement, the hypothesis, the latency and the
   kept/rejected verdict. Select the final HIR from that evidence.
4. When the final HIR is fixed, fix its instruction choices with schedule:
   - `tilefoundry schedule candidates` lists the instructions available at each
     unscheduled point.
   - `tilefoundry schedule facts --target` gives the constraints of the target on the
     selected instructions.
   - Write the choices in the HIR with `tf.schedule`.
   - `tilefoundry schedule finalize` lowers it to TIR.
   - `tilefoundry spec schedule` defines the authored form.
5. Write the production kernel from that TIR. Do not invent instructions, buffer depths or
   operand layouts. Then run correctness, the benchmark of every primary workload, the
   strongest external baseline that runs, and a profile again.

The current directory is the round directory. Write production code only in
`{{TILEOPS_WORKTREE}}`.

- Run commands directly. TileOPs is installed in editable mode, so do not set
  `PYTHONPATH`.
- Do not change the public Op, the manifest, the workloads, the reference, the benchmark
  or the evaluation path. For a new operator you may add its own entry under
  `src/tileops/manifest/spec/`, but do not change existing entries.
- C++/CUDA that TileLang cannot generate, or that you write or rewrite by hand, goes in
  `src/tileops/csrc/`. The kernel includes it with `tileops._csrc.csrc_include(...)`, like
  the existing `fp8_gqa_helper.h`.
- A `.py` file must not contain C++/CUDA source strings (`import_source(`, `prelude =`,
  `asm(`, `__device__` / `__global__`). The TileOPs pre-commit hook
  `native-source-strings-in-csrc` rejects them, and files in csrc must pass clang-format.

## Where commands run

You run on the host, and you read and write files locally. Each shell command goes to the
round container automatically. `git`, `gh`, `topa` and plain file commands stay on the
host. Everything else (python, pytest, nvcc, tilefoundry, nvidia-smi) runs in the
container. The three directories have the same paths in the container, so use paths as
they are. Do not write `ssh` or `docker` commands yourself.

## TileFoundry source

`{{TILEFOUNDRY_SOURCE}}` is a detached checkout of TileFoundry at base
`{{TILEFOUNDRY_BASE}}`. The `tilefoundry` in the container is its editable install.
`tilefoundry tutorial`, `spec` and `tests/fixtures/schedule/` read this source.

This source is read-only. Read it and run it. Do not change it, and do not open a PR on
`tile-ai/TileFoundry`. Record a TileFoundry bug that blocks you as a finding, and go
around it as the rule at the top says. Keep its minimal reproducer unchanged in
`work/blocked/<finding-id>/` and record it in `findings.json`.

**Report all findings of the round in one issue** on `tile-ai/TileFoundry`.

- Open it once, after the last finding and before the TileOPs PR. Write its URL in the
  `issue` field of `findings.json`.
- Give each finding one section. Paste the command, the minimal HIR or TIR and the raw
  output unchanged. The round directory is not public, so the issue alone must reproduce
  each finding.
- Add a later finding to the body of the same issue. Do not open a second one. With no
  finding, open no issue.

**Before you open the issue, read `{{TILEFOUNDRY_SOURCE}}/CONTRIBUTING.md`.** It sets the
title format and the body sections of the issue. It is not in your working directory, so
it does not come into your context by itself.

If the round ends with a `foundry.patch`, the round changed TileFoundry source and broke
the rule above. The deliverable is the TileOPs operator. TileFoundry is the tool that
writes it.

## Round deliverables

- `work/final_hir.py` (the version with `tf.schedule`), `work/runtime_twin.py`, and at least
  one candidate HIR with a different placement.
- The TIR from `schedule finalize`, and the raw candidates and facts reports.
- `provenance.json`: the bases, the classification, the final/runtime/kernel paths, check,
  iterations, decisions, correctness, benchmark and profile.
- For each iteration: the analyze JSON, a positive `measured_ms`, the placement, the
  hypothesis and the verdict.
- `findings.json`. With no finding: `{"findings": [], "issue": null}`. With findings,
  `issue` is the URL of the one TileFoundry issue. The `reproducer` of each finding points
  to the minimal HIR or TIR file in `work/blocked/<finding-id>/` that runs by itself. The
  same directory holds the exact command and its raw output.
- The raw correctness, benchmark, profile and baseline evidence, and `report.md`,
  `pr-title.txt` and `pr-body.md`.

When the round confirms a TileLang or ptxas fact that the next round would otherwise have
to find again (a trap, a convention read from generated code, a form that does not exist),
write it in the `## TileLang knowledge` section of `report.md`: what you did, the result,
and the build. Do not change `{{KNOWLEDGE}}`. A person adds entries to it.

Experiment scripts and evidence stay in the round directory. Only the production diff goes
in the TileOPs worktree.

## PR

Open a performance PR only when all of these are true: the candidate passes correctness,
every primary workload is compared under the same contract, the candidate is better than
the incumbent, and the production kernel has a structural change. Otherwise record
`no improvement` in `report.md`, and do not open or keep a PR.

A round that adds a new operator has no incumbent. Compare against the reference for
correctness and against the strongest external baseline that runs for performance. Remove
the incumbent column from the Performance table. Open the PR when correctness passes and
the candidate is not slower than the baseline. If it is slower, record `no improvement`
and open no PR.

Use this form for the commit and PR title:

```text
[Perf][foundry][<Scope>] <imperative description of the kernel change>
```

After the commit, run `{{TOPA}} pr`.

- The first call runs the artifact gate and stops for a semantic self-check. Read the
  actual final HIR, the analyze and measurement evidence and the production diff again,
  and only then run the second command.
- To check the artifacts only, run `{{TOPA}} gate`.
- Do not call `gh pr create` or `gh pr edit` to go around it.
- Use the global Git identity and add no other authorship. `topa pr` pushes to the fork
  and opens the PR. Do not merge. Continue to handle CI and review.

```bash
{{TOPA}} pr
{{TOPA}} pr --reviewed
```

When the base moves, rebase, verify again and push with `--force-with-lease`. With
findings, put the link to the TileFoundry issue in `report.md`.

When the TileOPs PR is open, stop and report its link (and the issue link, if there are
findings). Do not end the round yourself. The container, the worktree and this session
stay, and you follow CI and review in this session.

### Full PR template

The public PR body has exactly these four sections:

````markdown
## Summary

- <the key change of the production kernel, and its review boundary>
- <the public Op, fallback, output semantics or compatibility that stay the same>
- <candidate, incumbent, external baseline, and primary workload coverage>

## TileFoundry Description

```python
@module(
    entry="<entry>",
    target=<target>,
    <other module arguments from final_hir.py>,
)
class <ModuleName>:
    @func
    def <entry>(<all parameters and types>) -> <full return type>:
        <the full HIR body of final_hir.py exactly as analyzed, measured and finalized,
         with every tf.schedule instruction choice>
```

## Performance

Operator: `<exact public TileOPs Op name>`

| Environment | Value |
| --- | --- |
| image | `<runner image>` |
| digest | `sha256:<image digest>` |
| gpu | `<GPU model>` |
| driver | `<driver version>` |
| cuda | `<CUDA version>` |
| torch | `<PyTorch version>` |
| tilelang | `<TileLang version/commit>` |
| <external stack> | `<external baseline version/commit>` |
| timer | `<timer of the TileOPs benchmark>` |

Method: <the TileOPs benchmark used in this round.>

Ratio in comparator columns: implementation / candidate. &#x1F7E2; > 1 means the candidate is faster;
&#x1F534; <= 1 means it is not.

| Workload | <dim 1> | <dim 2> | Dtype | TileFoundry candidate (ms) | TileOPs incumbent (ms)<br>/ candidate (omit for a new operator) | <External baseline> (ms)<br>/ candidate |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| <primary workload 1> | <value> | <value> | <dtype> | <candidate median> | **<incumbent median><br><marker>&nbsp;<incumbent/candidate ratio>x** | <external median><br><marker>&nbsp;<external/candidate ratio>x |
| <one row per primary workload> | ... | ... | ... | ... | ... | ... |
| geometric mean |  |  |  | <candidate geomean> | **<incumbent geomean><br><marker>&nbsp;<incumbent/candidate ratio>x** | <external geomean><br><marker>&nbsp;<external/candidate ratio>x |

## Result And Limitations

**<measured SOTA | improvement without SOTA>**

- <the classification, explained with the row results and the geometric mean>
- <the workloads still slower than the incumbent or the external baseline>
- <specialization and fallback boundaries, and remaining risk>
- <TileFoundry, lowering, runtime or performance limits confirmed in this round>
````

The public title and body do not contain correctness or reproducer commands, internal file
names or logs, or local absolute paths. They do not claim SOTA, generality or provenance
that measurements do not support. That evidence stays in the round directory.
