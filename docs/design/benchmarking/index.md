# Benchmarking Architecture

This section describes the architecture of our benchmarking system which
satisfies the requirements defined in
[Requirements for Benchmarking](../../requirements/benchmark.md).

## Terminology

These terms are those defined in the
[benchmarking requirements](../../requirements/benchmark.md#terminology).

- **Logical benchmark (benchmark problem)** — an abstract, reusable definition
  of a problem class or evaluation task. It defines *what* is being measured
  without prescribing *how* it is instantiated or executed.
- **Benchmark instance** — the concrete realisation of a logical benchmark: the
  problem or task a target is intended to solve, including the associated
  inputs, data, and execution pattern.
- **Benchmark target** — the model, algorithm, or experiment being evaluated.
  For a given benchmark instance, this is the primary element that is varied.
- **Benchmark experiment** — a script, harness, or workflow that executes the
  benchmark target on the benchmark instance and collects measurements. It may
  take the target and instance as input (**parameterizable**) or hard-code one
  or both (**fixed**). An experiment may imply the target, and it may address
  one or more logical benchmarks.
- **Benchmark submission** — one registered use of a benchmark experiment on a
  benchmark instance for a specific benchmark target. A submission can be
  executed to produce results. It is not the experiment definition, and it is
  not an execution.
- **Benchmark result** — the quantitative measurements produced by executing a
  benchmark submission. Results are used to compare benchmark targets on a given
  benchmark instance.

```text
Benchmark Submission = Benchmark Experiment + Benchmark Target + Benchmark Instance
```

## Layers

There are three layers to the system

1. [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md) —
   covers problem definitions (logical benchmarks), defining concrete benchmark
   instances, and enabling comparable results
2. [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md)
   — adding benchmark experiments, and defining benchmark submissions that use
   them
3. [Benchmark Execution and Operations](./benchmark_execution.md) — `ado`
   experiment packages, Ray, and the result store.

## Requirements map

<!-- markdownlint-disable line-length -->

| Requirements                                      | Document                                                                                                                                                |
| --------------------------------------------------| --------------------------------------------------------------------------------------------------------------------------------------------------------|
| REQ-1, REQ-4, REQ-5.1, REQ-6, REQ-7.2, REQ-7.3    | [Benchmark Execution and Operations](./benchmark_execution.md)                                                                                          |
| REQ-2.3, REQ-2.4, REQ-3.1, REQ-3.2                | [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md)                                                                     |
| REQ-2.1, REQ-2.2, REQ-5.2, REQ-5.3, REQ-7.1       | [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md)                                                                               |
| REQ-2.5, REQ-3.3                                  | [Experiments and Submissions](./benchmark_experiments_and_submissions.md) and [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md) |

<!-- markdownlint-enable line-length -->

REQ-2.5 (discoverability) and REQ-3.3 (artifact reuse) span both registration
layers.
