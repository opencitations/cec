import io
import json
import shutil
import unittest
import os
import zipfile
from pathlib import Path

from pyparsing import oneOf

from extractor.cex.main import create_app
from werkzeug.datastructures import FileStorage

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "api")


class TestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the Flask app for testing
        cls.app = create_app()
        cls.app.config['TESTING'] = True  # Enable testing mode
        cls.app.config['UPLOAD_FOLDER'] = os.path.join(BASE, 'test_uploads')  # Use a test folder
        cls.app.config['DOWNLOAD_FOLDER'] = os.path.join(BASE, 'test_downloads')  # Use a test folder
        cls.client = cls.app.test_client()

        # Create test directories
        os.makedirs(cls.app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(cls.app.config['DOWNLOAD_FOLDER'], exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Clean up test directories after all tests
        shutil.rmtree(cls.app.config['UPLOAD_FOLDER'], ignore_errors=True)
        shutil.rmtree(cls.app.config['DOWNLOAD_FOLDER'], ignore_errors=True)

    def test_file_upload_success(self):
        """Test successful file upload."""

        pdf_file = open(os.path.join(BASE, 'PHY-AST_95.pdf'), 'rb')

        data = {
            'input_files_or_archives': pdf_file,
            'perform_alignment': 'false',
            'max_workers': 3
        }

        # Send the POST request with the file and data
        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('download_url', json_response)
        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'success' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_no_file_upload(self):
        """Test no file uploaded case."""
        data = {
            'max_workers': 2,
            'perform_alignment': 'false'
        }

        response = self.client.post('/api/extractor', data=data)

        self.assertEqual(response.status_code, 200)

        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'error' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_unsupported_file_type(self):
        """Test unsupported file type upload."""
        text_content = b'This is a test text file.'
        text_file = FileStorage(stream=io.BytesIO(text_content), filename='test.txt', content_type='text/plain')

        data = {
            'input_files_or_archives': text_file,
            'max_workers': 2,
            'perform_alignment': 'false'
        }

        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)

        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'error' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_different_archives_zip(self):
        pdf_file = open(os.path.join(BASE, 'prova_2_pdf.zip'), 'rb')

        data = {
            'input_files_or_archives': pdf_file,
            'perform_alignment': 'false',
            'max_workers': 2
        }

        # Send the POST request with the file and data
        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('download_url', json_response)
        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'success' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_different_archives_targz(self):
        pdf_file = open(os.path.join(BASE, 'prova_2_pdf_tar.gz'), 'rb')

        data = {
            'input_files_or_archives': pdf_file,
            'perform_alignment': 'false',
            'max_workers': 2
        }

        # Send the POST request with the file and data
        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('download_url', json_response)
        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'success' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_different_archives_zst(self):
        pdf_file = open(os.path.join(BASE, 'NOTES-1.pdf.zst'), 'rb')

        data = {
            'input_files_or_archives': pdf_file,
            'perform_alignment': 'false',
            'max_workers': 2
        }

        # Send the POST request with the file and data
        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('download_url', json_response)
        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(all(item['status'] == 'success' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)

    def test_different_archives_tar(self):
        """This tar contains also a JSON that cannot be processed """
        pdf_file = open(os.path.join(BASE, 'archive.tar'), 'rb')

        data = {
            'input_files_or_archives': pdf_file,
            'perform_alignment': 'false',
            'max_workers': 2
        }

        # Send the POST request with the file and data
        response = self.client.post('/api/extractor', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('download_url', json_response)
        # Get the JSON response and extract the download URL
        response_data = response.get_json()
        download_url = response_data.get('download_url')

        # Ensure that the download URL is present
        self.assertIsNotNone(download_url)

        # Download the zip file using the download URL
        file_response = self.client.get(download_url)

        # Check if the zip file was downloaded successfully
        self.assertEqual(file_response.status_code, 200)

        # Create a path for the downloaded zip file (in-memory check or save it temporarily)
        zip_file_path = os.path.join(self.app.config['DOWNLOAD_FOLDER'], 'processed_file.zip')

        # Write the content of the downloaded zip file to a temporary file
        with open(zip_file_path, 'wb') as temp_zip_file:
            temp_zip_file.write(file_response.data)

        # Open and inspect the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure that 'manifest.json' exists in the zip file
            self.assertIn('manifest.json', zip_ref.namelist())

            # Open and read the content of 'manifest.json'
            with zip_ref.open('manifest.json') as json_file:
                manifest_data = json.load(json_file)
                # Check if the manifest contains the expected error message
                self.assertTrue(any(item['status'] == 'error' for item in manifest_data) and any(item['status'] == 'success' for item in manifest_data))

        # Clean up: remove the temporary zip file
        os.remove(zip_file_path)




if __name__ == '__main__':
    unittest.main()