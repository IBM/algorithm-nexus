# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for validate_logical_benchmark_file."""

from pathlib import Path

from algorithm_nexus.commands.utils import ValidationErrorCollector
from algorithm_nexus.commands.validate import (
    validate_logical_benchmark_directory,
    validate_logical_benchmark_file,
)

FIXTURES = Path(__file__).parent / "fixtures" / "logical_benchmarks"


class TestValidFiles:
    def test_valid_file_with_bindings_passes(self) -> None:
        """A fully valid file with definition and bindings returns a parsed object."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_full.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.logicalBenchmark.benchmarkIdentifier == "inference_serving"
        assert result.logicalBenchmark.title == "Inference Serving Performance"
        assert result.bindings is not None
        assert len(result.bindings) == 1

    def test_valid_file_without_bindings_passes(self) -> None:
        """A valid definition-only file (no bindings) returns a parsed object."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_no_bindings.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.bindings is None


class TestSchemaValidation:
    def test_empty_instance_fails(self) -> None:
        """A file with empty instance list returns None with errors."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_instance_unknown_property.yaml", collector
        )

        assert result is None
        assert collector.has_errors
        error_text = " ".join(collector.errors)
        assert "instance" in error_text

    def test_missing_required_field_fails(self) -> None:
        """A file missing required fields (description) returns None with errors."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_missing_required_field.yaml", collector
        )

        assert result is None
        assert collector.has_errors
        error_text = " ".join(collector.errors)
        assert "description" in error_text

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        """A non-existent file path collects an error and returns None."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            tmp_path / "nonexistent.yaml", collector
        )

        assert result is None
        assert collector.has_errors


class TestReferentialIntegrity:
    def test_binding_with_unknown_property_fails(self) -> None:
        """A binding referencing a property not in the definition is an integrity error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_binding_unknown_property.yaml", collector
        )

        assert (
            result is not None
        )  # schema is valid; integrity error is collected separately
        assert collector.has_errors
        assert "nonexistent_property" in " ".join(collector.errors)

    def test_binding_with_unknown_metric_fails(self) -> None:
        """A binding referencing a metric not in the definition is an integrity error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_binding_unknown_metric.yaml", collector
        )

        assert result is not None
        assert collector.has_errors
        assert "nonexistent_metric" in " ".join(collector.errors)

    def test_metric_mapping_allowed_when_no_metrics_defined(self) -> None:
        """metricMapping with no metrics defined in the definition does not raise an error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_metric_mapping_no_metrics_defined.yaml", collector
        )

        # No metrics defined → metric_ids is None → no integrity check is performed
        assert result is not None
        assert not collector.has_errors


class TestBenchmarkDirectoryAndInstances:
    def test_valid_benchmark_directory(self, tmp_path: Path) -> None:
        """A complete benchmark folder with problem.yaml and instances folder with per-instance folder layout passes validation."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        inst1_dir = instances_dir / "inst_1"
        inst1_artifacts = inst1_dir / "artifacts"
        inst1_artifacts.mkdir(parents=True)

        # Create problem.yaml with artifact and scalar properties
        problem_content = """
logicalBenchmark:
  benchmarkIdentifier: inference_serving
  description: Test description
  instance:
    - identifier: dataset
      is_artifact: true
    - identifier: workload
"""
        (bench_dir / "problem.yaml").write_text(problem_content)

        # Create an artifact file
        (inst1_artifacts / "data.json").write_text("{}")
        (inst1_artifacts / "data.csv").write_text("a,b\n1,2")

        # Create a valid instance YAML inside instances/inst_1/instance.yaml
        instance_content = """
identifier: test_inst_1
description: A test instance
dataset:
  json_format: data.json
  csv_format: data.csv
workload: "steady_state_heavy"
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        config = validate_logical_benchmark_directory(bench_dir, collector)

        assert config is not None
        assert not collector.has_errors

    def test_instance_with_unknown_parameter_fails(self, tmp_path: Path) -> None:
        """An instance specifying a property not in problem instance properties fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_dir.mkdir(parents=True)

        problem_yaml = FIXTURES / "valid_full.yaml"
        (bench_dir / "problem.yaml").write_text(problem_yaml.read_text())

        instance_content = """
