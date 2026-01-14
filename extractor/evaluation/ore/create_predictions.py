import os
import shutil
import time
import json
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from multiprocessing import Process, Manager
import traceback



# Create a requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")



def run_with_timeout_process(func, args=(), timeout=300):
    """
    Runs a function in a separate process with a timeout.
    If it exceeds `timeout`, the process is terminated.
    Returns (success, error_message)
    """

    manager = Manager()
    result = manager.dict()
    result["success"] = False
    result["error"] = ""

    def wrapper():
        try:
            func(*args)
            result["success"] = True
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    p = Process(target=wrapper)
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return False, f"Timeout after {timeout} seconds"

    return result["success"], result["error"]


def process_pdf(pdf_to_process, zip_file_path, json_output_path):
    log(f"Starting processing for PDF: {pdf_to_process}")

    try:
        with open(pdf_to_process, 'rb') as pdf_file:
            log("Uploading PDF to CEX API...")
            files = {'input_files_or_archives': pdf_file}
            data = {
                'perform_alignment': 'false',
                'max_workers': 1,
                'create_rdf': 'false'
            }

            response = session.post('http://test.opencitations.net:81/cex/api/extractor', files=files, data=data)
            response.raise_for_status()
            json_response = response.json()
            download_url = json_response.get('download_url')
            log(f"Received response. Download URL: {download_url}")

            if not download_url:
                log("[ERROR] No download URL returned from API.")
                return

            if download_url.startswith("http"):
                log("Downloading ZIP file from API...")
                with session.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(zip_file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                log(f"ZIP file saved to {zip_file_path}")

                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    if 'manifest.json' not in zip_ref.namelist():
                        log("[ERROR] manifest.json not found in ZIP file.")
                        return

                    log("Reading manifest.json...")
                    with zip_ref.open('manifest.json') as manifest_file:
                        manifest_data = json.loads(manifest_file.read().decode('utf-8'))

                    if not all(item.get('status') == 'success' for item in manifest_data):
                        log("[WARNING] Some items in manifest.json were not successful.")

                    # Find the first JSON file (excluding manifest)
                    json_filename = None
                    for name in zip_ref.namelist():
                        if name.endswith('.json') and not name.startswith('manifest'):
                            json_filename = name
                            break

                    if not json_filename:
                        log("[ERROR] No JSON file found in ZIP!")
                        return

                    log(f"Extracting JSON file from ZIP: {json_filename}")
                    with zip_ref.open(json_filename) as src, open(json_output_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)

                    log(f"JSON output saved to {json_output_path}")


    except Exception as e:
        log(f"[ERROR] Exception occurred while processing PDF: {e}")






