# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Pydantic models."""

from textwrap import dedent

import pytest
import yaml
from ado.schema.reference import ExperimentReference
from pydantic import ValidationError

from algorithm_nexus.models import (
    AlgorithmNexusModelConfig,
    AlgorithmNexusPackageConfig,
    BenchmarkInstance,
    BindingFileConfig,
    ExperimentConfig,
    InstanceBinding,
    LogicalBenchmarkDefinition,
    ModelInfo,
    NexusPackageInfo,
    Property,
    VLLMConfig,
)


class TestPackageConfig:
    """Tests for PackageConfig model."""

    def test_valid_package_config(self) -> None:
        """Test valid package configuration."""
        data = {
            "name": "test-package",
        }
        config = NexusPackageInfo.model_validate(data)
        assert config.name == "test-package"

    def test_missing_name(self) -> None:
        """Test that missing name is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            NexusPackageInfo.model_validate(data)
        assert "name" in str(exc_info.value)


class TestVLLMConfig:
    """Tests for VLLMConfig model."""

    def test_vllm_with_plugins(self) -> None:
        """Test vLLM with plugins."""
        data = {
            "enabled": True,
            "plugins": {"io_processors": ["processor1", "processor2"]},
        }
        config = VLLMConfig.model_validate(data)

        assert config.enabled is True
        assert config.plugins is not None
        assert len(config.plugins.io_processors) == 2

    def test_vllm_with_general_plugin(self) -> None:
        """Test vLLM with general plugin."""
        data = {
            "enabled": True,
            "plugins": {"general": "my-vllm-plugin"},
        }
        config = VLLMConfig.model_validate(data)

        assert config.enabled is True
        assert config.plugins is not None
        assert config.plugins.general == "my-vllm-plugin"

    def test_vllm_disabled_fails(self) -> None:
        """Test that enabled=False is rejected."""
        data = {"enabled": False}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig.model_validate(data)

        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_missing_enabled_fails(self) -> None:
        """Test that missing enabled field is detected."""
        data = {"plugins": {"general": "my-plugin"}}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig.model_validate(data)

        assert "enabled" in str(exc_info.value)


class TestModelConfig:
    """Tests for ModelConfig model."""

    def test_valid_model_config(self) -> None:
        """Test valid model configuration."""
        data = {
            "id": "org/model",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"

    def test_model_without_vllm(self) -> None:
        """Test that models without vLLM configuration are valid."""
        data = {
            "id": "org/model",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"
        assert config.vllm is None

    def test_missing_model_id(self) -> None:
        """Test that missing model.id is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            ModelInfo.model_validate(data)

        assert "id" in str(exc_info.value)

    def test_valid_model_ids(self) -> None:
        """Test valid HuggingFace model IDs."""
        valid_ids = [
            "org/model",
            "my-org/my-model",
            "org123/model456",
            "a1/b2",  # minimum length (2 chars each)
            "a" * 42 + "/" + "b" * 42,  # maximum length for org (42 chars)
            "a" * 42 + "/" + "b" * 96,  # maximum length for model (96 chars)
            "user-name/model-name",
            "org1-2/model3-4",
            "org/model-1.0",  # model with version number
            "org/model-2.0.1",  # model with semantic version
            "ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL",  # real-world example
            "org.name/model.name",  # dots in both parts
            "org/model.1.2.3-beta",  # complex version with dots and dash
            "org/model_name",  # underscore in model name
            "org_name/model_name",  # underscores in both parts
            "org/model_v1.0",  # underscore and dot in model
            "org/my_model-2.0",  # combination of underscore, dash, and dot in model
            "org_name/model",  # underscore in org name
            "org.name/model",  # dot in org name
            "my_org.v2/model",  # underscore and dot in org name
            "org.v1_test/model-name",  # dots and underscores in org
        ]
        for model_id in valid_ids:
            data = {"id": model_id}
            config = ModelInfo.model_validate(data)

            assert config.id == model_id

    def test_invalid_model_ids(self) -> None:
        """Test invalid HuggingFace model IDs."""
        invalid_ids = [
            "org",  # missing slash and model name
            "/model",  # missing org name
            "org/",  # missing model name
            "-org/model",  # starts with dash
            "org-/model",  # ends with dash
            "org/-model",  # model starts with dash
            "org/model-",  # model ends with dash
            "org--name/model",  # double dash in org
            "org/model--name",  # double dash in model
            "123/456",  # digit-only names
            "123/model",  # digit-only org
            "org/456",  # digit-only model
            "o/model",  # org too short (1 char)
            "org/m",  # model too short (1 char)
            "a" * 43 + "/model",  # org too long (43 chars)
            "org/" + "b" * 97,  # model too long (97 chars)
            "org@name/model",  # illegal character in org
            "org/model@name",  # illegal character in model
            "org name/model",  # space in org
            "org/model name",  # space in model
            "org/model/extra",  # too many slashes
        ]
        for model_id in invalid_ids:
            data = {"id": model_id}
            with pytest.raises(ValidationError) as exc_info:
                ModelInfo.model_validate(data)

            assert "id" in str(exc_info.value).lower()

    def test_model_with_owner(self) -> None:
        """Test model configuration with owner."""
        data = {
            "id": "org/model",
            "owner": "github-username",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"
        assert config.owner == "github-username"

    def test_model_with_invalid_owner_id(self) -> None:
        """Test model configuration with owner."""
        data = {
            "id": "org/model",
        }

        # starts with a dash
        data["owner"] = "-github-username"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # ends with a dash
        data["owner"] = "github-username-"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # scontaines consecutive dashes
        data["owner"] = "github--username"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # contains an illegal character
        data["owner"] = "github-usern@me"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # longer than 39 characters
        data["owner"] = "ThisGitHubUsernameIsDefinitelyTooLongToBeValid"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

    def test_vllm_disabled_fails(self) -> None:
        """Test that vLLM enabled=False is rejected."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": False,
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelInfo.model_validate(data)

        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_with_plugins(self) -> None:
        """Test valid vLLM configuration with plugins."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": True,
                "plugins": {"io_processors": ["processor1"]},
            },
        }
        config = ModelInfo.model_validate(data)

        assert config.vllm is not None
        assert config.vllm.plugins is not None
        assert config.vllm.plugins.io_processors == ["processor1"]


