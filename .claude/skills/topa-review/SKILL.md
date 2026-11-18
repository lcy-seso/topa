---
name: topa-review
description: Review a TileOPs PR once, or on every change until it settles. Use when the user asks to review a TileOPs PR.
---

# topa review

Run `topa` from the topa virtual environment. The PR is a number in the `upstream`
repository of `topa config`. Set `GH_CONFIG_DIR` to post as another `gh` account.

| The user wants | Run |
| --- | --- |
| one review | `topa review <PR>` |
| reviews until the PR settles | `topa round review <PR>` |

Report the link and the open faults. Propose at most three one-sentence, pass/fail
checklist bullets for `src/topa/kit/review/checklists/` that would have caught a finding
earlier. Do not edit the review checklists unasked.
