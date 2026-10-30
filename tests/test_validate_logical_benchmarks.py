# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for validate_logical_benchmark_file."""

from pathlib import Path

import pytest
from ado.schema.domain import PropertyDomain
from ado.schema.property import Property, PropertyDescriptor

from algorithm_nexus.commands.utils import ValidationErrorCollector
from algorithm_nexus.commands.validate import (
    validate_experiment_yaml,
    validate_instance,
    validate_logical_benchmark_directory,
    validate_logical_benchmark_file,
)
from algorithm_nexus.models import (
    BenchmarkInstance,
    ExperimentConfig,
    ExperimentSpecifier,
    LogicalBenchmarkDefinition,
    PropertyValue,
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
  - property:
        identifier: dataset
    value: data/data.csv
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

    def test_instance_property_values_optional_and_valid(self, tmp_path: Path) -> None:
        """instancePropertyValues are optional; unique non-colliding ids validate."""
        bench_dir = tmp_path / "foo"
        inst_dir = bench_dir / "instances" / "ok"
        inst_dir.mkdir(parents=True)
        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[Property(identifier="graph")],
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: i1\nbenchmarkIdentifier: test_bench\n"
            "problemPropertyValues:\n  - property:\n      identifier: graph\n    value: g\n"
            "instancePropertyValues:\n  - property:\n      identifier: seed\n    value: 42\n"
        )
        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)
        assert not collector.has_errors, collector.errors

    def test_instance_property_value_collides_with_problem_property(
        self, tmp_path: Path
    ) -> None:
        """An instance property reusing a problem property identifier fails."""
        bench_dir = tmp_path / "foo"
        inst_dir = bench_dir / "instances" / "bad"
        inst_dir.mkdir(parents=True)
        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[Property(identifier="graph")],
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: i1\nbenchmarkIdentifier: test_bench\n"
            "problemPropertyValues:\n  - property:\n      identifier: graph\n    value: g\n"
            "instancePropertyValues:\n  - property:\n      identifier: graph\n    value: x\n"
        )
        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)
        assert collector.has_errors
        assert "conflicts with a problem property" in " ".join(collector.errors)

    def _variant_instance(
        self, tmp_path: Path, body: str, lam_domain: PropertyDomain | None = None
    ) -> ValidationErrorCollector:
        domain_kwargs = {"propertyDomain": lam_domain} if lam_domain else {}
        bench_dir = tmp_path / "foo"
        inst_dir = bench_dir / "instances" / "v"
        (inst_dir / "models").mkdir(parents=True)
        (inst_dir / "models" / "m1.lp").write_text("x")
        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[
                Property(identifier="n"),
                Property(identifier="lam", **domain_kwargs),
            ],
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: i1\nbenchmarkIdentifier: test_bench\n"
            "problemPropertyValues:\n  - property:\n      identifier: n\n    value: 1\n"
            "instanceArtifacts:\n  - property:\n      identifier: model\n"
            "    artifactsLocation: models\n" + body
        )
        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)
        return collector

    def test_instance_variants_valid(self, tmp_path: Path) -> None:
        collector = self._variant_instance(
            tmp_path,
            "variants:\n  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: 1e-4\n"
            "    instanceArtifactValues:\n      - property:\n          identifier: model\n"
            "        values: [m1.lp]\n",
        )
        assert not collector.has_errors, collector.errors

    def test_instance_variant_missing_value_fails(self, tmp_path: Path) -> None:
        collector = self._variant_instance(
            tmp_path,
            "variants:\n  - problemPropertyValues:\n      - property:\n"
            "          identifier: n\n        value: 2\n",
        )
        assert collector.has_errors
        assert "already has a value" in " ".join(collector.errors)
        assert "missing a value for problem property 'lam'" in " ".join(
            collector.errors
        )

    def test_instance_variant_shared_file_fails(self, tmp_path: Path) -> None:
        variant = (
            "  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: {v}\n"
            "    instanceArtifactValues:\n      - property:\n          identifier: model\n"
            "        values: [m1.lp]\n"
        )
        collector = self._variant_instance(
            tmp_path, "variants:\n" + variant.format(v=1) + variant.format(v=2)
        )
        assert collector.has_errors
        assert "listed in both variants[0] and variants[1]" in " ".join(
            collector.errors
        )

    def test_instance_variant_missing_artifact_fails(self, tmp_path: Path) -> None:
        collector = self._variant_instance(
            tmp_path,
            "variants:\n  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: 1\n"
            "    instanceArtifactValues:\n      - property:\n          identifier: model\n"
            "        values: [m1.lp]\n"
            "  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: 2\n",
        )
        assert collector.has_errors
        assert "variants[1] has no files for instance artifact 'model'" in " ".join(
            collector.errors
        )

    def test_instance_variant_value_outside_domain_fails(self, tmp_path: Path) -> None:
        body = (
            "variants:\n  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: {v}\n"
        )
        domain = PropertyDomain(values=[1, 2])
        assert not self._variant_instance(
            tmp_path / "ok", body.format(v=1), domain
        ).has_errors
        collector = self._variant_instance(tmp_path / "bad", body.format(v=3), domain)
        assert collector.has_errors
        assert "outside the property's domain" in " ".join(collector.errors)

    def test_instance_variant_missing_file_fails(self, tmp_path: Path) -> None:
        collector = self._variant_instance(
            tmp_path,
            "variants:\n  - problemPropertyValues:\n      - property:\n"
            "          identifier: lam\n        value: 1\n"
            "    instanceArtifactValues:\n      - property:\n          identifier: model\n"
            "        values: [nope.lp]\n",
        )
        assert collector.has_errors
        assert "nope.lp" in " ".join(collector.errors)

    def test_instance_missing_problem_property_value_fails(
        self, tmp_path: Path
    ) -> None:
        """An instance that does not define a value for every benchmark problemProperty fails."""
        bench_dir = tmp_path / "foo"
        inst_dir = bench_dir / "instances" / "should_fail"
        inst_dir.mkdir(parents=True)

        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[Property(identifier="graph")],
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )

        instance = BenchmarkInstance(
            instanceIdentifier="test_inst_1",
            benchmarkIdentifier="test_bench",
        )
        (inst_dir / "instance.yaml").write_text(
            instance.model_dump_json(exclude_none=True)
        )

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "graph" in " ".join(collector.errors)

    def test_instance_duplicate_problem_property_value_fails(
        self, tmp_path: Path
    ) -> None:
        """An instance that defines multiple values for the same benchmark problemProperty fails."""
        bench_dir = tmp_path / "foo"
        inst_dir = bench_dir / "instances" / "should_fail"
        inst_dir.mkdir(parents=True)

        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="Test description",
            problemProperties=[Property(identifier="graph")],
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )

        property = PropertyDescriptor(identifier="graph")
        instance = BenchmarkInstance(
            instanceIdentifier="test_inst_1",
            benchmarkIdentifier="test_bench",
            problemPropertyValues=[
                PropertyValue(value=1, property=property),
                PropertyValue(value=1, property=property),
            ],
        )
        (inst_dir / "instance.yaml").write_text(
            instance.model_dump_json(exclude_none=True)
        )

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "graph" in " ".join(collector.errors)

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

    def test_instance_with_mismatched_benchmark_identifier_fails(
        self, tmp_path: Path
    ) -> None:
        """An instance whose benchmarkIdentifier differs from the parent benchmark's benchmarkIdentifier fails."""
        bench_dir = tmp_path / "test_benchmark"
        inst1_dir = bench_dir / "instances" / "inst_1"
        inst1_dir.mkdir(parents=True)

        (bench_dir / "benchmark.yaml").write_text(
            "benchmarkIdentifier: foo\ndescription: Test\nproblemProperties:\n  - identifier: size\n"
        )
        (inst1_dir / "instance.yaml").write_text(
            "instanceIdentifier: inst_1\nbenchmarkIdentifier: not-foo\n"
        )

        collector = ValidationErrorCollector()
        validate_logical_benchmark_directory(bench_dir, collector)

        assert collector.has_errors
        assert "not-foo" in " ".join(collector.errors)


