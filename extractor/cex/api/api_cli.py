import requests
import argparse
import os
import datetime

from werkzeug.utils import secure_filename
from routes import process_pdf, get_all_files_by_type, upload_manifest
import shutil


def main():
    parser = argparse.ArgumentParser(description='Upload PDF files for processing.')
    parser.add_argument('input_files_or_archives', nargs='+', help='Paths to the PDF files or archives to upload')
    parser.add_argument('--download_folder', help='Folder to download the processed files', required=True)
    parser.add_argument('--zip_name', help='Name of the output zip file', required=False)
    parser.add_argument('--perform_alignment', action='store_true', help='Whether to perform semantic alignment')

    args = parser.parse_args()

    download_location = args.download_folder
    processing_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/processing_cli')

    os.makedirs(download_location, exist_ok=True)
    os.makedirs(processing_location, exist_ok=True)

    if args.zip_name:
        # Generate a unique filename for the ZIP
        zip_path = os.path.join(download_location, args.zip_name)
    else:
        current_datetime = datetime.datetime.now()
        timestamp = current_datetime.timestamp()
        zip_path = os.path.join(download_location, f"processed_pdfs{timestamp}.zip")

    manifest = list()

    files = args.input_files_or_archives
    if not files:
        manifest.append({"status": "error", "error": "No files selected"})
        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        return f"The output zip is available at {download_location}"

    perform_alignment = str(args.perform_alignment).lower() == 'true'

    pdfs_to_process = set()
    unsupported_files = set()

    for file_path in files:
        save_location = os.path.dirname(file_path)
        pdfs, unsupported_files_in_input, targz_fd = get_all_files_by_type(file_path, '.pdf', save_location)
        if pdfs:
            pdfs_to_process |= set(pdfs)
        if unsupported_files_in_input:
            unsupported_files |= set(unsupported_files_in_input)

    if unsupported_files and pdfs_to_process:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)

        for pdf in list(pdfs_to_process):
            process_pdf(pdf, processing_location, perform_alignment, manifest, config_path="extractor/cex/config.json")

        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        return print(f"The output zip is available at {download_location}")

    elif unsupported_files and not pdfs_to_process:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)
        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        return print(f"The output zip is available at {download_location}")

    elif pdfs_to_process:
        for pdf in list(pdfs_to_process):
            process_pdf(pdf, processing_location, perform_alignment, manifest, config_path="extractor/cex/config.json")

        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        return print(f"The output zip is available at {download_location}")

    upload_manifest(manifest, processing_location, zip_path)
    shutil.rmtree(processing_location)
    return print(f"The output zip is available at {download_location}")


if __name__ == '__main__':
    main()
