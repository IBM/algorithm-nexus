# bmfm-targets Candidate Variant Update

## Description

Adds `bmfm-targets[vllm]` and `vllm-ibm-biomed-rna-plugin` to the `candidate` variant,
and adds BiomedRNA vLLM model metadata to the `bmfm-targets` Nexus package.

## Changes Made

### Nexus Package Structure

Added two BiomedRNA model entries under `packages/bmfm-targets/models/`:

- `biomed.rna.llama.47m.wced.multitask.v1.vllm`
    - HuggingFace ID: `ibm-research/biomed.rna.llama.47m.wced.multitask.v1.vllm`
    - vLLM general plugin: `biomedrna`
    - vLLM IO processor plugin: `biomed_rna`

- `biomed.rna.llama.32m.mlm.multitask.v1.vllm`
    - HuggingFace ID: `ibm-research/biomed.rna.llama.32m.mlm.multitask.v1.vllm`
    - vLLM general plugin: `biomedrna`
    - vLLM IO processor plugin: `biomed_rna`

### Dependency Changes

- Added `bmfm-targets[vllm]` to the `candidate` variant.
- Added `vllm-ibm-biomed-rna-plugin` to the `candidate` variant, sourced from the
  `vllm` subdirectory of `biomed-multi-omic`.
- Regenerated `requirements-candidate.txt`.
