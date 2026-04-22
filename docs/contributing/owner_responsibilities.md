<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Model and Package Owner Responsibilities

This document defines the operational responsibilities of Nexus Package Owners
and Model Owners within the Algorithm Nexus ecosystem, with emphasis on
day-to-day operations, issue resolution, and maintaining system health.

## Package Owner Responsibilities

Package owners are responsible for the Python package integrated into Algorithm
Nexus and serve as the default owner for all models within their package unless
specific model owners are designated.

### 1. Python Package Requirements

To be integrated with Algorithm Nexus, your Python package must fulfill these
requirements (see
[REQ-1 in Nexus Package Requirements](../requirements/nexus_package.md#req-1-python-packages-used-in-nexus)
for full details):

- **Versioned releases**: Provide versioned releases using any versioning scheme
  that guarantees increasing version numbers represent newer releases. Releases
  must be published on GitHub or PyPI.
- **Package owner/maintainer**: Define at least one maintainer who will be
  considered the owner of the Nexus package.
- **Package metadata**: Include a description and link to documentation in the
  released wheel.
- **Dependencies**: Define all dependencies required for package use and
  testing.

**A Python package that does not meet these requirements will not be integrated
into Algorithm Nexus**.

### 2. Operational Monitoring and Response

#### Pull Requests Monitoring

- **Monitor CI pipeline status**: If a PR is in review phase, the Nexus package
  owner is responsible for monitoring the status of the CI pipeline and for
  promptly addressing any failures.
- **Escalate cross-package issues**: If a failure in the CI tasks involves
  another Nexus package, promptly contact the third party Nexus package owner
  and notify the Algorithm Nexus maintainers.

#### Dependency Resolution Failures

When the CI reports dependency conflicts or resolution failures:

- **Analyze conflict details**: Which packages are in conflict, version
  constraints causing the issue, and impact on models and functionality.
- **Propose and test solutions**: Such as relaxing version constraints where
  appropriate, updating dependencies to compatible versions, or providing
  alternative dependency specifications.
- **Escalate cross-package issues**: If a failure in the dependency checks
  involves another Nexus package, promptly contact the third party Nexus package
  owner and notify the Algorithm Nexus maintainers.

Failure in addressing dependency resolution failures in a timely manner might
result in the offending Nexus package and models being excluded from the next
Algorithm Nexus release until the failures are fixed.

\*\***Failure in addressing dependency issues for two consecutive releases will
result in the Nexus package being completely removed from Algorithm Nexus**\*\*.

## Model Owner Responsibilities

Model owners are responsible for individual models within a Nexus package. By
default, the package owner serves as the model owner unless a specific owner is
designated.

### 3. Operational Monitoring and Response

#### Test Failure Response

When CI/CD reports model test failures:

- **Investigate root cause**: Determine if a failure is due to model code
  changes, infrastructure issues, test environment problems, data or
  configuration issues, etc.
- **Reproduce the failure** locally when possible to speed up the resolution
  process.
- **Coordinate with package owner** if failure is dependency-related.
- **Submit fix via pull request**.

Failure in addressing test failures in a timely manner might result in the
offending model being excluded from the list of supported models in the next
Algorithm Nexus release, and from any benchmarking activity.

\***\*Failure in addressing test failures for two consecutive releases will
result in the model being completely removed from Algorithm Nexus\*\***.

### 4. Model Definition and Maintenance

For detailed requirements, see
[REQ-3: Model Definition](../requirements/nexus_package.md#req-3-model-definition)
and
[REQ-4: Artifact Specification](../requirements/nexus_package.md#req-4-artifact-specification).

- **Maintain model on Hugging Face** with proper documentation and weights
  (REQ-3.1).
- **Designate ownership** explicitly if different from package owner (REQ-3.4).
- **Provide usage documentation** to help users get started (REQ-4.1).
- **Document vLLM serving requirements** including specific plugins or
  configurations (REQ-4.3).

## Shared Responsibilities

### Communication and Collaboration

- **Respond to GitHub issues** related to their packages or models.
- **Participate in discussions** about integration improvements.
- **Coordinate with other owners** when issues span multiple packages or models.
- **Provide status updates** on ongoing issues or planned changes.
- **Escalate blockers** to Algorithm Nexus maintainers when necessary.

### Quality and Compliance

- **Follow contribution guidelines** as defined in
  [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Contact and Support

For questions about owner responsibilities or to report issues:

- **Issues**: [GitHub Issues](https://github.com/IBM/algorithm-nexus/issues)
- **Discussions**:
  [GitHub Discussions](https://github.com/IBM/algorithm-nexus/discussions)

## References

- [Requirements for a Nexus Package](../requirements/nexus_package.md)
- [Requirements for Model Testing](../requirements/models_testing.md)
- [Contributing Guide](../../CONTRIBUTING.md)
