# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for validate_logical_benchmark_file."""

from pathlib import Path

from algorithm_nexus.commands.utils import ValidationErrorCollector
from algorithm_nexus.commands.validate import validate_logical_benchmark_file

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
    def test_missing_required_field_fails(self) -> None:
        """A file missing required fields (description, target) returns None with errors."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_missing_required_field.yaml", collector
        )

        assert result is None
        assert collector.has_errors
        # Both missing fields should be reported
        error_text = " ".join(collector.errors)
        assert "description" in error_text
        assert "target" in error_text

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

    def test_binding_identifier_mismatch_fails(self) -> None:
        """A binding whose benchmarkIdentifier differs from the definition is an integrity error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "invalid_binding_id_mismatch.yaml", collector
        )

        assert result is not None
        assert collector.has_errors
        error_text = " ".join(collector.errors)
        assert "wrong_benchmark_id" in error_text
        assert "inference_serving" in error_text

    def test_metric_mapping_allowed_when_no_metrics_defined(self) -> None:
        """metricMapping with no metrics defined in the definition does not raise an error."""
        collector = ValidationErrorCollector()
        result = validate_logical_benchmark_file(
            FIXTURES / "valid_metric_mapping_no_metrics_defined.yaml", collector
        )

        # No metrics defined → metric_ids is None → no integrity check is performed
        assert result is not None
        assert not collector.has_errors
