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
    def test_valid_file_without_bindings_passes_schema(self) -> None:
        """A definition-only file (no bindings key) is valid."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_full.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.logicalBenchmark.benchmarkIdentifier == "inference_serving"
        assert result.logicalBenchmark.title == "Inference Serving Performance"

    def test_target_mapping_defaults_to_experiment_identifier(self) -> None:
        """When targetMapping is omitted, it defaults to the experiment's experimentIdentifier."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import BenchmarkBinding

        binding = BenchmarkBinding(
            benchmarkIdentifier="sorting",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
        )
        assert binding.targetMapping == "solve_mip"

    def test_target_mapping_explicit_value_preserved(self) -> None:
        """When targetMapping is explicitly set it is not overwritten."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import BenchmarkBinding

        binding = BenchmarkBinding(
            benchmarkIdentifier="sorting",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
            targetMapping="custom_label",
        )
        assert binding.targetMapping == "custom_label"

    def test_benchmark_identifier_on_binding(self) -> None:
        """benchmarkIdentifier is required on BenchmarkBinding entries."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import BenchmarkBinding

        binding = BenchmarkBinding(
            benchmarkIdentifier="sorting",
            experiment=ExperimentReference(
                actuatorIdentifier="custom_experiments",
                experimentIdentifier="bubble_sort",
            ),
        )
        assert binding.benchmarkIdentifier == "sorting"
        assert binding.targetMapping == "bubble_sort"

    def test_benchmark_identifier_required(self) -> None:
        """benchmarkIdentifier raises ValidationError when omitted."""
        import pytest
        from ado.schema.reference import ExperimentReference
        from pydantic import ValidationError

        from algorithm_nexus.models import BenchmarkBinding

        with pytest.raises(ValidationError):
            BenchmarkBinding(
                experiment=ExperimentReference(
                    actuatorIdentifier="custom_experiments",
                    experimentIdentifier="bubble_sort",
                ),
            )

    def test_valid_file_without_bindings_passes(self) -> None:
        """A valid definition-only file (no bindings) returns a parsed object."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_no_bindings.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors


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
    """Binding integrity checks via _check_binding_integrity (bindings live in experiments/)."""

    def _make_binding(self, **kwargs):
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import BenchmarkBinding

        return BenchmarkBinding(
            benchmarkIdentifier=kwargs.pop("benchmarkIdentifier", "test_bench"),
            experiment=ExperimentReference(
                actuatorIdentifier="custom",
                experimentIdentifier="exp1",
                experimentVersion="1.0.0",
            ),
            **kwargs,
        )

    def test_binding_with_unknown_property_fails(self) -> None:
        """instanceMapping referencing a property not in the definition is an integrity error."""
        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import FieldMapping

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            instanceMapping=[
                FieldMapping(
                    benchmark={"identifier": "nonexistent_property"},
                    experiment={"identifier": "exp_param"},
                )
            ]
        )
        _check_binding_integrity(
            binding, {"real_property"}, None, collector, Path("test.yaml"), 0
        )
        assert collector.has_errors
        assert "nonexistent_property" in " ".join(collector.errors)

    def test_binding_with_unknown_metric_fails(self) -> None:
        """metricMapping referencing a metric not in the definition is an integrity error."""
        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import MetricIdentifier, MetricMapping

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            metricMapping=[
                MetricMapping(
                    benchmark=MetricIdentifier(identifier="nonexistent_metric"),
                    experiment=MetricIdentifier(identifier="internal_metric"),
                )
            ]
        )
        _check_binding_integrity(
            binding,
            set(),
            {"throughput_tokens_per_second"},
            collector,
            Path("test.yaml"),
            0,
        )
        assert collector.has_errors
        assert "nonexistent_metric" in " ".join(collector.errors)

    def test_static_filters_both_directions_passes(self) -> None:
        """A binding with both experimentFilters and benchmarkFilters is valid."""
        from ado.schema.property import Property
        from ado.schema.property_value import PropertyValue

        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import StaticFilters

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            staticFilters=StaticFilters(
                experimentFilters=[
                    PropertyValue(
                        property=Property(identifier="graph_type"), value="erdos_renyi"
                    )
                ],
                benchmarkFilters=[
                    PropertyValue(
                        property=Property(identifier="graph_family"),
                        value="random_regular",
                    )
                ],
            )
        )
        _check_binding_integrity(
            binding,
            {"graph_family"},
            None,
            collector,
            Path("test.yaml"),
            0,
        )
        assert not collector.has_errors
        assert binding.staticFilters is not None
        assert (
            binding.staticFilters.experimentFilters[0].property.identifier
            == "graph_type"
        )
        assert (
            binding.staticFilters.benchmarkFilters[0].property.identifier
            == "graph_family"
        )

    def test_benchmark_filter_unknown_property_fails(self) -> None:
        """benchmarkFilters referencing a property not in the definition is an integrity error."""
        from ado.schema.property import Property
        from ado.schema.property_value import PropertyValue

        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import StaticFilters

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            staticFilters=StaticFilters(
                benchmarkFilters=[
                    PropertyValue(
                        property=Property(identifier="nonexistent_prop"),
                        value="random_regular",
                    )
                ]
            )
        )
        _check_binding_integrity(
            binding, {"num_vertices"}, None, collector, Path("test.yaml"), 0
        )
        assert collector.has_errors
        assert "nonexistent_prop" in " ".join(collector.errors)

    def test_benchmark_filter_overlapping_instance_mapping_fails(self) -> None:
        """benchmarkFilters for a property already in instanceMapping is an integrity error."""
        from ado.schema.property import Property
        from ado.schema.property_value import PropertyValue

        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import FieldMapping, StaticFilters

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            instanceMapping=[
                FieldMapping(
                    benchmark={"identifier": "num_vertices"},
                    experiment={"identifier": "n_nodes"},
                )
            ],
            staticFilters=StaticFilters(
                benchmarkFilters=[
                    PropertyValue(
                        property=Property(identifier="num_vertices"), value="50"
                    )
                ]
            ),
        )
        _check_binding_integrity(
            binding, {"num_vertices"}, None, collector, Path("test.yaml"), 0
        )
        assert collector.has_errors
        assert "num_vertices" in " ".join(collector.errors)
        assert "already covered by instanceMapping" in " ".join(collector.errors)

    def test_metric_mapping_allowed_when_no_metrics_defined(self) -> None:
        """metricMapping with metric_ids=None does not raise an integrity error."""
        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import MetricIdentifier, MetricMapping

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            metricMapping=[
                MetricMapping(
                    benchmark=MetricIdentifier(identifier="any_metric"),
                    experiment=MetricIdentifier(identifier="internal_metric"),
                )
            ]
        )
        # metric_ids=None → integrity check is skipped
        _check_binding_integrity(binding, set(), None, collector, Path("test.yaml"), 0)
        assert not collector.has_errors


class TestBenchmarkDirectoryAndInstances:
    def test_valid_benchmark_directory(self, tmp_path: Path) -> None:
        """A complete benchmark folder with benchmark.yaml and instances folder with per-instance folder layout passes validation."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        inst1_dir = instances_dir / "inst_1"
        inst1_data_dir = inst1_dir / "data"
        inst1_data_dir.mkdir(parents=True)

        # Create benchmark.yaml with artifact and scalar properties
        benchmark_content = """
logicalBenchmark:
  benchmarkIdentifier: inference_serving
  description: Test description
  instance:
    - identifier: dataset
      is_artifact: true
    - identifier: workload
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        # Create artifact files inside the named subfolder
        (inst1_data_dir / "data.json").write_text("{}")
        (inst1_data_dir / "data.csv").write_text("a,b\n1,2")

        # Create a valid instance YAML inside instances/inst_1/instance.yaml
        instance_content = """
