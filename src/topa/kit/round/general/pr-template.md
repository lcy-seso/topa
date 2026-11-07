# [<Type>] <Imperative description of the change>

## Summary

- <the change>
- <the cause it addresses>

## Test plan

- [x] `pre-commit run --all-files`
- [x] `pytest` on the affected files

## Test node delta

```text
<the output of python scripts/test_node_delta.py --base <remote>/main>
```

- <one line per new case: the code path, dtype, feature or regression it guards>

## Regression

- <the test that would have caught the bug>
