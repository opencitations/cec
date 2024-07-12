from os import makedirs, sep, walk
from os.path import basename, exists, isdir
import shutil
import tarfile
import pathlib
import zipfile
import zstandard as zstd
import os
import json
from flask import Blueprint, request, jsonify, current_app, url_for, send_file, after_this_request
from werkzeug.utils import secure_filename
from extractor.cex.combined import PDFProcessor
from extractor.cex.semantic_alignment.align_headings import run
import logging
import datetime
import traceback
from extractor.cex.settings import PREDEFINED_MAPPINGS_PATH
api_blueprint = Blueprint('api', __name__)

def get_all_files_by_type(i_dir_or_compr_or_file:str, req_type:str, save_location):
    result = []
    unsupported_file_type = []
    targz_fd = None
    if isdir(i_dir_or_compr_or_file):
        for cur_dir, cur_subdir, cur_files in walk(i_dir_or_compr_or_file):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(os.path.join(cur_dir, cur_file))
    if i_dir_or_compr_or_file.endswith("tar.gz"):
        targz_fd = tarfile.open(i_dir_or_compr_or_file, "r:gz", encoding="utf-8")
        for cur_file in targz_fd:
            if cur_file.name.endswith(req_type) and not basename(cur_file.name).startswith("."):
                result.append(cur_file)
        #targz_fd.close()
    elif i_dir_or_compr_or_file.endswith(".tar"):
        dest_dir = save_location + sep + "decompr_tar_dir"
        if not exists(dest_dir):
            makedirs(dest_dir)
        targz_fd = tarfile.open(i_dir_or_compr_or_file, "r:*", encoding="utf-8")
        targz_fd.extractall(dest_dir)

        for cur_dir, cur_subdir, cur_files in walk(dest_dir):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(cur_dir + sep + cur_file)

        targz_fd.close()

    elif i_dir_or_compr_or_file.endswith("zip"):
        with zipfile.ZipFile(i_dir_or_compr_or_file, 'r') as zip_ref:
            dest_dir = save_location + sep + "decompr_zip_dir"
            if not exists(dest_dir):
                makedirs(dest_dir)
            zip_ref.extractall(dest_dir)
        for cur_dir, cur_subdir, cur_files in walk(dest_dir):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(cur_dir + sep + cur_file)

    elif i_dir_or_compr_or_file.endswith("zst"):
        input_file = pathlib.Path(i_dir_or_compr_or_file)
        dest_dir = save_location + sep + "_decompr_zst_dir"
        with open(input_file, 'rb') as compressed:
            decomp = zstd.ZstdDecompressor()
            if not exists(dest_dir):
                makedirs(dest_dir)
            output_path = pathlib.Path(dest_dir) / input_file.stem
            if not exists(output_path):
                with open(output_path, 'wb') as destination:
                    decomp.copy_stream(compressed, destination)
        for cur_dir, cur_subdir, cur_files in walk(dest_dir):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(cur_dir + sep + cur_file)
    elif os.path.isfile(i_dir_or_compr_or_file):
        if i_dir_or_compr_or_file.endswith(req_type):
            result.append(i_dir_or_compr_or_file)
        else:
            unsupported_file_type.append(i_dir_or_compr_or_file)
    return result, unsupported_file_type, targz_fd


def upload_manifest(manifest_list, processing_location, zip_path):
    with open(os.path.join(processing_location, "manifest.json"), 'w') as file:
        json.dump(manifest_list, file, indent=4)

    temp_dir_path = pathlib.Path(processing_location)

    with zipfile.ZipFile(zip_path, mode="w") as archive:
        for file_path in temp_dir_path.rglob("*"):
            archive.write(file_path,
                          arcname=file_path.relative_to(temp_dir_path))

def validate_file_list(file_list):
    # Required file types and their initial counts
    required_counts = {'.xml': 0, '.json': 0, '.ttl': 0}

    # Check each file in the list
    for file in file_list:
        ext = file.lower().rsplit('.', 1)[-1]  # Extract file extension and make it lowercase
        ext = '.' + ext
        if ext in required_counts:
            required_counts[ext] += 1
        else:
            return False  # A file with an unexpected extension is found

    # Ensure each required file type is present exactly once
    return all(count == 1 for count in required_counts.values()) and len(file_list) == 3


