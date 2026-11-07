# Benchmarks

Apply when the diff touches `benchmarks/`. The rules are `docs/design/testing.md` § Benchmarks and `docs/design/layer-boundaries.md` § Benchmark; hooks `bench-baseline-lint`, `baseline-import-lint` and `workload-names-lint`, and the `bench` level of CI job `validate-manifest`, check the bench files.

| Criterion | Pass | Fail |
| --- | --- | --- |
| Native baseline work | a baseline's timed callable runs only what the library's serving integration runs per op call | it also times a layout conversion, transpose or metadata build that the integration runs once per batch or per model, outside the op call |
| Rows reach each branch | each branch in a `benchmarks/ops/` file that changes the call or the set of implementations compared runs for at least one manifest workload row of the op | no row reaches such a branch; a branch that only raises on bad input is not one |
