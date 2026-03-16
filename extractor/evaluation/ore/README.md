# Process for creating the ORE corpus

The `main.py` orchestrator automates the end-to-end workflow for extracting citations from Open Research Europe (ORE) articles. It integrates XML downloading, corpus creation (PDF/TEI), and CEX prediction generation into a single execution flow.

## Overview

The pipeline executes the following steps in order:

1.  **Download (`download`)**: Fetches JATS XML files from the ORE published list.
2.  **Corpus Creation (`corpus`)**: Processes XML, downloads corresponding PDFs, and transforms JATS to TEI XML (requires Saxon).
3.  **Predictions (`predictions`)**: Sends the processed PDFs to the CEX API and saves the resulting predictions (JSON) and extraction details (ZIP).

## 📋 Prerequisites

-   **Python 3.9+**
-   **Java Runtime Environment (JRE)**: Required for Saxon XSLT transformations.
-   **Saxon HE**: A local copy of the `saxon-he-x.x.jar` file.
-   **Network Access**: Ability to reach `open-research-europe.ec.europa.eu` and your configured CEX API endpoint.

## ⚙️ Configuration

Before running the pipeline, open `main.py` and configure the `CONFIG` dictionary at the top of the file to match your local environment:

```python
CONFIG = {
    'dirs': {
        'log_dir': '/path/to/logs',           # Where logs are saved
        'xml_download': '/path/to/xml',       # Destination for ORE XML files
        'corpus': '/path/to/corpus',          # Destination for PDFs and TEI files
        'predictions': '/path/to/json',       # Destination for CEX JSON output
        'cex_zips': '/path/to/zips',          # Destination for CEX ZIP output
    },
    'files': {
        'saxon_jar': '/path/to/saxon-he.jar', # Absolute path to Saxon JAR
        'xslt': 'jats-to-tei.xsl',            # Path to the XSLT stylesheet
    },
    'cex_api': {
        'url': 'http://localhost:8000/api',   # CEX Extractor API URL
        'timeout': 480,                       # Timeout in seconds per PDF
    }
}
```

## 🏃 Usage

You can run the entire pipeline or specific steps using the command line interface.

### Run Everything

Executes Download → Corpus → Predictions in sequence.

```bash
python main.py --all
```

### Run Specific Steps

You can run individual steps or combinations of steps.

#### Only Download:

```bash
python main.py --step download
```

#### Only Corpus Creation:

```bash
python main.py --step corpus
```

#### Only Predictions:

```bash
python main.py --step predictions
```

#### Multiple Steps (e.g., Corpus and Predictions):

```bash
python main.py --step corpus --step predictions
```