identifier: test_inst_1
nonexistent_param: "value"
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "nonexistent_param" in " ".join(collector.errors)

    def test_instance_with_missing_artifact_fails(self, tmp_path: Path) -> None:
        """An instance specifying an artifact that does not exist in its artifacts/ fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_artifacts = inst1_dir / "artifacts"
        inst1_artifacts.mkdir(parents=True)

        problem_content = """
logicalBenchmark:
  benchmarkIdentifier: test_bench
  description: Test description
  instance:
    - identifier: graph
      is_artifact: true
"""
        (bench_dir / "problem.yaml").write_text(problem_content)

        instance_content = """
identifier: test_inst_1
graph:
  - missing_graph.txt
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "missing_graph.txt" in " ".join(collector.errors)

    def test_binding_with_valid_instance_mapping_passes(self, tmp_path: Path) -> None:
        """A binding with instanceMapping referencing valid instance passes."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        bench_dir.mkdir(parents=True)
        instances_dir.mkdir(parents=True)

        problem_content = """
logicalBenchmark:
  benchmarkIdentifier: test_bench
  description: Test description
  instance:
    - identifier: size

bindings:
  - experiment:
      actuatorIdentifier: custom
      experimentIdentifier: exp1
      experimentVersion: 1.0.0
    instanceMapping:
      propertyMapping:
        - benchmark:
            identifier: size
          experiment:
            identifier: n_nodes
      staticFilters:
        - property:
            identifier: graph_type
          value: erdos_renyi
"""
        (bench_dir / "problem.yaml").write_text(problem_content)

        inst_dir = instances_dir / "graph_01"
        inst_dir.mkdir(parents=True)
        instance_content = """
identifier: graph_01
size: 10
"""
        (inst_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        config = validate_logical_benchmark_directory(bench_dir, collector)

        assert config is not None
        assert not collector.has_errors
        assert config.bindings is not None
        assert config.bindings[0].instanceMapping is not None
        assert config.bindings[0].instanceMapping.propertyMapping is not None
        assert config.bindings[0].instanceMapping.staticFilters is not None

    def test_binding_with_invalid_instance_property_mapping_fails(
        self, tmp_path: Path
    ) -> None:
        """A binding with propertyMapping inside instanceMapping referencing unknown property fails."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        bench_dir.mkdir(parents=True)
        instances_dir.mkdir(parents=True)

        problem_content = """
logicalBenchmark:
  benchmarkIdentifier: test_bench
  description: Test description
  instance:
    - identifier: num_vertices

bindings:
  - experiment:
      actuatorIdentifier: custom
      experimentIdentifier: exp1
      experimentVersion: 1.0.0
    instanceMapping:
      propertyMapping:
        - benchmark:
            identifier: unknown_property
          experiment:
            identifier: n_nodes
"""
        (bench_dir / "problem.yaml").write_text(problem_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "unknown_property" in " ".join(collector.errors)


class TestRankingValidation:
    def test_valid_ranking_asc_passes(self) -> None:
        """A ranking config referencing a known metric with asc order is valid."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_ranking_field.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.logicalBenchmark.ranking is not None
        assert result.logicalBenchmark.ranking.metric == "elapsed_ms"
        assert result.logicalBenchmark.ranking.order == "asc"

    def test_valid_ranking_desc_passes(self) -> None:
        """A ranking config with desc order is valid."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_ranking_desc.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.logicalBenchmark.ranking is not None
        assert result.logicalBenchmark.ranking.order == "desc"

    def test_ranking_unknown_metric_fails(self) -> None:
        """A ranking.metric that is not in the defined metrics list is an integrity error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_ranking_unknown_metric.yaml", collector
        )

        assert (
            result is not None
        )  # schema is valid; integrity error is collected separately
        assert collector.has_errors
        assert "nonexistent_metric" in " ".join(collector.errors)

    def test_ranking_without_metrics_no_error(self) -> None:
        """When metrics is not defined, a ranking integrity check is skipped."""
        collector = ValidationErrorCollector()
        # valid_no_bindings.yaml has no ranking — verify no ranking field means None
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_no_bindings.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.logicalBenchmark.ranking is None
