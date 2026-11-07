# Tests

Apply when the diff touches `tests/`, `benchmarks/tests/` or `workloads/`. The rules are `docs/design/testing.md` § Tests and § Test case policy, and `docs/design/layer-boundaries.md` § Test and § Workloads layer.

## Case verdicts

1. Read `## Test node delta` in the PR body. When the worktree's Python imports `torch` and `tilelang`, rerun `python scripts/test_node_delta.py --base <base>` there, `<base>` being `base` in `pr.json`, and use its numbers instead. The script finds changed files under `tests/` only; pass changed `benchmarks/tests/` files as arguments.
2. Give each added or changed test case one verdict:

   | Verdict | When | Comment |
   | --- | --- | --- |
   | `keep` | it reaches a code path, dtype, feature or regression no other case reaches | none |
   | `shrink` | its parameters cross axes whose cells reach the same code paths | name the axis to fold; keep the boundary cells and one interior cell |
   | `delete` | another case already fails on the same fault | name the case it duplicates |

3. Ask the author for the purpose of a case you cannot give a verdict; it blocks like `shrink`.
4. Never ask to remove the last case on an input that changes the output: a tile boundary, an unaligned vector width, a size-1 dimension, or a dispatch branch.
5. Give an acceptance criterion of an issue no weight: a case it asks for gets the same verdict as any other.

Done when every added or changed case has a verdict and every `shrink`, `delete` and unknown case has a comment.

## Case shape

| Criterion | Pass | Fail |
| --- | --- | --- |
| One behavior per function | every parameter cell of a test function runs the same assertions | an `if` on a parameter value adds or skips assertions for some cells (`testing.md` § Growth) |
| Smoke size | each `smoke` case the diff adds uses a dtype the op's smoke cases do not yet cover, or a shape they already use for it | it adds a second smoke shape for a dtype of the op, in any test function (`testing.md` § Test case policy, Dtype) |
| Architecture mark | an architecture mark sits on a case whose path dispatch selects only on that architecture | the marked path is also selected on another architecture the suite runs on (`testing.md` § Tests, Reachability) |
| Special values | each special-value behavior the diff adds or documents (NaN, `inf`, `-inf`, an empty or fully masked row, a sentinel such as `-1`) has a case that passes that value | a documented or handled special value appears in no case |

## Workloads

| Criterion | Pass | Fail |
| --- | --- | --- |
| Measured bound | a bound the diff loosens names the measured error it covers, and applies only to rows or dtypes whose measured error exceeds the old bound | the bound is loosened without a measurement, or also for rows whose measured error fits the old bound |
| Rejecting verification | a `verification()` the diff changes is shown, by a test or in the PR, to reject an output the op must not return | no wrong output is shown to fail the changed verification |
