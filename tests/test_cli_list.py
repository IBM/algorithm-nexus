# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for CLI list commands."""

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


@pytest.fixture
def experiments_root() -> Path:
    """Return the path to the test experiments fixtures directory."""
    return Path(__file__).parent / "fixtures" / "experiments"


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

    def test_list_packages_warns_on_bad_yaml(self, tmp_path: Path) -> None:
        """Test that a nexus.yaml with invalid content always warns on stderr."""
        pkg_dir = tmp_path / "bad-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "nexus.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

        result = runner.invoke(
            app, ["list", "packages", str(tmp_path)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "Warning" in result.output or "Warning" in (result.stderr or "")

    def test_list_packages_strict_exits_on_bad_yaml(self, tmp_path: Path) -> None:
        """Test that --strict causes exit 1 when a nexus.yaml fails to load."""
        pkg_dir = tmp_path / "bad-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "nexus.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

        result = runner.invoke(
            app, ["list", "packages", str(tmp_path), "--strict"], catch_exceptions=False
        )

        assert result.exit_code == 1

    def test_list_packages_strict_passes_when_all_valid(
        self, fixtures_root: Path
    ) -> None:
        """Test that --strict exits 0 when all packages load successfully."""
        # Use a directory containing only valid packages
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            valid_src = fixtures_root / "valid-package"
            shutil.copytree(valid_src, Path(tmpdir) / "valid-package")

            result = runner.invoke(app, ["list", "packages", tmpdir, "--strict"])
            assert result.exit_code == 0


class TestListExperimentPackages:
    """Tests for 'nexus list experiment-packages' command."""

    def test_list_experiment_packages_default(self, experiments_root: Path) -> None:
        """Test listing experiment packages with default table output."""
        result = runner.invoke(
            app,
            ["list", "experiment-packages", str(experiments_root)],
            env={"COLUMNS": "200"},
        )

        assert result.exit_code == 0
        assert "Discovered Experiment Packages" in result.stdout
        assert "vllm-performance" in result.stdout
        assert "ado-vllm-performance" in result.stdout
        assert "Total:" in result.stdout

    def test_list_experiment_packages_shows_folder(
        self, experiments_root: Path
    ) -> None:
        """Test that the experiment folder is shown in output."""
        result = runner.invoke(
            app,
            ["list", "experiment-packages", str(experiments_root)],
            env={"COLUMNS": "200"},
        )

        assert result.exit_code == 0
        assert "Experiment Folder" in result.stdout
        assert "vllm-performance" in result.stdout

    def test_list_experiment_packages_json_output(self, experiments_root: Path) -> None:
        """Test listing experiment packages with JSON output."""
        result = runner.invoke(
            app,
            ["list", "experiment-packages", str(experiments_root), "-o", "json"],
        )

        assert result.exit_code == 0
        clean_output = strip_ansi(result.stdout)
        assert clean_output.startswith("[")
        assert "vllm-performance" in clean_output
        assert "Experiment Folder" in clean_output

    def test_list_experiment_packages_csv_output(self, experiments_root: Path) -> None:
        """Test listing experiment packages with CSV output."""
        result = runner.invoke(
            app,
            ["list", "experiment-packages", str(experiments_root), "-o", "csv"],
        )

        assert result.exit_code == 0
        assert "Experiment Folder" in result.stdout
        assert "Requirement Specifier" in result.stdout
        assert "Experiments" in result.stdout
        assert "Bindings" in result.stdout

    def test_list_experiment_packages_nonexistent_directory(self) -> None:
        """Test listing experiment packages from nonexistent directory."""
        result = runner.invoke(
            app, ["list", "experiment-packages", "/nonexistent/path"]
        )

        assert result.exit_code == 1
        assert "not a directory" in result.stdout

    def test_list_experiment_packages_empty_directory(self, tmp_path: Path) -> None:
        """Test listing experiment packages from empty directory."""
        empty_dir = tmp_path / "experiments"
        empty_dir.mkdir()
        result = runner.invoke(app, ["list", "experiment-packages", str(empty_dir)])

        assert result.exit_code == 0
        assert "No experiment packages found" in result.stdout

    def test_list_experiment_packages_with_bindings(self, tmp_path: Path) -> None:
        """Test listing experiment packages shows associated bindings."""
        experiments_root = tmp_path / "experiments"
        exp_dir = experiments_root / "my-experiment"
        exp_dir.mkdir(parents=True)

        (exp_dir / "experiment_package.yaml").write_text(
            "experiment_package:\n"
            "  requirement_specifier: my-package>=1.0\n"
            "  experiments:\n"
            "    - exp_id_1\n"
            "    - exp_id_2\n",
            encoding="utf-8",
        )

        bindings_dir = exp_dir / "bindings"
        bindings_dir.mkdir()
        (bindings_dir / "my_binding.yaml").write_text(
            "instanceBindingIdentifier: my_binding\n"
            "instanceReference: my_logical_benchmark/instance_1\n"
            "experiment:\n"
            "  experimentIdentifier: exp_id_1\n"
            "  actuatorIdentifier: my_actuator\n"
            "  experimentVersion: 1.0.0\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["list", "experiment-packages", str(experiments_root)],
            env={"COLUMNS": "200"},
        )

        assert result.exit_code == 0
        assert "my-experiment" in result.stdout
        assert "my-package>=1.0" in result.stdout
        assert "my_logical_benchmark" in result.stdout


class TestListBenchmarkExperiments:
    """Tests for 'nexus list experiments' command."""

    def test_list_benchmark_experiments_default(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with default table output."""
        experiments_root = fixtures_root.parent / "experiments"
        result = runner.invoke(
            app,
            ["list", "experiments", str(experiments_root)],
            env={"COLUMNS": "160"},
        )

        assert result.exit_code == 0
        assert "Discovered Benchmark Experiments" in result.stdout
        assert "vllm-bench-deployment" in result.stdout
        assert "guidellm-bench-deployment" in result.stdout
        assert "vllm-performance" in result.stdout
        assert "ado-vllm-performance" in result.stdout
        assert "Total:" in result.stdout
        assert "For further details" in result.stdout

    def test_list_benchmark_experiments_json_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with JSON output."""
        experiments_root = fixtures_root.parent / "experiments"
        result = runner.invoke(
            app, ["list", "experiments", str(experiments_root), "-o", "json"]
        )

        assert result.exit_code == 0
        # Should be valid JSON (after stripping ANSI codes)
        clean_output = strip_ansi(result.stdout)
        assert clean_output.startswith("[")
        assert "vllm-bench-deployment" in clean_output

    def test_list_benchmark_experiments_csv_output(self, fixtures_root: Path) -> None:
        """Test listing benchmark experiments with CSV output."""
        experiments_root = fixtures_root.parent / "experiments"
        result = runner.invoke(
            app, ["list", "experiments", str(experiments_root), "-o", "csv"]
        )

        assert result.exit_code == 0
        assert "Experiment ID" in result.stdout
        assert "Experiment Folder" in result.stdout
        assert "Requirement Specifier" in result.stdout
        assert "vllm-bench-deployment" in result.stdout

    def test_list_benchmark_experiments_with_bindings(self, tmp_path: Path) -> None:
        """Test listing benchmark experiments with logical benchmark bindings."""
        experiments_root = tmp_path / "experiments"
        exp_dir = experiments_root / "my-experiment"
        exp_dir.mkdir(parents=True)

        # Write experiment_package.yaml
        (exp_dir / "experiment_package.yaml").write_text(
            "experiment_package:\n"
            "  requirement_specifier: my-package\n"
            "  experiments:\n"
            "    - exp_id_1\n"
            "    - exp_id_2\n",
            encoding="utf-8",
        )

        # Write binding file under bindings/
        bindings_dir = exp_dir / "bindings"
        bindings_dir.mkdir()
        (bindings_dir / "my_binding.yaml").write_text(
            "instanceBindingIdentifier: my_binding\n"
            "instanceReference: my_logical_benchmark/instance_1\n"
            "experiment:\n"
            "  experimentIdentifier: exp_id_1\n"
            "  actuatorIdentifier: my_actuator\n"
            "  experimentVersion: 1.0.0\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["list", "experiments", str(experiments_root)],
            env={"COLUMNS": "160"},
        )

        assert result.exit_code == 0
        assert "exp_id_1" in result.stdout
        assert "exp_id_2" in result.stdout
        assert "my-experiment" in result.stdout


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