class TestModelYAML:
    """Tests for ModelYAML model."""

    def test_valid_model_yaml(self) -> None:
        """Test valid model.yaml structure."""
        yaml_content = dedent("""
            model:
              id: "org/test-model"
            """)
        data = yaml.safe_load(yaml_content)
        model_yaml = AlgorithmNexusModelConfig.model_validate(data)

        assert model_yaml.model.id == "org/test-model"

    def test_model_yaml_with_vllm(self) -> None:
        """Test model.yaml with vLLM configuration."""
        yaml_content = dedent("""
            model:
              id: "org/test-model"
              vllm:
                enabled: true
                plugins:
                  io_processors:
                    - "processor1"
            """)
        data = yaml.safe_load(yaml_content)
        model_yaml = AlgorithmNexusModelConfig.model_validate(data)

        assert model_yaml.model.vllm is not None
        assert model_yaml.model.vllm.plugins is not None
        assert model_yaml.model.vllm.plugins.io_processors == ["processor1"]


class TestNexusYAML:
    """Tests for NexusYAML model."""

    def test_valid_nexus_yaml(self) -> None:
        """Test valid nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "test-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_yaml.package.name == "test-package"

    def test_nexus_yaml_minimal(self) -> None:
        """Test minimal nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "minimal-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_yaml.package.name == "minimal-package"