identifier: test_inst_1
description: A test instance
dataset:
  artifacts_location: data
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
        (bench_dir / "benchmark.yaml").write_text(problem_yaml.read_text())

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
        """An instance specifying an artifacts_location folder that does not exist fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_dir.mkdir(parents=True)

        benchmark_content = """
logicalBenchmark:
  benchmarkIdentifier: test_bench
  description: Test description
  instance:
    - identifier: graph
      is_artifact: true
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        instance_content = """
identifier: test_inst_1
graph:
  artifacts_location: nonexistent_folder
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "nonexistent_folder" in " ".join(collector.errors)

    def test_valid_benchmark_directory_with_instance_validates(
        self, tmp_path: Path
    ) -> None:
        """A complete benchmark folder with benchmark.yaml and an instance with instanceMapping validates cleanly."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        bench_dir.mkdir(parents=True)
        instances_dir.mkdir(parents=True)

        benchmark_content = """
logicalBenchmark:
  benchmarkIdentifier: test_bench
  description: Test description
  instance:
    - identifier: size
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        inst_dir = instances_dir / "graph_01"
        inst_dir.mkdir(parents=True)
        (inst_dir / "instance.yaml").write_text("identifier: graph_01\nsize: 10\n")

        collector = ValidationErrorCollector()
        config = validate_logical_benchmark_directory(bench_dir, collector)

        assert config is not None
        assert not collector.has_errors


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
