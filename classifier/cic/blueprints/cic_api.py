from flask import Blueprint, request, jsonify, send_file, Response
import ast
import zipfile
import tarfile
import gzip
import bz2
import lzma
import py7zr
import os
import tempfile
import json
from io import BytesIO
from src.predictor import *
from src.data_processor import *

api_bp = Blueprint('api', __name__)

SRC_PATH = "/Users/lorenzo/Desktop/cec/classifier/cic/src/" # era "src/", penso debba tornare tale nel server

# Debug test funzionamento server
"""@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "API is working"})"""

def instantiate_predictor(selected_mode, manifest_dict):#, data, temporary_data, json_instance: bool):
    print("Instantiating Predictor")
    try:
        #print(f"Instantiating predictor with mode: {selected_mode}, data: {data}, temporary_data: {temporary_data}")
        predictor_instance = Predictor(
            selected_mode,
            "allenai/scibert_scivocab_cased",
            "xlnet/xlnet-base-cased",
            [
                [
                    SRC_PATH + "models/Sections/SciBERT_method_model.pt",
                    SRC_PATH + "models/Sections/SciBERT_background_model.pt",
                    SRC_PATH + "models/Sections/SciBERT_result_model.pt"
                ],
                [
                    SRC_PATH + "models/Sections/XLNet_method_model.pt",
                    SRC_PATH + "models/Sections/XLNet_background_model.pt",
                    SRC_PATH + "models/Sections/XLNet_result_model.pt"
                ],
            ],
            [
                [
                    SRC_PATH + "models/NoSections/NoSec_SciBERT_method_model.pt",
                    SRC_PATH + "models/NoSections/NoSec_SciBERT_background_model.pt",
                    SRC_PATH + "models/NoSections/NoSec_SciBERT_result_model.pt"
                ],
                [
                    SRC_PATH + "models/NoSections/NoSec_XLNet_method_model.pt",
                    SRC_PATH + "models/NoSections/NoSec_XLNet_background_model.pt",
                    SRC_PATH + "models/NoSections/NoSec_XLNet_result_model.pt"
                ],
            ],
            SRC_PATH + "models/Sections/MetaClassifierSections.pth",
            SRC_PATH + "models/NoSections/MetaClassifierNoSections.pth",
            #data,
            #temporary_data,
            #from_json=json_instance
        )
        print("Predictor correctly instantiated")
        manifest_dict["Initialization"] = {
            "Status": "Success",
            "Summary": {
                "Data Upload": "Success",
                "Classification Mode Selection": "Success",
                "Predictor Instantiation": "Success"
            }
        }
        return (predictor_instance, manifest_dict)
    except Exception as e:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "Data Upload": "Success",
                "Classification Mode Selection": "Success",
                "Predictor Instantiation": "Error",
                "Error details": f"Failed to instantiate Predictor: {e}"
            }
        }
        print(f"Failed to instantiate Predictor: {e}")
        return (None, manifest_dict)

def create_zip_with_manifest(manifest_dict, zip_file_path):
    manifest_file_path = os.path.join(os.path.dirname(zip_file_path), 'manifest.json')
    with open(manifest_file_path, 'w') as manifest_file:
        json.dump(manifest_dict, manifest_file)

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_file_path, 'manifest.json')
    os.remove(manifest_file_path)


