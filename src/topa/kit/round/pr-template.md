# [Perf][foundry][<Scope>] <Imperative description of the kernel change>

## Summary

- <the key change of the production kernel, and its review boundary>
- <the public Op, fallback, output semantics or compatibility that stay the same>
- <candidate, incumbent, external baseline, and primary workload coverage>

## TileFoundry Description

```python
<work/final_hir.py, character for character: the HIR that was analyzed, measured and finalized, with every tf.schedule instruction choice>
```

## Performance

Operator: `<exact public TileOPs Op name>`

| Environment | Value |
| --- | --- |
| image | `<runner image>` |
| digest | `sha256:<image digest>` |
| gpu | `<GPU model>` |
| driver | `<driver version>` |
| cuda | `<CUDA version>` |
| torch | `<PyTorch version>` |
| tilelang | `<TileLang version/commit>` |
| <external stack> | `<external baseline version/commit>` |
| timer | `<timer of the TileOPs benchmark>` |

Method: <the TileOPs benchmark used in this round.>

Ratio in comparator columns: implementation / candidate. &#x1F7E2; > 1 means the candidate is faster;
&#x1F534; <= 1 means it is not.

| Workload | <dim 1> | <dim 2> | Dtype | TileFoundry candidate (ms) | TileOPs incumbent (ms)<br>/ candidate | <External baseline> (ms)<br>/ candidate |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| <primary workload 1> | <value> | <value> | <dtype> | <candidate median> | **<incumbent median><br><marker>&nbsp;<incumbent/candidate ratio>x** | <external median><br><marker>&nbsp;<external/candidate ratio>x |
| <one row per primary workload> | <value> | <value> | <dtype> | <candidate median> | **<incumbent median><br><marker>&nbsp;<incumbent/candidate ratio>x** | <external median><br><marker>&nbsp;<external/candidate ratio>x |
| geometric mean |  |  |  | <candidate geomean> | **<incumbent geomean><br><marker>&nbsp;<incumbent/candidate ratio>x** | <external geomean><br><marker>&nbsp;<external/candidate ratio>x |

## Result And Limitations

**<measured SOTA | improvement without SOTA>**

- <the classification, explained with the row results and the geometric mean>
- <the workloads still slower than the incumbent or the external baseline>
- <specialization and fallback boundaries, and remaining risk>
- <TileFoundry, lowering, runtime or performance limits confirmed in this round>