class TestBenchmarkDirectoryContents:
    """Checks that a benchmark folder rejects unexpected entries and warns about missing instances."""

    @pytest.fixture
    def minimal_benchmark_yaml(self) -> str:
        import yaml

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
            "problemPropertyValues:\n  - property:\n        identifier: size\n    value: 10\n"
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


class TestManifestMetadataValidation:
    """Tests that all Nexus manifests accept valid metadata and that validation succeeds."""

    def test_benchmark_with_metadata_passes_validation(self, tmp_path: Path) -> None:
        """A benchmark.yaml with metadata passes validate_logical_benchmark_file."""
        bench_file = tmp_path / "benchmark.yaml"
        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="inference_serving",
            title="Inference Serving Benchmark",
            description="Evaluates inference serving performance",
            problemProperties=[Property(identifier="model_size")],
            metadata={
                "data_source_version": "v2.1.0",
                "owning_team": "platform-perf",
            },
        )
        bench_file.write_text(benchmark.model_dump_json(exclude_none=True))

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(bench_file, collector)

        assert result is not None
        assert not collector.has_errors
        assert result.metadata == {
            "data_source_version": "v2.1.0",
            "owning_team": "platform-perf",
        }

    def test_instance_with_metadata_passes_validation(self, tmp_path: Path) -> None:
        """An instance.yaml with metadata passes validate_instance."""
        inst_dir = tmp_path / "instances" / "small_model_8b"
        inst_dir.mkdir(parents=True)
        instance_file = inst_dir / "instance.yaml"

        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
            problemPropertyValues=[
                PropertyValue(
                    property=PropertyDescriptor(identifier="model_size"),
                    value="8B",
                )
            ],
            metadata={
                "region": "us-south",
                "endpoint-url": "http://ibm.com/my-endpoint/",
            },
        )
        instance_file.write_text(instance.model_dump_json(exclude_none=True))

        collector = ValidationErrorCollector()
        result = validate_instance(
            inst_dir, {"model_size"}, collector, "inference_serving"
        )

        assert result is not None
        assert not collector.has_errors
        assert result.metadata == {
            "region": "us-south",
            "endpoint-url": "http://ibm.com/my-endpoint/",
        }

    def test_benchmark_directory_with_metadata_passes_validation(
        self, tmp_path: Path
    ) -> None:
        """A benchmark directory with metadata in both benchmark.yaml and instance.yaml passes validation."""
        bench_dir = tmp_path / "inference_serving"
        inst_dir = bench_dir / "instances" / "small_model_8b"
        inst_dir.mkdir(parents=True)

        benchmark = LogicalBenchmarkDefinition(
            benchmarkIdentifier="inference_serving",
            title="Inference Serving Benchmark",
            description="Evaluates inference serving performance",
            problemProperties=[Property(identifier="model_size")],
            metadata={
                "data_source_version": "v2.1.0",
                "owning_team": "platform-perf",
            },
        )
        (bench_dir / "benchmark.yaml").write_text(
            benchmark.model_dump_json(exclude_none=True)
        )

        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
            problemPropertyValues=[
                PropertyValue(
                    property=PropertyDescriptor(identifier="model_size"),
                    value="8B",
                )
            ],
            metadata={
                "region": "us-south",
                "endpoint-url": "http://ibm.com/my-endpoint/",
            },
        )
        (inst_dir / "instance.yaml").write_text(
            instance.model_dump_json(exclude_none=True)
        )

        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_directory(bench_dir, collector)

        assert result is not None
        assert not collector.has_errors
        assert result.metadata == {
            "data_source_version": "v2.1.0",
            "owning_team": "platform-perf",
        }

    def test_experiment_package_yaml_with_metadata_passes_validation(
        self, tmp_path: Path
    ) -> None:
        """An experiment_package.yaml with metadata passes validate_experiment_yaml."""
        exp_dir = tmp_path / "my_experiment"
        exp_dir.mkdir(parents=True)

        exp_config = ExperimentConfig(
            experiment_package=ExperimentSpecifier(
                requirement_specifier="https://github.com/IBM/my-experiment.git",
                experiments=["my_experiment"],
            ),
            metadata={"author": "IBM"},
        )
        (exp_dir / "experiment_package.yaml").write_text(
            exp_config.model_dump_json(exclude_none=True)
        )

        collector = ValidationErrorCollector()
        result = validate_experiment_yaml(exp_dir, collector)

        assert result is not None
        assert not collector.has_errors
        assert result.metadata == {"author": "IBM"}

    def test_binding_yaml_with_metadata_roundtrip(self, tmp_path: Path) -> None:
        """A binding file with metadata created via BindingFileConfig passes validation and checks."""
        import yaml
        from ado.schema.reference import ExperimentReference

        from algorithm_nexus.models import BindingFileConfig

        binding = BindingFileConfig(
            instanceBindingIdentifier="my_binding",
            instanceReference="inference_serving/small_model_8b",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="solve_mip",
            ),
            metadata={"run_label": "nightly-2025-07-01"},
        )
        binding_file = tmp_path / "binding.yaml"
        binding_file.write_text(binding.model_dump_json(exclude_none=True))

        loaded = yaml.safe_load(binding_file.read_text())
        parsed = BindingFileConfig.model_validate(loaded)
        assert parsed.metadata == {"run_label": "nightly-2025-07-01"}


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


