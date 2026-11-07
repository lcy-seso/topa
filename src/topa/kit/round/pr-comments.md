## TileFoundry Description

- **Floor.** `analyze --compute-cost --memory --roofline` of the whole op: <workload> <floor> us (<bound-by>-bound); <one entry per workload>
- **Placement.** `analyze --memory --performance` of <placement>: <what the waves, storage use and predicted time show>

| Workload | Placement | Waves | Predicted (us) | Floor (us) | Shipped |
| --- | --- | ---: | ---: | ---: | --- |
| <workload> | <placement> | <waves> | <predicted> | <floor> | <yes or no> |

Floor and predicted times are the reports' `ideal-ns` and `predicted-ns`, in microseconds.
Analysis: tilefoundry `<version>`, `<target>`. `run.sh` below reproduces every number.

<details><summary><code>final_hir.py</code>: final HIR program</summary>

```python
<work/final_hir.py, character for character: the HIR that was analyzed, measured and finalized, with every tf.schedule instruction choice>
```

</details>

<details><summary><code>run.sh</code>: every analysis above</summary>

```bash
<a script that runs every analyze above and prints each number of the tables>
```

</details>

## Performance

| Environment | Value |
| --- | --- |
| image | `<runner image>` |
| digest | `sha256:<image digest>` |
| gpu | `<GPU model>, driver <version>, CUDA <version>` |
| torch / tilelang | `<PyTorch version> / <TileLang version>` |
| timer | `<timer of the TileOPs benchmark>` |
| timer step (us) | <the timer's resolution in microseconds> |

Method: <how main, the candidate and the comparators were alternated on one GPU, and how many runs give each median>. Every comparator counted toward the bar passes the case reference before timing. Times are `device_busy_ms`. Ratio: comparator / candidate.

| Workload | main (us) | candidate (us) | floor (us) | candidate / floor | <comparator> (us) | ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| <workload> | <main median> | <candidate median> | <floor> | <candidate / floor> | <comparator median> | <comparator / candidate> |

Other ops that share a changed kernel:

| Op | Workload | main (us) | candidate (us) |
| --- | --- | ---: | ---: |
| <op> | <workload> | <main median> | <candidate median> |

## Result And Limitations

**<bar met | below bar>**

- <whether every row reaches its fastest comparator; a tie names the timer step or the floor it rests on>
- Rows furthest from the floor:

| Workload | candidate / floor | Located cause | Evidence |
| --- | ---: | --- | --- |
| <workload> | <ratio> | <cause> | <ncu or analyze data> |

- <rows below the bar, comparator pairs that are not comparable, and unsupported shapes>
- <directions measured without gain, and their results>

## TileFoundry Findings

**Structural decisions**

| Decision | Basis | Outcome |
| --- | --- | --- |
| <decision> | <analyze number or hardware fact> | <measured outcome> |

**Prediction against measurement**

| Prediction | Basis | Measured | Cause |
| --- | --- | --- | --- |
| <prediction> | <basis> | <measurement> | <cause> |

**Gaps in TileFoundry seen here**

- <what TileFoundry could not express or price, and what located it instead>

Analysis: tilefoundry `<version>`, `<target>`. Measurement: <GPU, image, timer>.
