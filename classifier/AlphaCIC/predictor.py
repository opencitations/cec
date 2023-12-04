from binary_classifiers import *
from data_processor import *
from tqdm import tqdm


"""
"allenai/scibert_scivocab_cased"

[
    "./models/ModelsWithSections/background_model.pt",
    "./models/ModelsWithSections/method_model.pt",
    "./models/ModelsWithSections/result_model.pt"
],
"""


class Predictor:
    def __init__(self, case, model_ckp, SECTIONS_binaryCLS_state_dict_paths_list, NO_SECTIONS_binaryCLS_state_dict_paths_list, SECTIONS_metaclassifier_state_dict_path, NO_SECTIONS_metaclassifier_state_dict_path, data, temporary_data=None, from_json=False):
        valid_cases = ["with sections", "without sections", "mixed"]
        if case not in valid_cases:
            raise ValueError(f"Invalid case: {case}. Expected one of: {valid_cases}")
        self.case = case
        self.model_ckp = model_ckp
        self.device = self.retrieve_device()
        self.SECTIONS_binaryCLS_state_dict_paths_list = SECTIONS_binaryCLS_state_dict_paths_list
        self.NO_SECTIONS_binaryCLS_state_dict_paths_list = NO_SECTIONS_binaryCLS_state_dict_paths_list
        self.SECTIONS_metaclassifier_state_dict_path = SECTIONS_metaclassifier_state_dict_path
        self.NO_SECTIONS_metaclassifier_state_dict_path = NO_SECTIONS_metaclassifier_state_dict_path
        self.from_json = from_json
        if self.from_json:
            self.data = DataProcessor(data, self.from_json).data
        else:
            self.data = DataProcessor(data, self.from_json).mapped_data
        self.temporary_dict = temporary_data

        if self.case == valid_cases[0]:
            self.binary_classifier = EnsembleClassifier(
                self.model_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list,
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            self.metaclassifier_CNN = self.load_metaclassifier()

        elif self.case == valid_cases[1]:
            self.binary_classifier = EnsembleClassifier(
                self.model_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list,
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            self.metaclassifier_CNN = self.load_metaclassifier()

        elif self.case == valid_cases[2]:

            self.sections_classifier = EnsembleClassifier(
                self.model_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list,
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )

            self.no_sections_classifier = EnsembleClassifier(
                self.model_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list,
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )

            self.metaclassifiers = self.load_metaclassifier()
            self.sections_CNN = self.metaclassifiers[0]
            self.no_sections_CNN = self.metaclassifiers[1]

    def retrieve_device(self):
        """
        Retrieve the device on which to run the model.
        """
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
        return device

    def load_metaclassifier(self):
        """
        Load the CNN metaclassifier.
        """
        if self.case != "mixed":
            if self.case == "with sections":
                metaclassifier_CNN = SectionsMetaClassifierCNN()
                metaclassifier_CNN.load_state_dict(torch.load(self.SECTIONS_metaclassifier_state_dict_path, map_location=self.device))
                metaclassifier_CNN = metaclassifier_CNN.to(self.device).eval()
                return metaclassifier_CNN

            elif self.case == "without sections":
                metaclassifier_CNN = NoSectionsMetaClassifierCNN()
                metaclassifier_CNN.load_state_dict(torch.load(self.NO_SECTIONS_metaclassifier_state_dict_path, map_location=self.device))
                metaclassifier_CNN = metaclassifier_CNN.to(self.device).eval()
                return metaclassifier_CNN
        else:
            SECTIONS_metaclassifier_CNN = SectionsMetaClassifierCNN()
            SECTIONS_metaclassifier_CNN.load_state_dict(torch.load(self.SECTIONS_metaclassifier_state_dict_path, map_location=self.device))
            SECTIONS_metaclassifier_CNN = SECTIONS_metaclassifier_CNN.to(self.device).eval()

            NO_SECTIONS_metaclassifier_CNN = NoSectionsMetaClassifierCNN()
            NO_SECTIONS_metaclassifier_CNN.load_state_dict(torch.load(self.NO_SECTIONS_metaclassifier_state_dict_path, map_location=self.device))
            NO_SECTIONS_metaclassifier_CNN = NO_SECTIONS_metaclassifier_CNN.to(self.device).eval()
            return (SECTIONS_metaclassifier_CNN, NO_SECTIONS_metaclassifier_CNN)
        
        raise ValueError(f"Invalid case: {self.case}. Expected one of: ['with sections', 'without sections', 'mixed']")

    def tokenize(self):
        if self.case != "mixed":
            if self.case == "with sections":
                for datapoint in self.data:
                    context = self.data[datapoint]['SECTION'] + ". " + self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized'] = self.binary_classifier.tokenizer(context, return_tensors="pt")
            elif self.case == "without sections":
                for datapoint in self.data:
                    context = self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized'] = self.binary_classifier.tokenizer(context, return_tensors="pt")
        else:
            for datapoint in self.data:
                if self.data[datapoint]['SECTION'] == "":
                    context = self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized'] = self.no_sections_classifier.tokenizer(context, return_tensors="pt")
                else:
                    context = self.data[datapoint]['SECTION'] + ". " + self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized'] = self.sections_classifier.tokenizer(context, return_tensors="pt")
        return self.data

    def binary_predictions(self):
        self.data = self.tokenize()   

        if self.case != "mixed":
            model1 = self.binary_classifier.background_model.to(self.device).eval()
            model2 = self.binary_classifier.method_model.to(self.device).eval()
            model3 = self.binary_classifier.result_model.to(self.device).eval()

            all_predictions = {}

            with torch.no_grad():
                for datapoint in tqdm(self.data):
                    input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized'].items()}

                    out1 = torch.softmax(model1(**input_data).logits, dim=-1) # background
                    out2 = torch.softmax(model2(**input_data).logits, dim=-1) # method
                    out3 = torch.softmax(model3(**input_data).logits, dim=-1) # result

                    # The probabilities predicted for each class, for each model, are stacked
                    out = torch.stack([out1, out2, out3], dim=-1)
                    all_predictions[datapoint] = out
        
        else:
            model1_sections = self.sections_classifier.background_model.to(self.device).eval()
            model2_sections = self.sections_classifier.method_model.to(self.device).eval()
            model3_sections = self.sections_classifier.result_model.to(self.device).eval()

            model1_no_sections = self.no_sections_classifier.background_model.to(self.device).eval()
            model2_no_sections = self.no_sections_classifier.method_model.to(self.device).eval()
            model3_no_sections = self.no_sections_classifier.result_model.to(self.device).eval()

            all_predictions = {
                "NO-SECTIONS": {},
                "SECTIONS": {}
            }

            with torch.no_grad():
                for datapoint in tqdm(self.data):
                    if self.data[datapoint]['SECTION'] == "":
                        input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized'].items()}

                        out1 = torch.softmax(model1_no_sections(**input_data).logits, dim=-1)
                        out2 = torch.softmax(model2_no_sections(**input_data).logits, dim=-1)
                        out3 = torch.softmax(model3_no_sections(**input_data).logits, dim=-1)

                        out = torch.stack([out1, out2, out3], dim=-1)
                        all_predictions['NO-SECTIONS'][datapoint] = out

                    else:
                        input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized'].items()}

                        out1 = torch.softmax(model1_sections(**input_data).logits, dim=-1)
                        out2 = torch.softmax(model2_sections(**input_data).logits, dim=-1)
                        out3 = torch.softmax(model3_sections(**input_data).logits, dim=-1)

                        out = torch.stack([out1, out2, out3], dim=-1)
                        all_predictions['SECTIONS'][datapoint] = out

        return all_predictions
  
    def final_classification(self):
        """
        Please be careful:
        Even though the predictions from the binary classifiers are in the order:
        1. Background
        2. Method
        3. Result
        The order of the predictions in the final tensor is:
        0 == Method
        1 == Background
        2 == Result
        This is because of the way the metaclassifier is trained.
        """
        all_predictions = self.binary_predictions()

        if self.case != "mixed":
            final_predictions = {}
            model = self.metaclassifier_CNN.to(self.device).eval()
            with torch.no_grad():
                for id, prediction in all_predictions.items():
                    input_data = prediction.view(-1, prediction.numel()).to(self.device)  # Flatten the inputs and move to device 
                    # The .numel in pytorch returns the entire number of elements in a tensor
                    
                    # Inference
                    output_probabilities = model(input_data) # It directly returns probabilities since the softmax has been applied in the model

                    # Get the predicted class (0 - method, 1 - background, or 2 - result)
                    _, predicted_class = torch.max(output_probabilities, 1)  # 1 = dimension over which to return the maximum
                    final_predictions[id] = {'FinalPrediction': (predicted_class.item(), output_probabilities[0].tolist())}  
        
        else:
            final_predictions = {
                "NO-SECTIONS": {},
                "SECTIONS": {}
            }
            sections_model = self.sections_CNN.to(self.device).eval()
            no_sections_model = self.no_sections_CNN.to(self.device).eval()

            with torch.no_grad():
                for id, prediction in all_predictions['SECTIONS'].items():
                    input_data = prediction.view(-1, prediction.numel()).to(self.device)
                    output_probabilities = sections_model(input_data) # It directly returns probabilities since the softmax has been applied in the model
                    _, predicted_class = torch.max(output_probabilities, 1)
                    final_predictions['SECTIONS'][id] = {'FinalPrediction': (predicted_class.item(), output_probabilities[0].tolist())}

                for id, prediction in all_predictions['NO-SECTIONS'].items():
                    input_data = prediction.view(-1, prediction.numel()).to(self.device)
                    output_probabilities = no_sections_model(input_data) # It directly returns probabilities since the softmax has been applied in the model
                    _, predicted_class = torch.max(output_probabilities, 1)
                    final_predictions['NO-SECTIONS'][id] = {'FinalPrediction': (predicted_class.item(), output_probabilities[0].tolist())}

        # output_probabilities (in final_predictions) is a tensor of shape (1, 3) - 1 datapoint and 3 labels -
        # containing the probabilities for each class in the following order (method, background, result)
        output_dict = self.create_json(all_predictions, final_predictions)
        print("Final output:", output_dict)  # Debug print
        return output_dict  # return a new dictionary containing final predictions
    
    def create_json(self, predictions, final_predictions):

        def final_prediction_string(prediction_integer, metaclassifier_probabilities, background_positive_probability, method_positive_probability, result_positive_probability):
            """
            OLD THRESHOLD BASED ON BINARY PROBABILITIES
            if background_positive_probability >= 0.6 or method_positive_probability >= 0.6 or result_positive_probability >= 0.6:
            """
            # New threshold based on metaclassifier probabilities 
            if metaclassifier_probabilities[0] >= 0.9 or metaclassifier_probabilities[1] >= 0.9 or metaclassifier_probabilities[2] >= 0.9:
                if prediction_integer == 0:
                    return "usesMethodIn (METHOD)"
                elif prediction_integer == 1:
                    return "obtainsBackgroundFrom (BACKGROUND)"
                elif prediction_integer == 2:
                    return "usesConclusionsFrom (RESULT)"
            else:
                return "citesForInformation (UNRELIABLE)"

        if self.case != "mixed":
            # final_predictions is a dict
            merged_dict = {}
            for id in self.data:
                merged_dict[id] = {
                    "SECTION": self.data[id]['SECTION'],
                    "CITATION": self.data[id]['CITATION'],
                    "BACKGROUND BINARY POSITIVE PROBABILITY": predictions[id][0][1][0].item(),
                    "METHOD BINARY POSITIVE PROBABILITY": predictions[id][0][1][1].item(),
                    "RESULT BINARY POSITIVE PROBABILITY": predictions[id][0][1][2].item(),
                    "BACKGROUND MODEL CONFIDENCE": final_predictions[id]['FinalPrediction'][1][1],
                    "METHOD MODEL CONFIDENCE": final_predictions[id]['FinalPrediction'][1][0],
                    "RESULT MODEL CONFIDENCE": final_predictions[id]['FinalPrediction'][1][2],
                    "FINAL PREDICTION": final_prediction_string(final_predictions[id]['FinalPrediction'][0], final_predictions[id]['FinalPrediction'][1], predictions[id][0][1][0].item(), predictions[id][0][1][1].item(), predictions[id][0][1][2].item())
                }

            """# Write the merged dictionary to a JSON file
            with open('./Outputs/output.json', 'w') as json_file:
                json.dump(merged_dict, json_file, indent=4)"""

        else:
            # final_predictions is a dict of dicts, with the keys being "NO-SECTIONS" and "SECTIONS"
            merged_dict = {}
            for id in self.data:
                merged_dict[id] = {
                    "SECTION": self.data[id]['SECTION'],
                    "CITATION": self.data[id]['CITATION']
                }
                if self.data[id]['SECTION'] == "":
                    merged_dict[id]["BACKGROUND BINARY POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][0][1][0].item()
                    merged_dict[id]["METHOD BINARY POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][0][1][1].item()
                    merged_dict[id]["RESULT BINARY POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][0][1][2].item()
                    merged_dict[id]["BACKGROUND MODEL CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][1]
                    merged_dict[id]["METHOD MODEL CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][0]
                    merged_dict[id]["RESULT MODEL CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][2]
                    merged_dict[id]["FINAL PREDICTION"] = final_prediction_string(final_predictions['NO-SECTIONS'][id]['FinalPrediction'][0], final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1], predictions['NO-SECTIONS'][id][0][1][0].item(), predictions['NO-SECTIONS'][id][0][1][1].item(), predictions['NO-SECTIONS'][id][0][1][2].item())
                else:
                    merged_dict[id]["BACKGROUND BINARY POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][0][1][0].item()
                    merged_dict[id]["METHOD BINARY POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][0][1][1].item()
                    merged_dict[id]["RESULT BINARY POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][0][1][2].item()
                    merged_dict[id]["BACKGROUND MODEL CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][1]
                    merged_dict[id]["METHOD MODEL CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][0]
                    merged_dict[id]["RESULT MODEL CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][2]
                    merged_dict[id]["FINAL PREDICTION"] = final_prediction_string(final_predictions['SECTIONS'][id]['FinalPrediction'][0], final_predictions['SECTIONS'][id]['FinalPrediction'][1], predictions['SECTIONS'][id][0][1][0].item(), predictions['SECTIONS'][id][0][1][1].item(), predictions['SECTIONS'][id][0][1][2].item())

            """# Write the merged dictionary to a JSON file
            with open('./Outputs/output.json', 'w') as json_file:
                json.dump(merged_dict, json_file, indent=4)"""
        if self.temporary_dict is not None:
            merged_dict = self.update_with_original_metadata_dict(merged_dict)
        return merged_dict
    
    def update_with_original_metadata_dict(self, result_dict):
        final_dict = {}
        for id in result_dict: 
            if id in self.temporary_dict:
                final_dict[id] = {**self.temporary_dict[id], **result_dict[id]}
            else:
                raise ValueError(f"Invalid temporary data dictionary: {self.temporary_dict}. Expected one of: {self.data}. A backend error has occurred.")
        return final_dict




"""

########### USAGE EXAMPLE ###########


data = [
    {
        'SECTION': 'Introduction',
        'CITATION': 'This is a citation'
    },
    {
        'SECTION': 'Introduction',
        'CITATION': 'This is a background citation'
    },
    {
        'SECTION': 'Methods',
        'CITATION': 'Here I use the method of Jhonson et al. (2020)'
    },
    {
        'SECTION': 'This will be removed because has no citation',
        'CITATION': ''
    },
    {
        'SECTION': '',
        'CITATION': 'These are the results of my experiment'
    }
]

p = Predictor(
    "mixed",
    "allenai/scibert_scivocab_cased", 
    [
        "./models/ModelsWithSections/background_model.pt",
        "./models/ModelsWithSections/method_model.pt",
        "./models/ModelsWithSections/result_model.pt"
    ],
    [
        "./models/ModelsWithoutSections/background_model_no_sections.pt",
        "./models/ModelsWithoutSections/method_model_no_sections.pt",
        "./models/ModelsWithoutSections/result_model_no_sections.pt"
    ],
    "./models/ModelsWithSections/CNN.pt",
    "./models/ModelsWithoutSections/CNN_no_sections.pt",
    data
)

print(p.final_classification())

"""

"""
Must remember to call p.tokenize() before calling p.binary_predictions()
This MATRIOSKA has to be done inside the methods, so that I can call only
the final method of the class and carry out all the operations in a single call.

Additionally, must find a way to stack the predicted outputs of the binary classifiers, as it is
now it returns only the last sentence.

Finally, this is the form of a prediction:
tensor([[[0.0447, 0.9534, 0.9897],
         [0.9553, 0.0466, 0.0103]]], device='mps:0')
Thus, percentages are coupled the one above with the one below, but which is which is a mistery now...

Rsults have the following format:
[ 
    [NO- Background_probability, NO- Method_probability, NO- Result_probability],
    [YES-Background_probability, YES-Method_probability, YES-Result_probability]
]
"""