#!/bin/bash

# Check if both BASE_URL and INPUT_DIR are provided as arguments
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <base_url> <input_dir>"
  exit 1
fi

# Assign the base URL and input directory from the arguments
BASE_URL="$1"
INPUT_DIR="$2"
OUTPUT_DIR="$INPUT_DIR/CorrectResults"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# FOLDERS

echo "Processing ZIP file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_cls.zip" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Results_ZIP.zip"

echo "Processing TAR file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_cls.tar" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Results_TAR.zip"

echo "Processing 7Z file..."
curl -X POST -F "file=@$INPUT_DIR/json_to_cls.7z" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Results_7Z.zip"

# SINGLE FILES

echo "Processing BZ2 file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.bz2" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Result_BZ2.zip"

echo "Processing GZ file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.gz" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Result_GZ.zip"

echo "Processing XZ file..."
curl -X POST -F "file=@$INPUT_DIR/compression_test.json.xz" -F "mode=M" "$BASE_URL/api/classify" --output "$OUTPUT_DIR/Result_XZ.zip"

echo "All API tests completed successfully."
