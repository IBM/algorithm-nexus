# Benchmarking Architecture

This section describes the architecture of our benchmarking system which
satisfies the requirements defined in
[Requirements for models benchmarking](../../requirements/benchmark.md).

## Terminology

- **Benchmark experiment** — a script, harness, or workflow that runs a
  benchmark target on a benchmark instance and collects measurements.
- **Benchmark submission** — one run of an experiment on a problem: the
  experiment plus the parameter values for that run.
- **Benchmark target** — the model or algorithm being evaluated.
- **Logical benchmark** — the shared problem definition: which properties define
  an instance, and which metric names results are reported under.
- **Benchmark instance** — one concrete realisation of a logical benchmark.
- **Benchmark result** — the measurements from a submission, labeled so results
  from different experiments can be compared.

## Layers

There are three layers to the system

1. [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md). —
   covers problem definitions (logical benchmarks), defining concrete benchmark
   instances, and enabling comparable results
2. [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md).
   — adding benchmark experiments, and defining benchmark submissions that uses
   them
3. [Benchmark Execution and Operations](./benchmark_execution.md).— `ado`
   experiment packages, Ray, and the result store.

## Requirements map

| Requirements                        | Document                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------- |
| REQ-1, REQ-4, REQ-5.1, REQ-6, REQ-7 | [Benchmark Execution and Operations](./benchmark_execution.md)                      |
| REQ-2, REQ-3                        | [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md) |
| REQ-5.2, REQ-5.3                    | [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md)           |

REQ-5.1 (centralized result storage) is part of execution. REQ-5.2 and REQ-5.3
(a common results schema and custom metadata used for aggregation) are answered
by logical benchmarks and instances.
