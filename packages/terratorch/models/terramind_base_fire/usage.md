# Using the TerraMind Base Fire Model

This guide provides instructions on how to use the TerraMind Base Fire model for
geospatial fire/burn scar segmentation tasks using vLLM serving.

## Overview

The TerraMind Base Fire model (`ibm-esa-geospatial/TerraMind-base-Fire`) is a
geospatial foundation model designed for fire detection and burn scar
segmentation in Earth observation imagery. It processes multi-modal satellite
data including DEM (Digital Elevation Model), Sentinel-1 RTC, and Sentinel-2 L2A
imagery. The model can be served using vLLM with TerraTorch integration for
efficient inference.

## Prerequisites

## Starting the vLLM Server

Start the vLLM server with the following command:

```bash
vllm serve ibm-esa-geospatial/TerraMind-base-Fire \
  --model-impl terratorch \
  --trust-remote-code \
  --skip-tokenizer-init \
  --enforce-eager \
  --max-num-seqs 32 \
  --io-processor-plugin terratorch_tm_segmentation \
  --enable-mm-embeds
```

### Command Arguments Explained

- `--model-impl terratorch`: Uses TerraTorch as the model implementation
- `--trust-remote-code`: Allows execution of remote code (required for custom
  models)
- `--skip-tokenizer-init`: Skips tokenizer initialization (not needed for vision
  models)
- `--enforce-eager`: Uses eager execution mode instead of CUDA graphs
- `--max-num-seqs 32`: Maximum number of sequences to process in parallel
- `--io-processor-plugin terratorch_tm_segmentation`: Enables the TerraMind
  segmentation I/O processor plugin (see
  [TerraTorch I/O Processor Plugins documentation](https://terrastackai.github.io/terratorch/stable/vllm_serving.html#io-processor-plugins))
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

# Prepare the request payload with multi-modal input
request_payload = {
    "data": {
        "data": {
            "DEM": "https://huggingface.co/datasets/christian-pinto/TestTerraMindDataset/resolve/main/fire/EMSR686_1_35TMF_x413905_y4537585_DEM.tif",
            "S1RTC": "https://huggingface.co/datasets/christian-pinto/TestTerraMindDataset/resolve/main/fire/EMSR686_1_35TMF_x413905_y4537585_S1RTC.zarr.zip",
            "S2L2A": "https://huggingface.co/datasets/christian-pinto/TestTerraMindDataset/resolve/main/fire/EMSR686_1_35TMF_x413905_y4537585_S2L2A.zarr.zip",
        },
        "data_format": "url",
        "out_data_format": "b64_json",
        "image_format": "",
    },
    "model": "ibm-esa-geospatial/TerraMind-base-Fire",
}

# Send the request
response = requests.post(VLLM_SERVER_ENDPOINT, json=request_payload)

# Check response status
if response.status_code == 200:
    result = response.json()

    # Decode the base64 encoded output
    decoded_image = base64.b64decode(result["data"]["data"])

    # Save the prediction
    output_path = Path.cwd() / "terramind_fire_prediction.tiff"
    with open(output_path, "wb") as f:
        f.write(decoded_image)

    print(f"Output saved to: {output_path}")
else:
    print(f"Error: {response.status_code} - {response.reason}")
```

### Request Payload Structure

The request payload consists of the following fields:

- **`data`**: Contains the input data configuration
  - **`data`**: A dictionary containing URLs or paths to the multi-modal input
    data:
    - **`DEM`**: Digital Elevation Model (TIFF format)
    - **`S1RTC`**: Sentinel-1 Radiometrically Terrain Corrected data (Zarr
      format)
    - **`S2L2A`**: Sentinel-2 Level-2A data (Zarr format)
  - **`data_format`**: Format of the input data (`"url"` or `"path"`)
  - **`image_format`**: Leave as empty string `""` for multi-modal inputs
  - **`out_data_format`**: Format for the output data (`"b64_json"` for base64
    encoded, or `"path"` to save to disk)
- **`priority`**: Request priority (0 = normal priority)
- **`model`**: The model identifier

### Input Formats

The TerraMind Base Fire model requires **multi-modal input** consisting of three
data sources:

1. **DEM (Digital Elevation Model)**: TIFF format file
2. **S1RTC (Sentinel-1 RTC)**: Zarr archive (.zarr.zip)
3. **S2L2A (Sentinel-2 L2A)**: Zarr archive (.zarr.zip)

You can provide these inputs in two ways:

#### 1. URL Format

Provide URLs to the data files:

```python
"data": {
    "DEM": "https://example.com/dem.tif",
    "S1RTC": "https://example.com/s1rtc.zarr.zip",
    "S2L2A": "https://example.com/s2l2a.zarr.zip",
},
"data_format": "url"
```

#### 2. Local Path Format

Provide local file paths:

```python
"data": {
    "DEM": "/path/to/dem.tif",
    "S1RTC": "/path/to/s1rtc.zarr.zip",
    "S2L2A": "/path/to/s2l2a.zarr.zip",
},
"data_format": "path"
```

### Output Formats

The model supports two output formats:

1. **Base64 JSON** (`"b64_json"`): Returns the segmentation mask as base64
   encoded data in the JSON response
2. **Path** (`"path"`): Saves the output to disk and returns the file path

You can optionally specify a custom output directory using the `out_path`
parameter:

```python
"data": {
    "data": {...},
    "data_format": "url",
    "out_data_format": "path",
    "out_path": "/custom/output/directory",
    "image_format": "",
}
```

## Output

The model returns fire/burn scar segmentation predictions as a TIFF file. The
output contains:

- Segmentation masks indicating burned areas
- Same spatial dimensions as the input imagery
- Pixel values representing different classes (e.g., burned, unburned)

## Use Cases

The TerraMind Base Fire model is particularly useful for:

- **Fire Detection**: Identifying active fire areas and burn scars using
  multi-modal satellite data
- **Post-Fire Assessment**: Mapping the extent of burned areas after wildfires
- **Emergency Response**: Rapid fire extent mapping for disaster response
- **Environmental Monitoring**: Tracking fire patterns and recovery over time
- **Risk Assessment**: Analyzing fire-prone regions with elevation and
  vegetation context
- **Forest Management**: Assessing fire damage for forest restoration planning

## Troubleshooting

### Server Won't Start

- Ensure all dependencies are installed: `pip install terratorch[vllm]`
- Check that the model can be downloaded from Hugging Face
- Verify sufficient GPU memory is available

### Request Fails

- Confirm the server is running and accessible at the specified endpoint
- Verify all three input data sources (DEM, S1RTC, S2L2A) are accessible
- Ensure the input data is in the correct format (TIFF for DEM, Zarr for
  S1RTC/S2L2A)
- Check that the request payload structure matches the expected format
- Verify the Zarr files are properly formatted and not corrupted

### Out of Memory Errors

- Reduce input image size or spatial extent
- Use smaller batch sizes (adjust `--max-num-seqs`)
- Consider using a GPU with more memory

### Invalid Output Path

- Ensure the output directory exists and is writable
- Use absolute paths when specifying custom output directories
- Check file system permissions

## Additional Resources

- [TerraTorch Documentation](https://terrastackai.github.io/terratorch/stable/)
- [TerraTorch vLLM Serving Guide](https://terrastackai.github.io/terratorch/stable/vllm_serving.html)
- [TerraTorch I/O Processor Plugins](https://terrastackai.github.io/terratorch/stable/vllm_serving.html#io-processor-plugins)
- [vLLM Documentation](https://docs.vllm.ai/)
