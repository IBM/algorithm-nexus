# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for run command helper functions."""

from pathlib import Path

import pytest

from algorithm_nexus.commands.run import (
    BenchmarkManager,
    create_random_walk_operation_config,
)
from algorithm_nexus.models import BenchmarkExecutionResult


class TestParseInstancePath:
    """Tests for _parse_instance_path method."""

    def test_parse_model_level_instance(self) -> None:
        """Test parsing model-level benchmark instance path."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        package, model, instance = manager._parse_instance_path(
            Path("packages/terratorch/models/prithvi/benchmark_instances/flood-test")
        )

        assert package == "terratorch"
        assert model == "prithvi"
        assert instance == "flood-test"

    def test_parse_package_level_instance(self) -> None:
        """Test parsing package-level benchmark instance path."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        package, model, instance = manager._parse_instance_path(
            Path("packages/terratorch/benchmark_instances/base-test")
        )

        assert package == "terratorch"
        assert model == "base"
        assert instance == "base-test"

    def test_parse_invalid_path_too_short(self) -> None:
        """Test parsing fails for path that's too short."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark instance path format",
        ):
            manager._parse_instance_path(Path("packages"))

    def test_parse_invalid_model_level_path(self) -> None:
        """Test parsing fails for incomplete model-level path."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark instance path format",
        ):
            manager._parse_instance_path(
                Path("packages/terratorch/models/prithvi/benchmark_instances")
            )

    def test_parse_invalid_package_level_path(self) -> None:
        """Test parsing fails for incomplete package-level path."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        with pytest.raises(
            ValueError,
            match="Invalid benchmark instance path format",
        ):
            manager._parse_instance_path(
                Path("packages/terratorch/benchmark_instances")
            )


class TestFindBenchmarkInstances:
    """Tests for find_benchmark_instances method."""

    def test_find_model_level_instances(self) -> None:
        """Test finding model-level benchmark instances from changed files."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/flood-test/space.yaml",
            "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/flood-test/config.json",
            "tests/fixtures/packages/terratorch/models/prithvi/model.yaml",
        ]

        instances = manager.find_benchmark_instances(changed_files)

        assert len(instances) == 1
        assert instances[0] == Path(
            "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/flood-test"
        )

    def test_find_package_level_instances(self) -> None:
        """Test finding package-level benchmark instances from changed files."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "tests/fixtures/packages/terratorch/benchmark_instances/base-test/space.yaml",
            "tests/fixtures/packages/terratorch/nexus.yaml",
        ]

        instances = manager.find_benchmark_instances(changed_files)

        assert len(instances) == 1
        assert instances[0] == Path(
            "tests/fixtures/packages/terratorch/benchmark_instances/base-test"
        )

    def test_find_multiple_instances(self) -> None:
        """Test finding multiple benchmark instances."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/flood-test/space.yaml",
            "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/fire-test/space.yaml",
            "tests/fixtures/packages/tokamind/benchmark_instances/base-test/space.yaml",
        ]

        instances = manager.find_benchmark_instances(changed_files)

        assert len(instances) == 3
        assert (
            Path(
                "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/flood-test"
            )
            in instances
        )
        assert (
            Path(
                "tests/fixtures/packages/terratorch/models/prithvi/benchmark_instances/fire-test"
            )
            in instances
        )
        assert (
            Path("tests/fixtures/packages/tokamind/benchmark_instances/base-test")
            in instances
        )

    def test_find_no_instances(self) -> None:
        """Test when no benchmark instances are found."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "packages/terratorch/models/prithvi/model.yaml",
            "packages/terratorch/nexus.yaml",
            "README.md",
        ]

        instances = manager.find_benchmark_instances(changed_files)

        assert len(instances) == 0

    def test_find_instances_deduplicates(self) -> None:
        """Test that duplicate instances are deduplicated."""
        manager = BenchmarkManager(
            pr_url="https://github.com/test/repo/pull/123", execute=False
        )

        changed_files = [
            "packages/terratorch/models/prithvi/benchmark_instances/flood-test/space.yaml",
            "packages/terratorch/models/prithvi/benchmark_instances/flood-test/config.json",
            "packages/terratorch/models/prithvi/benchmark_instances/flood-test/data.csv",
        ]

        instances = manager.find_benchmark_instances(changed_files)

        assert len(instances) == 1


class TestCreateRandomWalkOperationConfig:
    """Tests for create_random_walk_operation_config function."""

    def test_create_basic_config(self) -> None:
        """Test creating basic operation config."""
        config = create_random_walk_operation_config(space_id="test-space-123")

        assert config["spaces"] == ["test-space-123"]
        assert config["metadata"]["name"] == "randomwalk-all"
        assert (
            config["metadata"]["description"]
            == "Perform a random walk on all points in a space"
        )
        assert config["operation"]["module"]["operatorName"] == "random_walk"
        assert config["operation"]["module"]["operationType"] == "search"
        assert config["operation"]["parameters"]["numberEntities"] == "all"
        assert config["operation"]["parameters"]["singleMeasurement"] is True

    def test_create_config_with_custom_metadata(self) -> None:
        """Test creating config with custom metadata."""
        custom_meta = {
            "algorithm-nexus.pr_url": "https://github.com/test/repo/pull/123",
            "algorithm-nexus.instance_path": "packages/test/benchmark_instances/test",
        }

        config = create_random_walk_operation_config(
            space_id="test-space-123",
            metadata_name="custom-walk",
            metadata_description="Custom walk description",
            custom_metadata=custom_meta,
        )

        assert config["metadata"]["name"] == "custom-walk"
        assert config["metadata"]["description"] == "Custom walk description"
        # Custom metadata is stored in the labels field
        assert (
            config["metadata"]["labels"]["algorithm-nexus.pr_url"]
            == "https://github.com/test/repo/pull/123"
        )
        assert (
            config["metadata"]["labels"]["algorithm-nexus.instance_path"]
            == "packages/test/benchmark_instances/test"
        )


class TestBenchmarkExecutionResult:
    """Tests for BenchmarkExecutionResult model."""

    def test_create_with_defaults(self) -> None:
        """Test creating result with default values."""
        result = BenchmarkExecutionResult(
            instance_path="packages/test/benchmark_instances/test"
        )

        assert result.instance_path == "packages/test/benchmark_instances/test"
        assert result.status == "unknown"
        assert result.message == ""
        assert result.space_id is None
        assert result.operation_id is None
        assert result.ray_job_id is None

    def test_create_with_all_fields(self) -> None:
        """Test creating result with all fields."""
        result = BenchmarkExecutionResult(
            instance_path="packages/test/benchmark_instances/test",
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
                instance_path="test",
                status=status,  # type: ignore[arg-type]
            )
            assert result.status == status

    def test_model_dump(self) -> None:
        """Test converting model to dictionary."""
        result = BenchmarkExecutionResult(
            instance_path="packages/test/benchmark_instances/test",
            status="success",
            space_id="space-123",
        )

        data = result.model_dump()

        assert isinstance(data, dict)
        assert data["instance_path"] == "packages/test/benchmark_instances/test"
        assert data["status"] == "success"
        assert data["space_id"] == "space-123"
        assert data["operation_id"] is None


# Made with Bob
