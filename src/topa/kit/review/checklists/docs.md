# Docs

Apply when the diff touches `docs/` or a Markdown file.

| Criterion | Pass | Fail |
| --- | --- | --- |
| Consistent | each statement agrees with the other docs, the manifest and the code | a statement contradicts one of them; cite both sides as `path:line` |
| Met | each target the diff states is met by the code, or the PR changes the code or links a follow-up issue | the code does not meet a stated target and the PR does neither |
| Stated once | each rule the diff adds has no earlier statement in the docs | the rule is already stated elsewhere; cite the first |
| Not reintroduced | each passage the diff adds was not removed by an earlier commit | `git log -S` finds the commit that removed it; cite that commit |
| Top-level decisions only | in `docs/design/`, each added passage states a top-level design decision: a contract, a convention or a module boundary; the names, paths and numbers in it identify what the decision requires | it describes how this PR implements a decision (implementation choices, an inventory of files or cases, measurements) or narrates history; cite the passage and name a code change that would make it stale while the decision still holds |
| Design weight | in `docs/design/`, each added passage changes what a rule allows | it is an example, a rationale or a narration that changes no rule |
