import os
import zipfile
import shutil
from zipfile import Path

from setuptools.py312compat import shutil_rmtree


def unzip_and_sort(zip_path, output_dir):
    """
    Unzips a file and sorts extracted files into folders based on their extension.

    Args:
        zip_path (str): Path to the zip file.
        output_dir (str): Directory where files will be extracted and sorted.
    """

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Extract all files to a temp folder
    temp_extract_dir = os.path.join(output_dir, "temp_extract")
    os.makedirs(temp_extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    # Walk through extracted files
    for root, _, files in os.walk(temp_extract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower().lstrip('.')  # get extension without dot

            # If no extension, put in "no_extension" folder
            if not ext:
                ext = "no_extension"

            # Create directory for extension
            ext_dir = os.path.join(output_dir, ext.upper())
            os.makedirs(ext_dir, exist_ok=True)

            # Move file to corresponding folder
            shutil.move(file_path, os.path.join(ext_dir, file))

    # Remove temporary extraction folder
    shutil.rmtree(temp_extract_dir)
    print(f"Files extracted and sorted into folders inside '{output_dir}'.")

#unzip_and_sort("/media/marta/T7 Touch/ORE_corpus/GROBID/Grobid_base/from_processed/processed_pdfs_1757839815.921441.zip", "/media/marta/T7 Touch/ORE_corpus/GROBID/Grobid_base/from_processed")

from pathlib import Path
import shutil


def create_ground_truth_to_use(ground_truth, predictions, output_path):
    gt_dir = Path(ground_truth)
    pred_dir = Path(predictions)
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Make a dict mapping gt filenames → Path object
    gt_files = {f.name: f for f in gt_dir.glob("*.json")}

    # Iterate over prediction files
    for pred_file in pred_dir.glob("*.json"):
        pred_name = pred_file.name

        if pred_name in gt_files:
            shutil.copy(gt_files[pred_name], out_dir / pred_name)
        else:
            print(f"No GT file for prediction: {pred_name}")


def remove_pre_json(folder):

    json_to_remove = list(Path(folder).rglob("*pre.json"))

    for json_file in json_to_remove:
        os.remove(json_file)
