# Every PR

Apply to every TileOPs PR. Rules TileOPs documents or checks in CI are cited, not restated.

## Where the rules live

| Rule | Source |
| --- | --- |
| the design doc each area is reviewed against | `CONTRIBUTING.md` § Design first |
| title, branch and issue names | `CONTRIBUTING.md` § Naming, CI job `validate-pr-title` |
| PR body sections | `.github/PULL_REQUEST_TEMPLATE.md` |
| code rules a reader applies | `docs/code-style.md` |
| public API compatibility | `docs/stability.md` § Compatibility, `scripts/ci/check_api_compat.py` in CI job `compile-contract-gate` |
| lint, format, secrets, manifest validation | `.pre-commit-config.yaml` and the `Preflight Checks` workflow |

- Do not comment on what a CI check of the PR reports.
- Cite the source row when a finding breaks a rule from this table.

## Correctness

| Criterion | Pass | Fail |
| --- | --- | --- |
| Oracle | the expected value comes from the workload's `ref_program`, PyTorch, NumPy or a closed form | a literal computed outside the test is the expected value |
| Coverage set | the dtypes, shapes and modes the tests reach stay the same or grow | a case is removed while the code path it reaches stays |
| New paths | each code path the diff adds is reached by a test whose input makes its output differ from every other path | an added path has no such test |

- Name the failing criterion in the comment.
- A path no input can tell apart from another passes `New paths` without a test.

## Code

| Criterion | Pass | Fail |
| --- | --- | --- |
| Reachable | each function, class, branch and `__all__` name the diff adds outside `tests/` and `benchmarks/tests/` runs on some call of a public op, a benchmark or a script | it runs only when a test calls it directly, or never |
| One copy | each run of five or more statements the diff adds has no copy elsewhere in the repository that differs only in names and literals | the diff adds such a copy instead of a shared helper or `@T.macro` |
| Positional order | a parameter the diff adds to an existing function goes after its existing positional parameters, or is keyword-only | an added parameter shifts an existing positional parameter |
| Reason in comments | a comment beside a chosen value (a tile size, a threshold, a stage count) states why the value holds | the comment gives only a measurement, a date or the history of the choice |

## PR body

- Check that the body has each section `.github/PULL_REQUEST_TEMPLATE.md` requires for what the diff touches.
- Check each claim in `## Summary` against the diff.
- Check that `## Summary` names each change to what an existing call returns or raises, and to the call or timing of an existing benchmark row.
- Apply the `FIXME(staged-rollout)` rule of `docs/code-style.md` to each `xfail`, `skip` or loosened assertion the diff adds.
