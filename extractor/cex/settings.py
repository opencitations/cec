from pathlib import Path

# Define the root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure

# Define the path to the predefined mappings file
PREDEFINED_MAPPINGS_PATH = '/semantic_alignment/predefined_mappings.json'
SPECIAL_CASES_PATH = '/special_cases.json'
CONFIG_PATH = '/config.json'
UPLOAD_FOLDER = '/static/files'
DOWNLOAD_FOLDER = '/static/output'
PROCESSING_FOLDER = '/static/processing'
