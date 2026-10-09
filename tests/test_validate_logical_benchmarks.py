# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for validate_logical_benchmark_file."""

from pathlib import Path

import pytest

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
        assert result.benchmarkIdentifier == "inference_serving"
        assert result.title == "Inference Serving Performance"

    def test_target_mapping_defaults_to_static_experiment_identifier(self) -> None:
        """When targetMapping is omitted, it defaults to a StaticTargetMapping with the experiment identifier."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import InstanceBinding, StaticTargetMapping

        binding = InstanceBinding(
            instanceBindingIdentifier="test_binding",
            instanceReference="sorting/instance_1",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
        )
        assert isinstance(binding.targetMapping, StaticTargetMapping)
        assert binding.targetMapping.static == "solve_mip"

    def test_target_mapping_static_explicit(self) -> None:
        """When targetMapping.static is explicitly set it is preserved."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import InstanceBinding, StaticTargetMapping

        binding = InstanceBinding(
            instanceBindingIdentifier="test_binding",
            instanceReference="sorting/instance_1",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
            targetMapping=StaticTargetMapping(static="custom_label"),
        )
        assert isinstance(binding.targetMapping, StaticTargetMapping)
        assert binding.targetMapping.static == "custom_label"

    def test_target_mapping_experiment_property(self) -> None:
        """experimentProperty targetMapping resolves to the named experiment input."""
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import (
            ExperimentPropertyTargetMapping,
            InstanceBinding,
        )

        binding = InstanceBinding(
            instanceBindingIdentifier="test_binding",
            instanceReference="sorting/instance_1",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
            targetMapping=ExperimentPropertyTargetMapping(experimentProperty="model"),
        )
        assert isinstance(binding.targetMapping, ExperimentPropertyTargetMapping)
        assert binding.targetMapping.experimentProperty == "model"

    def test_instance_binding_identifier_required(self) -> None:
        """instanceBindingIdentifier raises ValidationError when omitted."""
        from ado.schema.reference import ExperimentReference
        from pydantic import ValidationError

        from algorithm_nexus.models import InstanceBinding

        with pytest.raises(ValidationError):
            InstanceBinding(
                instanceReference="sorting/instance_1",
                experiment=ExperimentReference(
                    actuatorIdentifier="custom_experiments",
                    experimentIdentifier="bubble_sort",
                ),
            )

    def test_instance_reference_required(self) -> None:
        """instanceReference raises ValidationError when omitted."""
        from ado.schema.reference import ExperimentReference
        from pydantic import ValidationError

        from algorithm_nexus.models import InstanceBinding

        with pytest.raises(ValidationError):
            InstanceBinding(
                instanceBindingIdentifier="test_binding",
                experiment=ExperimentReference(
                    actuatorIdentifier="custom_experiments",
                    experimentIdentifier="bubble_sort",
                ),
            )

    def test_instance_reference_pattern_validated(self) -> None:
        """instanceReference must contain exactly one slash."""
        from ado.schema.reference import ExperimentReference
        from pydantic import ValidationError

        from algorithm_nexus.models import InstanceBinding

        with pytest.raises(ValidationError):
            InstanceBinding(
                instanceBindingIdentifier="test_binding",
                instanceReference="no_slash_here",
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
    def test_empty_problem_properties_fails(self) -> None:
        """A file with empty problemProperties list returns None with errors."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_instance_unknown_property.yaml", collector
        )

        assert result is None
        assert collector.has_errors
        error_text = " ".join(collector.errors)
        assert "problemProperties" in error_text

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

        from algorithm_nexus.models import InstanceBinding

        return InstanceBinding(
            instanceBindingIdentifier=kwargs.pop(
                "instanceBindingIdentifier", "test_binding"
            ),
            instanceReference=kwargs.pop("instanceReference", "test_bench/inst_1"),
            experiment=ExperimentReference(
                actuatorIdentifier="custom",
                experimentIdentifier="exp1",
                experimentVersion="1.0.0",
            ),
            **kwargs,
        )

    def test_binding_with_unknown_property_fails(self) -> None:
        """problemPropertyMapping referencing a property not in the definition is an integrity error."""
        from algorithm_nexus.commands.validate import _check_binding_integrity
        from algorithm_nexus.models import FieldMapping

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            problemPropertyMapping=[
                FieldMapping(
                    instance={"identifier": "nonexistent_property"},
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

    def test_static_filters_are_flat_list(self) -> None:
        """staticFilters is now a flat list of PropertyValue, not a nested structure."""
        from ado.schema.property import Property
        from ado.schema.property_value import PropertyValue

        from algorithm_nexus.commands.validate import _check_binding_integrity

        collector = ValidationErrorCollector()
        binding = self._make_binding(
            staticFilters=[
                PropertyValue(property=Property(identifier="dataset"), value="random")
            ]
        )
        _check_binding_integrity(
            binding,
            set(),
            None,
            collector,
            Path("test.yaml"),
            0,
        )
        assert not collector.has_errors
        assert binding.staticFilters is not None
        assert binding.staticFilters[0].property.identifier == "dataset"


class TestBenchmarkDirectoryAndInstances:
    def test_valid_benchmark_directory(self, tmp_path: Path) -> None:
        """A complete benchmark folder with benchmark.yaml and instances folder with per-instance folder layout passes validation."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        inst1_dir = instances_dir / "inst_1"
        inst1_data_dir = inst1_dir / "data"
        inst1_data_dir.mkdir(parents=True)

        # Create benchmark.yaml with problem properties (no artifact marker — artifacts are now in instanceArtifacts)
        benchmark_content = """
benchmarkIdentifier: inference_serving
description: Test description
problemProperties:
  - identifier: dataset
  - identifier: workload
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        # Create artifact files inside the named subfolder
        (inst1_data_dir / "data.json").write_text("{}")
        (inst1_data_dir / "data.csv").write_text("a,b\n1,2")

        # Create a valid instance YAML inside instances/inst_1/instance.yaml
        instance_content = """
instanceIdentifier: test_inst_1
benchmarkIdentifier: inference_serving
description: A test instance
problemPropertyValues:
  - property:
        identifier: workload
    value: "steady_state_heavy"
instanceArtifacts:
  - property:
        identifier: dataset
    artifactsLocation: data
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        config = validate_logical_benchmark_directory(bench_dir, collector)

        assert config is not None
        assert not collector.has_errors

    def test_instance_with_unknown_problem_property_fails(self, tmp_path: Path) -> None:
        """An instance specifying a problemPropertyValue not in problemProperties fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_dir.mkdir(parents=True)

        problem_yaml = FIXTURES / "valid_full.yaml"
        (bench_dir / "benchmark.yaml").write_text(problem_yaml.read_text())

        instance_content = """
instanceIdentifier: test_inst_1
benchmarkIdentifier: inference_serving
problemPropertyValues:
  - property:
        identifier: nonexistent_param
    value: "value"
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "nonexistent_param" in " ".join(collector.errors)

    def test_instance_with_missing_artifact_fails(self, tmp_path: Path) -> None:
        """An instance specifying an artifactsLocation folder that does not exist fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_dir.mkdir(parents=True)

        benchmark_content = """
benchmarkIdentifier: test_bench
description: Test description
problemProperties:
  - identifier: graph
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        instance_content = """
instanceIdentifier: test_inst_1
benchmarkIdentifier: test_bench
instanceArtifacts:
  - property:
        identifier: graph
    artifactsLocation: nonexistent_folder
"""
        (inst1_dir / "instance.yaml").write_text(instance_content)

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "nonexistent_folder" in " ".join(collector.errors)

    def test_valid_benchmark_directory_with_instance_validates(
        self, tmp_path: Path
    ) -> None:
        """A complete benchmark folder with benchmark.yaml and an instance with problemPropertyValues validates cleanly."""
        bench_dir = tmp_path / "test_benchmark"
        instances_dir = bench_dir / "instances"
        bench_dir.mkdir(parents=True)
        instances_dir.mkdir(parents=True)

        benchmark_content = """
benchmarkIdentifier: test_bench
description: Test description
problemProperties:
  - identifier: size
"""
        (bench_dir / "benchmark.yaml").write_text(benchmark_content)

        inst_dir = instances_dir / "graph_01"
        inst_dir.mkdir(parents=True)
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: graph_01\nbenchmarkIdentifier: test_bench\n"
            "problemPropertyValues:\n  - property:\n        identifier: size\n    value: 10\n"
        )

        collector = ValidationErrorCollector()
        config = validate_logical_benchmark_directory(bench_dir, collector)

        assert config is not None
        assert not collector.has_errors


