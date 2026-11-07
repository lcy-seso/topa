# [Perf][foundry][<Family>] <Imperative description of the kernel change>

## Summary

- <the key change of the production kernel>
- <the root cause of the gap it closes>

## Test plan

- [x] `pre-commit run --all-files`
- [x] `pytest` on the affected files, on a real GPU

## Test node delta

```text
<the output of python scripts/test_node_delta.py --base <remote>/main>
```

- <one line per new case: the code path, dtype, feature or regression it guards>

## Benchmark

**Environment**: <GPU>, CUDA <version>, PyTorch <version>, TileLang <version>

### <exact public TileOPs Op name>

| Shape | dtype | TileOPs (ms) | <fastest comparator> (ms) | Speedup | <TFLOPS or BW (TB/s)> |
| --- | --- | ---: | ---: | ---: | ---: |
| <shape as a tuple> | <dtype> | <candidate median> | <comparator median> | <comparator / candidate> | <throughput> |
