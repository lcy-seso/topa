# Ops and kernels

Apply when the diff touches `src/tileops/_ops/`, `src/tileops/_kernels/`, `src/tileops/_utils/`, `src/tileops/csrc/` or `src/tileops/backend/`. The rules are `docs/design/ops-design.md`, `docs/design/op-slot-rules.md` and `docs/code-style.md`; CI job `validate-manifest` checks each implemented op's `__init__` and `forward` against its entry.

## Performance

| Criterion | Pass | Fail |
| --- | --- | --- |
| No slower row | for each manifest row that exists on base and whose dispatch or kernel the diff changes, the PR gives base and head medians on one GPU, and no head median exceeds base by more than the spread of repeated base runs | a row is missing, or one is slower by more than that spread |
| Host cost | for a call that does not use the feature the diff adds, the PR shows host time per call on head within the spread of base | the PR shows no such measurement, or host time grows beyond that spread |
| Row reaches new code | each implementation the diff adds is selected by at least one manifest workload row on an architecture it supports | no row selects it, so the nightly benchmark never times it |

## Kernels

| Criterion | Pass | Fail |
| --- | --- | --- |
| Shared-memory budget | the budget that `refusal` or the config choice compares against counts every `T.alloc_shared` buffer the program allocates, for each architecture in `supported_archs` | a shared buffer the diff adds or resizes is left out of the budget |
| Index width | an offset computed from a product of dimensions the manifest leaves unbounded is 64-bit, or `refusal` bounds the product below 2^31 | the offset is 32-bit and a legal call overflows it |
| Coupled values | values that must agree (a tile size and the threshold, buffer size or launch shape derived from it) are one name, or one is computed from the other | two literals must be changed together to stay correct |
| Device facts | selection and build read device facts from the call spec (`ops-design.md` § Kernel selection) | they read the current device, such as `torch.cuda.current_device()` or `get_device_properties()` without the call's device |
| Cache identity | a key that names a tensor by `data_ptr()` or `id()` belongs to a cache that holds that tensor while the key lives | the cache does not hold the tensor, so a new tensor can repeat the key |
| Dynamic dimensions | a dimension the program takes as dynamic is left out of the entry identity | the identity holds it, so each new value builds or tunes again |

## Ops

| Criterion | Pass | Fail |
| --- | --- | --- |
| Selection in implementations | each implementation's `refusal` decides the calls it serves (`ops-design.md` § Kernel selection) | op code picks an implementation by shape, dtype or architecture |
| Manifest shapes to the kernel | the op passes tensors to the kernel interface in the shapes the manifest declares (`op-slot-rules.md` § Slot S16) | the op reshapes, pads or flattens a tensor for the kernel |
| Docstring holds | each claim the diff adds to a class docstring holds for that class's `forward` on every implementation that serves it | a claim holds only for some implementation, or describes a feature the class lacks |
