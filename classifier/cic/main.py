from flask import Flask, request, jsonify, render_template
import ast
from src.predictor import *
from src.data_processor import *


PREFIX="/cic/"
SRC_PATH="../src/"
app = Flask(__name__, static_url_path=PREFIX+'static', static_folder="static")

@app.route(PREFIX)
#@app.route('/<prefix>')
def index():
    return render_template('index.html',prefix=PREFIX)

@app.route(PREFIX+'classifier')
#@app.route('/<prefix>classifier')
def classifier_page():
    return render_template('classifier.html',prefix=PREFIX)

#@app.route(PREFIX+'/upload_json', methods=['POST'])
@app.route(PREFIX+'upload_json', methods=['POST'])
def upload_json():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    sentences = request.form.get('sentences')

    if file.filename == '' and sentences is None:
        return jsonify({'error': 'No selected file or sentences'})

    if file and allowed_file(file.filename): # Check if file is a JSON file
        try:
            if file.filename != '':
                # Process the uploaded JSON file
                returned_data = read_json(file.stream)
            else:
                raise ValueError("Error processing file: No file uploaded")

            temporary_data = None
            if isinstance(returned_data, tuple):
                data = returned_data[0]
                temporary_data = returned_data[1]
            else:
                data = returned_data

            print("Processed data in route:", data)  # Debug print

            # Get selected_mode from form-data (if it's included there)
            selected_mode = request.form.get('mode')
            if not selected_mode:
                return jsonify({'error': 'Mode not specified'})

            predictor = Predictor(
                selected_mode,
                "allenai/scibert_scivocab_cased",
                [
                    SRC_PATH+"models/ModelsWithSections/background_model.pt",
                    SRC_PATH+"models/ModelsWithSections/method_model.pt",
                    SRC_PATH+"models/ModelsWithSections/result_model.pt"
                ],
                [
                    SRC_PATH+"models/ModelsWithoutSections/background_model_no_sections.pt",
                    SRC_PATH+"models/ModelsWithoutSections/method_model_no_sections.pt",
                    SRC_PATH+"models/ModelsWithoutSections/result_model_no_sections.pt"
                ],
                SRC_PATH+"models/ModelsWithSections/CNN.pt",
                SRC_PATH+"models/ModelsWithoutSections/CNN_no_sections.pt",
                data,
                temporary_data,
                from_json=True
            )

            output = predictor.final_classification()
            return jsonify(output)
        except ValueError as e:
            print("Error processing file:", e)  # Debug print
            return jsonify({'error': str(e)})
    return jsonify({'error': 'Invalid file type'})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'json'

#@app.route(PREFIX+'/classify', methods=['POST'])
@app.route(PREFIX+'classify', methods=['POST'])
def classify_text():
    data = request.json
    selected_mode = data.get('mode')
    sentences = data.get('sentences')
    # Safely evaluate the string and convert it to a list of tuples
    datapoints = ast.literal_eval(sentences)
    print("Datapoints (processed in route):", datapoints) # Debug print
    processor = Predictor(
        selected_mode,
        "allenai/scibert_scivocab_cased",
        [
            SRC_PATH+"models/ModelsWithSections/background_model.pt",
            SRC_PATH+"models/ModelsWithSections/method_model.pt",
            SRC_PATH+"models/ModelsWithSections/result_model.pt"
        ],
        [
            SRC_PATH+"models/ModelsWithoutSections/background_model_no_sections.pt",
            SRC_PATH+"models/ModelsWithoutSections/method_model_no_sections.pt",
            SRC_PATH+"models/ModelsWithoutSections/result_model_no_sections.pt"
        ],
        SRC_PATH+"models/ModelsWithSections/CNN.pt",
        SRC_PATH+"models/ModelsWithoutSections/CNN_no_sections.pt",
        datapoints,
        from_json=False
    )

    output = processor.final_classification()
    return jsonify(output)

if __name__ == '__main__':
    app.run(debug=True)


"""
[
("Literature Review", "In their comprehensive review, Smith and colleagues (2019) delineate the historical development of nanomaterials in modern applications."),
("", "The foundational work by Doe et al. (2015) establishes the prevailing theoretical framework guiding current research paradigms."),
("Research Methodology", "Our process analysis technique was adopted from the methodology proposed by Johnson et al. (2018) in their study on efficient data algorithms."),
("Experimental Procedures", ""),
("Findings and Analysis", "Consistent with the observations reported by Lee and Khan (2020), our results indicate a significant correlation between sunlight exposure and the rate of photosynthesis."),
("Discussion", "Contrary to the predictions made by Fujiwara's model (2016), our experiment did not observe a steady quantum coherence under thermal fluctuations.")
]
"""