class TestLogicalBenchmarkProperties:
    def test_logical_benchmark_problem_properties(self) -> None:
        """Test LogicalBenchmarkDefinition problemProperties field."""
        from algorithm_nexus.models import LogicalBenchmarkDefinition

        data = {
            "benchmarkIdentifier": "test_bench",
            "description": "A test benchmark",
            "problemProperties": [
                {"identifier": "graph"},
                {"identifier": "num_nodes"},
                {"identifier": "density"},
            ],
        }
        config = LogicalBenchmarkDefinition.model_validate(data)
        props = config.problemProperties
        assert len(props) == 3
        assert props[0].identifier == "graph"
        assert props[1].identifier == "num_nodes"
        assert props[2].identifier == "density"

    def test_logical_benchmark_metadata_valid(self) -> None:
        """Test LogicalBenchmarkDefinition with valid metadata."""
        config = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="A test benchmark",
            problemProperties=[Property(identifier="num_nodes")],
            metadata={
                "data_source_version": "v2.1.0",
                "owning_team": "platform-perf",
            },
        )
        assert config.metadata == {
            "data_source_version": "v2.1.0",
            "owning_team": "platform-perf",
        }

    def test_logical_benchmark_metadata_max_length(self) -> None:
        """Test LogicalBenchmarkDefinition metadata allows 4096 character keys and values."""
        long_key = "k" * 4096
        long_val = "v" * 4096
        config = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="A test benchmark",
            problemProperties=[Property(identifier="num_nodes")],
            metadata={long_key: long_val},
        )
        assert config.metadata is not None
        assert config.metadata[long_key] == long_val

    def test_logical_benchmark_metadata_key_too_long(self) -> None:
        """Test LogicalBenchmarkDefinition rejects metadata key longer than 4096 characters."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[Property(identifier="num_nodes")],
                metadata={"k" * 4097: "valid_value"},
            )

    def test_logical_benchmark_metadata_value_too_long(self) -> None:
        """Test LogicalBenchmarkDefinition rejects metadata value longer than 4096 characters."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[Property(identifier="num_nodes")],
                metadata={"valid_key": "v" * 4097},
            )

    def test_logical_benchmark_metadata_non_string_value_rejected(self) -> None:
        """Test LogicalBenchmarkDefinition rejects non-string metadata values."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[Property(identifier="num_nodes")],
                metadata={"nested": {"key": "val"}},  # type: ignore[dict-item]
            )


# Made with Bob


def _pkg(spec: str, *experiments: str | dict) -> dict:
    """Build one experiment_package entry from identifiers or full mappings."""
    return {
        "requirement_specifier": spec,
        "experiments": [
            e if isinstance(e, dict) else {"experimentIdentifier": e}
            for e in experiments
        ],
    }


def _cfg(*packages: dict) -> dict:
    return {"experiment_package": list(packages)}


class TestExperimentConfig:
    """Tests for ExperimentConfig and ExperimentSpecifier models."""

    def test_valid_pypi_specifier(self) -> None:
        """Test valid experiment config with a PyPI package name."""
        config = ExperimentConfig.model_validate(
            _cfg(_pkg("sorting-benchmarks>=1.0.0", "bubble_sort", "merge_sort"))
        )
        assert config.packages[0].requirement_specifier == "sorting-benchmarks>=1.0.0"
        assert config.packages[0].experiment_ids == ["bubble_sort", "merge_sort"]

    def test_valid_github_https_url(self) -> None:
        """Test valid experiment config with a GitHub HTTPS URL."""
        config = ExperimentConfig.model_validate(
            _cfg(_pkg("https://github.com/org/repo.git", "exp_one"))
        )
        assert (
            config.packages[0].requirement_specifier
            == "https://github.com/org/repo.git"
        )

    def test_valid_git_plus_prefix(self) -> None:
        """Test valid experiment config with git+ prefixed URL."""
        config = ExperimentConfig.model_validate(
            _cfg(_pkg("git+https://github.com/org/repo@main", "exp_one"))
        )
        assert (
            config.packages[0].requirement_specifier
            == "git+https://github.com/org/repo@main"
        )

    @pytest.mark.parametrize(
        "spec",
        [
            "sorting-benchmarks",
            "sorting_benchmarks",
            "pkg.name",
            "pkg==1.2.3",
            "pkg>=1.0,<2",
            "pkg >= 1.0, < 2",
            "pkg~=1.4",
            "pkg[ado]",
            "pkg[ado,extra]>=1.0",
            "https://github.com/org/repo",
            "https://github.com/org/repo.git",
            "https://github.ibm.com/org/repo.git",
            "git+https://github.com/org/repo.git@main",
            "git+https://github.com/org/repo.git@21e38a9#egg=pkg",
            "git+ssh://git@github.com/org/repo.git@21e38a9[ado]",
            "ssh://git@github.com/org/repo.git",
            "git@github.com:org/repo.git",
            "git@github.ibm.com/org/repo.git@branch",
            # Every allowed host over every HTTPS and SSH form
            *(
                form.format(host=host)
                for host in (
                    "github.com",
                    "github.ibm.com",
                    "research.github.ibm.com",
                    "GitHub.com",
                )
                for form in (
                    "https://{host}/org/repo",
                    "git+https://{host}/org/repo.git@v1.0",
                    "ssh://git@{host}/org/repo.git",
                    "git+ssh://git@{host}/org/repo.git@main[ado]",
                    "git@{host}:org/repo.git",
                    "git@{host}/org/repo.git@branch",
                )
            ),
        ],
    )
    def test_allowed_specifiers_accepted(self, spec: str) -> None:
        """Test that PyPI names and remote git URLs are accepted."""
        config = ExperimentConfig.model_validate(_cfg(_pkg(spec, "exp_one")))
        assert config.packages[0].requirement_specifier == spec

    @pytest.mark.parametrize(
        "spec",
        [
            # Local paths in every form
            "./packages/my-benchmark",
            "/usr/local/my-pkg",
            "~/my-pkg",
            "experiments/evil",
            "sub/dir",
            "../evil",
            "evil/",
            "C:\\evil",
            "..",
            # file URLs and direct references
            "file:///tmp/evil",
            "git+file:///tmp/evil",
            "pkg @ file:///tmp/evil",
            "pkg @ https://github.com/org/repo",
            # installer option injection
            "--no-deps",
            "--index-url=https://evil.example/simple",
            "-e",
            "-r requirements.txt",
            # plain http, unsupported schemes, missing path
            "http://github.com/org/repo",
            "git+http://github.com/org/repo",
            "ftp://example.com/pkg.tar.gz",
            "https://github.com",
            "https://github.com/",
            # whitespace-separated extra tokens and markers
            "pkg evil",
            "https://github.com/org/repo --no-deps",
            'pkg; python_version < "3.13"',
            # hosts not on the allowlist
            "https://gitlab.com/org/repo",
            "git+https://bitbucket.org/org/repo.git",
            "git@bitbucket.org:org/repo.git",
            "ssh://git@gitlab.com/org/repo.git",
            "https://evil.example/org/repo",
            # look-alike and sub/sibling domains of allowed hosts
            "https://github.com.evil.com/org/repo",
            "https://evilgithub.com/org/repo",
            "https://api.github.com/org/repo",
            "https://raw.github.com/org/repo",
            "https://other.github.ibm.com/org/repo",
            "https://ibm.com/org/repo",
            "git@github.com.evil.com:org/repo.git",
            # allowed host appearing only in the path
            "https://evil.com/github.com/org/repo",
            # user info / credentials in the URL
            "https://github.com@evil.com/org/repo",
            "https://token@github.com/org/repo",
            "https://user:pass@github.ibm.com/org/repo",
            # ports
            "https://github.com:443/org/repo",
            "ssh://git@github.com:22/org/repo.git",
            # SSH user other than git
            "ssh://bob@github.com/org/repo.git",
            "git+ssh://root@github.ibm.com/org/repo.git",
            "bob@github.com:org/repo.git",
            # path that does not start with a normal segment
            "https://github.com//evil",
            "git@github.com:-oProxyCommand=evil",
        ],
    )
    def test_disallowed_specifiers_rejected(self, spec: str) -> None:
        """Test that local paths, file URLs and installer options are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(_cfg(_pkg(spec, "exp_one")))
        assert "invalid requirement_specifier" in str(exc_info.value).lower()

    def test_empty_experiments_list_rejected(self) -> None:
        """Test that an empty experiments list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(_cfg(_pkg("my-package")))
        assert "experiments" in str(exc_info.value).lower()

    def test_missing_requirement_specifier_rejected(self) -> None:
        """Test that missing requirement_specifier is rejected."""
        data = _cfg({"experiments": [{"experimentIdentifier": "exp_one"}]})
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "requirement_specifier" in str(exc_info.value)

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are rejected."""
        pkg = _pkg("my-package", "exp_one")
        pkg["extra_field"] = "not allowed"
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(_cfg(pkg))
        assert "extra_field" in str(exc_info.value).lower()

    def test_extra_top_level_fields_forbidden(self) -> None:
        """Test that extra top-level fields are rejected."""
        data = _cfg(_pkg("my-package", "exp_one"))
        data["unexpected"] = "value"
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "unexpected" in str(exc_info.value).lower()

    def test_valid_metadata(self) -> None:
        """Test valid experiment config with metadata."""
        data = _cfg(_pkg("my-package", "exp_one"))
        data["metadata"] = {"author": "IBM", "tier": "production"}
        config = ExperimentConfig.model_validate(data)
        assert config.metadata == {"author": "IBM", "tier": "production"}

    def test_metadata_value_too_long_rejected(self) -> None:
        """Test that metadata value exceeding 4096 chars is rejected."""
        data = _cfg(_pkg("my-package", "exp_one"))
        data["metadata"] = {"author": "a" * 4097}
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(data)


