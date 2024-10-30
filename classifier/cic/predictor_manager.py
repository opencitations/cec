import os
import sys
import logging
from flask import current_app
from .src.predictor import Predictor
import ast

class PredictorManager:
    """
    Manages the instantiation of the Predictor and processing of data,
    while maintaining the manifest dictionary for logging purposes.
    """

    def __init__(self):
        self.manifest_dict = {}
        self.predictor = None
        self.SRC_PATH = self.get_src_path()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_src_path(self):
        """
        Retrieves the SRC_PATH from the Flask application's configuration.

        Returns:
            str: The source path where models and other resources are located.

        Raises:
            SystemExit: If SRC_PATH is not set in the application configuration.
        """
        src_path = current_app.config.get('SRC_PATH')
        if not src_path:
            self.logger.error("SRC_PATH is not set in the application configuration.")
            sys.exit(1)
        return src_path

    def instantiate_predictor(self, selected_mode):
        """
        Instantiates the Predictor object based on the selected mode.

        Args:
            selected_mode (str): The classification mode selected by the user.

        Returns:
            bool: True if instantiation is successful, False otherwise.
        """
        self.logger.info("Instantiating Predictor")
        try:
            # Predictor instantiation with correct models according tothe selected mode
            self.predictor = Predictor(
                selected_mode,
                "allenai/scibert_scivocab_cased",
                "xlnet-base-cased",
                [
                    [
                        os.path.join(self.SRC_PATH, "models", "Sections", "SciBERT_method_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "Sections", "SciBERT_background_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "Sections", "SciBERT_result_model.pt")
                    ],
                    [
                        os.path.join(self.SRC_PATH, "models", "Sections", "XLNet_method_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "Sections", "XLNet_background_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "Sections", "XLNet_result_model.pt")
                    ],
                ],
                [
                    [
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_SciBERT_method_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_SciBERT_background_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_SciBERT_result_model.pt")
                    ],
                    [
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_XLNet_method_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_XLNet_background_model.pt"),
                        os.path.join(self.SRC_PATH, "models", "NoSections", "NoSec_XLNet_result_model.pt")
                    ],
                ],
                os.path.join(self.SRC_PATH, "models", "Sections", "MetaClassifierSections.pth"),
                os.path.join(self.SRC_PATH, "models", "NoSections", "MetaClassifierNoSections.pth"),
            )
            self.logger.info("Predictor instantiated successfully.")
            self.manifest_dict["Initialization"] = {
                "Status": "Success",
                "Summary": {
                    "SRC_PATH setup": "Success",
                    "Predictor Instantiation": "Success"
                }
            }
            return True
        except Exception as e:
            self.manifest_dict["Initialization"] = {
                "Status": "Error",
                "Summary": {
                    "SRC_PATH setup": "Success",
                    "Predictor Instantiation": "Error",
                    "Error details": f"Failed to instantiate Predictor: {e}"
                }
            }
            self.logger.error(f"Failed to instantiate Predictor: {e}")
            return False

    def process_data(self, data, filename, from_json, request_source):
        """
        Processes the data using the instantiated Predictor.

        Args:
            data (dict or tuple): The data to be processed.
            filename (str): The name of the file being processed.
            from_json (bool): Whether the data comes from a JSON file.
            request_source (str): The source of the request (e.g., 'web-interface').

        Returns:
            dict: The classification output if successful, None otherwise.
        """
        temporary_data = None
        try:
            if not from_json:
                cls_data = data
                if isinstance(cls_data, str):
                    # Evaluate the string input into a Python object
                    cls_data = ast.literal_eval(cls_data)
                if not isinstance(cls_data, list):
                    raise ValueError("Data passed in input is not a list of tuples. Please read the documentation.")
            else:
                if isinstance(data, tuple):
                    cls_data, temporary_data = data
                else:
                    cls_data = data

            # Set data in the Predictor
            self.predictor.set_data(cls_data, temporary_data, from_json=from_json)
            # Does classification operation
            output = self.predictor.final_classification()
            if "Classification" not in self.manifest_dict:
                self.manifest_dict["Classification"] = {}
            self.manifest_dict["Classification"][filename] = {
                "Filename": filename,
                "Status": "Success",
                "Summary": {
                    "Classification process": "Success",
                }
            }
            return output
        except Exception as e:
            if request_source == 'web-interface':
                raise ValueError(f"Error processing data: {e}")
            else:
                if "Classification" not in self.manifest_dict:
                    self.manifest_dict["Classification"] = {}
                self.manifest_dict["Classification"][filename] = {
                    "Status": "Error during processing",
                    "Summary": {
                        "Data processing": "Error",
                        "Error details": f"Error while trying to process data: {e}"
                    }
                }
                self.logger.error(f"Error processing data: {e}")
                return None
