import logging
import shutil
import json

from flask import Flask, render_template, send_from_directory, after_this_request, jsonify, url_for
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, IntegerField
from werkzeug.utils import secure_filename
import tarfile
import os
import pathlib
from os import makedirs, sep, walk
from os.path import basename, exists, isdir
from wtforms.fields.simple import BooleanField
from wtforms.validators import InputRequired
from combined import PDFProcessor
import zipfile
from datetime import datetime
import concurrent.futures
from wtforms.validators import NumberRange
import zstandard as zstd
from .settings import UPLOAD_FOLDER, DOWNLOAD_FOLDER, PROCESSING_FOLDER

def get_all_files(folder_path):
    files = []
    for entry in os.scandir(folder_path):
        if entry.is_file():
            files.append(entry.name)
    return files

def get_all_files_by_type(i_dir_or_compr_or_file:str, req_type:str, save_location):
    result = []
    unsupported_file_type = []
    targz_fd = None
    if isdir(i_dir_or_compr_or_file):
        for cur_dir, cur_subdir, cur_files in walk(i_dir_or_compr_or_file):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(os.path.join(cur_dir, cur_file))
                elif not cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    unsupported_file_type.append(cur_dir + sep + cur_file)
    if i_dir_or_compr_or_file.endswith("tar.gz"):
        dest_dir = save_location + sep + "decompr_targz_dir"
        if not exists(dest_dir):
            makedirs(dest_dir)
        targz_fd = tarfile.open(i_dir_or_compr_or_file, "r:gz", encoding="utf-8")
        targz_fd.extractall(dest_dir)
        # Iterate over the extracted files and check if they match the required type
        for cur_dir, cur_subdir, cur_files in walk(dest_dir):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(os.path.join(cur_dir, cur_file))  # Add full file path to result list
                elif not cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    unsupported_file_type.append(cur_dir + sep + cur_file)
        targz_fd.close()  # Close the tar.gz file

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
                elif not cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    unsupported_file_type.append(cur_dir + sep + cur_file)
        targz_fd.close()

    elif i_dir_or_compr_or_file.endswith("zip"):
        with zipfile.ZipFile(i_dir_or_compr_or_file, 'r') as zip_ref:
            dest_dir = os.path.join(save_location, "decompr_zip_dir")
            if not exists(dest_dir):
                makedirs(dest_dir)
            zip_ref.extractall(dest_dir)
        for cur_dir, cur_subdir, cur_files in walk(dest_dir):
            for cur_file in cur_files:
                if cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    result.append(cur_dir + sep + cur_file)
                elif not cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    unsupported_file_type.append(cur_dir + sep + cur_file)

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
                elif not cur_file.endswith(req_type) and not basename(cur_file).startswith("."):
                    unsupported_file_type.append(cur_dir + sep + cur_file)

    elif os.path.isfile(i_dir_or_compr_or_file):
        if i_dir_or_compr_or_file.endswith(req_type):
            result.append(i_dir_or_compr_or_file)
        else:
            unsupported_file_type.append(i_dir_or_compr_or_file)

    return result, unsupported_file_type, targz_fd

def create_zip_folder(input_folder, output_zip_file):
    files = get_all_files(input_folder)
    with zipfile.ZipFile(output_zip_file, 'w') as zip_file:
        for file in files:
            if (file[-4:] == '.xml') | (file[-5:] == '.json') | (file[-7:] == '.jsonld'):
                file_path = os.path.join(input_folder, file)
                zip_file.write(file_path, os.path.relpath(file_path, input_folder))

def delete_all_files(folder_path):
    files = get_all_files(folder_path)
    for file in files:
        os.remove(os.path.join(folder_path, file))

def upload_manifest(manifest_list, processing_location):
    with open(os.path.join(processing_location, "manifest.json"), 'w') as file:
        json.dump(manifest_list, file, indent=4)

