# Perf Tracker 2026-11-06

Nightly run [42257687830](https://github.com/tile-ai/TileOPs/actions/runs/42257687830), commit [`6da068de6`](https://github.com/tile-ai/TileOPs/commit/6da068de6055db5e1f31f43fba83860d257f0d98), NVIDIA H200, CUDA 13.2, driver 580.178.04, torch 2.13.0+cu132, TileLang 0.1.12, image `ghcr.io/tile-ai/tileops-ci-runner:local-runner-2.338.2`. Times are CUPTI `device_busy_ms`.

A row is behind when its fastest comparator's time over TileOPs' time is below 0.99. A row whose fastest comparator takes under 10 us is behind only if it was also behind the night before. An op is labelled by its worst row: P0 < 0.50, P1 < 0.80, P2 < 0.90, P3 < 0.95, P4 < 0.99.

## Summary

| Measure | Value |
| --- | --- |
| Ops behind | 19 of 206 |
| Rows behind | 34 of 2330 |
| By label | P0 0, P1 0, P2 2, P3 1, P4 16 |
| Failed rows | 0 |

Since nightly run [42070378706](https://github.com/tile-ai/TileOPs/actions/runs/42070378706) (2026-11-05):

- Newly behind: `BMMFwdOp`, `BitwiseXorFwdOp`, `GtFwdOp`, `LtFwdOp`, `MaxPool2dIndicesFwdOp`, `ReciprocalFwdOp`
- Caught up: `ErfFwdOp`, `GQAPagedFwdOp`, `INT8DequantPerTensorFwdOp`

## Queue

Ordered by label, then by worst ratio. Nightlies behind counts the consecutive nightlies, up to 30, in which the op had a row behind.

| # | Op | Category | Label | Worst ratio | Rows behind | Nightlies behind |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | [GQAVarlenFwdOp](#gqavarlenfwdop) | attention | P2 | 0.8119 | 2 of 63 | 3 |
| 2 | [GroupedGEMMFwdOp](#groupedgemmfwdop) | gemm | P2 | 0.8588 | 2 of 10 | 2 |
| 3 | [SoftmaxFwdOp](#softmaxfwdop) | reduction | P3 | 0.9487 | 5 of 42 | 3 |
| 4 | [DivFwdOp](#divfwdop) | elementwise | P4 | 0.9547 | 4 of 16 | 3 |
| 5 | [RMSNormFwdOp](#rmsnormfwdop) | norm | P4 | 0.9654 | 2 of 34 | 4 |
| 6 | [GEMMFwdOp](#gemmfwdop) | gemm | P4 | 0.9675 | 4 of 24 | 3 |
| 7 | [MoEGroupedGEMMFP8FwdOp](#moegroupedgemmfp8fwdop) | moe | P4 | 0.9705 | 1 of 18 | 2 |
| 8 | [NeFwdOp](#nefwdop) | elementwise | P4 | 0.9781 | 2 of 13 | 2 |
| 9 | [BMMFwdOp](#bmmfwdop) | gemm | P4 | 0.9801 | 1 of 16 | 1 |
| 10 | [GEMMFP8FwdOp](#gemmfp8fwdop) | gemm | P4 | 0.9847 | 1 of 39 | 3 |
| 11 | [GtFwdOp](#gtfwdop) | elementwise | P4 | 0.9853 | 1 of 13 | 1 |
| 12 | [EqFwdOp](#eqfwdop) | elementwise | P4 | 0.9854 | 1 of 14 | 2 |
| 13 | [LogicalOrFwdOp](#logicalorfwdop) | elementwise | P4 | 0.9855 | 2 of 18 | 2 |
| 14 | [LtFwdOp](#ltfwdop) | elementwise | P4 | 0.9855 | 1 of 13 | 1 |
| 15 | [RemainderFwdOp](#remainderfwdop) | elementwise | P4 | 0.9866 | 1 of 14 | 3 |
| 16 | [GEMMINT8W8A8FwdOp](#gemmint8w8a8fwdop) | gemm | P4 | 0.9867 | 1 of 29 | 3 |
| 17 | [BitwiseXorFwdOp](#bitwisexorfwdop) | elementwise | P4 | 0.9873 | 1 of 13 | 1 |
| 18 | [MaxPool2dIndicesFwdOp](#maxpool2dindicesfwdop) | pool | P4 | 0.9875 | 1 of 9 | 1 |
| 19 | [ReciprocalFwdOp](#reciprocalfwdop) | elementwise | P4 | 0.9896 | 1 of 5 | 1 |

## Rows behind

### GQAVarlenFwdOp

Benchmark `benchmarks.ops.bench_gqa`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `llama-8b-chunk-decodes-bfloat16` | 262.609 | fa3 | 213.201 | 0.8119 |
| `llama-8b-chunk-decodes-float16` | 264.578 | fa3 | 215.553 | 0.8147 |

### GroupedGEMMFwdOp

Benchmark `benchmarks.ops.bench_grouped_gemm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `qwen3-30b-ep8-skew-down-bfloat16` | 48.160 | quack | 41.361 | 0.8588 |
| `qwen3-30b-ep8-skew-up-bfloat16` | 84.447 | quack | 80.944 | 0.9585 |

### SoftmaxFwdOp

Benchmark `benchmarks.ops.bench_softmax`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `quack-throughput-4096-bfloat16` | 133.186 | quack | 126.354 | 0.9487 |
| `quack-throughput-4096-float16` | 130.498 | quack | 126.273 | 0.9676 |
| `quack-throughput-8192-bfloat16` | 262.483 | quack | 258.723 | 0.9857 |
| `quack-throughput-512-bfloat16` | 16.672 | quack | 16.465 | 0.9876 |
| `quack-throughput-2048-bfloat16` | 63.697 | quack | 62.913 | 0.9877 |

### DivFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-bfloat16` | 5.631 | torch-compile | 5.376 | 0.9547 |
| `cnn-feat-broadcast-float32` | 23.809 | torch-compile | 23.391 | 0.9824 |
| `hidden-state-prefill-bfloat16` | 12.384 | torch-compile | 12.224 | 0.9871 |
| `linear-bias-float32` | 9.072 | torch-compile | 8.960 | 0.9877 |

### RMSNormFwdOp

Benchmark `benchmarks.ops.bench_norm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `quack-throughput-8192-float16` | 256.449 | torch-compile | 247.568 | 0.9654 |
| `quack-throughput-8192-bfloat16` | 255.489 | torch-compile | 250.977 | 0.9823 |

### GEMMFwdOp

Benchmark `benchmarks.ops.bench_gemm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `ds-v3-m96-qkv-a-bfloat16` | 14.752 | torch-cublas | 14.272 | 0.9675 |
| `ds-v3-m2-qkv-a-bfloat16` | 12.416 | cublaslt-best | 12.032 | 0.9691 |
| `qwen3-8b-gate-up-b32-bfloat16` | 49.088 | cublaslt-best | 48.209 | 0.9821 |
| `ds-v3-m64-down-bfloat16` | 9.984 | cublaslt-best | 9.856 | 0.9872 |

### MoEGroupedGEMMFP8FwdOp

Benchmark `benchmarks.ops.bench_moe_grouped_gemm_fp8`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `qwen3-30b-ep8-skew-up` | 48.800 | deepgemm | 47.361 | 0.9705 |

### NeFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-bfloat16` | 4.384 | torch-compile | 4.288 | 0.9781 |
| `linear-bias-float16` | 4.384 | torch-compile | 4.320 | 0.9854 |

### BMMFwdOp

Benchmark `benchmarks.ops.bench_bmm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `square-512-float16` | 11.264 | quack | 11.040 | 0.9801 |

### GEMMFP8FwdOp

Benchmark `benchmarks.ops.bench_gemm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `ds-v3-o-proj-m128-s128-float8_e4m3fn-bfloat16` | 41.824 | flashinfer-fp8-blockscale-sm90 | 41.184 | 0.9847 |

### GtFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-bfloat16` | 4.352 | torch-compile | 4.288 | 0.9853 |

### EqFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-float16` | 4.352 | torch-compile | 4.288 | 0.9854 |

### LogicalOrFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-float16` | 4.416 | torch-compile | 4.352 | 0.9855 |
| `linear-bias-bfloat16` | 4.416 | torch-compile | 4.352 | 0.9855 |

### LtFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `linear-bias-bfloat16` | 4.351 | torch-compile | 4.288 | 0.9855 |

### RemainderFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `cnn-feat-broadcast-float32` | 23.872 | torch-compile | 23.553 | 0.9866 |

### GEMMINT8W8A8FwdOp

Benchmark `benchmarks.ops.bench_gemm`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `llama3-8b-decode-qkv-bfloat16` | 12.000 | vllm | 11.840 | 0.9867 |

### BitwiseXorFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `llama-7b-ffn-int64` | 60.320 | torch-compile | 59.553 | 0.9873 |

### MaxPool2dIndicesFwdOp

Benchmark `benchmarks.ops.bench_pool`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `vgg-block-float16` | 9.008 | torch-compile | 8.896 | 0.9875 |

### ReciprocalFwdOp

Benchmark `benchmarks.ops.bench_elementwise`.

| Workload | TileOPs (us) | Fastest comparator | Comparator (us) | Ratio |
| --- | ---: | --- | ---: | ---: |
| `16M-float32` | 30.752 | torch-compile | 30.432 | 0.9896 |

