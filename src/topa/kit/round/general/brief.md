## Stages

### 1. Requirement

1. Read the issue, the code, tests and docs it names, and the `docs/design/` pages on that
   code.
2. Reproduce the bug, or locate the code the change touches.
3. Write under `## Plan` in `report.md` what the change is and which test shows it.

Exit: the plan states when the issue is done. If the issue is unclear or needs a decision
a person must make, follow [Ending without a PR](#ending-without-a-pr).

### 2. Failing test

1. When the change is testable, add a test to the repository's tests that fails on the
   base for the reason the issue states.
2. Record the failing run in `evidence/`.
3. When the change is not testable (docs, comments), write why under `## Plan`.

Exit: the new test fails on the base, or `report.md` says why there is none.

### 3. Implementation

1. Make the change in the worktree.
2. Run the [Verification](#verification).

Exit: the new test and the verification pass.

### 4-6. Review, cleanup and PR

Follow [Review](#review), [Cleanup](#cleanup) and [PR](#pr).

## Verification

1. Run the tests of every file the diff touches and the new tests, on the GPU when they
   need one, and record them in `tests` of `provenance.json`.
2. Pass `pre-commit run --all-files`.

## PR files

Title: `[<Type>] <imperative description>` or `[<Type>][<Scope>] <imperative description>`,
with `<Type>` from TileOPs `scripts/ci/types.sh` for the issue's type.

| File | Becomes | Holds |
| --- | --- | --- |
| `pr-template.md` | the title (line 1, same as the commit) and the body | Summary, Test plan, Test node delta (`scripts/test_node_delta.py` output and the path each new case guards), Regression |

- Delete Test node delta when the PR touches no test, and Regression when it fixes no bug.
- Keep the other `## ` headings, in order.