class TestExperimentPackageList:
    """Tests for multiple packages and versioned experiment entries."""

    def test_old_single_package_format_rejected(self) -> None:
        """experiment_package must be a list of packages."""
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(
                {
                    "experiment_package": {
                        "requirement_specifier": "pkg",
                        "experiments": [{"experimentIdentifier": "e"}],
                    }
                }
            )

    def test_plain_string_experiments_rejected(self) -> None:
        """Experiments must be mappings with an experimentIdentifier."""
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(
                {
                    "experiment_package": [
                        {"requirement_specifier": "pkg", "experiments": ["e"]}
                    ]
                }
            )

    def test_versioned_experiment_entries(self) -> None:
        config = ExperimentConfig.model_validate(
            _cfg(
                _pkg(
                    "pkg",
                    {"experimentIdentifier": "exp_a", "experimentVersion": "1.2.3"},
                    "exp_b",
                )
            )
        )
        entries = config.packages[0].experiment_entries
        assert [(e.experimentIdentifier, e.experimentVersion) for e in entries] == [
            ("exp_a", "1.2.3"),
            ("exp_b", None),
        ]
        assert config.experiment_ids == {"exp_a", "exp_b"}

    def test_list_of_packages(self) -> None:
        config = ExperimentConfig.model_validate(
            _cfg(
                _pkg(
                    "git+ssh://git@github.com/org/repo.git@21e38a9[ado]",
                    {"experimentIdentifier": "exp", "experimentVersion": "1.2.3"},
                ),
                _pkg(
                    "git+ssh://git@github.com/org/repo.git@5489863[ado]",
                    {"experimentIdentifier": "exp", "experimentVersion": "1.3.0"},
                ),
            )
        )
        assert len(config.packages) == 2
        assert config.experiment_ids == {"exp"}

    def test_empty_package_list_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate({"experiment_package": []})

    def test_local_path_rejected_in_list(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(_cfg(_pkg("./local", "e")))

    def test_unknown_entry_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(
                _cfg(_pkg("pkg", {"experimentIdentifier": "e", "bogus": 1}))
            )

    def test_duplicate_experiment_in_one_package_rejected(self) -> None:
        with pytest.raises(ValidationError, match="more than once"):
            ExperimentConfig.model_validate(
                _cfg(
                    _pkg(
                        "pkg",
                        {"experimentIdentifier": "e", "experimentVersion": "1.0.0"},
                        {"experimentIdentifier": "e", "experimentVersion": "2.0.0"},
                    )
                )
            )

    def test_duplicate_experiment_across_entries_same_specifier_rejected(self) -> None:
        with pytest.raises(ValidationError, match="more than once"):
            ExperimentConfig.model_validate(_cfg(_pkg("pkg", "e"), _pkg("pkg", "e")))

    def test_same_experiment_different_specifiers_allowed(self) -> None:
        config = ExperimentConfig.model_validate(
            _cfg(_pkg("pkg==1.0.0", "e"), _pkg("pkg==2.0.0", "e"))
        )
        assert len(config.packages) == 2

    def test_same_experiment_in_several_entries_allows_any_specifier(self) -> None:
        """Specifiers are assumed static; branches, tags and ranges are accepted."""
        config = ExperimentConfig.model_validate(
            _cfg(
                _pkg("git+ssh://git@github.com/org/repo.git@main", "e"),
                _pkg("pkg>=2.0", "e"),
            )
        )
        assert len(config.packages) == 2

    def test_non_semver_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate(
                _cfg(
                    _pkg(
                        "pkg", {"experimentIdentifier": "e", "experimentVersion": "1.2"}
                    )
                )
            )

    def test_identifier_with_at_rejected(self) -> None:
        with pytest.raises(ValidationError, match="@"):
            ExperimentConfig.model_validate(_cfg(_pkg("pkg", "e@v1")))


class TestBenchmarkInstanceMetadata:
    """Tests for BenchmarkInstance metadata validation."""

    def test_valid_metadata(self) -> None:
        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
            metadata={
                "region": "us-south",
                "endpoint-url": "http://ibm.com/my-endpoint/",
            },
        )
        assert instance.metadata == {
            "region": "us-south",
            "endpoint-url": "http://ibm.com/my-endpoint/",
        }

    def test_metadata_optional(self) -> None:
        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
        )
        assert instance.metadata is None

    def test_metadata_non_string_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BenchmarkInstance(
                instanceIdentifier="small_model_8b",
                benchmarkIdentifier="inference_serving",
                metadata={"tags": ["a", "b"]},  # type: ignore[dict-item]
            )


class TestInstanceBindingMetadata:
    """Tests for InstanceBinding and BindingFileConfig metadata validation."""

    def test_instance_binding_valid_metadata(self) -> None:
        binding = InstanceBinding(
            instanceBindingIdentifier="my_binding",
            instanceReference="inference_serving/small_model_8b",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator", experimentIdentifier="exp1"
            ),
            metadata={"run_label": "nightly-2025-07-01"},
        )
        assert binding.metadata == {"run_label": "nightly-2025-07-01"}

    def test_binding_file_config_valid_metadata(self) -> None:
        config = BindingFileConfig(
            instanceBindingIdentifier="my_binding",
            instanceReference="inference_serving/small_model_8b",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="exp1",
            ),
            metadata={"run_label": "nightly-2025-07-01"},
        )
        assert config.metadata == {"run_label": "nightly-2025-07-01"}

    def test_binding_metadata_key_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BindingFileConfig(
                instanceBindingIdentifier="my_binding",
                instanceReference="inference_serving/small_model_8b",
                experiment=ExperimentReference(
                    actuatorIdentifier="my_actuator",
                    experimentIdentifier="exp1",
                ),
                metadata={"k" * 4097: "val"},
            )
