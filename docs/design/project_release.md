# Algorithm Nexus Release

## Release Definition

A release of this project represents a stable point in the software lifecycle.
Each release is officially designated as a **GitHub Release**, built upon a
specific Git tag.

---

### Release Standards

| Attribute         | Specification                                             |
| ----------------- | --------------------------------------------------------- |
| **Platform**      | Published as a GitHub Release on the official repository. |
| **Branch Origin** | Created exclusively from the `main` branch.               |
| **Tagging**       | Follows Semantic Versioning (SemVer).                     |
| **Documentation** | Accompanied by comprehensive release notes detailing changes, features, and fixes. |
| **Source Bundle** | Includes a full source release bundle (archives of the repository at that tag). |

---

### Release Payload

Each release contains the necessary components to deploy and interact with the
framework. The following core elements are guaranteed in every distribution:

| Component                 | Description                                                                                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **CLI**                   | The central Command Line Interface tool for project interaction (`nexus`).                                                                                                                 |
| **Nexus Packages**        | The most recent version of the algorithm stack packages (Nexus).                                                                                                                           |
| **Distribution Variants** | Three optional and mutually-exclusive dependency groups tailored for specific environments (`ecosystem`, `candidate`, `product`) with pinned requirements in dedicated requirements files. |

---

### Release versioning

The versioning of the release follows the
[Semantic Versioning](https://semver.org/) specification. The version number is
composed of three parts:

- **Major version**: Incremented when the release includes major changes (not
  compatible with any previous version) in the benchmarking, testing or
  dependencies validation protocols or breaking changes to the Nexus cli.
- **Minor version**: Incremented when the release includes new algorithm stack
  packages or new models are added to an existing package.
- **Patch version**: Incremented for updates to existing Nexus packages or
  models (e.g., adding model tests, benchmarks or incrementing the algorithm
  stack package version) and for not breaking changes to the Nexus cli.

### Release cadence

- We aim at releasing a new version within a week of adding or updating an
  algorithm stack package.
- The release for product is the version that is available by the product
  planning freeze date.
