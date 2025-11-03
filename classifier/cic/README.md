[![Read The Paper](https://img.shields.io/badge/Read_The_Paper-red?style=flat-square)](https://arxiv.org/abs/2407.13329) [![Go to the web application](https://img.shields.io/badge/Go%20to%20the%20web%20application-blue?style=flat-square)](http://137.204.64.4:81/cic/)

# Citation Intent Classifier [Release Candidate]

**Comprehensive Guide and Documentation**

---

## Table of Contents

- [Introduction](#introduction)
- [Folder Structure](#folder-structure)
- [Setup and Installation](#setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
- [Running the Application Locally](#running-the-application-locally)
- [Using the Web Interface](#using-the-web-interface)
  - [Access the Web Interface](#access-the-web-interface)
  - [Classify Text Manually](#classify-text-manually)
  - [Upload a JSON File](#upload-a-json-file)
- [Using the API](#using-the-api)
  - [API Endpoints](#api-endpoints)
  - [Request Parameters](#request-parameters)
  - [Usage with `curl`](#usage-with-curl)
    - [Classify Text Data](#classify-text-data)
    - [Upload a JSON File](#upload-a-json-file-1)
- [Testing with Shell Script](#testing-with-shell-script)
  - [Script Content](#script-content)
  - [Modifying the Script](#modifying-the-script)
  - [Making the Script Executable](#making-the-script-executable)
  - [Executing the Script](#executing-the-script)
- [JSON File Format](#json-file-format)
- [Notes and Best Practices](#notes-and-best-practices)
- [Acknowledgements](#acknowledgements)

---

## Introduction

The **Citation Intent Classifier** is made up of a web application and an API designed to classify citation contexts within research papers. Utilizing pre-trained language models, it analyzes citations to determine the intent of the author when citing.

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
│   │   │   ├── ModelsWithSections
│   │   │   │   ├── FFNN_SciCiteWS.pth
│   │   │   │   ├── WS_SciBERT_bkg.pt
│   │   │   │   ├── WS_SciBERT_met.pt
│   │   │   │   ├── WS_SciBERT_res.pt
│   │   │   │   ├── WS_XLNet_bkg.pt
│   │   │   │   ├── WS_XLNet_met.pt
│   │   │   │   └── WS_XLNet_res.pt
│   │   │   └── README.md
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

## Setup and Installation

### Prerequisites

- **Python 3.9 or higher**
- **`pip` package manager**

### Installation Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/opencitations/cec.git
    cd cec/classifier
    ```

2. **Create a Virtual Environment (Optional but Recommended)**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Required Packages**

    ```bash
    pip install -r requirements.txt
    ```

4. **Download Model Files**

    Download and place the pre-trained model files in the appropriate directories as shown in the folder structure. Ensure that the `models/` directory contains all necessary `.pt` and `.pth` files (7 models each dir).</br>Download links:
   - **Ensemble Model Without Section Titles**: [EnsIntWos](https://doi.org/10.5281/zenodo.11652578)
   - **Ensemble Model With Section Titles**: [EnsIntWS](https://doi.org/10.5281/zenodo.11653642)

## Running the Application Locally

To run the application locally, you need to specify the path to the `src` directory, which contains the necessary source code and models.
Do it after installation and within the classifier directory, as shown above.

```bash
python -m cic.main --src_path "/absolute/path/to/cic/src"
```

**Note:** Replace `"/absolute/path/to/cic/src"` with the actual absolute path to your `cic/src` directory.

- **Example:**

    If your project is located at `/home/user/projects/cec`, the command would be:

    ```bash
    python -m cic.main --src_path "/home/user/projects/cec/classifier/cic/src"
    ```

    If prefix is requested then use `"/cic"` as follows:

    ```bash
    python -m cic.main --src_path "/home/user/projects/cec/classifier/cic/src" --prefix "/cic"
    ```

The application will start running locally by default.

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

> [!NOTE]  
> All the examples are presented with the local endpoint: `http://127.0.0.1:5000/`.</br>
> To interact with the live API, replace the base URL with the production endpoint:
> `http://137.204.64.4:81/`.

### API Endpoints

- **POST** `/api/classify`: Classify citation contexts provided in the request.

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

## Testing with Shell Script

To automate testing of the API with various compressed files, you can use the provided shell script, which presents different compression formats. Adapt it to your needs.

### Script Content

```bash
#!/bin/bash

# Define base directories
INPUT_DIR="/path/to/your/input_directory"
OUTPUT_DIR="$INPUT_DIR/Results"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# FOLDERS

echo "Processing ZIP file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_classify.zip" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Results_ZIP.zip"

echo "Processing TAR file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_classify.tar" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Results_TAR.zip"

echo "Processing 7Z file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_classify.7z" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Results_7Z.zip"

# SINGLE FILES

echo "Processing BZ2 file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.bz2" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Result_BZ2.zip"

echo "Processing GZ file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.gz" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Result_GZ.zip"

echo "Processing XZ file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.xz" -F "mode=mixed" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Result_XZ.zip"

echo "All API tests completed successfully."
```

### Modifying the Script

- **`INPUT_DIR`**: Change `"/path/to/your/input_directory"` to the path where your input files are located.
- **`OUTPUT_DIR`**: By default, it creates a `Results` directory inside your input directory to store the outputs. You can change this if desired.

### Making the Script Executable

1. Save the script to a file, for example, `test_api.sh`.
2. Make the script executable:

    ```bash
    chmod +x test_api.sh
    ```

### Executing the Script

Run the script using the following command:

```bash
./test_api.sh
```

Ensure that the server is running before executing the script.

## JSON File Format:
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

## Docker compose
See this file **DOCKER_HOW_TO.md**

## Notes and Best Practices

- **Data Format**: Ensure that all JSON files follow the required structure for the classifier to work properly.
- **Error Handling**: The application provides manifest files detailing any errors encountered during processing.
- **Logging**: Logs are essential for debugging. Check the application logs if you encounter issues.

## Acknowledgements

This project utilizes several open-source libraries and pre-trained models. We acknowledge the contributors of these resources for their work.