class TestBindingValidation:
    """validate_bindings checks experiments/*/bindings against the benchmarks."""

    def _setup(self, tmp_path: Path, binding: str) -> tuple[Path, Path]:
        benchmarks = tmp_path / "benchmarks"
        inst_dir = benchmarks / "foo" / "instances" / "i1"
        (inst_dir / "models").mkdir(parents=True)
        (inst_dir / "models" / "m1.lp").write_text("x")
        (benchmarks / "foo" / "benchmark.yaml").write_text(
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="foo",
                description="d",
                problemProperties=[Property(identifier="n")],
            ).model_dump_json(exclude_none=True)
        )
        (inst_dir / "instance.yaml").write_text(
            "instanceIdentifier: i1\nbenchmarkIdentifier: foo\n"
            "problemPropertyValues:\n  - property:\n      identifier: n\n    value: 1\n"
            "instanceArtifacts:\n  - property:\n      identifier: model\n"
            "    artifactsLocation: models\n"
        )
        exp = tmp_path / "experiments" / "e1"
        (exp / "bindings").mkdir(parents=True)
        (exp / "experiment_package.yaml").write_text(
            "experiment_package:\n  requirement_specifier: pkg\n  experiments: [exp1]\n"
        )
        (exp / "bindings" / "b.yaml").write_text(
            "instanceBindingIdentifier: b1\ninstanceReference: foo/i1\n"
            "experiment:\n  actuatorIdentifier: a\n  experimentIdentifier: exp1\n"
            "  experimentVersion: 1.0.0\n" + binding
        )
        return tmp_path / "experiments", benchmarks

    def _errors(self, tmp_path: Path, binding: str = "") -> str:
        from algorithm_nexus.commands.validate import validate_bindings

        exps, benches = self._setup(tmp_path, binding)
        results = validate_bindings(exps, benches)
        assert len(results) == 1
        return " ".join(results[0]["errors"])

    def test_valid_binding_passes(self, tmp_path: Path) -> None:
        assert (
            self._errors(
                tmp_path,
                "instanceArtifactMapping:\n  - instance: {identifier: model}\n"
                "    experiment: {identifier: f}\n    validValues: [m1.lp]\n",
            )
            == ""
        )

    def test_unknown_instance_fails(self, tmp_path: Path) -> None:
        from algorithm_nexus.commands.validate import validate_bindings

        exps, benches = self._setup(tmp_path, "")
        f = exps / "e1" / "bindings" / "b.yaml"
        f.write_text(f.read_text().replace("foo/i1", "foo/nope"))
        assert "unknown instance 'nope'" in " ".join(
            validate_bindings(exps, benches)[0]["errors"]
        )

    def test_unknown_benchmark_fails(self, tmp_path: Path) -> None:
        from algorithm_nexus.commands.validate import validate_bindings

        exps, benches = self._setup(tmp_path, "")
        f = exps / "e1" / "bindings" / "b.yaml"
        f.write_text(f.read_text().replace("foo/i1", "bar/i1"))
        assert "unknown benchmark 'bar'" in " ".join(
            validate_bindings(exps, benches)[0]["errors"]
        )

    def test_experiment_not_in_package_fails(self, tmp_path: Path) -> None:
        from algorithm_nexus.commands.validate import validate_bindings

        exps, benches = self._setup(tmp_path, "")
        f = exps / "e1" / "bindings" / "b.yaml"
        f.write_text(
            f.read_text().replace(
                "experimentIdentifier: exp1", "experimentIdentifier: zzz"
            )
        )
        assert "not listed in experiment_package.yaml" in " ".join(
            validate_bindings(exps, benches)[0]["errors"]
        )

    def test_unknown_artifact_and_missing_file_fail(self, tmp_path: Path) -> None:
        errs = self._errors(
            tmp_path,
            "instanceArtifactMapping:\n  - instance: {identifier: other}\n"
            "    experiment: {identifier: f}\n    validValues: [m1.lp]\n"
            "  - instance: {identifier: model}\n"
            "    experiment: {identifier: g}\n    validValues: [nope.lp]\n",
        )
        assert "unknown instance artifact 'other'" in errs
        assert "'nope.lp'" in errs

    def test_duplicate_binding_identifier_fails(self, tmp_path: Path) -> None:
        from algorithm_nexus.commands.validate import validate_bindings

        exps, benches = self._setup(tmp_path, "")
        b = exps / "e1" / "bindings"
        (b / "c.yaml").write_text((b / "b.yaml").read_text())
        results = validate_bindings(exps, benches)
        assert [r["status"] for r in results] == ["success", "failed"]
        assert "already used" in " ".join(results[1]["errors"])

    def test_validate_experiments_command_reports_binding_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`nexus validate experiments` validates bindings and fails on errors."""
        from typer.testing import CliRunner

        from algorithm_nexus.cli import app
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager
        from algorithm_nexus.models import ValidationReport

        monkeypatch.setattr(
            BenchmarkManager,
            "validate",
            lambda self, **kw: ValidationReport(
                instances=[], successful=0, failed=0, total=0
            ),
        )
        exps, benches = self._setup(tmp_path, "")
        runner = CliRunner()
        args = [
            "validate",
            "experiments",
            "--experiments-root",
            str(exps),
            "--benchmarks-root",
            str(benches),
        ]
        assert runner.invoke(app, args).exit_code == 0

        f = exps / "e1" / "bindings" / "b.yaml"
        f.write_text(f.read_text().replace("foo/i1", "foo/nope"))
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert "nope" in result.output
