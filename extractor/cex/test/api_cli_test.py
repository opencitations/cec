import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
import zipfile
import json
import argparse
from pathlib import Path
from extractor.cex.api.api_cli import create_zip_file, delete_files, process_pdf_file, main

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "api_cli")

class TestScriptFunctions(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for each test
        self.temp_directory = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up by removing the directory after each test
        shutil.rmtree(self.temp_directory)

    def test_create_zip_file(self):
        # Create sample files
        sample_file_1 = os.path.join(self.temp_directory, "file1.xml")
        sample_file_2 = os.path.join(self.temp_directory, "file2.json")
        with open(sample_file_1, "w") as f:
            f.write("Test content")
        with open(sample_file_2, "w") as f:
            f.write("Test content")

        # Call the function
        zip_path = create_zip_file(self.temp_directory, "test.zip")

        # Check if the zip file exists and contains the expected files
        self.assertTrue(os.path.exists(zip_path))
        with zipfile.ZipFile(zip_path, "r") as zipf:
            self.assertIn("file1.xml", zipf.namelist())
            self.assertIn("file2.json", zipf.namelist())

    def test_delete_files(self):
        # Create sample files
        sample_file_1 = os.path.join(self.temp_directory, "file1.xml")
        zip_path = create_zip_file(self.temp_directory, "test.zip")
        os.mkdir(os.path.join(self.temp_directory, "subdir"))

        with open(sample_file_1, "w") as f:
            f.write("Test content")

        # Call the delete function
        delete_files(self.temp_directory)

        # Ensure only the zip file remains
        self.assertFalse(os.path.exists(sample_file_1))
        self.assertTrue(os.path.exists(zip_path))

    @patch("extractor.cex.api.api_cli.PDFProcessor")
    def test_process_pdf_file(self, mock_processor):
        # Mock the process_pdf method
        mock_instance = mock_processor.return_value
        mock_instance.process_pdf.return_value = {"filename": "sample.pdf", "status": "processed"}

        # Call the function
        result = process_pdf_file("sample.pdf", self.temp_directory, perform_alignment=True, create_rdf=True)

        # Check if the result matches expected manifest
        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["filename"], "sample.pdf")

    @patch("extractor.cex.api.api_cli.get_all_files_by_type", return_value=(["sample.pdf"], [], None))
    @patch("extractor.cex.api.api_cli.process_pdf_file", return_value={"filename": "sample.pdf", "status": "processed"})
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_integration(self, mock_args, mock_process_pdf, mock_get_all_files):
        # Mock the arguments
        mock_args.return_value = argparse.Namespace(
            input_files_or_archives=["sample.tar"],
            download_folder=self.temp_directory,
            zip_name="output.zip",
            perform_alignment=False,
            max_workers=2,
            create_rdf=True
        )

        # Call main
        main()

        # Check if zip file is created and contains the manifest
        zip_path = os.path.join(self.temp_directory, "output.zip")
        self.assertTrue(os.path.exists(zip_path))
        with zipfile.ZipFile(zip_path, "r") as zipf:
            self.assertIn("manifest.json", zipf.namelist())



    @patch("extractor.cex.api.api_cli.get_all_files_by_type", return_value=([], ["unsupported.txt"], None))
    @patch("argparse.ArgumentParser.parse_args")
    def test_unsupported_files(self, mock_args, mock_get_all_files):
        # Mock the arguments
        mock_args.return_value = argparse.Namespace(
            input_files_or_archives=["unsupported.txt"],
            download_folder=self.temp_directory,
            zip_name="output.zip",
            perform_alignment=False,
            max_workers=1,
            create_rdf=True
        )

        # Call main
        main()

        # Verify manifest file contains unsupported file entry
        zip_path = os.path.join(self.temp_directory, "output.zip")
        with zipfile.ZipFile(zip_path, "r") as zipf:
            self.assertIn("manifest.json", zipf.namelist())
            with zipf.open("manifest.json") as json_file:
                manifest = json.load(json_file)
                self.assertTrue(
                    any("unsupported.txt" in entry["filename"] and "unsupported file type" in entry["error"] for entry
                        in manifest)
                )

    @patch("argparse.ArgumentParser.parse_args")
    def test_main_integration_real_file(self, mock_args):
        # Mock the arguments
        path_file = os.path.join(BASE, "NOTES-2.pdf")
        mock_args.return_value = argparse.Namespace(
            input_files_or_archives=[path_file],
            download_folder=self.temp_directory,
            zip_name="",
            perform_alignment=False,
            max_workers=2,
            create_rdf=True
        )

        # Call main
        main()

        # Check if zip file is created and contains the manifest
        zip_name = [el if el.endswith('zip') else None for el in os.listdir(self.temp_directory)][0]
        zip_path = os.path.join(self.temp_directory, zip_name)
        with zipfile.ZipFile(zip_path, "r") as zipf:
            self.assertIn("manifest.json", zipf.namelist())
            with zipf.open("manifest.json") as json_file:
                manifest = json.load(json_file)
                self.assertTrue(
                    all("success" in entry["status"] for entry
                        in manifest)
                )


if __name__ == '__main__':
    unittest.main()
