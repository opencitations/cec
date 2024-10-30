from flask import jsonify, send_file, make_response
import json
import os
import zipfile
import io
import logging

logger = logging.getLogger(__name__)

def create_error_response(manifest_dict, status_code):
    response = jsonify(manifest_dict)
    response.status_code = status_code
    return response

def create_success_response(result, manifest_dict, filename):
    response_data = {
        "result": result
    }
    if manifest_dict is not None:
        response_data["manifest"] = manifest_dict

    return jsonify(response_data), 200

def create_zip_response(results_list, manifest_dict):
    """
    Create a ZIP file containing the results and manifest, preserving the original directory structure.

    Args:
        results_list (list): List of dictionaries with 'filename', 'rel_path', and 'result' keys.
        manifest_dict (dict): The manifest dictionary to include in the ZIP.

    Returns:
        Flask response: The response containing the ZIP file.
    """
    try:
        # Create an in-memory ZIP file using BytesIO
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the manifest file at the root of the ZIP archive if provided
            if manifest_dict is not None:
                manifest_json = json.dumps(manifest_dict, indent=4)
                zipf.writestr('manifest.json', manifest_json)

            # Add each result file, preserving directory structure
            for item in results_list:
                original_rel_path = item.get('rel_path', item['filename'])
                # Get the directory part and filename
                dir_name, original_filename = os.path.split(original_rel_path)
                # Remove the .json extension from the original filename
                base_name, ext = os.path.splitext(original_filename)
                # Avoid adding '.json' twice
                if ext == '.json':
                    new_filename = f"{base_name}_result.json"
                else:
                    new_filename = f"{original_filename}_result.json"
                # Construct the new relative path
                new_rel_path = os.path.join(dir_name, new_filename)
                # Convert the result to JSON string
                result_json = json.dumps(item['result'], indent=4)
                # Write the result to the ZIP archive
                zipf.writestr(new_rel_path, result_json)

        # Seek to the beginning of the BytesIO buffer (cause after writing the pointer is at the end)
        memory_file.seek(0)

        # Create the flask response
        response = make_response(send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='results.zip'
        ))

        # Set headers
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = 'attachment; filename=results.zip'

        return response
    except Exception as e:
        logger.error(f"Error creating ZIP response: {e}")
        # Update the manifest with the error if manifest_dict is provided
        if manifest_dict is not None:
            manifest_dict["Response Creation"] = {
                "Status": "Error",
                "Error details": f"Failed to create ZIP response: {e}"
            }
            return create_error_response(manifest_dict, 500)
        else:
            # If there is no manifest_dict -> create a simple error response
            error_response = {
                "Status": "Error",
                "Error details": f"Failed to create ZIP response: {e}"
            }
            return create_error_response(error_response, 500)
