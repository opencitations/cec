import os
import json
import zipfile
import tarfile
import gzip
import bz2
import lzma
import py7zr
import shutil
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the file.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    ALLOWED_EXTENSIONS = {'json', 'zip', 'tar', 'gz', 'bz2', 'xz', '7z'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_json(json_file_path, request_source):
    """
    Read and validate a JSON file containing citation data.

    Args:
        json_file_path (str): Path to the JSON file.
        request_source (str): Source of the request (e.g. 'web-interface' [or 'unknown' for now]).

    Returns:
        dict or tuple: The data to be processed.

    Raises:
        ValueError: If the JSON file is invalid.
    """
    manifest_id_errors = {}
    correctly_processed_ids = []
    try:
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
                    manifest_id_errors[id] = f"Invalid JSON entry, missing 'SECTION' or 'CITATION' key for ID {id}. Each entry must have these keys. This entry will not be processed."
                    continue
                if len(data[id]) > 2:
                    simple_format_check = False
                correctly_processed_ids.append(id)

            if simple_format_check:
                return data
            else:
                clean_data = {}
                temporary_data = data
                for id in data:
                    clean_data[id] = {
                        'SECTION': data[id]['SECTION'],
                        'CITATION': data[id]['CITATION']
                    }
                return (clean_data, temporary_data)

    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.error(f"Invalid JSON file: {e}")
        if request_source == 'web-interface':
            raise ValueError(f"Invalid JSON file: {e}")
        else:
            raise

def process_compressed_file(file_path, temp_dir, predictor_manager):
    """
    Process a compressed file containing JSON files (or folders with JSON files) with citation data.

    Args:
        file_path (str): Path to the compressed file.
        temp_dir (str): Temporary directory to extract files.
        predictor_manager (PredictorManager): Instance of PredictorManager to update the manifest_dict.

    Returns:
        tuple: (data_list, manifest_dict)
    """
    extract_file(file_path, temp_dir)
    data_list = []
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
                        id_errors = False
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
                                    "Error details": f"Invalid JSON entry, missing keys for ID {id} in file {name}. Must have 'SECTION' and 'CITATION'. This entry will not be processed."
                                }
                                continue
                            if 'SECTION' not in keys or 'CITATION' not in keys:
                                id_errors = True
                                general_id_errors = True
                                if name not in manifest_id_errors:
                                    manifest_id_errors[name] = {}
                                manifest_id_errors[name][id] = {
                                    "Citation ID": id,
                                    "Error details": f"Invalid JSON entry, missing 'SECTION' or 'CITATION' for ID {id}. This entry will not be processed."
                                }
                                continue
                            if 'CITATION' in keys and json_data[id]['CITATION'] == '':
                                id_errors = True
                                if name not in manifest_id_errors:
                                    manifest_id_errors[name] = {}
                                manifest_id_errors[name][id] = {
                                    "Citation ID": id,
                                    "Error details": f"Invalid JSON entry, 'CITATION' is empty for ID {id}. This entry will not be processed."
                                }
                                continue

                            if len(json_data[id]) > 2:
                                simple_format_check = False

                            if name not in correctly_processed_map_file_id:
                                correctly_processed_map_file_id[name] = []
                            correctly_processed_map_file_id[name].append(id)

                        if simple_format_check:
                            data_list.append({'path': file_path, 'filename': name, 'rel_path': rel_path, 'data': json_data})
                        else:
                            clean_data = {}
                            temporary_data = json_data
                            for id in json_data:
                                clean_data[id] = {
                                    'SECTION': json_data[id]['SECTION'],
                                    'CITATION': json_data[id]['CITATION']
                                }
                            extended_data = (clean_data, temporary_data)
                            data_list.append({'path': file_path, 'filename': name, 'rel_path': rel_path, 'data': extended_data})

                        if id_errors:
                            general_id_errors = True
                        else:
                            files_with_all_correctly_processed_ids.append(name)

                    correctly_read_files.append(name)
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    read_errors = True
                    manifest_read_errors[name] = {
                        "Filename": name,
                        "Error details": str(e)
                    }
            elif not name.startswith('._') and not allowed_file(name):
                read_errors = True
                manifest_read_errors[name] = {
                    "Filename": name,
                    "Error details": f"File {name} cannot be read or is of unsupported type."
                }

    # Update the manifest_dict
    if read_errors:
        predictor_manager.manifest_dict["Data Loading"] = {
            "Files processing": {
                "Status": "Partial Processing",
                "Description": "Not all files in the archive were loaded successfully.",
                "Correctly loaded files": correctly_read_files,
                "Files generating errors": manifest_read_errors
            }
        }
    else:
        predictor_manager.manifest_dict["Data Loading"] = {
            "Files processing": {
                "Status": "Success",
                "Description": "All files in the archive were loaded successfully.",
                "Correctly loaded files": correctly_read_files
            }
        }

    if general_id_errors:
        predictor_manager.manifest_dict["Single entries processing"] = {
            "Citation IDs Processing": {
                "Status": "Partial Processing",
                "Description": "Some IDs were not processed.",
                "Files entirely processed": files_with_all_correctly_processed_ids,
                "Correctly loaded IDs": correctly_processed_map_file_id,
                "Files generating errors": manifest_id_errors
            }
        }
    else:
        predictor_manager.manifest_dict["Single entries processing"] = {
            "Citation IDs Processing": {
                "Status": "Success",
                "Description": "All IDs in all files were processed successfully.",
                "Files entirely processed": files_with_all_correctly_processed_ids
            }
        }

    return data_list, predictor_manager.manifest_dict

