from pathlib import Path

# Define the root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure

# Define the path to the predefined mappings file
PREDEFINED_MAPPINGS_PATH = ROOT_DIR / 'cex/semantic_alignment/predefined_mappings.json'
SPECIAL_CASES_PATH = ROOT_DIR / 'cex/special_cases.json'
CONFIG_PATH = ROOT_DIR / 'cex/config.json'
UPLOAD_FOLDER = ROOT_DIR / 'cex/static/files'
DOWNLOAD_FOLDER = ROOT_DIR / 'cex/static/output'
PROCESSING_FOLDER = ROOT_DIR / 'cex/static/processing'