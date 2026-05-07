# Using the Prithvi Model

This guide provides instructions on how to use the Prithvi EO 2.0 model for
geospatial segmentation tasks using vLLM serving.

## Overview

The Prithvi model (`ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11`) is
a geospatial foundation model designed for Earth observation tasks, particularly
flood segmentation. It can be served using vLLM with TerraTorch integration for
efficient inference.

## Prerequisites

### Installation

Install TerraTorch with vLLM extra dependencies:

```bash
pip install terratorch[vllm]
```

## Starting the vLLM Server

Start the vLLM server with the following command:

```bash
vllm serve ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11 \
  --model-impl terratorch \
  --trust-remote-code \
  --skip-tokenizer-init \
  --enforce-eager \
  --io-processor-plugin terratorch_segmentation \
  --enable-mm-embeds
```

### Command Arguments Explained

- `--model-impl terratorch`: Uses TerraTorch as the model implementation
- `--trust-remote-code`: Allows execution of remote code (required for custom
  models)
- `--skip-tokenizer-init`: Skips tokenizer initialization (not needed for vision
  models)
- `--enforce-eager`: Uses eager execution mode instead of CUDA graphs
- `--io-processor-plugin terratorch_segmentation`: Enables the TerraTorch
  segmentation I/O processor plugin (see
  [TerraTorch I/O Processor Plugins documentation](https://torchgeo.org/terratorch/stable/guide/vllm/vllm_io_plugins/))
- `--enable-mm-embeds`: Enables multimodal embeddings support

The server will start on `http://localhost:8000` by default.

## Making Inference Requests

### Python Client Example

```python
import base64
from pathlib import Path
import requests

# Server endpoint
VLLM_SERVER_ENDPOINT = "http://localhost:8000/pooling"

# Prepare the request payload
request_payload = {
    "data": {
        "data": "https://huggingface.co/christian-pinto/Prithvi-EO-2.0-300M-TL-VLLM/resolve/main/valencia_example_2024-10-26.tiff",
        "data_format": "url",
        "image_format": "tiff",
        "out_data_format": "b64_json",
    },
    "priority": 0,
    "model": "ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11",
}

# Send the request
response = requests.post(VLLM_SERVER_ENDPOINT, json=request_payload)

# Check response status
if response.status_code == 200:
    result = response.json()

    # Decode the base64 encoded output
    decoded_image = base64.b64decode(result["data"]["data"])

    # Save the prediction
    output_path = Path.cwd() / "prithvi_prediction.tiff"
    with open(output_path, "wb") as f:
        f.write(decoded_image)

    print(f"Output saved to: {output_path}")
else:
    print(f"Error: {response.status_code} - {response.reason}")
```

### Request Payload Structure

The request payload consists of the following fields:

- **`data`**: Contains the input data configuration
  - **`data`**: The input TIFF image (URL or base64 encoded data)
  - **`data_format`**: Format of the input data (`"url"` or `"b64_json"`)
  - **`image_format`**: Must be `"tiff"` (only TIFF format is supported)
  - **`out_data_format`**: Format for the output data (`"b64_json"` for base64
    encoded)
- **`priority`**: Request priority (0 = normal priority)
- **`model`**: The model identifier

### Input Formats

**Important**: The Prithvi model only accepts TIFF (`.tiff` or `.tif`) format
images. Other image formats are not supported.

The model supports two ways to provide input TIFF images:

1. **URL**: Provide a direct URL to the TIFF image

   ```python
   "data": "https://example.com/image.tiff",
   "data_format": "url",
   "image_format": "tiff"
   ```

2. **Base64 Encoded**: Provide base64 encoded TIFF image data

   ```python
   "data": "<base64_encoded_tiff_string>",
   "data_format": "b64_json",
   "image_format": "tiff"
   ```

Check the
[Terratorch Segmentation IO Processor plugin documentation](https://torchgeo.org/terratorch/stable/guide/vllm/plugins/segmentation_io_plugin/)
for full details on the input format.

## Output

The model returns segmentation predictions as a base64 encoded TIFF file. The
output contains:

- Segmentation masks indicating flood-affected areas
- Same spatial dimensions as the input image
- Pixel values representing different classes (e.g., water, no water)

Check the
[Terratorch Segmentation IO Processor plugin documentation](https://torchgeo.org/terratorch/stable/guide/vllm/plugins/segmentation_io_plugin/)
for full details on the output formats.

## Additional Resources

- [TerraTorch Documentation](https://torchgeo.org/terratorch/stable/)
- [TerraTorch vLLM Serving Guide](https://torchgeo.org/terratorch/stable/guide/vllm/intro/)
- [TerraTorch I/O Processor Plugins](https://torchgeo.org/terratorch/stable/guide/vllm/vllm_io_plugins/)
- [vLLM Documentation](https://docs.vllm.ai/)
