# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for CLI list and get commands."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from algorithm_nexus.cli import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.fixture
def fixtures_root() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "packages"


class TestListPackages:
    """Tests for 'nexus list packages' command."""

    def test_list_packages_default(self, fixtures_root: Path) -> None:
        """Test listing packages with default table output."""
        result = runner.invoke(app, ["list", "packages", str(fixtures_root)])

        assert result.exit_code == 0
        assert "Discovered Nexus Packages" in result.stdout
        assert "example-nexus-package" in result.stdout
        assert "test-package-benchmarks" in result.stdout
        assert "Total:" in result.stdout

    def test_list_packages_json_output(self, fixtures_root: Path) -> None:
        """Test listing packages with JSON output."""
        result = runner.invoke(
            app, ["list", "packages", str(fixtures_root), "-o", "json"]
        )

        assert result.exit_code == 0
        # Strip ANSI codes for comparison
        clean_output = strip_ansi(result.stdout)
        assert '"Nexus Package": "example-nexus-package"' in clean_output
        assert '"Nexus Package": "test-package-benchmarks"' in clean_output

    def test_list_packages_csv_output(self, fixtures_root: Path) -> None:
        """Test listing packages with CSV output."""
        result = runner.invoke(
            app, ["list", "packages", str(fixtures_root), "-o", "csv"]
        )

        assert result.exit_code == 0
        assert "Nexus Package" in result.stdout
        assert "example-nexus-package" in result.stdout
        assert "test-package-benchmarks" in result.stdout

    def test_list_packages_json_to_file(
        self, fixtures_root: Path, tmp_path: Path
    ) -> None:
        """Test listing packages with JSON output to file."""
        output_file = tmp_path / "packages.json"
        result = runner.invoke(
            app,
            [
                "list",
                "packages",
                str(fixtures_root),
                "-o",
                "json",
                "--output-file",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert '"Nexus Package": "example-nexus-package"' in content

    def test_list_packages_csv_to_file(
        self, fixtures_root: Path, tmp_path: Path
    ) -> None:
        """Test listing packages with CSV output to file."""
        output_file = tmp_path / "packages.csv"
        result = runner.invoke(
            app,
            [
                "list",
                "packages",
                str(fixtures_root),
                "-o",
                "csv",
                "--output-file",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Nexus Package" in content
        assert "example-nexus-package" in content

    def test_list_packages_invalid_format(self, fixtures_root: Path) -> None:
        """Test listing packages with invalid output format."""
        result = runner.invoke(
            app, ["list", "packages", str(fixtures_root), "-o", "xml"]
        )

        assert result.exit_code == 1
        assert "Invalid output format" in result.stdout

    def test_list_packages_nonexistent_directory(self) -> None:
        """Test listing packages from nonexistent directory."""
        result = runner.invoke(app, ["list", "packages", "/nonexistent/path"])

        assert result.exit_code == 1
        assert "not a directory" in result.stdout

    def test_list_packages_skips_invalid_packages(self, fixtures_root: Path) -> None:
        """Test that invalid packages are silently skipped."""
        result = runner.invoke(app, ["list", "packages", str(fixtures_root)])

        assert result.exit_code == 0
        # Should not include invalid-package directory name
        # (test-invalid-benchmarks is the package name from invalid-package-benchmarks/nexus.yaml)
        # Should show valid packages
        assert "example-nexus-package" in result.stdout
        assert "test-package-benchmarks" in result.stdout


class TestListBenchmarkPackages:
    """Tests for 'nexus list benchmark-packages' command."""

    def test_list_benchmark_packages_default(self, fixtures_root: Path) -> None:
        """Test listing benchmark packages with default table output."""
        result = runner.invoke(app, ["list", "benchmark-packages", str(fixtures_root)])

        assert result.exit_code == 0
        assert "Discovered Benchmark Packages" in result.stdout
        assert "Total:" in result.stdout

    def test_list_benchmark_packages_with_filter(self, fixtures_root: Path) -> None:
        """Test listing benchmark packages filtered by nexus package."""
        result = runner.invoke(
            app,
            [
                "list",
                "benchmark-packages",
                str(fixtures_root),
                "--nexus-package",
                "test-package-benchmarks",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Benchmark Packages for Nexus Package: test-package-benchmarks"
            in result.stdout
        )

    def test_list_benchmark_packages_filter_not_found(
        self, fixtures_root: Path
    ) -> None:
        """Test filtering by nonexistent nexus package."""
        result = runner.invoke(
            app,
            [
                "list",
                "benchmark-packages",
                str(fixtures_root),
                "--nexus-package",
                "nonexistent-package",
            ],
        )

        assert result.exit_code == 0
        assert "No benchmark packages found" in result.stdout

    def test_list_benchmark_packages_json_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark packages with JSON output."""
        result = runner.invoke(
            app, ["list", "benchmark-packages", str(fixtures_root), "-o", "json"]
        )

        assert result.exit_code == 0
        # Should be valid JSON (after stripping ANSI codes)
        clean_output = strip_ansi(result.stdout)
        assert clean_output.startswith("[")

    def test_list_benchmark_packages_csv_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark packages with CSV output."""
        result = runner.invoke(
            app, ["list", "benchmark-packages", str(fixtures_root), "-o", "csv"]
        )

        assert result.exit_code == 0
        assert "Benchmark Package" in result.stdout


class TestListBenchmarkExperiments:
    """Tests for 'nexus list benchmark-experiments' command."""

    def test_list_benchmark_experiments_default(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with default table output."""
        result = runner.invoke(
            app, ["list", "benchmark-experiments", str(fixtures_root)]
        )

        assert result.exit_code == 0
        assert "Discovered Benchmark Experiments" in result.stdout
        assert "Total:" in result.stdout
        assert "For further details" in result.stdout

    def test_list_benchmark_experiments_with_filter(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments filtered by nexus package."""
        result = runner.invoke(
            app,
            [
                "list",
                "benchmark-experiments",
                str(fixtures_root),
                "--nexus-package",
                "test-package-benchmarks",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Benchmark Experiments for Nexus Package: test-package-benchmarks"
            in result.stdout
        )

    def test_list_benchmark_experiments_filter_not_found(
        self, fixtures_root: Path
    ) -> None:
        """Test filtering by nonexistent nexus package."""
        result = runner.invoke(
            app,
            [
                "list",
                "benchmark-experiments",
                str(fixtures_root),
                "--nexus-package",
                "nonexistent-package",
            ],
        )

        assert result.exit_code == 0
        assert "No benchmark experiments found" in result.stdout

    def test_list_benchmark_experiments_json_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with JSON output."""
        result = runner.invoke(
            app, ["list", "benchmark-experiments", str(fixtures_root), "-o", "json"]
        )

        assert result.exit_code == 0
        # Should be valid JSON (after stripping ANSI codes)
        clean_output = strip_ansi(result.stdout)
        assert clean_output.startswith("[")

    def test_list_benchmark_experiments_csv_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with CSV output."""
        result = runner.invoke(
            app, ["list", "benchmark-experiments", str(fixtures_root), "-o", "csv"]
        )

        assert result.exit_code == 0
        assert "Experiment ID" in result.stdout
        assert "Benchmark Package" in result.stdout


class TestGetBenchmarkRequirements:
    """Tests for 'nexus get benchmark-requirements' command."""

    def test_get_benchmark_requirements_default(self, fixtures_root: Path) -> None:
        """Test getting benchmark requirements with default table output."""
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "test-package-benchmarks",
                str(fixtures_root),
            ],
        )

        assert result.exit_code == 0
        assert (
            "Benchmark Requirements for Nexus Package: test-package-benchmarks"
            in result.stdout
        )
        assert "Total:" in result.stdout

    def test_get_benchmark_requirements_txt_output(self, fixtures_root: Path) -> None:
        """Test getting benchmark requirements with txt output."""
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "test-package-benchmarks",
                str(fixtures_root),
                "-o",
                "txt",
            ],
        )

        assert result.exit_code == 0
        # Should output requirements in txt format (one per line)
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0

    def test_get_benchmark_requirements_txt_to_file(
        self, fixtures_root: Path, tmp_path: Path
    ) -> None:
        """Test getting benchmark requirements with txt output to file."""
        output_file = tmp_path / "requirements.txt"
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "test-package-benchmarks",
                str(fixtures_root),
                "-o",
                "txt",
                "--output-file",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content.strip()) > 0

    def test_get_benchmark_requirements_package_not_found(
        self, fixtures_root: Path
    ) -> None:
        """Test getting requirements for nonexistent package."""
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "nonexistent-package",
                str(fixtures_root),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_get_benchmark_requirements_no_benchmarks(
        self, fixtures_root: Path
    ) -> None:
        """Test getting requirements for package without benchmarks."""
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "example-nexus-package",
                str(fixtures_root),
            ],
        )

        assert result.exit_code == 0
        assert "No benchmark packages found" in result.stdout

    def test_get_benchmark_requirements_invalid_format(
        self, fixtures_root: Path
    ) -> None:
        """Test getting requirements with invalid output format."""
        result = runner.invoke(
            app,
            [
                "get",
                "benchmark-requirements",
                "test-package-benchmarks",
                str(fixtures_root),
                "-o",
                "json",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid output format" in result.stdout


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_packages_directory(self, tmp_path: Path) -> None:
        """Test commands with empty packages directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(app, ["list", "packages", str(empty_dir)])
        assert result.exit_code == 0
        assert "No Nexus packages found" in result.stdout

    def test_list_with_only_invalid_packages(self, fixtures_root: Path) -> None:
        """Test listing when only invalid packages exist."""
        # Create a temporary directory with only invalid package
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_src = fixtures_root / "invalid-package"
            invalid_dst = Path(tmpdir) / "invalid-package"
            shutil.copytree(invalid_src, invalid_dst)

            result = runner.invoke(app, ["list", "packages", tmpdir])
            assert result.exit_code == 0
            assert "No Nexus packages found" in result.stdout


# Made with Bob
