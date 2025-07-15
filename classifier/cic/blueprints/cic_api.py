from flask import Blueprint, request, jsonify, send_file, current_app, make_response
from ..predictor_manager import PredictorManager
from ..utils.file_processing import allowed_file, read_json, process_compressed_file
from ..utils.response_helpers import create_error_response, create_success_response, create_zip_response
import tempfile
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/classify', methods=['POST'])
def classify():
    request_source = request.headers.get('X-Request-Source', 'unknown')

    # Initialize manifest_dict
    manifest_dict = {}

    # Check for file or JSON data. If no file -> error return manifest
    if 'file' not in request.files and not request.json:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "Data Upload": "Error",
                "Error details": "No file or JSON data uploaded"
            }
        }
        return create_error_response(manifest_dict, 400)

    # Otherwise continue and determine the classification mode
    if 'file' in request.files:
        selected_mode = request.form.get('mode')
    else:
        selected_mode = request.json.get('mode')

    if not selected_mode or selected_mode not in ["WS", "WoS", "M"]:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "Classification Mode Selection": "Error",
                "Error details": "Mode not specified or invalid mode"
            }
        }
        return create_error_response(manifest_dict, 400)

    # Get SRC_PATH from app config
    src_path = current_app.config.get('SRC_PATH')
    if not src_path:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "SRC_PATH setup": "Error",
                "Error details": "SRC_PATH is not set in the application configuration."
            }
        }
        return create_error_response(manifest_dict, 500)

    # Instantiate the predictor manager
    predictor_manager = PredictorManager()
    predictor_manager.SRC_PATH = src_path
    if not predictor_manager.instantiate_predictor(selected_mode):
        manifest_dict = predictor_manager.manifest_dict
        return create_error_response(manifest_dict, 500)

    # Reset manifest_dict for the request
    predictor_manager.manifest_dict = {}

    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        filename = file.filename
        if filename == '' or not allowed_file(filename):
            manifest_dict["Data Processing"] = {
                "Filename": filename or "Empty",
                "Status": "Error",
                "Summary": {
                    "Data format check": "Error",
                    "Error details": f"Invalid file type or empty filename. File types supported are: 'json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z'."
                }
            }
            return create_error_response(manifest_dict, 400)

        # Save file to a temporary dir
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, filename)
            file.save(temp_file_path)

            # Process the file accordin to its type
            if filename.endswith('.json'):
                try:
                    read_data = read_json(temp_file_path, request_source)
                    # Process data
                    result = predictor_manager.process_data(read_data, filename, from_json=True, request_source=request_source)
                    if result is None:
                        manifest_dict = predictor_manager.manifest_dict
                        return create_error_response(manifest_dict, 500)
                    # Prepare response. 2 scenarios: web or terminal
                    if request_source == 'web-interface':
                        return jsonify(result)
                    else:
                        manifest_dict = predictor_manager.manifest_dict
                        return create_success_response(result, manifest_dict, filename)
                except ValueError as e:
                    manifest_dict["Data Processing"] = {
                        "Filename": filename,
                        "Status": "Error",
                        "Summary": {
                            "Data format check": "Error",
                            "Error details": str(e)
                        }
                    }
                    return create_error_response(manifest_dict, 400)
            else:
                # Handle compressed foiles
                data_list, _ = process_compressed_file(temp_file_path, temp_dir, predictor_manager)
                all_results = []
                for item in data_list:
                    json_data = item['data']
                    json_filename = item['filename']
                    rel_path = item.get('rel_path', json_filename)
                    result = predictor_manager.process_data(json_data, json_filename, from_json=True, request_source=request_source)
                    if result is not None:
                        all_results.append({'filename': json_filename, 'rel_path': rel_path, 'result': result})
                # Prepare response. 2 scenarios: web or terminal
                if request_source == 'web-interface':
                    return create_zip_response(all_results, None)
                else:
                    manifest_dict = predictor_manager.manifest_dict
                    return create_zip_response(all_results, manifest_dict)
    else:
        # Handle JSON data from request body
        data = request.json.get('data')
        if not data:
            manifest_dict["Data Processing"] = {
                "Status": "Error",
                "Summary": {
                    "Data format check": "Error",
                    "Error details": "No data provided"
                }
            }
            return create_error_response(manifest_dict, 400)

        # Process data
        result = predictor_manager.process_data(data, "input_data", from_json=False, request_source=request_source)
        if result is None:
            manifest_dict = predictor_manager.manifest_dict
            return create_error_response(manifest_dict, 500)

        # Prepare response. 2 scenarios: web or terminal
        if request_source == 'web-interface':
            return jsonify(result)
        else:
            manifest_dict = predictor_manager.manifest_dict
            return create_success_response(result, manifest_dict, "result")
