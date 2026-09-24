# Using the GridFM PowerFlow Reconstruction Model

This guide explains how to serve the GridFM heterogeneous GNN for PowerFlow
reconstruction through vLLM's `/pooling` endpoint.

## Overview

GridFM (`gridfm/gridfm-pf-reconstruction`) is a heterogeneous graph neural
network (`GNS_heterogeneous`) over power-grid graphs. Buses and generators are
nodes; branches and bus↔generator connections are typed edges. Served for the
**PowerFlow reconstruction** task, it returns, per request:

- per-node latent **embeddings** (bus and generator), and
- **predictions**: bus voltage magnitude/angle (Vm, Va) and generator active
  power (Pg), denormalized back to physical units.

Because the model consumes a graph rather than text, it is served as a vLLM
**pooling** model paired with an I/O processor plugin that translates a
power-grid case into the graph tensors the model expects and translates the
pooled output back into a structured response.

## Prerequisites

### Installation

Install gridfm-graphkit with its vLLM extra (pulls in `vllm==0.26.x`):

```bash
pip install "gridfm-graphkit[vllm]"
```

This installs two entry points that vLLM discovers at startup:

- `vllm.general_plugins` → `gridfm_gns` — registers the `GridFMGNS` pooling
  model architecture.
- `vllm.io_processor_plugins` → `gridfm_pf_reconstruction` — the PowerFlow
  reconstruction I/O processor.

## Starting the vLLM Server

```bash
vllm serve gridfm/gridfm-pf-reconstruction \
  --runner pooling \
  --trust-remote-code \
  --skip-tokenizer-init \
  --enforce-eager \
  --io-processor-plugin gridfm_pf_reconstruction \
  --enable-mm-embeds
```

### Command Arguments Explained

- `--runner pooling`: serve as a pooling/encoder model (no token generation).
- `--trust-remote-code`: allow loading the model's config/architecture.
- `--skip-tokenizer-init`: no tokenizer is needed for a graph model.
- `--enforce-eager`: eager execution (the model is attention-free).
- `--io-processor-plugin gridfm_pf_reconstruction`: enable the PowerFlow
  reconstruction I/O processor.
- `--enable-mm-embeds`: enable the multimodal path used to ship graph tensors.

The server starts on `http://localhost:8000` by default.

## Making Inference Requests

The I/O processor accepts a power-grid case as record lists for buses,
generators and branches (the same columns GridFM's dataset builder consumes).
Send it to the `/pooling` endpoint.

### Python Client Example

```python
import requests

VLLM_SERVER_ENDPOINT = "http://localhost:8000/pooling"

request_payload = {
    "data": {
        "case": {
            "bus": [ /* per-bus records */ ],
            "gen": [ /* per-generator records */ ],
            "branch": [ /* per-branch records */ ],
        },
        "return_embeddings": True,
        "return_predictions": True,
    },
    "priority": 0,
    "model": "gridfm/gridfm-pf-reconstruction",
}

response = requests.post(VLLM_SERVER_ENDPOINT, json=request_payload)
response.raise_for_status()
result = response.json()["data"]

print("num buses:", result["num_buses"])
print("num gens: ", result["num_gens"])
# result["bus_predictions"]  -> per-bus [Vm, Va, ...] in physical units
# result["gen_predictions"]  -> per-generator [Pg, ...] in physical units
# result["bus_embeddings"]   -> per-bus latent vectors
# result["gen_embeddings"]   -> per-generator latent vectors
```

### Request Payload Structure

- **`data`**: the input configuration
    - **`case`**: the power-grid case as `bus` / `gen` / `branch` record lists.
    - **`return_embeddings`**: include per-node latent embeddings in the response.
    - **`return_predictions`**: include per-node Vm/Va/Pg predictions.
- **`priority`**: request priority (0 = normal).
- **`model`**: the model identifier.

## Output

The response `data` object contains:

- **`num_buses`**, **`num_gens`**: node counts for the served case.
- **`bus_predictions`**, **`gen_predictions`**: denormalized per-node
  predictions (bus Vm/Va, generator Pg).
- **`bus_embeddings`**, **`gen_embeddings`**: per-node latent embeddings.

## Additional Resources

- [gridfm-graphkit](https://github.com/gridfm/gridfm-graphkit)
- [vLLM pooling models](https://docs.vllm.ai/en/latest/models/pooling_models.html)
- [vLLM I/O processor plugins](https://docs.vllm.ai/en/latest/design/io_processor_plugins.html)
