import os
import pathlib
import shutil
import tarfile
import zipfile
from os import makedirs, sep, walk
from os.path import basename, exists, isdir
import json
from urllib3.response import zstd
from combined import PDFProcessor


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

def clean_upload_folder(upload_folder):
    for entry in os.scandir(upload_folder):
        if entry.is_file():
            os.remove(entry.path)
        elif entry.is_dir():
            shutil.rmtree(entry.path)

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