def process_pdf(pdf, processing_location, perform_alignment, manifest, config_path):
    pdf_filename = os.path.basename(pdf)
    manifest_info = {"filename": pdf_filename}
    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.timestamp()
    output_intermediate_dir = os.path.join(processing_location, f"{pdf_filename.replace('.pdf', '')}_{timestamp}")
    os.makedirs(output_intermediate_dir, exist_ok=True)
    current_stage = "Initializing PDF processor"
    generated_xml = False

    processor = PDFProcessor(input_pdf_path=pdf, output_tei_path=output_intermediate_dir,
                             output_json_path=output_intermediate_dir, config_path=config_path)

    try:
        # grobid extraction
        current_stage = "Generating TEI/XML file"
        input_pdf_path, output_tei_path = processor.create_xml_tei()
        generated_xml = True

    except Exception as e:
        current_datetime = datetime.datetime.now()
        timestamp = current_datetime.timestamp()
        error_log_path = os.path.join(output_intermediate_dir, f"error_log_{timestamp}.json")
        with open(error_log_path, 'w') as error_file:
            json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                       "traceback": traceback.format_exc()}, error_file, indent=4)

    if generated_xml:
        try:
            # citations' context + section heading
            current_stage = "Generating JSON file"
            processor.create_json(input_pdf_path, output_tei_path)
            # aligning headings
            if perform_alignment:
                current_stage = "Aligning headings"
                json_files = [el for el in os.listdir(output_intermediate_dir) if
                              el.endswith(".json") and el.startswith(str(pdf_filename).replace(".pdf", ""))]
                if json_files:
                    json_file_path = os.path.join(output_intermediate_dir, json_files[0])
                    try:
                        run(json_file_path,
                            ["Introduction", "Related Works", "Methods and Materials", "Results", "Discussion",
                             "Conclusion"],
                            json_file_path, str(PREDEFINED_MAPPINGS_PATH))
                    except Exception as e:
                        current_datetime = datetime.datetime.now()
                        timestamp = current_datetime.timestamp()
                        error_log_path = os.path.join(output_intermediate_dir, f"error_log_{timestamp}.json")
                        with open(error_log_path, 'w') as error_file:
                            json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                                       "traceback": traceback.format_exc()}, error_file, indent=4)
        except Exception as e:
            current_datetime = datetime.datetime.now()
            timestamp = current_datetime.timestamp()
            error_log_path = os.path.join(output_intermediate_dir, f"error_log_{timestamp}.json")
            with open(error_log_path, 'w') as error_file:
                json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                           "traceback": traceback.format_exc()}, error_file, indent=4)
        try:
            # rdf creation
            current_stage = "Generating RDF file"
            processor.create_rdf(input_pdf_path, output_tei_path)

        except Exception as e:
            current_datetime = datetime.datetime.now()
            timestamp = current_datetime.timestamp()
            error_log_path = os.path.join(output_intermediate_dir, f"error_log_{timestamp}.json")
            with open(error_log_path, 'w') as error_file:
                json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                           "traceback": traceback.format_exc()}, error_file, indent=4)

    single_pdf = os.path.join(processing_location, "single_pdf")
    shutil.copytree(output_intermediate_dir, single_pdf)
    processing_outputs = os.listdir(single_pdf)
    files = dict()
    status = "error"
    if validate_file_list(processing_outputs):
        status = "success"
    just_error_logs = all(el.startswith('error_log') for el in processing_outputs)

    if just_error_logs:
        files['errors'] = [el for el in processing_outputs if el.startswith('error_log')]
    else:
        for el in processing_outputs:
            if el.endswith('.tei.xml'):
                files["tei"] = {'status': 'processed', 'file': el}
            if el.endswith('.json') and not el.startswith('error_log'):
                files["json"] = {'status': 'processed', 'file': el}
            if el.endswith('.ttl'):
                files["rdf"] = {'status': 'processed', 'file': el}
            if el.startswith('error_log'):
                status = "partial processing"
                log_file_path = os.path.join(single_pdf, el)
                with open(log_file_path, 'r') as file:
                    data = json.load(file)
                    stage = data['current_stage']
                    if 'TEI/XML' in stage:
                        files["tei"] = {'status': 'error', 'error': data['error'], 'file': el}

                    if 'JSON' in stage or 'headings' in stage:
                        files["json"] = {'status': 'error', 'error': data['error'], 'file': el}

                    if 'RDF' in stage:
                        files["rdf"] = {'status': 'error', 'error': data['error'], 'file': el}

    manifest_info["status"] = status
    manifest_info["output_directory"] = f"{pdf_filename.replace('.pdf', '')}_{timestamp}"
    manifest_info["files"] = files
    manifest.append(manifest_info)

    shutil.rmtree(single_pdf)