@api_bp.route('/classify', methods=['POST'])
def classify():
    manifest_dict = {}
    request_source = request.headers.get('X-Request-Source', 'unknown')
    if 'file' not in request.files and not request.json:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "Data Upload": "Error",
                "Classification Mode Selection": "Unknown",
                "Predictor Instantiation": "Unknown",
                "Error details": "No file or JSON data uploaded"
            }
        }
        temp_dir = tempfile.mkdtemp()
        zip_file_path = os.path.join(temp_dir, 'error_results.zip')
        create_zip_with_manifest(manifest_dict, zip_file_path)
        response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
        clean_up(temp_dir)
        return response, 400

    # Determine the mode
    selected_mode = request.form.get('mode') if 'file' in request.files else request.json.get('mode')
    if not selected_mode or selected_mode not in ["with sections", "without sections", "mixed"]:
        manifest_dict["Initialization"] = {
            "Status": "Error",
            "Summary": {
                "Data Upload": "Success",
                "Classification Mode Selection": "Error",
                "Predictor Instantiation": "Unknown",
                "Error details": "Mode not specified"
            }
        }
        temp_dir = tempfile.mkdtemp()
        zip_file_path = os.path.join(temp_dir, 'error_results.zip')
        create_zip_with_manifest(manifest_dict, zip_file_path)
        response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
        clean_up(temp_dir)
        return response, 400
    
    predictor, manifest_dict = instantiate_predictor(selected_mode, manifest_dict)
    if predictor is None:
        temp_dir = tempfile.mkdtemp()
        zip_file_path = os.path.join(temp_dir, 'error_results.zip')
        create_zip_with_manifest(manifest_dict, zip_file_path)
        response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
        clean_up(temp_dir)
        return response, 500

    # Handle file upload
    original_file_path = None
    compressed_data = False
    #data_from_folder = False
    if 'file' in request.files:
        #print("DATA FROM FILE FOUND")
        from_file = True
        file = request.files['file']
        original_file_path = file.filename
        #original_file_dir = os.path.dirname(original_file_path)
        #print(f"Original file directory: {original_file_dir}")

        #print(f"file.filename: {file.filename}")
        #print(f"Is it allowed: {allowed_file(file.filename)}")
        #print(f"Is it folder: {os.path.isdir(file.filename)}")

        if file.filename == '' or not allowed_file(file.filename):
            if file.filename == '':
                filename = "Empty"
            else:
                filename = file.filename
            manifest_dict["Data Processing"] = {
                "Setup": {
                    "Filename": filename,
                    "Status": "Error",
                    "Summary": {
                        "Data format check": "Error",
                        "Error details": f"Not a file, or invalid file type (uploaded file: {file.filename}). File types supported are: 'json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z'. You cannot directly upload a folder. If you are trying to upload a folder, please consider compressing it and trying again the upload of the compressed folder."
                    }
                }
            }
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, 'error_results.zip')
            create_zip_with_manifest(manifest_dict, zip_file_path)
            response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
            clean_up(temp_dir)
            return response, 400

        temp_dir = tempfile.mkdtemp()
        print(f"Temporary directory created at: {temp_dir}")
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)

        if file.filename.endswith('.json'):
            # case JSON file
            try:
                read_data = read_json(temp_file_path, request_source)
                if len(read_data) == 3:
                    data, manifest_id_errors, correctly_processed_ids = read_data
                elif len(read_data) == 4:
                    data = (read_data[0], read_data[1])
                    manifest_id_errors = read_data[2]
                    correctly_processed_ids = read_data[3]

                if len(manifest_id_errors)!=0:
                    manifest_dict["Single entries processing"][file.filename] = {
                        "Filename": file.filename,
                        "Citation IDs Processing": {
                            "Status": "Partial Procesing",
                            "Description": "Not all the ids of the file have been correctly processed. This may mean also that none of them has been processed. Check below for details.",
                            "Correctly processed IDs": correctly_processed_ids,
                            "IDs generating errors": manifest_id_errors
                        }
                    }
                elif len(manifest_id_errors)==0:
                    manifest_dict["Single entries processing"][file.filename] = {
                        "Filename": file.filename,
                        "Citation IDs Processing": {
                            "Status": "Success",
                            "Description": "All the IDs have been correctly processed.",
                            "Correctly processed IDs": correctly_processed_ids
                        }
                    }

            except json.JSONDecodeError as e:
                manifest_dict["Data Processing"] = {
                    "Filename": file.filename,
                    "Status": "Error",
                    "Summary": {
                        "Data format check": "Success",
                        "File type": "JSON",
                        "JSON validation": "Error",
                        "Error details": f"Invalid JSON file. Please check the structure. Detailed error: {e}"
                    }
                }
                zip_file_path = os.path.join(temp_dir, 'error_results.zip')
                create_zip_with_manifest(manifest_dict, zip_file_path)
                response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
                clean_up(temp_dir)
                return response, 400
        elif '.' in file.filename:
            if file.filename.rsplit('.', 1)[1].lower() in ['zip', 'tar', 'gz', 'bz2', 'xz', '7z']:
                # case compressed file/folder
                compressed_data = True
                data, manifest_dict = process_compressed_file(temp_file_path, temp_dir, manifest_dict)
        else:
            manifest_dict["Data Processing"] = {
                "Filename": file.filename,
                "Status": "Error",
                "Summary": {
                    "Data format check": "Error",
                    "Error details": "Unsupported file type. File types supported are: 'json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z'. You cannot directly upload a folder. If you are trying to upload a folder, please consider compressing it and trying again the upload of the compressed folder."
                }
            }
            zip_file_path = os.path.join(temp_dir, 'error_results.zip')
            create_zip_with_manifest(manifest_dict, zip_file_path)
            response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
            clean_up(temp_dir)
            return response, 400
        
    else:
        #print("DATA --NOT-- FROM FILE FOUND")
        from_file = False
        # Handle JSON data
        data = request.json.get('data')
        #print(data)
        #print(type(data))
        if not data:
            manifest_dict["Data Processing"] = {
                "Status": "Error",
                "Summary": {
                    "Data format check": "Error",
                    "Error details": "No data provided"
                }
            }
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, 'error_results.zip')
            create_zip_with_manifest(manifest_dict, zip_file_path)
            response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
            clean_up(temp_dir)
            return response, 400

        # Handle list of tuples
        if isinstance(data, str):
            data = ast.literal_eval(data)

    all_results = []
    if not compressed_data:
        try:
            result, manifest_dict = process_data(predictor, data, manifest_dict, request_source, file.filename, from_json=from_file)
            if result is None:
                if request_source == 'web-interface': #isinstance(result, Response):
                    raise ValueError("Error processing data")
                else:
                    temp_dir = tempfile.mkdtemp()
                    zip_file_path = os.path.join(temp_dir, 'error_results.zip')
                    create_zip_with_manifest(manifest_dict, zip_file_path)
                    response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
                    clean_up(temp_dir)
                    return response, 500
            if request_source == 'web-interface':
                temp_dir = None
                return jsonify(result) # In case of web-interface with data upload
            # Save the result to a temporary directory
            result_file_path = os.path.join(temp_dir, 'result.json')
            with open(result_file_path, 'w') as result_file:
                json.dump(result, result_file)
            all_results.append({'result_path': result_file_path, 'rel_path': 'result.json'})

            manifest_file_path = os.path.join(temp_dir, 'manifest.json')
            with open(manifest_file_path, 'w') as manifest_file:
                json.dump(manifest_dict, manifest_file)

            # Create ZIP file with results
            if '.' in file.filename:
                original_file_name = os.path.splitext(os.path.basename(original_file_path))[0]
            else:
                original_file_name = file.filename
            zip_file_path = os.path.join(temp_dir, f'{original_file_name}_results.zip')
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for result in all_results:
                    zf.write(result['result_path'], result['rel_path'])
                zf.write(manifest_file_path, 'manifest.json')
            print(f"ZIP file created at: {zip_file_path}")

            # Send the ZIP file
            print(f"Sending ZIP file from: {zip_file_path}")
            response = send_file(zip_file_path, download_name=f'{original_file_name}_results.zip', as_attachment=True)

            # Cleanup temp dir
            print(f"Cleaning up path: {temp_dir}")
            clean_up(temp_dir)
            return response

        except Exception as e:
            manifest_dict["Single file Classification"] = {
                "Status": "Error",
                "Summary": {
                    "Error details": f"Error processing data: {e}"
                }
            }
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, 'error_results.zip')
            create_zip_with_manifest(manifest_dict, zip_file_path)
            response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
            clean_up(temp_dir)
            return response, 500
    
        finally:
            if temp_dir:
                clean_up(temp_dir)

    else:
        # Process each JSON file individually
        for item in data:
            #print(data)
            json_data = item['data']
            #print(isinstance(json_data, tuple))
            json_path = item['path']
            json_filename = item['filename']
            rel_path = item['rel_path']

            result, manifest_dict = process_data(predictor, json_data, manifest_dict, request_source, json_filename, from_json=from_file)
            if result is None:
                if request_source == 'web-interface': #isinstance(result, Response):
                    raise ValueError("Error processing data")
                """else:
                    temp_dir = tempfile.mkdtemp()
                    zip_file_path = os.path.join(temp_dir, 'error_results.zip')
                    create_zip_with_manifest(manifest_dict, zip_file_path)
                    response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
                    clean_up(temp_dir)
                    return response, 500"""

            result_file_path = os.path.join(temp_dir, rel_path.replace('.json', '_result.json'))
            os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            with open(result_file_path, 'w') as result_file:
                json.dump(result, result_file)

            all_results.append({'result_path': result_file_path, 'rel_path': rel_path.replace('.json', '_result.json')})

        
        manifest_file_path = os.path.join(temp_dir, 'manifest.json')
        with open(manifest_file_path, 'w') as manifest_file:
            json.dump(manifest_dict, manifest_file)

        # Create ZIP file with results
        if '.' in file.filename:
            original_file_name = os.path.splitext(os.path.basename(original_file_path))[0]
        else:
            original_file_name = file.filename
        zip_file_path = os.path.join(temp_dir, f'{original_file_name}_results.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for result in all_results:
                zf.write(result['result_path'], result['rel_path'])
            zf.write(manifest_file_path, 'manifest.json')
        print(f"ZIP file created at: {zip_file_path}")

        # Send the ZIP file
        print(f"Sending ZIP file from: {zip_file_path}")
        response = send_file(zip_file_path, download_name=f'{original_file_name}_results.zip', as_attachment=True)
        # Cleanup temp dir
        print(f"Cleaning up path: {temp_dir}")
        clean_up(temp_dir)
        return response
    
        """except Exception as e:
            manifest_dict["Unknown Classification Error"] = {
                "Status": "Error",
                "Summary": {
                    "Error details": f"Error processing data: {e}"
                }
            }
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, 'error_results.zip')
            create_zip_with_manifest(manifest_dict, zip_file_path)
            response = send_file(zip_file_path, download_name='error_results.zip', as_attachment=True)
            clean_up(temp_dir)
            return response, 500
        finally:
            if temp_dir:
                clean_up(temp_dir)"""


def allowed_file(filename):
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ['json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z']:
        return True
    elif '.' not in filename:
        return True
    else: 
        return False


def read_json(json_file_path, request_source):
    manifest_id_errors = {}
    correctly_processed_ids = []
    try:
        # forse può generare errore se non tutte le entry hanno la stessa struttura.
        # nel caso l'ultima richieda simple format e quelle prima no
        # ma forse non da errore, DA CONTROLLARE
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            simple_format_check = True
            for id in data:
                if not isinstance(data[id], dict):
                    manifest_id_errors[id] = f"Invalid entry format for ID {id} in file. Each entry must be a dictionary. This entry will not be processed."
                    continue

                keys = data[id].keys()
                if len(keys) < 2:
                    manifest_id_errors[id] = f"Invalid JSON entry, the number of keys is not correct for ID {id} in file. The keys must be at least 'SECTION' and 'CITATION' in each entry. This entry will not be processed."
                    continue
                if 'SECTION' not in keys or 'CITATION' not in keys:
                    manifest_id_errors[id] = f"Invalid JSON entry, the number of keys is not correct for ID {id}. The keys must be at least 'SECTION' and 'CITATION' in each entry. This entry will not be processed."
                    continue
                if len(data[id]) > 2:
                    simple_format_check = False
                correctly_processed_ids.append(id)

            if simple_format_check:
                return (data, manifest_id_errors, correctly_processed_ids)
            else:
                clean_data = {}
                temporary_data = data
                for id in data:
                    clean_data[id] = {}
                    clean_data[id]['SECTION'] = data[id]['SECTION']
                    clean_data[id]['CITATION'] = data[id]['CITATION']
                return (clean_data, temporary_data, manifest_id_errors, correctly_processed_ids)
        
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        if request_source == 'web-interface':
            raise ValueError("Invalid JSON file")

def process_data(predictor, data, manifest_dict, request_source, filename, from_json: bool):
    if from_json or not from_json:
        pass
    else:
        raise ValueError("Not clear if data comes from a file or not")
    temporary_data = None
    if not from_json:
        cls_data = data
        if not isinstance(cls_data, list):
            raise ValueError("Data passed in input in the form is not a list of tuples. Please read documentation.")
    else:
        if isinstance(data, tuple):
            cls_data, temporary_data = data
        else:
            cls_data = data
        
    try:
        predictor.set_data(cls_data, temporary_data, from_json=from_json)
        output = predictor.final_classification()
        if "Classification" not in manifest_dict:
            manifest_dict["Classification"] = {}
        manifest_dict["Classification"][filename] = {
            "Filename": filename,
            "Status": "Success",
            "Summary": {
                "Classification process": "Success",
            }
        }
        return (output, manifest_dict)
    
    except Exception as e:
        if request_source == 'web-interface':
            raise ValueError("Error processing data")
        else:
            if "Classification" not in manifest_dict:
                manifest_dict["Classification"] = {}
            manifest_dict["Classification"][filename] = {
                "Status": "Error inside processing",
                "Summary": {
                    "Data processing": "Error",
                    "Error details": "Error while trying to process data",
                    "Real details": e
                }
            }
            return (output, manifest_dict)
        

def process_compressed_file(file_path, temp_dir, manifest_dict):
    original_file_path = file_path
    extract_file(file_path, temp_dir)
    data = []
    manifest_read_errors = {}
    read_errors = False

    manifest_id_errors = {}
    general_id_errors = False

    correctly_read_files = []
    files_with_all_correctly_processed_ids = []
    correctly_processed_map_file_id = {}

    for root, _, files in os.walk(temp_dir):
        for name in files:
            file_path = os.path.join(root, name)
            if name.endswith('.json') and not name.startswith('._'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                        rel_path = os.path.relpath(file_path, temp_dir)

                        simple_format_check = True
                        for id in json_data:
                            if not isinstance(json_data[id], dict):
                                id_errors = True
                                general_id_errors = True
                                if name not in manifest_id_errors:
                                    manifest_id_errors[name] = {}
                                manifest_id_errors[name][id] = {
                                    "Citation ID": id,
                                    "Error details": f"Invalid entry format for ID {id} in file {name}. Each entry must be a dictionary. This entry will not be processed."
                                }
                                continue
                            keys = json_data[id].keys()
                            if len(keys) < 2:
                                id_errors = True
                                general_id_errors = True
                                if name not in manifest_id_errors:
                                    manifest_id_errors[name] = {}
                                manifest_id_errors[name][id] = {
                                    "Citation ID": id,
                                    "Error details": f"Invalid JSON entry, the number of keys is not correct for ID {id} in file {name}. The keys must be at least 'SECTION' and 'CITATION' in each entry. This entry will not be processed."
                                }
                                continue
                            if 'SECTION' not in keys or 'CITATION' not in keys:
                                id_errors = True
                                general_id_errors = True
                                if name not in manifest_id_errors:
                                    manifest_id_errors[name] = {}
                                manifest_id_errors[name][id] = {
                                    "Citation ID": id,
                                    "Error details": f"Invalid JSON entry, the number of keys is not correct for ID {id}. The keys must be at least 'SECTION' and 'CITATION' in each entry. This entry will not be processed."
                                }
                                continue
                            if 'CITATION' in keys:
                                if json_data[id]['CITATION'] == '':
                                    id_errors = True
                                    if name not in manifest_id_errors:
                                        manifest_id_errors[name] = {}
                                    manifest_id_errors[name][id] = {
                                        "Citation ID": id,
                                        "Error details": f"Invalid JSON entry, the CITATION key for ID {id} is empty. Each entry must contain a citation to classify. This entry will not be processed."
                                    }
                                    continue

                            if len(json_data[id]) > 2:
                                simple_format_check = False
                            
                            if name not in correctly_processed_map_file_id:
                                correctly_processed_map_file_id[name] = []
                            correctly_processed_map_file_id[name].append(id)
                        
                        if simple_format_check:
                            data.append({'path': file_path, 'filename': name, 'rel_path': rel_path, 'data': json_data})
                        else:
                            clean_data = {}
                            temporary_data = json_data
                            for id in json_data:
                                clean_data[id] = {}
                                clean_data[id]['SECTION'] = json_data[id]['SECTION']
                                clean_data[id]['CITATION'] = json_data[id]['CITATION']
                            extended_data = (clean_data, temporary_data)
                            data.append({'path': file_path, 'filename': name, 'rel_path': rel_path, 'data': extended_data})
                        if id_errors:
                            general_id_errors = True
                        else:
                            files_with_all_correctly_processed_ids.append(name)
                        #print(f"Processed JSON file: {file_path}")
                    correctly_read_files.append(name)
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    read_errors = True
                    manifest_read_errors[name] = {
                        "Filename": name,
                        "Error details": e
                    }
            elif not name.startswith('._') and not name.rsplit('.', 1)[1].lower() in ['json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z']:
                read_errors = True
                manifest_read_errors[name] = {
                    "Filename": name,
                    "Error details": f"File {name} cannot be read."
                }
            id_errors = False


    # Manifest update
    if read_errors: #case reading errors
        if general_id_errors: # case single id errors + reading errors
            manifest_dict["Data Loading"] = {
                "Files processing": {
                    "Status": "Partial Procesing",
                    "Description": "Not all the Files of the archive have been correctly loaded. This may mean also that none of them has been processed. Check below for details.",
                    "Correctly loaded files": correctly_read_files,
                    "Files generating errors": manifest_read_errors
                }
            }

            manifest_dict["Single entries processing"] = {
                "Citation IDs Processing": {
                    "Status": "Partial Procesing",
                    "Description": "Not all the ids of the file have been correctly processed. This may mean also that none of them has been processed. Check below for details.",
                    "Files entirely processed": files_with_all_correctly_processed_ids,
                    "Correctly loaded IDs": correctly_processed_map_file_id,
                    "Files generating errors": manifest_id_errors
                }
            }

            
        else: # case reading errors, no single id errors
            manifest_dict["Data Loading"] = {
                "Files processing": {
                    "Status": "Partial Procesing",
                    "Description": "Not all the Files of the archive have been correctly loaded. This may mean also that none of them has been processed. Check below for details.",
                    "Correctly loaded files": correctly_read_files,
                    "Files generating errors": manifest_read_errors
                }
            }

            manifest_dict["Single entries processing"] = {
                "Citation IDs Processing": {
                    "Status": "Success",
                    "Description": "All the ids of all the file have been correctly processed. Check below for details.",
                    "Files entirely processed": files_with_all_correctly_processed_ids,
                }
            }

    else: # Case no reading error
        manifest_dict["Data Loading"] = {
                "Files processing": {
                    "Status": "Success",
                    "Description": "All the Files of the archive have been correctly loaded. Check below for details.",
                    "Correctly loaded files": correctly_read_files,
                }
            }

        if general_id_errors: # case only id errors
            manifest_dict["Single entries processing"] = {
                "Citation IDs Processing": {
                    "Status": "Partial Procesing",
                    "Description": "Not all the ids of the file have been correctly processed. This may mean also that none of them has been processed. Check below for details.",
                    "Files entirely processed": files_with_all_correctly_processed_ids,
                    "Correctly loaded IDs": correctly_processed_map_file_id,
                    "Files generating errors": manifest_id_errors
                }
            }

        else: # case no error at all
            manifest_dict["Single entries processing"] = {
                "Citation IDs Processing": {
                    "Status": "Success",
                    "Description": "All the ids of all the file have been correctly processed. Check below for details.",
                    "Files entirely processed": files_with_all_correctly_processed_ids,
                }
            }

    return (data, manifest_dict)

def extract_file(file_path, temp_dir):
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    elif file_path.endswith('.tar'):
        with tarfile.open(file_path, mode='r') as tar_ref:
            tar_ref.extractall(temp_dir)
    elif file_path.endswith('.gz'):
        with gzip.open(file_path, 'rb') as gz_ref:
            with open(os.path.join(temp_dir, os.path.basename(file_path)[:-3]), 'wb') as out_f:
                out_f.write(gz_ref.read())
    elif file_path.endswith('.bz2'):
        with bz2.open(file_path, 'rb') as bz2_ref:
            with open(os.path.join(temp_dir, os.path.basename(file_path)[:-4]), 'wb') as out_f:
                out_f.write(bz2_ref.read())
    elif file_path.endswith('.xz'):
        with lzma.open(file_path, 'rb') as xz_ref:
            with open(os.path.join(temp_dir, os.path.basename(file_path)[:-3]), 'wb') as out_f:
                out_f.write(xz_ref.read())
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(temp_dir)

def clean_up(temp_path):
    print(f"Cleaning up path: {temp_path}")
    if os.path.isfile(temp_path):
        os.remove(temp_path)
    elif os.path.isdir(temp_path):
        for root, _, files in os.walk(temp_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in os.listdir(root):
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_path)
    return True

def send_result_as_zip(results):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, result in enumerate(results):
            zf.writestr(f'result_{idx}.json', json.dumps(result))
    memory_file.seek(0)
    return send_file(memory_file, download_name='results.zip', as_attachment=True)