class TestBenchmarkDirectoryContents:
    """Checks that a benchmark folder rejects unexpected entries and warns about missing instances."""

    @pytest.fixture
    def minimal_benchmark_yaml(self) -> str:
        import yaml
        from ado.schema.property import Property

        from algorithm_nexus.models import LogicalBenchmarkDefinition

        model = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[Property(identifier="size")],
        )
        return yaml.dump(
            model.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
            sort_keys=False,
        )

    def test_unexpected_file_in_benchmark_dir_fails(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """Any file other than benchmark.yaml, README.md, or instances/ causes a validation error."""
        bench_dir = tmp_path / "my_benchmark"
        bench_dir.mkdir()
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)
        (bench_dir / "extra_file.txt").write_text("oops")

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is None
        assert collector.has_errors
        assert "extra_file.txt" in " ".join(collector.errors)

    def test_unexpected_directory_in_benchmark_dir_fails(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """An unexpected subdirectory (not 'instances') causes a validation error."""
        bench_dir = tmp_path / "my_benchmark"
        bench_dir.mkdir()
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)
        (bench_dir / "random_subdir").mkdir()

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is None
        assert collector.has_errors
        assert "random_subdir" in " ".join(collector.errors)

    def test_readme_and_instances_are_allowed(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """benchmark.yaml + README.md + instances/ is a fully valid layout."""
        bench_dir = tmp_path / "my_benchmark"
        instances_dir = bench_dir / "instances"
        inst_dir = instances_dir / "inst_1"
        inst_dir.mkdir(parents=True)
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)
        (bench_dir / "README.md").write_text("# Benchmark")
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: inst_1\nbenchmarkIdentifier: test_bench\n"
        )

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is not None
        assert not collector.has_errors

    def test_notice_file_is_allowed(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """benchmark.yaml + NOTICE is a valid layout."""
        bench_dir = tmp_path / "my_benchmark"
        bench_dir.mkdir()
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)
        (bench_dir / "NOTICE").write_text("Copyright notice")

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is not None
        assert not collector.has_errors

    def test_no_instances_folder_produces_info(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """When instances/ is absent, no error is raised but an info note is added."""
        bench_dir = tmp_path / "my_benchmark"
        bench_dir.mkdir()
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is not None
        assert not collector.has_errors
        assert collector.has_info
        assert "no instances" in " ".join(collector.info)

    def test_empty_instances_folder_produces_info(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """When instances/ exists but is empty, no error is raised but an info note is added."""
        bench_dir = tmp_path / "my_benchmark"
        instances_dir = bench_dir / "instances"
        instances_dir.mkdir(parents=True)
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is not None
        assert not collector.has_errors
        assert collector.has_info
        assert "no instances" in " ".join(collector.info)

    def test_no_instances_info_present_even_on_failed_benchmark(
        self, tmp_path: Path, minimal_benchmark_yaml: str
    ) -> None:
        """Even when a benchmark fails (unexpected file), the no-instances info note still appears."""
        bench_dir = tmp_path / "my_benchmark"
        bench_dir.mkdir()
        (bench_dir / "benchmark.yaml").write_text(minimal_benchmark_yaml)
        (bench_dir / "extra_file.txt").write_text("oops")
        # no instances/ folder

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is None
        assert collector.has_errors
        assert "extra_file.txt" in " ".join(collector.errors)
        assert collector.has_info
        assert "no instances" in " ".join(collector.info)


class TestRankingValidation:
    def test_valid_ranking_asc_passes(self) -> None:
        """A ranking config referencing a known metric with asc order is valid."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_ranking_field.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.ranking is not None
        assert result.ranking.metric == "elapsed_ms"
        assert result.ranking.order == "asc"

    def test_valid_ranking_desc_passes(self) -> None:
        """A ranking config with desc order is valid."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_ranking_desc.yaml", collector
        )

        assert result is not None
        assert not collector.has_errors
        assert result.ranking is not None
        assert result.ranking.order == "desc"

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
        assert result.ranking is None