@api_blueprint.route('/extractor', methods=['POST', 'GET'])

def api_process_file():

    save_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), current_app.config['UPLOAD_FOLDER'])
    download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), current_app.config['DOWNLOAD_FOLDER'])
    processing_location = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                       current_app.config['PROCESSING_FOLDER'])

    os.makedirs(save_location, exist_ok=True)
    os.makedirs(download_location, exist_ok=True)
    os.makedirs(processing_location, exist_ok=True)

    manifest = list()

    output_dir = request.form.get('output')
    if output_dir:
        # Generate a unique filename for the ZIP
        zip_path = os.path.join(download_location, output_dir)
    else:
        current_datetime = datetime.datetime.now()
        timestamp = current_datetime.timestamp()
        zip_path = os.path.join(download_location, f"processed_pdfs{timestamp}.zip")

    # Check if a file was uploaded
    if 'input_files_or_archives' not in request.files:
        manifest.append({"status": "error", "error": "No files uploaded"})
        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        download_url = url_for('api.download_file', _external=True)

        return jsonify({'download_url': download_url}), 200

    files = request.files.getlist('input_files_or_archives')
    if not files:
        manifest.append({"status": "error", "error": "No files selected"})
        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(processing_location)
        download_url = url_for('api.download_file', _external=True)

        return jsonify({'download_url': download_url}), 200

    perform_alignment = request.form.get('perform_alignment', 'false').lower() == 'true'

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

    if unsupported_files and pdfs_to_process:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)

        for pdf in list(pdfs_to_process):
            process_pdf(pdf, processing_location, perform_alignment, manifest, config_path="config.json")

        upload_manifest(manifest, processing_location, zip_path)

        shutil.rmtree(save_location)
        shutil.rmtree(processing_location)

        download_url = url_for('api.download_file', _external=True)

        return jsonify({'download_url': download_url}), 200

    elif unsupported_files and not pdfs_to_process:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)
        upload_manifest(manifest, processing_location, zip_path)
        shutil.rmtree(save_location)
        shutil.rmtree(processing_location)
        download_url = url_for('api.download_file', _external=True)

        return jsonify({'download_url': download_url}), 200

    elif pdfs_to_process:
        for pdf in list(pdfs_to_process):
            process_pdf(pdf, processing_location, perform_alignment, manifest, config_path="config.json")
            print(f"{pdf} processed")

        upload_manifest(manifest, processing_location, zip_path)

        shutil.rmtree(save_location)
        shutil.rmtree(processing_location)

        download_url = url_for('api.download_file', _external=True)

        return jsonify({'download_url': download_url}), 200

    upload_manifest(manifest, processing_location, zip_path)

    shutil.rmtree(save_location)
    shutil.rmtree(processing_location)

    download_url = url_for('api.download_file', _external=True)

    return jsonify({'download_url': download_url}), 200


@api_blueprint.route('/download', methods=['GET'])
def download_file():
    try:
        download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                         current_app.config['DOWNLOAD_FOLDER'])
        output_content = os.listdir(download_location)
        zip_file = [el for el in output_content if el.endswith('.zip')][0]
        zip_path = os.path.join(download_location, zip_file)

        @after_this_request
        def delete_zip(response):
            # Elimina il file dopo il download
            download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                             current_app.config['DOWNLOAD_FOLDER'])
            files = []
            for entry in os.scandir(download_location):
                if entry.is_file():
                    files.append(entry.name)
            for file in files:
                os.remove(os.path.join(download_location, file))
            return response

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Error serving file: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 500