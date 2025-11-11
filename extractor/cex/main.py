
import logging
import shutil
import zipfile
from datetime import datetime
from concurrent.futures import as_completed, ProcessPoolExecutor
from flask import Flask, render_template, send_from_directory, after_this_request, jsonify, url_for
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, IntegerField
from werkzeug.utils import secure_filename
import os
from wtforms.fields.simple import BooleanField
from wtforms.validators import InputRequired, NumberRange
from settings import UPLOAD_FOLDER, DOWNLOAD_FOLDER
from cleanup import register_cleanup, clean_folder
from utils import get_all_files_by_type, upload_manifest, process_pdf_file

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

    os.makedirs(os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER']), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

    @app.route(PREFIX,methods=['GET', "POST"])
    @app.route(PREFIX+'home', methods=['GET', 'POST'])

    def home():

        clean_folder(app.config['UPLOAD_FOLDER'])
        clean_folder(app.config['DOWNLOAD_FOLDER'])

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
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    future_to_pdf = {
                        executor.submit(process_pdf_file, pdf, download_location, perform_alignment, create_rdf): pdf for pdf
                        in pdf_files}
                    for future in as_completed(future_to_pdf):
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
        download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['DOWNLOAD_FOLDER'])

        @after_this_request
        def delete_zip(response):
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
    app.register_blueprint(api_blueprint, url_prefix=PREFIX+'api')

    from flask import Blueprint, send_from_directory

    docs_blueprint = Blueprint('docs', __name__)

    @app.route('/openapi.json')
    def openapi():
        return send_from_directory('docs', 'openapi.json')

    @app.route('/docs')
    def swagger_ui():
        return render_template('swagger.html')

    return app

# Create the Flask app that works with Gunicorn
app = create_app()
register_cleanup(UPLOAD_FOLDER, DOWNLOAD_FOLDER)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
