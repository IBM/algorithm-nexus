<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Nexus Package Owner and Nexus Package Model Owner Responsibilities

This document defines the operational responsibilities of Nexus Package Owners
and Nexus Package Model Owners, with emphasis on day-to-day operations, issue
resolution, and maintaining system health.

## 1. Nexus Package Owner Responsibilities

Nexus Package owners are responsible for the related algorithm stack package
integrated into Algorithm Nexus and serve as the default owner for all models
declared in their Nexus package unless specific model owners are designated. As
explicitly mentioned in the
[requirements](../requirements/nexus_package.md#req-1-python-packages-used-in-nexus)
for full details), each Nexus Package is required to define an owner.

### 1.1 Algorithm Stack Python Package Requirements

Nexus Package owners are expected to guarantee that the Algorithm Stack python
package meets the requirements set in
[REQ-1 in Nexus Package Requirements](../requirements/nexus_package.md#req-1-python-packages-used-in-nexus).
**A Nexus Package depending on an Algorithm Stack python package that does not
meet these requirements will not be integrated into Algorithm Nexus**.

### 1.2 Operational Monitoring and Response

#### 1.2.1 Pull Requests Monitoring

The author of the PR is expected to:

- **Monitor CI pipeline status**: If a PR is in review phase, the PR author is
  responsible for monitoring the status of the CI pipeline and for promptly
  addressing any failures.
- **Escalate cross-package issues**: If a failure in the CI tasks involves
  another Nexus package, promptly contact the third party Nexus package owner
  and notify the Algorithm Nexus maintainers.

#### 1.2.2 Dependency Resolution Failures

Algorithm Stack packages are expected to satisfy the dependencies of the target
distribution variants they are added to (i.e., ecosystem, product, candidate).
Dependencies resolution is performed separately for each variant. While
performing dependencies resolution we expect two possible causes for failure: 1)
the dependencies tree cannot be resolved because of cross-package conflicting
versions. 2) One of the dependencies that is resolved introduces a CVE. When the
CI reports failures for any of the above the Nexus Package owner is expected to:

- **Analyze conflict details**: Which packages are in conflict, version
  constraints causing the issue, and impact on models and functionality.
- **Propose and test solutions**: Such as relaxing version constraints where
  appropriate, updating dependencies to compatible versions, or providing
  alternative dependency specifications.
- **Escalate cross-package issues**: If a failure in the dependency checks
  involves another Nexus package, promptly contact the third party Nexus package
  owner and notify the Algorithm Nexus maintainers.

In case of failures for an Algorithm Stack Package added to the product variant,
the owner is expected to react and address the issue within 1 week from the
notification of the failure. Failing to do so will result in the Nexus Package
being removed from the product distribution variant in the next Algorithm Nexus
release.

For the ecosystem and candidate variants, failure in addressing dependency
resolution failures in a timely manner will result in the offending Nexus
package and models being excluded from the next Algorithm Nexus release until
the failures are fixed.

\*\***Failure in addressing dependency issues for two consecutive releases will
result in the Nexus package being completely removed from Algorithm Nexus,
regardless of the target variant**\*\*.

## 2. Model Owner Responsibilities

Model owners are responsible for individual models within a Nexus package. By
default, the Nexus Package owner serves as the model owner unless a specific
owner is designated.

### 2.1 Operational Monitoring and Response

#### 2.1.1 Test Failure Response

Each model is tested on each target variant where the Algorithm Stack Package is
included. When CI/CD reports model test failures the model owner is expected to:

- **Investigate root cause**: Determine if a failure is due to model code
  changes, infrastructure issues, test environment problems, data or
  configuration issues, etc.
- **Reproduce the failure** locally when possible to speed up the resolution
  process.
- **Coordinate with package owner** if failure is dependency-related.
- **Submit fix via pull request**.

For test failures of models belonging to Nexus Packages added to the product
variant, the owner is expected to react and address the issue within 1 week from
the notification of the failure. Failing to do so will result in the Nexus
Package being removed from the product distribution variant in the next
Algorithm Nexus release.

For the ecosystem and candidate variants, failure in addressing test failures in
a timely manner might result in the offending model being excluded from the list
of supported models in the next Algorithm Nexus release for the targeted
variant, and from any benchmarking activity.

\***\*Failure in addressing test failures for two consecutive releases will
result in the model being completely removed from Algorithm Nexus, regardless of
the target variant.\*\***.

### 2.2 Model Definition and Maintenance

Model owners are expected to guarantee their models meet the requirements
defined in [REQ-3](../requirements/nexus_package.md#req-3-model-definition) and
[REQ-4](../requirements/nexus_package.md#req-4-artifact-specification) in the
Nexus Package requirements.

**\*\*Models failing to meet these requirements cannot be included in the list
of supported models in Algorithm Nexus\*\***.

## 3. Shared Responsibilities

### 3.1 Communication and Collaboration

- **Respond to GitHub issues** related to their packages or models.
- **Participate in discussions** about integration improvements.
- **Coordinate with other owners** when issues span multiple packages or models.
- **Provide status updates** on ongoing issues or planned changes.
- **Escalate blockers** to Algorithm Nexus maintainers when necessary.

### 3.2 Quality and Compliance

- **Follow contribution guidelines** as defined in
  [CONTRIBUTING.md](../../CONTRIBUTING.md).

## 4. Contact and Support

For questions about owner responsibilities or to report issues:

- **Issues**: [GitHub Issues](https://github.com/IBM/algorithm-nexus/issues)
- **Discussions**:
  [GitHub Discussions](https://github.com/IBM/algorithm-nexus/discussions)

## 5. References

- [Requirements for a Nexus Package](../requirements/nexus_package.md)
- [Requirements for Model Testing](../requirements/models_testing.md)
- [Contributing Guide](../../CONTRIBUTING.md)
