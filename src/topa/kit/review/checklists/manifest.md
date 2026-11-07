# Manifest

Apply when the diff touches `src/tileops/manifest/`. The rules are `docs/design/manifest.md`; CI job `validate-manifest` checks each entry's structure, its workload rows and, for an `implemented` entry, its class's `__init__` and `forward`.

| Criterion | Pass | Fail |
| --- | --- | --- |
| Reference-derived | each changed contract field (signature, dtypes, shape rules, roofline) matches the entry's `ref_api` or the reference its comment cites (`manifest.md` § Layer Boundaries) | a field changes to match TileOPs code, or no reference supports it |
| Reference covers the entry | when the entry has `ref_api`, it accepts every param and every dtype the entry declares, or a comment on the entry names each one it does not | the entry declares a param or dtype its `ref_api` rejects or lacks, without such a comment |
| Row coverage | the rows of an added or changed entry cover its dtype domain and at least three shapes, one not a power of two where the op supports it (`manifest.md` § Workloads) | a dtype or the shape count is missing |
| Row labels | a row whose call changes (a shape or param value) takes a new label, since the case id keys nightly history (`manifest.md` § Rows) | the call changes under the old label; a key rename that leaves the call the same is not a change |
| Promotion | on a change to `status: implemented`, no `skip`, `xfail` or loosened assertion in `tests/` or `benchmarks/` hides a non-conformance with the entry, and no `FIXME(staged-rollout)` naming the op remains | one remains; a device or capability exclusion that `testing.md` § Tests allows is not one |
| Demotion | a change to `status: spec-only` names the non-conformance, as `manifest.md` § Layer Boundaries requires | the PR gives another reason or none |
