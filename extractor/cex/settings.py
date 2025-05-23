from pathlib import Path

# Define the root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure

ROOT_DIR = "/cex/"

# Define the path to the predefined mappings file
PREDEFINED_MAPPINGS_PATH = ROOT_DIR+'semantic_alignment/predefined_mappings.json'
SPECIAL_CASES_PATH = ROOT_DIR+'special_cases.json'
CONFIG_PATH = ROOT_DIR+'config.json'
UPLOAD_FOLDER = ROOT_DIR+'static/files'
DOWNLOAD_FOLDER = ROOT_DIR+'static/output'
PROCESSING_FOLDER = ROOT_DIR+'static/processing'
