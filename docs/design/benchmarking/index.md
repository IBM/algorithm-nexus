# Benchmarking Architecture

This is the entry point for the benchmarking design. It names the concepts, the
three layers, and which document answers each requirement group. Schemas and
operational detail live in the child documents.

The requirements are in
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

1. **Execution** — `ado` experiment packages, Ray, and the result store.
   [Benchmark Execution and Operations](./benchmark_execution.md).
2. **Experiments and submissions** — which experiments a package exposes, and
   which submissions run them.
   [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md).
3. **Logical benchmarks and instances** — the shared problem definition,
   concrete instances, and comparable results.
   [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md).

Experiment binding (how an experiment's outputs map onto a logical benchmark)
stays in the logical benchmarks document for now.

## Requirements map

| Requirements | Document |
| --- | --- |
| REQ-1, REQ-4, REQ-5.1, REQ-6, REQ-7 | [Benchmark Execution and Operations](./benchmark_execution.md) |
| REQ-2, REQ-3 | [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md) |
| REQ-5.2, REQ-5.3 | [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md) |

REQ-5.1 (centralized result storage) is part of execution. REQ-5.2 and REQ-5.3
(a common results schema and custom metadata used for aggregation) are answered
by logical benchmarks and instances.
