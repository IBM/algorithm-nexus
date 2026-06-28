# bmfm-targets Candidate Variant Update

## Description

Adds `bmfm-targets[vllm]` to the `candidate` variant and adds BiomedRNA vLLM
model metadata to the `bmfm-targets` Nexus package.

## Changes Made

### Nexus Package Structure

Added two BiomedRNA model entries under `packages/bmfm-targets/models/`:

- `biomed.rna.llama.47m.wced.multitask.v1.vllm`
    - HuggingFace ID: `ibm-research/biomed.rna.llama.47m.wced.multitask.v1.vllm`
    - vLLM general plugin: `biomed_rna_model`
    - vLLM IO processor plugin: `biomed_rna`

- `biomed.rna.llama.32m.mlm.multitask.v1.vllm`
    - HuggingFace ID: `ibm-research/biomed.rna.llama.32m.mlm.multitask.v1.vllm`
    - vLLM general plugin: `biomed_rna_model`
    - vLLM IO processor plugin: `biomed_rna`

### Dependency Changes

- Added `bmfm-targets[vllm]` to the `candidate` variant. The vLLM plugin entry
  points (`biomed_rna_model`, `biomed_rna`) are registered by `bmfm-targets` itself.
- Regenerated `requirements-candidate.txt`.
