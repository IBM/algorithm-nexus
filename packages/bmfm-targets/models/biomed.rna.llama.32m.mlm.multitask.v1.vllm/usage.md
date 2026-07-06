# Using the BiomedRNA 32M MLM Multitask Model

This guide provides instructions on how to use the BiomedRNA 32M MLM Multitask
model for single-cell RNA embedding generation using vLLM serving.

## Overview

The BiomedRNA 32M MLM Multitask model
(`ibm-research/biomed.rna.llama.32m.mlm.multitask.v1.vllm`) is a 32M parameter
RNA foundation model for generating single-cell RNA embeddings. It can be served
using vLLM with the `biomed_rna` IO processor plugin for efficient inference over
the `/pooling` endpoint.

## Prerequisites

### Installation

Install `bmfm-targets` with vLLM extra dependencies:

```bash
pip install bmfm-targets[vllm]
```

## Starting the vLLM Server

```bash
vllm serve ibm-research/biomed.rna.llama.32m.mlm.multitask.v1.vllm \
    --runner pooling \
    --trust-remote-code \
    --enforce-eager \
    --no-enable-prefix-caching \
    --dtype float32 \
    --gpu-memory-utilization 0.1 \
    --io-processor-plugin biomed_rna \
    --enable-mm-embeds
```

### Command Arguments Explained

- `--runner pooling`: Uses the pooling runner for embedding generation
- `--trust-remote-code`: Allows execution of remote code (required for custom models)
- `--enforce-eager`: Uses eager execution mode instead of CUDA graphs
- `--no-enable-prefix-caching`: Disables prefix caching (required for RNA models)
- `--dtype float32`: Uses float32 precision
- `--gpu-memory-utilization 0.1`: Fraction of GPU memory to use
- `--io-processor-plugin biomed_rna`: Enables the BiomedRNA IO processor plugin for
  RNA data serialization/deserialization
- `--enable-mm-embeds`: Enables multimodal embeddings support

The server will start on `http://localhost:8000` by default.

## Making Inference Requests

Input data must be an [AnnData](https://anndata.readthedocs.io) `.h5ad` file.
Use the `vllm_biomed_rna_plugin` preprocessing utilities to prepare cell data
before sending to the server.

### Python Client Example

```python
import anndata
import numpy as np
import requests
from vllm_biomed_rna_plugin.preprocess import preprocess_anndata
from vllm_biomed_rna_plugin.utils import MLM_MULTITASK_MODEL, load_tokenizer

MODEL_REPO = MLM_MULTITASK_MODEL  # "ibm-research/biomed.rna.llama.32m.mlm.multitask.v1.vllm"
SERVER_URL = "http://localhost:8000/pooling"

# Load and preprocess h5ad data
adata = anndata.read_h5ad("cells.h5ad")[:10]
tokenizer = load_tokenizer(MODEL_REPO)
cell_data = preprocess_anndata(adata, tokenizer, max_length=1024)

# Generate embeddings
embeddings = []
for cell in cell_data:
    rna_data = cell["multi_modal_data"]["rna"]
    payload = {
        "model": MODEL_REPO,
        "data": {
            "gene_ids": rna_data["gene_ids"].tolist(),
            "expr_values": rna_data["expr_values"].tolist(),
            "attention_mask": rna_data["attention_mask"].tolist(),
        },
    }
    response = requests.post(SERVER_URL, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    embeddings.append(np.array(result["data"]["embedding"]))

embeddings_array = np.array(embeddings)  # shape: [num_cells, hidden_size]
```
