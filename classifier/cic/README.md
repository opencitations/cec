[![Read The Paper](https://img.shields.io/badge/Read_The_Paper-red?style=flat-square)](https://link.springer.com/article/10.1007/s11192-025-05418-8)
[![Go to the web application](https://img.shields.io/badge/Go%20to%20the%20web%20application-blue?style=flat-square)](http://137.204.64.4:81/cic/)

# Citation Intent Classifier [Release Candidate]

Usage guide and API reference.

---

## Table of Contents

- [Introduction](#introduction)
- [Folder Structure](#folder-structure)
- [Running the Classifier](#running-the-classifier)
- [Using the Web Interface](#using-the-web-interface)
- [Using the API](#using-the-api)
- [JSON File Format](#json-file-format)
- [Acknowledgements](#acknowledgements)

---

## Introduction

The Citation Intent Classifier is a web application and API that classifies citation contexts in research papers. It uses pre-trained language models to determine the author's intent in citing.

## Folder Structure

```plaintext
project_root/
.
├── cic
│   ├── __init__.py
│   ├── blueprints
│   │   ├── __init__.py
│   │   ├── cic_api.py
│   │   └── web_interface.py
│   ├── main.py
│   ├── predictor_manager.py
│   ├── README.md
│   ├── sh
│   │   ├── check-and-run.sh
│   │   ├── log.txt
│   │   ├── README.md
│   │   ├── run.sh
│   │   └── stop.sh
│   ├── src
│   │   ├── __init__.py
│   │   ├── binary_classifiers.py
│   │   ├── data_processor.py
│   │   ├── metaclassifiers.py
│   │   ├── models
│   │   │   ├── ModelsWithoutSections
│   │   │   │   ├── FFNN_SciCiteWoS.pth
│   │   │   │   ├── WoS_SciBERT_bkg.pt
│   │   │   │   ├── WoS_SciBERT_met.pt
│   │   │   │   ├── WoS_SciBERT_res.pt
│   │   │   │   ├── WoS_XLNet_bkg.pt
│   │   │   │   ├── WoS_XLNet_met.pt
│   │   │   │   └── WoS_XLNet_res.pt
│   │   │   └── ModelsWithSections
│   │   │       ├── FFNN_SciCiteWS.pth
│   │   │       ├── WS_SciBERT_bkg.pt
│   │   │       ├── WS_SciBERT_met.pt
│   │   │       ├── WS_SciBERT_res.pt
│   │   │       ├── WS_XLNet_bkg.pt
│   │   │       ├── WS_XLNet_met.pt
│   │   │       └── WS_XLNet_res.pt
│   │   └── predictor.py
│   ├── static
│   │   ├── css
│   │   │   ├── classifier.css
│   │   │   └── index.css
│   │   ├── img
│   │   │   ├── graspos_white.svg
│   │   │   ├── graspos.svg
│   │   │   ├── oc_white.svg
│   │   │   └── oc.svg
│   │   └── js
│   │       ├── classifier.js
│   │       └── conf.js
│   ├── templates
│   │   ├── classifier.html
│   │   └── index.html
│   └── utils
│       ├── __init__.py
│       ├── file_processing.py
│       └── response_helpers.py
├── clean_tree.txt
├── README.md
├── requirements.txt
└── test
    ├── ...
    ├── ...
```

## Running the Classifier

The classifier runs via Docker Compose. See the [root README](../../README.md) for the full stack (uses the `V2_full` image with the model weights baked in), or [../DOCKER_HOW_TO.md](../DOCKER_HOW_TO.md) for the classifier-only setup with externally mounted weights.

Once the stack is running, the API listens on `http://127.0.0.1:5000/cic` and the web interface on `http://127.0.0.1:5000/cic/classifier`.

## Using the Web Interface

### Access the Web Interface

Open a web browser and navigate to the [classifier website](http://test.opencitations.net:81/cic/).

### Classify Text Manually

1. Navigate to the classification page.
2. Enter the text you wish to classify in the provided text area in the form of a list of tuples.
3. Select the classification mode (*with sections*, *without sections*, or *mixed*).
4. Click the **Classify** button.
5. The results will be displayed on the page.

### Upload a JSON File

1. Prepare a JSON file with the appropriate structure.
2. On the classification page, click on **Choose File** and select your JSON file.
3. Select the classification mode.
4. Click the **Classify JSON** button.
5. The results will be displayed on the page.

## Using the API

Examples below target the local endpoint `http://127.0.0.1:5000`. Replace the base URL with your deployment URL if different.

### API Endpoints

- `POST /cic/api/classify`: Classify citation contexts provided in the request.

### Request Parameters

| Name               | In              | Required | Type        | Description |
|--------------------|-----------------|----------|-------------|-------------|
| `mode`             | JSON body or form field | :white_check_mark: | `string`    | Classification mode. Must be one of: `WS` (with sections), `WoS` (without sections), or `M` (mixed). |
| `file`             | form-data       | :white_check_mark: (if uploading a file) | `file` | A `.json` or compressed file (`.zip`, `.tar`, `.gz`, `.bz2`, `.xz`, `.7z`) to be classified. |
| `data`             | JSON body       | :white_check_mark: (if not uploading a file) | `list of [SECTION, CITATION]` tuples | Citation data to classify. |
| `X-Request-Source` | HTTP header     | :x:       | `string`    | Optional. `"cli"` (default to unknown which works as cli) or `"web-interface"` (for web-application). Used to determine output formatting. |

### Usage with `curl`

#### Basic Example Usage with `curl`

```bash
curl -X POST \
  -F "file=@/path/to/input/compression_test.zip" \
  -F "mode=M" \
  "http://127.0.0.1:5000/cic/api/classify" \
  -o "/path/to/output/Result_XZ.zip"
```

More than this, the `/cic/api/classify` endpoint accepts **two types** of request bodies: JSON and form-based file uploads.

#### Option 1 — JSON Body (`application/json`)

Use this when you want to send citation data directly (inline) in the request.

**Sample input file (`test_payload.json`)**
```json
{
  "mode": "WS",
  "data": [
    ["Introduction", "This method is based on Smith et al. (2020)."],
    ["", "Our results build upon prior work."]
  ]
}
```

curl command:

```bash
curl -X POST http://127.0.0.1:5000/cic/api/classify \
     -H "Content-Type: application/json" \
     -H "X-Request-Source: cli" \
     -d @/absolute/path/to/test_payload.json
```

#### Option 2 — File Upload (multipart/form-data)

Use this to upload a .json or a compressed file.

**Sample payload (test_file.json)**
```json
{
  "ID1": {
    "SECTION": "Introduction",
    "CITATION": "This method is based on Smith et al. (2020)."
  },
  "ID2": {
    "SECTION": "",
    "CITATION": "Our results build upon prior work."
  }
}
```

curl command:

```bash
curl -X POST http://127.0.0.1:5000/cic/api/classify \
     -H "X-Request-Source: cli" \
     -F "file=@/absolute/path/to/test_file.json" \
     -F "mode=WS"
```

*Supported file types include .json, .zip, .tar, .gz, .bz2, .xz, and .7z.*
**If you pass an archive, remember to include the output file.zip and its path as `-o`**

:arrow_right: **In Option 2, mode must be passed as a separate form field (not embedded inside the file).**

### Batch testing

A ready-to-use test script is available at [`classifier/test/cic_test.sh`](../test/cic_test.sh). It submits several archive formats against a given base URL:

```bash
./cic_test.sh http://127.0.0.1:5000/cic /path/to/input_directory
```

The base URL must include the `/cic` prefix; the script appends `/api/classify` internally.

## JSON File Format
JSON files to be classified must contain citation organized with the same underlying structure, composed by `SECTION` and `CITATION` at least.
`SECTION` may also contain an empty value - empty string - while `CITATION` cannot be empty. Finally, beside this structure it is possible to include additional metadata which will be maintained and returned together with classification results, but will not be taken into account for the classification process.

```json
{
    "ID1": {
        "SECTION": "Introduction",
        "CITATION": "This is the citation context."
    },
    "ID2": {
        "SECTION": "Methods",
        "CITATION": "Another citation context."
    }
}
```

## Acknowledgements

This project uses open-source libraries and pre-trained models. We acknowledge the contributors of these resources.
