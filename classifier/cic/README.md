[![Read The Paper](https://img.shields.io/badge/Read_The_Paper-red?style=flat-square)](https://arxiv.org/abs/2407.13329) [![Go to the web application](https://img.shields.io/badge/Go%20to%20the%20web%20application-blue?style=flat-square)](http://137.204.64.4:81/cic/)

# Citation Intent Classifier [Version: Alpha]

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
  - [Example Usage with `curl`](#example-usage-with-curl)
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
├── ExampleAPI_Command.txt
├── README.md
├── cic
│   ├── README.md
│   ├── __init__.py
│   ├── blueprints
│   │   ├── __init__.py
│   │   ├── cic_api.py
│   │   └── web_interface.py
│   ├── main.py
│   ├── predictor_manager.py
│   ├── sh
│   │   ├── README.md
│   │   ├── check-and-run.sh
│   │   ├── run.sh
│   │   └── stop.sh
│   ├── src
│   │   ├── __init__.py
│   │   ├── binary_classifiers.py
│   │   ├── data_processor.py
│   │   ├── metaclassifiers.py
│   │   ├── models
│   │   │   ├── NoSections
│   │   │   │   ├── MetaClassifierNoSections.pth
│   │   │   │   ├── NoSec_SciBERT_background_model.pt
│   │   │   │   ├── NoSec_SciBERT_method_model.pt
│   │   │   │   ├── NoSec_SciBERT_result_model.pt
│   │   │   │   ├── NoSec_XLNet_background_model.pt
│   │   │   │   ├── NoSec_XLNet_method_model.pt
│   │   │   │   └── NoSec_XLNet_result_model.pt
│   │   │   ├── README.md
│   │   │   └── Sections
│   │   │       ├── MetaClassifierSections.pth
│   │   │       ├── SciBERT_background_model.pt
│   │   │       ├── SciBERT_method_model.pt
│   │   │       ├── SciBERT_result_model.pt
│   │   │       ├── XLNet_background_model.pt
│   │   │       ├── XLNet_method_model.pt
│   │   │       └── XLNet_result_model.pt
│   │   └── predictor.py
│   ├── static
│   │   ├── css
│   │   │   ├── classifier.css
│   │   │   └── index.css
│   │   ├── img
│   │   │   ├── graspos.svg
│   │   │   ├── graspos_white.svg
│   │   │   ├── oc.svg
│   │   │   └── oc_white.svg
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
└── requirements.txt
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

    Download and place the pre-trained model files in the appropriate directories as shown in the folder structure. Ensure that the `models/` directory contains all necessary `.pt` and `.pth` files (7 models each dir).
Download links:
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

The application will start running locally by default.

## Using the Web Interface

### Access the Web Interface

Open a web browser and navigate to ?????.

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

### API Endpoints

- **POST** `/api/classify`: Classify citation contexts provided in the request.

### Request Parameters

????

### Example Usage with `curl`

curl -X POST -F "file=@$INPUT_DIR/compression_test.zip" -F "mode=M" "http://127.0.0.1:5000/api/classify" --output "$OUTPUT_DIR/Result_XZ.zip"

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

## Notes and Best Practices

- **Data Format**: Ensure that all JSON files follow the required structure for the classifier to work properly.
- **Error Handling**: The application provides manifest files detailing any errors encountered during processing.
- **Logging**: Logs are essential for debugging. Check the application logs if you encounter issues.

## Acknowledgements

This project utilizes several open-source libraries and pre-trained models. We acknowledge the contributors of these resources for their work.
