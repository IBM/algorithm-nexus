---
name: New Nexus Package
about: Submit a new Nexus package to Algorithm Nexus
title: "feat(package): Add biomed-multi-alignment Nexus package"
labels: "nexus-package"
---

## Description

Adds the [biomed-multi-alignment](https://github.com/BiomedSciAI/biomed-multi-alignment)
package as a new Nexus package. This package provides MAMMAL (Molecular Aligned
Multi-Modal Architecture and Language), a 458M-parameter T5-style biomedical
foundation model trained on over 2 billion biological samples across proteins,
small molecules, and single-cell gene expression data.

### Changes made

- Created `packages/biomed-multi-alignment/nexus.yaml` with the Nexus package
  definition.
- Created `packages/biomed-multi-alignment/models/biomed.omics.bl.sm.ma-ted-458m/model.yaml`
  with the HuggingFace model ID (`ibm-research/biomed.omics.bl.sm.ma-ted-458m`)
  and vLLM plugin configuration (general plugin: `mammal`).
- Added `biomed-multi-alignment` as a dependency to both the `ecosystem` and
  `candidate` variants in `pyproject.toml`, pointing at the `main` branch of
  the GitHub repository (`git+https://github.com/BiomedSciAI/biomed-multi-alignment`).
  The package is **vllm-agnostic** (vLLM is an optional dependency via the
  `[vllm]` extra), so it is added without extras for `ecosystem` and with
  `[vllm]` for `candidate`.
- Updated `uv.lock` and exported updated `requirements-ecosystem.txt` and
  `requirements-candidate.txt`.

### Variant classification

The package declares `vllm` as an **optional** dependency (via the `[vllm]`
extra in its `pyproject.toml`). It therefore belongs to both the **ecosystem**
and **candidate** variants per the Variant Association Rules.

### Notes

- The latest GitHub release (`0.2.4`) has a `transformers<5.0.0` constraint
  that conflicts with `bmfm-targets` (which requires `transformers>=5`). The
  `main` branch already fixes this to `transformers>=5.0.0,<6.0.0`. The
  dependency therefore points at `main` until a new release is tagged.

## Additional Information

The vLLM plugin (`vllm_mammal_plugin`) is located under the `mammal_vllm/`
subdirectory of the repository and is included when installing with the `[vllm]`
extra. The plugin is registered via the `vllm.general_plugins` entry point and
exposes the MAMMAL model as a pooling-runner embedding model in vLLM.

## I need help with this PR

N/A — all steps completed successfully.

## Related Issues

N/A