def extract_file(file_path, temp_dir):
    """
    Securely extract compressed files to a temporary directory.

    Args:
        file_path (str): Path to the compressed file.
        temp_dir (str): Temporary directory to extract files.

    Raises:
        Exception: If an unsupported file type is provided.
    """

    def is_within_directory(directory, target):
        """
        Check if the target path is within the given directory.

        Args:
            directory (str): The base directory.
            target (str): The target path to check.

        Returns:
            bool: True if the target is within the directory, False otherwise.
        """
        abs_directory = os.path.abspath(directory)
        abs_target = os.path.abspath(target)

        return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

    def safe_extract_archive(archive, path="."):
        """
        Safely extract an archive, preventing path traversal attacks.

        Args:
            archive: Archive object (ZipFile or TarFile).
            path (str): Destination path for extraction.

        Raises:
            Exception: If a path traversal attempt is detected.
        """
        # Determine the list of members based on the type of archive
        if isinstance(archive, zipfile.ZipFile):
            members = archive.namelist()
            is_tar = False
        elif isinstance(archive, tarfile.TarFile):
            members = archive.getmembers()
            is_tar = True
        else:
            raise Exception("Unsupported archive type")

        for member in members:
            # For TarFile, member is a TarInfo object; for ZipFile, it's a string
            if is_tar:
                member_name = member.name
            else:
                member_name = member

            member_path = os.path.join(path, member_name)
            if not is_within_directory(path, member_path):
                raise Exception("Attempted Path Traversal in Archive File")

        # Extract all members
        archive.extractall(path)

    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            safe_extract_archive(zip_ref, temp_dir)
    elif file_path.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')):
        with tarfile.open(file_path, mode='r:*') as tar_ref:
            safe_extract_archive(tar_ref, temp_dir)
    elif file_path.endswith('.gz') and not file_path.endswith('.tar.gz'):
        with gzip.open(file_path, 'rb') as gz_ref:
            output_file = os.path.join(temp_dir, os.path.basename(file_path)[:-3])
            with open(output_file, 'wb') as out_f:
                shutil.copyfileobj(gz_ref, out_f)
    elif file_path.endswith('.bz2') and not file_path.endswith('.tar.bz2'):
        with bz2.open(file_path, 'rb') as bz2_ref:
            output_file = os.path.join(temp_dir, os.path.basename(file_path)[:-4])
            with open(output_file, 'wb') as out_f:
                shutil.copyfileobj(bz2_ref, out_f)
    elif file_path.endswith('.xz') and not file_path.endswith('.tar.xz'):
        with lzma.open(file_path, 'rb') as xz_ref:
            output_file = os.path.join(temp_dir, os.path.basename(file_path)[:-3])
            with open(output_file, 'wb') as out_f:
                shutil.copyfileobj(xz_ref, out_f)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(temp_dir)
    else:
        raise Exception("Unsupported compressed file type.")
