from os import makedirs, sep, walk
from os.path import basename, exists, isdir
import shutil
import tarfile
import pathlib
import zipfile
import zstandard as zstd
import os
import json
from flask import Blueprint, request, jsonify, current_app, url_for, send_file, after_this_request, send_from_directory
from werkzeug.utils import secure_filename
from extractor.cex.combined import PDFProcessor
from extractor.cex.semantic_alignment.align_headings import run
import logging
import datetime
import traceback
from extractor.cex.settings import PREDEFINED_MAPPINGS_PATH
from extractor.cex.main import get_all_files_by_type, upload_manifest
from extractor.cex.api.api_cli import process_pdf_file
import concurrent.futures

api_blueprint = Blueprint('api', __name__)
PREFIX="/"

@api_blueprint.route('/extractor', methods=['POST', 'GET'])

def api_process_file():

    save_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), current_app.config['UPLOAD_FOLDER'])
    download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), current_app.config['DOWNLOAD_FOLDER'])

    os.makedirs(save_location, exist_ok=True)
    os.makedirs(download_location, exist_ok=True)

    manifest = list()

    # Check if a file was uploaded
    if 'input_files_or_archives' not in request.files:
        manifest.append({"status": "error", "error": "No files uploaded"})
        upload_manifest(manifest, download_location)

        download_url = create_zip_file(download_location)

        return jsonify({'download_url': download_url}), 200

    files = request.files.getlist('input_files_or_archives')
    if not files:
        manifest.append({"status": "error", "error": "No files selected"})
        upload_manifest(manifest, download_location)

        download_url = create_zip_file(download_location)

        return jsonify({'download_url': download_url}), 200

    perform_alignment = request.form.get('perform_alignment', 'false').lower() == 'true'
    create_rdf = request.form.get('create_rdf', 'false').lower() == 'true'
    max_workers = request.form.get('max_workers')
    if max_workers:
        max_workers = int(max_workers)
    else:
        max_workers = 1

    pdfs_to_process = set()
    unsupported_files = set()

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(save_location, filename)
        file.save(file_path)
        pdfs, unsupported_files_in_input, targz_fd = get_all_files_by_type(file_path, '.pdf', save_location)
        if pdfs:
            pdfs_to_process |= set(pdfs)
        if unsupported_files_in_input:
            unsupported_files |= set(unsupported_files_in_input)

    if unsupported_files:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)

    if pdfs_to_process:
        # Parallel processing of PDF files
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_pdf = {
                executor.submit(process_pdf_file, pdf, download_location, perform_alignment, create_rdf): pdf for pdf
                in pdfs_to_process}
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    # Collect the result (manifest_info) from each worker process
                    manifest_info = future.result()
                    manifest.append(manifest_info)
                except Exception as exc:
                    manifest_info = {"filename": os.path.basename(pdf), "status": "error", "error": str(exc)}
                    manifest.append(manifest_info)

    upload_manifest(manifest, download_location)

    shutil.rmtree(save_location)

    download_url = create_zip_file(download_location)

    return jsonify({'download_url': download_url}), 200

def create_zip_file(download_location):
    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.timestamp()

    zip_name = 'processed_pdfs_' + str(timestamp) + '.zip'
    zip_path = os.path.join(download_location, zip_name)

    # Create the zip file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(download_location):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                # Exclude the zip file itself from being zipped
                if file_path != zip_path:
                    zipf.write(file_path, os.path.relpath(file_path, download_location))

    download_url = url_for('api.download_file', filename=zip_name, _external=True)
    return download_url


@api_blueprint.route(PREFIX+'/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                         current_app.config['DOWNLOAD_FOLDER'])
        @after_this_request
        def delete_zip(response):
            # Elimina il file dopo il download
            files = []
            dir = []
            for entry in os.scandir(download_location):
                if entry.is_file():
                    files.append(entry.name)
                elif entry.is_dir():
                    dir.append(entry)
            for file in files:
                os.remove(os.path.join(download_location, file))
            for x in dir:
                shutil.rmtree(x)
            return response

        return send_from_directory(download_location, filename, as_attachment=True)

    except Exception as e:
        logging.error(f"Error serving file: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500