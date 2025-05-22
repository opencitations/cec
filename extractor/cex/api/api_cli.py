import argparse
import os
import datetime
from extractor.cex.main import get_all_files_by_type, upload_manifest
from extractor.cex.combined import PDFProcessor
import zipfile
import concurrent.futures
import shutil

def create_zip_file(download_location, zip_name):
    # Get current timestamp to use in the zip file name if zip_name is not provided

    zip_path = os.path.join(download_location, zip_name)

    # Create the zip file while avoiding recursion
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(download_location):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)

                # Ensure the zip file itself is not included in the archive
                if os.path.abspath(file_path) == os.path.abspath(zip_path):
                    continue

                # Add the file to the zip archive
                zipf.write(file_path, os.path.relpath(file_path, download_location))

    return zip_path

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

def delete_files(download_location):
    files = []
    dir = []
    for entry in os.scandir(download_location):
        if entry.is_file() and not entry.name.endswith('zip'):
            files.append(entry.name)
        elif entry.is_dir():
            dir.append(entry)
    for file in files:
        os.remove(os.path.join(download_location, file))
    for x in dir:
        shutil.rmtree(x)

def main():
    parser = argparse.ArgumentParser(description='Upload PDF files for processing.')
    parser.add_argument('input_files_or_archives', nargs='+', help='Paths to the PDF files or archives to upload')
    parser.add_argument('--download_folder', help='Empty folder to store the processed zip', required=True)
    parser.add_argument('--zip_name', help='Name of the output zip file', required=False, default="")
    parser.add_argument('--perform_alignment', action='store_true', help='Whether to perform semantic alignment')
    parser.add_argument('--create_rdf', help='Whether to generate a JSONld file')
    parser.add_argument('--max_workers', help='to set the number of worker threads', default=1)

    args = parser.parse_args()

    download_location = args.download_folder
    os.makedirs(download_location, exist_ok=True)
    os.chmod(download_location, 0o777)

    manifest = list()

    files = args.input_files_or_archives
    if not files:
        manifest.append({"status": "error", "error": "No files selected"})
        upload_manifest(manifest, download_location)
        current_datetime = datetime.datetime.now()
        timestamp = current_datetime.timestamp()
        zip_name = args.zip_name or f'processed_pdfs_{timestamp}.zip'
        create_zip_file(download_location, zip_name)
        delete_files(download_location)
        return f"The output zip is available at {download_location}"

    pdfs_to_process = set()
    unsupported_files = set()

    for file_path in files:
        save_location = os.path.dirname(file_path)
        pdfs, unsupported_files_in_input, targz_fd = get_all_files_by_type(file_path, '.pdf', save_location)
        if pdfs:
            pdfs_to_process |= set(pdfs)
        if unsupported_files_in_input:
            unsupported_files |= set(unsupported_files_in_input)

    if unsupported_files:
        for el in list(unsupported_files):
            manifest_info = {"filename": os.path.basename(el), "status": "error", "error": f"unsupported file type"}
            manifest.append(manifest_info)

    if pdfs_to_process:
        # Parallel processing of PDF files
        max_workers = int(args.max_workers)
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_pdf = {
                executor.submit(process_pdf_file, pdf, download_location, args.perform_alignment, args.create_rdf): pdf for pdf
                in pdfs_to_process}
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    # Collect the result (manifest_info) from each worker process
                    manifest_info = future.result()
                    manifest.append(manifest_info)
                except Exception as exc:
                    manifest_info = {"filename": os.path.basename(pdf), "status": "error", "error": str(exc)}
                    manifest.append(manifest_info)

    upload_manifest(manifest, download_location)
    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.timestamp()
    zip_name = args.zip_name or f'processed_pdfs_{timestamp}.zip'
    create_zip_file(download_location, zip_name)
    delete_files(download_location)
    return print(f"The output zip is available at {download_location}")


if __name__ == '__main__':
    main()