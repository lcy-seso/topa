# Review a TileOPs PR

The inputs are in `dir` and the PR head is at `worktree`. `dir` holds `pr.json` (title, body, author, association, base, head, changed
files), `pr.diff`, `threads.json` (unresolved threads topa started) and `comments.json`
(what others wrote).

## Review

1. Read each changed file in full in `worktree`.
2. Review freely first: logic errors, edge cases, API misuse, races, leaks, broken
   invariants, error handling, performance regressions, dead code, missing tests.
3. Apply every listed checklist; skip a row whose `When` clause the diff does not meet.
   Read a TileOPs doc only when a checklist names it and the diff leaves that rule's
   outcome unclear.
4. Do not raise the finding of a thread in `threads.json` again.
5. Read the review knowledge file. A comment needs a fault in the code; a candidate alone
   is not one. Do not flag what its `Do not flag` section names.

## Findings

```json
{"summary": "<text>",
 "comments": [{"path": "<file>", "line": 1, "side": "RIGHT", "body": "<text>"}],
 "threads": [{"id": 123, "status": "fixed", "evidence": "<file>:<line> now <what changed>"}],
 "open_faults": 0}
```

- Set `open_faults` to the number of faults the head still has: new comments, `open` threads
  and faults named only in the summary.

- Give every thread of `threads.json` an entry: `fixed` when the head's code removes the
  fault, `open` otherwise. Name the code that shows it in `evidence`. An author's reply
  alone does not fix a thread.

- Anchor each comment on a line of `pr.diff`: `RIGHT` for an added or context line of the
  new file, `LEFT` for a removed line of the old one.
- Write one comment per finding, naming the function, variable or pattern. Each bullet is
  one sentence of at most 30 words:

  ```markdown
  - **Problem:** <what is wrong>
  - **Case:** <one input or call that shows it>
  - **Fix:** <what to change>
  ```

- Give at most one example or measured number per comment; leave out what the code or a
  docstring already says.
- State **Problem** and **Case** as claims that are true or false, and **Fix** as a direct
  instruction; hedges such as "consider" fail this.
- Write the summary as bullets of one sentence each: what spans files, which `threads.json`
  threads the head fixes, and answers to questions in `comments.json` addressed to the review. Write `No findings.` when there is
  nothing. Do not repeat inline comments there.
- For an external PR (`association` in `pr.json` is not `OWNER`, `MEMBER` or
  `COLLABORATOR`), also follow the External PRs section of `general.md`: base-branch
  faults and missing tests go in the summary, and `Approve.` replaces `No findings.`.
- Write in English.
