# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for run command helper functions."""

from pathlib import Path

import pytest
from ado.core.operation.config import (
    DiscoveryOperationEnum,
    DiscoveryOperationResourceConfiguration,
)

from algorithm_nexus.commands.benchmark_manager import (
    BenchmarkManager,
    create_random_walk_operation_config,
)
from algorithm_nexus.models import BenchmarkExecutionResult


class TestParseInstancePath:
    """Tests for _parse_submission_path method."""

    def test_parse_experiment_submission(self) -> None:
        """Test parsing an experiment submission path."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        experiment, model, instance = manager._parse_submission_path(
            Path("experiments/sorting_algorithms/submissions/bubble_sort")
        )

        assert experiment == "sorting_algorithms"
        assert model == "base"
        assert instance == "bubble_sort"

    def test_parse_invalid_path_too_short(self) -> None:
        """Test parsing fails for path that's too short."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark submission path format",
        ):
            manager._parse_submission_path(Path("experiments"))

    def test_parse_invalid_path_missing_submissions(self) -> None:
        """Test parsing fails when 'submissions' segment is absent."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark submission path format",
        ):
            manager._parse_submission_path(
                Path("experiments/sorting_algorithms/bubble_sort")
            )

    def test_parse_invalid_path_old_packages_format(self) -> None:
        """Test that old packages/<pkg>/benchmark_submissions/<sub> paths are rejected."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark submission path format",
        ):
            manager._parse_submission_path(
                Path("packages/terratorch/benchmark_submissions/base-test")
            )


class TestFindBenchmarkInstances:
    """Tests for find_benchmark_submissions method."""

    def test_find_experiment_submission(self) -> None:
        """Test finding an experiment submission from changed files."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml",
            "experiments/sorting_algorithms/submissions/bubble_sort/operation.yaml",
            "experiments/sorting_algorithms/experiment_package.yaml",
        ]

        instances = manager.find_benchmark_submissions(changed_files)

        assert len(instances) == 1
        assert instances[0] == Path(
            "experiments/sorting_algorithms/submissions/bubble_sort"
        )

    def test_find_multiple_experiment_submissions(self) -> None:
        """Test finding multiple experiment submissions from changed files."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml",
            "experiments/sorting_algorithms/submissions/merge_sort/space.yaml",
            "experiments/qubit_routing/submissions/run1/space.yaml",
        ]

        instances = manager.find_benchmark_submissions(changed_files)

        assert len(instances) == 3
        assert (
            Path("experiments/sorting_algorithms/submissions/bubble_sort") in instances
        )
        assert (
            Path("experiments/sorting_algorithms/submissions/merge_sort") in instances
        )
        assert Path("experiments/qubit_routing/submissions/run1") in instances

    def test_find_no_instances(self) -> None:
        """Test when no benchmark instances are found."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "packages/terratorch/models/prithvi/model.yaml",
            "packages/terratorch/nexus.yaml",
            "experiments/sorting_algorithms/experiment_package.yaml",
            "README.md",
        ]

        instances = manager.find_benchmark_submissions(changed_files)

        assert len(instances) == 0

    def test_find_instances_deduplicates(self) -> None:
        """Test that duplicate instances are deduplicated."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml",
            "experiments/sorting_algorithms/submissions/bubble_sort/config.json",
            "experiments/sorting_algorithms/submissions/bubble_sort/data.csv",
        ]

        instances = manager.find_benchmark_submissions(changed_files)

        assert len(instances) == 1


class TestCreateRandomWalkOperationConfig:
    """Tests for create_random_walk_operation_config function."""

    def test_create_basic_config(self) -> None:
        """Test creating basic operation config."""
        config: DiscoveryOperationResourceConfiguration = (
            create_random_walk_operation_config(space_id="test-space-123")
        )

        assert config.spaces == ["test-space-123"]
        assert config.metadata.name == "randomwalk-all"
        assert (
            config.metadata.description
            == "Perform a random walk on all points in a space"
        )
        assert config.operation.module.operatorName == "random_walk"
        assert config.operation.module.operationType == DiscoveryOperationEnum.EXPLORE
        assert config.operation.parameters.numberEntities == "all"
        assert config.operation.parameters.singleMeasurement is True

    def test_create_config_with_custom_metadata(self) -> None:
        """Test creating config with custom metadata."""
        custom_meta = {
            "algorithm-nexus.pr_url": "https://github.com/test/repo/pull/123",
            "algorithm-nexus.submission_path": "packages/test/benchmark_submissions/test",
        }

        config: DiscoveryOperationResourceConfiguration = (
            create_random_walk_operation_config(
                space_id="test-space-123",
                metadata_name="custom-walk",
                metadata_description="Custom walk description",
                custom_metadata=custom_meta,
            )
        )

        assert config.metadata.name == "custom-walk"
        assert config.metadata.description == "Custom walk description"
        # Custom metadata is stored in the labels field
        assert config.metadata.labels is not None
        assert (
            config.metadata.labels["algorithm-nexus.pr_url"]
            == "https://github.com/test/repo/pull/123"
        )
        assert (
            config.metadata.labels["algorithm-nexus.submission_path"]
            == "packages/test/benchmark_submissions/test"
        )


class TestBenchmarkExecutionResult:
    """Tests for BenchmarkExecutionResult model."""

    def test_create_with_defaults(self) -> None:
        """Test creating result with default values."""
        result = BenchmarkExecutionResult(
            submission_path="packages/test/benchmark_submissions/test"
        )

        assert result.submission_path == "packages/test/benchmark_submissions/test"
        assert result.status == "unknown"
        assert result.message == ""
        assert result.space_id is None
        assert result.operation_id is None
        assert result.ray_job_id is None

    def test_create_with_all_fields(self) -> None:
        """Test creating result with all fields."""
        result = BenchmarkExecutionResult(
            submission_path="packages/test/benchmark_submissions/test",
            status="success",
            message="Successfully executed",
            space_id="space-123",
            operation_id="op-456",
            ray_job_id="raysubmit_789",
        )

        assert result.status == "success"
        assert result.message == "Successfully executed"
        assert result.space_id == "space-123"
        assert result.operation_id == "op-456"
        assert result.ray_job_id == "raysubmit_789"

    def test_status_literal_validation(self) -> None:
        """Test that status field only accepts valid literals."""
        # Valid statuses
        for status in ["success", "failed", "started", "unknown"]:
            result = BenchmarkExecutionResult(
                submission_path="test",
                status=status,  # type: ignore[arg-type]
            )
            assert result.status == status

    def test_model_dump(self) -> None:
        """Test converting model to dictionary."""
        result = BenchmarkExecutionResult(
            submission_path="packages/test/benchmark_submissions/test",
            status="success",
            space_id="space-123",
        )

        data = result.model_dump()

        assert isinstance(data, dict)
        assert data["submission_path"] == "packages/test/benchmark_submissions/test"
        assert data["status"] == "success"
        assert data["space_id"] == "space-123"
        assert data["operation_id"] is None


# Made with Bob