def process_pdf_file(pdf, download_location, perform_alignment, create_rdf):
    processor = PDFProcessor(input_pdf_path=pdf, output_tei_path=download_location,
                             output_json_path=download_location)
    try:
        if create_rdf:
            create_rdf = True
        if perform_alignment:
            perform_alignment = True
        manifest_info = processor.process_pdf(perform_alignment, create_rdf)

    except Exception as e:
        manifest_info = {"filename": os.path.basename(pdf), "status": "error", "error": str(e)}
    return manifest_info

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    agree = BooleanField("Perform semantic alignment of sections' headings")
    agree2 = BooleanField("Generate JSONld file")
    submit = SubmitField("Process File")
    max_workers = IntegerField('Max Workers', default=1, validators=[NumberRange(min=1, max=50)])


def create_app():
    PREFIX="/"

    # change to default as:
    # PREFIX="/"
    app = Flask(__name__, static_url_path=PREFIX+'static', static_folder="static")

    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
    app.config['PROCESSING_FOLDER'] = PROCESSING_FOLDER

    os.makedirs(os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER']), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

    @app.route(PREFIX,methods=['GET', "POST"])
    @app.route(PREFIX+'home', methods=['GET', 'POST'])



    def home():
        os.makedirs('output', exist_ok=True)
        form = UploadFileForm()

        if form.validate_on_submit():

            file = form.file.data
            max_workers = form.max_workers.data
            perform_alignment = form.agree.data
            create_rdf = form.agree2.data
            save_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename))  # Then save the file
            file.save(save_location)
            download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                             app.config['DOWNLOAD_FOLDER'])  # Then save the file

            pdf_files, unsupported_file_types, targz_fd = get_all_files_by_type(save_location, ".pdf", app.config['UPLOAD_FOLDER'])
            manifest = []
            if pdf_files:
                # Parallel processing of PDF files
                with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                    future_to_pdf = {
                        executor.submit(process_pdf_file, pdf, download_location, perform_alignment, create_rdf): pdf for pdf
                        in pdf_files}
                    for future in concurrent.futures.as_completed(future_to_pdf):
                        pdf = future_to_pdf[future]
                        try:
                            # Collect the result (manifest_info) from each worker process
                            manifest_info = future.result()
                            manifest.append(manifest_info)
                        except Exception as exc:
                            manifest_info = {"filename": os.path.basename(pdf), "status": "error", "error": str(exc)}
                            manifest.append(manifest_info)

            #empty static/files
            files=[]
            dir=[]
            for entry in os.scandir(app.config['UPLOAD_FOLDER']):
                if entry.is_file():
                    files.append(entry.name)
                elif entry.is_dir():
                    dir.append(entry)
            for file in files:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
            for x in dir:
                shutil.rmtree(x)

            upload_manifest(manifest, download_location)

            current_datetime = datetime.now()
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

            # Return the download URL as JSON response
            return jsonify({"download_url": url_for('download_file', filename=zip_name)})

        return render_template('index.html', form=form)



    @app.route(PREFIX+'download/<filename>', methods=['GET'])
    def download_file(filename):
        download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['DOWNLOAD_FOLDER']) # Aggiungi il percorso corretto

        @after_this_request
        def delete_zip(response):
            # Elimina il file dopo il download
            folder_path = DOWNLOAD_FOLDER
            files = []
            dir = []
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    files.append(entry.name)
                elif entry.is_dir():
                    dir.append(entry)
            for file in files:
                os.remove(os.path.join(folder_path, file))
            for x in dir:
                shutil.rmtree(x)
            return response

        return send_from_directory(download_location, filename, as_attachment=True)

    from api.routes import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from flask import Blueprint, send_from_directory

    docs_blueprint = Blueprint('docs', __name__)

    @app.route('/openapi.json')
    def openapi():
        return send_from_directory('docs', 'openapi.json')

    @app.route('/docs')
    def swagger_ui():
        return render_template('swagger.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001)
