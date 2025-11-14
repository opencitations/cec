
import shutil
import zipfile
import os
from flask import Blueprint, request, jsonify, current_app, url_for, send_file, after_this_request, send_from_directory
from werkzeug.utils import secure_filename
import logging
import datetime
from utils import get_all_files_by_type, upload_manifest, process_pdf_file
import concurrent.futures
import uuid

api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/extractor', methods=['POST', 'GET'])

def api_process_file():
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    save_location = os.path.join(current_app.config['UPLOAD_FOLDER'], request_id)
    download_location = os.path.join(current_app.config['DOWNLOAD_FOLDER'], request_id)

    # Clean up just in case (should be empty anyway)
    os.makedirs(save_location, exist_ok=True)
    os.makedirs(download_location, exist_ok=True)

    manifest = list()

    # Check if a file was uploaded
    if 'input_files_or_archives' not in request.files:
        manifest.append({"status": "error", "error": "No files uploaded"})
        upload_manifest(manifest, download_location)
        zip_url = create_zip_file(download_location, request_id)
        return jsonify({'download_url': zip_url}), 200

    files = request.files.getlist('input_files_or_archives')
    if not files:
        manifest.append({"status": "error", "error": "No files selected"})
        upload_manifest(manifest, download_location)
        zip_url = create_zip_file(download_location, request_id)
        return jsonify({'download_url': zip_url}), 200

    perform_alignment = request.form.get('perform_alignment', 'false').lower() == 'true'
    create_rdf = request.form.get('create_rdf', 'false').lower() == 'true'
    max_workers = int(request.form.get('max_workers', 1))

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

    for el in unsupported_files:
        manifest.append({"filename": os.path.basename(el), "status": "error", "error": "unsupported file type"})

    if pdfs_to_process:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_pdf = {
                executor.submit(process_pdf_file, pdf, download_location, perform_alignment, create_rdf): pdf
                for pdf in pdfs_to_process
            }
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    manifest.append(future.result())
                except Exception as exc:
                    manifest.append({
                        "filename": os.path.basename(pdf),
                        "status": "error",
                        "error": str(exc)
                    })

    upload_manifest(manifest, download_location)
    shutil.rmtree(save_location, ignore_errors=True)
    zip_url = create_zip_file(download_location, request_id)

    return jsonify({'download_url': zip_url}), 200

def create_zip_file(download_location, request_id):
    timestamp = int(datetime.datetime.now().timestamp())
    zip_name = f'processed_pdfs_{timestamp}.zip'
    zip_path = os.path.join(download_location, zip_name)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for foldername, _, filenames in os.walk(download_location):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                if file_path != zip_path:
                    zipf.write(file_path, os.path.relpath(file_path, download_location))

    # Return the download route with the folder name
    return url_for('api.download_file', folder=request_id, filename=zip_name, _external=True)



@api_blueprint.route('/download/<folder>/<filename>', methods=['GET'])
def download_file(folder, filename):
    try:
        download_location = os.path.join(current_app.config['DOWNLOAD_FOLDER'], folder)

        @after_this_request
        def delete_zip(response):
            shutil.rmtree(download_location, ignore_errors=True)
            return response

        return send_from_directory(download_location, filename, as_attachment=True)

    except Exception as e:
        logging.error(f"Error serving file: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500
