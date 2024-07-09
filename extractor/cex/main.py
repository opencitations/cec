from flask import Flask, render_template, send_from_directory, after_this_request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.fields.simple import BooleanField
from wtforms.validators import InputRequired
from combined import PDFProcessor
import zipfile
from semantic_alignment.align_headings import run

def get_all_files(folder_path):
    files = []
    for entry in os.scandir(folder_path):
        if entry.is_file():
            files.append(entry.name)
    return files

def create_zip_folder(input_folder, output_zip_file):
    files = get_all_files(input_folder)
    with zipfile.ZipFile(output_zip_file, 'w') as zip_file:
        for file in files:
            if (file[-4:] == '.xml') | (file[-5:] == '.json'):
                file_path = os.path.join(input_folder, file)
                zip_file.write(file_path, os.path.relpath(file_path, input_folder))

def delete_all_files(folder_path):
    files = get_all_files(folder_path)
    for file in files:
        os.remove(os.path.join(folder_path, file))

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    agree = BooleanField("Perform semantic alignment of sections' headings")
    submit = SubmitField("Process File")

def create_app():
    PREFIX="/cex/"

    # change to default as:
    # PREFIX="/"

    app = Flask(__name__, static_url_path=PREFIX+'static', static_folder="static")

    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['UPLOAD_FOLDER'] = 'static/files'
    app.config['DOWNLOAD_FOLDER'] = 'static/output'

    os.makedirs(os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER']), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

    @app.route(PREFIX,methods=['GET', "POST"])
    @app.route(PREFIX+'home', methods=['GET', 'POST'])

    def home():
        os.makedirs('output', exist_ok=True)
        form = UploadFileForm()

        if form.validate_on_submit():

            file = form.file.data
            save_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename))  # Then save the file
            file.save(save_location)

            download_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['DOWNLOAD_FOLDER'])  # Then save the file
            processor = PDFProcessor(input_pdf_path=save_location, output_tei_path=download_location, output_json_path=download_location)
            processor.process_pdf()

            os.remove(save_location)

            if form.agree.data:
                # implement sections' headings alignment
                output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/output')
                json_file = [el for el in os.listdir(output_dir) if el.endswith(".json")]
                run(os.path.join(output_dir, json_file[0]), ["Introduction", "Related Works", "Methods and Materials",
                                                             "Results", "Discussion", "Conclusion"],
                    os.path.join(output_dir, json_file[0]), "../semantic_alignment/predefined_mappings.json")

            zip_name = os.path.basename(save_location).split(".pdf")[0] + '.zip'
            zip_path = os.path.join(download_location, zip_name)

            create_zip_folder(download_location, zip_path)

            @after_this_request
            def delete_zip(response):
                # Elimina il file dopo il download
                folder_path = 'static/output'
                files = []
                for entry in os.scandir(folder_path):
                    if entry.is_file():
                        files.append(entry.name)
                for file in files:
                    os.remove(os.path.join(folder_path, file))
                return response

            return send_from_directory(download_location, zip_name, as_attachment=True)


        return render_template('index.html', form=form)


    @app.route(PREFIX+'download/<filename>', methods=['GET'])
    def download_file(filename):
        download_location = 'resources/pdf2'  # Aggiungi il percorso corretto
        return send_from_directory(download_location, filename, as_attachment=True)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5001)
