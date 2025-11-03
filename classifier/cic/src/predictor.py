from cic.src.binary_classifiers import *
from cic.src.data_processor import *
from tqdm import tqdm

class Predictor:
    def __init__(self, case, model_1_ckp, model_2_ckp, SECTIONS_binaryCLS_state_dict_paths_list, NO_SECTIONS_binaryCLS_state_dict_paths_list, SECTIONS_metaclassifier_state_dict_path, NO_SECTIONS_metaclassifier_state_dict_path, data=None, temporary_data=None, from_json=False):
        self.valid_cases = ["WS", "WoS", "M"]
        if case not in self.valid_cases:
            raise ValueError(f"Invalid case: {case}. Expected one of: {self.valid_cases}")
        self.case = case
        self.model_1_ckp = model_1_ckp
        self.model_2_ckp = model_2_ckp
        self.device = self.retrieve_device()
        self.SECTIONS_binaryCLS_state_dict_paths_list = SECTIONS_binaryCLS_state_dict_paths_list
        self.NO_SECTIONS_binaryCLS_state_dict_paths_list = NO_SECTIONS_binaryCLS_state_dict_paths_list
        self.SECTIONS_metaclassifier_state_dict_path = SECTIONS_metaclassifier_state_dict_path
        self.NO_SECTIONS_metaclassifier_state_dict_path = NO_SECTIONS_metaclassifier_state_dict_path
        self.from_json = from_json
        self.data = None
        self.temporary_dict = None
        self.initialize_classifiers()

    def set_data(self, data, temporary_data, from_json=False):
        self.from_json = from_json
        self.temporary_dict = temporary_data
        self.data = DataProcessor(data, self.from_json).data if self.from_json else DataProcessor(data, self.from_json).mapped_data

    def initialize_classifiers(self):
        if self.case == self.valid_cases[0]:
            # Model 1
            self.binary_classifier_SciBERT = EnsembleClassifier(
                self.model_1_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list[0], # List for SciBERT (contains the 3 scibert models)
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            # Model 2
            self.binary_classifier_XLNet = EnsembleClassifier(
                self.model_2_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list[1], # List for XLNet (contains the 3 xlnet models)
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            # Metaclassifier
            self.metaclassifier = self.load_metaclassifier()

        elif self.case == self.valid_cases[1]:
            # Model 1
            self.binary_classifier_SciBERT = EnsembleClassifier(
                self.model_1_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list[0], # List for SciBERT (contains the 3 scibert models)
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            # Model 2
            self.binary_classifier_XLNet = EnsembleClassifier(
                self.model_2_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list[1], # List for XLNet (contains the 3 xlnet models)
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            # Metaclassifier
            self.metaclassifier = self.load_metaclassifier()

        elif self.case == self.valid_cases[2]:
            # SECTIONS BINARY MODELS
            self.sections_binary_classifier_SciBERT = EnsembleClassifier(
                self.model_1_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list[0],
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            self.sections_binary_classifier_XLNet = EnsembleClassifier(
                self.model_2_ckp,
                self.SECTIONS_binaryCLS_state_dict_paths_list[1],
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )

            # NO-SECTIONS BINARY MODELS
            self.no_sections_binary_classifier_SciBERT = EnsembleClassifier(
                self.model_1_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list[0],
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            self.no_sections_binary_classifier_XLNet = EnsembleClassifier(
                self.model_2_ckp,
                self.NO_SECTIONS_binaryCLS_state_dict_paths_list[1],
                {0: "no", 1: "yes"},
                {"no": 0, "yes": 1}
            )
            
            # METACLASSIFIERS
            self.metaclassifiers = self.load_metaclassifier()
            self.metaclassifier_sections = self.metaclassifiers[0]
            self.metaclassifier_no_sections = self.metaclassifiers[1]

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
        Load the metaclassifier model (compat: accetta sia checkpoint wrappati con 'model_state_dict' sia state_dict puri)
        """
        def _load_into(model, ckpt_path):
            checkpoint = torch.load(ckpt_path, map_location=self.device)  # weights_only=False di default
            # Usa la stessa logica dell'eval in training
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                state = checkpoint["model_state_dict"]
            else:
                state = checkpoint
            # (opzionale ma utile) gestisci il caso DataParallel: rimuovi 'module.' se presente
            if isinstance(state, dict) and any(k.startswith("module.") for k in state.keys()):
                state = {k[len("module."):] if k.startswith("module.") else k: v for k, v in state.items()}
            model.load_state_dict(state)     # strict=True default
            return model.to(self.device).eval()

        if self.case != "M":
            if self.case == "WS":
                metaclassifier = MetaClassifierSection()
                return _load_into(metaclassifier, self.SECTIONS_metaclassifier_state_dict_path)

            elif self.case == "WoS":
                metaclassifier = MetaClassifierNoSection()
                return _load_into(metaclassifier, self.NO_SECTIONS_metaclassifier_state_dict_path)

        else:
            SECTIONS_metaclassifier = _load_into(MetaClassifierSection(), self.SECTIONS_metaclassifier_state_dict_path)
            NO_SECTIONS_metaclassifier = _load_into(MetaClassifierNoSection(), self.NO_SECTIONS_metaclassifier_state_dict_path)
            return (SECTIONS_metaclassifier, NO_SECTIONS_metaclassifier)

        raise ValueError(f"Invalid case: {self.case}.\nExpected one of: {self.valid_cases}")



    def tokenize(self):
        if self.case != "M":
            if self.case == "WS":
                for datapoint in self.data:
                    context = self.data[datapoint]['SECTION'] + ". " + self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized_SciBERT'] = self.binary_classifier_SciBERT.tokenizer(context, return_tensors="pt")
                    self.data[datapoint]['tokenized_XLNet'] = self.binary_classifier_XLNet.tokenizer(context, return_tensors="pt")
            elif self.case == "WoS":
                for datapoint in self.data:
                    context = self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized_SciBERT'] = self.binary_classifier_SciBERT.tokenizer(context, return_tensors="pt")
                    self.data[datapoint]['tokenized_XLNet'] = self.binary_classifier_XLNet.tokenizer(context, return_tensors="pt")
        else:
            for datapoint in self.data:
                if self.data[datapoint]['SECTION'] == "":
                    context = self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized_SciBERT'] = self.no_sections_binary_classifier_SciBERT.tokenizer(context, return_tensors="pt")
                    self.data[datapoint]['tokenized_XLNet'] = self.no_sections_binary_classifier_XLNet.tokenizer(context, return_tensors="pt")
                else:
                    context = self.data[datapoint]['SECTION'] + ". " + self.data[datapoint]['CITATION']
                    self.data[datapoint]['tokenized_SciBERT'] = self.no_sections_binary_classifier_SciBERT.tokenizer(context, return_tensors="pt")
                    self.data[datapoint]['tokenized_XLNet'] = self.no_sections_binary_classifier_XLNet.tokenizer(context, return_tensors="pt")
        return self.data

    def binary_predictions(self):
        self.data = self.tokenize()

        if self.case != "M":
            # SciBERT
            scibert_model1 = self.binary_classifier_SciBERT.method_model.to(self.device).eval()
            scibert_model2 = self.binary_classifier_SciBERT.background_model.to(self.device).eval()
            scibert_model3 = self.binary_classifier_SciBERT.result_model.to(self.device).eval()
            # XLNet
            xlnet_model1 = self.binary_classifier_XLNet.method_model.to(self.device).eval()
            xlnet_model2 = self.binary_classifier_XLNet.background_model.to(self.device).eval()
            xlnet_model3 = self.binary_classifier_XLNet.result_model.to(self.device).eval()

            all_predictions = {}

            with torch.no_grad():
                for datapoint in tqdm(self.data):
                    # SciBERT Predictions
                    scibert_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_SciBERT'].items()}
                    scibert_out1 = torch.softmax(scibert_model1(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                    scibert_out2 = torch.softmax(scibert_model2(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                    scibert_out3 = torch.softmax(scibert_model3(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result
                    # XLNet Predictions
                    xlnet_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_XLNet'].items()}
                    xlnet_out1 = torch.softmax(xlnet_model1(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                    xlnet_out2 = torch.softmax(xlnet_model2(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                    xlnet_out3 = torch.softmax(xlnet_model3(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result

                    # The positive probabilities predicted for each class, for each model, are concatenated
                    out = torch.cat([scibert_out1, scibert_out2, scibert_out3, 
                                    xlnet_out1, xlnet_out2, xlnet_out3], dim=0).squeeze()
                                        
                    all_predictions[datapoint] = out

        else:
            # SECTIONS MODELS
            scibert_model1_sections = self.sections_binary_classifier_SciBERT.method_model.to(self.device).eval()
            scibert_model2_sections = self.sections_binary_classifier_SciBERT.background_model.to(self.device).eval()
            scibert_model3_sections = self.sections_binary_classifier_SciBERT.result_model.to(self.device).eval()

            xlnet_model1_sections = self.sections_binary_classifier_XLNet.method_model.to(self.device).eval()
            xlnet_model2_sections = self.sections_binary_classifier_XLNet.background_model.to(self.device).eval()
            xlnet_model3_sections = self.sections_binary_classifier_XLNet.result_model.to(self.device).eval()

            # NO SECTIONS MODELS
            scibert_model1_no_sections = self.no_sections_binary_classifier_SciBERT.method_model.to(self.device).eval()
            scibert_model2_no_sections = self.no_sections_binary_classifier_SciBERT.background_model.to(self.device).eval()
            scibert_model3_no_sections = self.no_sections_binary_classifier_SciBERT.result_model.to(self.device).eval()

            xlnet_model1_no_sections = self.no_sections_binary_classifier_XLNet.method_model.to(self.device).eval()
            xlnet_model2_no_sections = self.no_sections_binary_classifier_XLNet.background_model.to(self.device).eval()
            xlnet_model3_no_sections = self.no_sections_binary_classifier_XLNet.result_model.to(self.device).eval()

            all_predictions = {
                "NO-SECTIONS": {},
                "SECTIONS": {}
            }

            with torch.no_grad():
                for datapoint in tqdm(self.data):
                    if self.data[datapoint]['SECTION'] == "": # NO SECTIONS case
                        # SciBERT Predictions
                        scibert_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_SciBERT'].items()}
                        scibert_out1 = torch.softmax(scibert_model1_no_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                        scibert_out2 = torch.softmax(scibert_model2_no_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                        scibert_out3 = torch.softmax(scibert_model3_no_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result
                        # XLNet Predictions
                        xlnet_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_XLNet'].items()}
                        xlnet_out1 = torch.softmax(xlnet_model1_no_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                        xlnet_out2 = torch.softmax(xlnet_model2_no_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                        xlnet_out3 = torch.softmax(xlnet_model3_no_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result

                        # The positive probabilities predicted for each class, for each model, are concatenated
                        out = torch.cat([scibert_out1, scibert_out2, scibert_out3, 
                                        xlnet_out1, xlnet_out2, xlnet_out3], dim=0).squeeze()
                        
                        all_predictions['NO-SECTIONS'][datapoint] = out

                    else: # With Section case
                        # SciBERT Predictions
                        scibert_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_SciBERT'].items()}
                        scibert_out1 = torch.softmax(scibert_model1_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                        scibert_out2 = torch.softmax(scibert_model2_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                        scibert_out3 = torch.softmax(scibert_model3_sections(**scibert_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result
                        # XLNet Predictions
                        xlnet_input_data = {key: val.to(self.device) for key, val in self.data[datapoint]['tokenized_XLNet'].items()}
                        xlnet_out1 = torch.softmax(xlnet_model1_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive method
                        xlnet_out2 = torch.softmax(xlnet_model2_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive background
                        xlnet_out3 = torch.softmax(xlnet_model3_sections(**xlnet_input_data).logits, dim=-1)[:, 1].unsqueeze(0)  # Positive result

                        # The positive probabilities predicted for each class, for each model, are concatenated
                        out = torch.cat([scibert_out1, scibert_out2, scibert_out3, 
                                        xlnet_out1, xlnet_out2, xlnet_out3], dim=0).squeeze()
                        
                        all_predictions['SECTIONS'][datapoint] = out

        return all_predictions


    def final_classification(self):
        """
        The order of the predictions in the final tensor is:
        0 == Method
        1 == Background
        2 == Result
        """
        all_predictions = self.binary_predictions()
        #print(all_predictions) #debug print

        if self.case != "M":
            final_predictions = {}
            model = self.metaclassifier.to(self.device).eval()
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
            sections_model = self.metaclassifier_sections.to(self.device).eval()
            no_sections_model = self.metaclassifier_no_sections.to(self.device).eval()

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
        #print("Final output:", output_dict)  # Debug print
        return output_dict  # return a new dictionary containing final predictions

    def create_json(self, predictions, final_predictions):
        def final_prediction_string(prediction_integer, metaclassifier_probabilities):
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

        if self.case != "M":
            merged_dict = {}
            for id in self.data:
                merged_dict[id] = {
                    "SECTION": self.data[id]['SECTION'],
                    "CITATION": self.data[id]['CITATION'],
                    "SCIBERT MET POSITIVE PROBABILITY": predictions[id][0].item(),
                    "SCIBERT BKG POSITIVE PROBABILITY": predictions[id][1].item(),
                    "SCIBERT RES POSITIVE PROBABILITY": predictions[id][2].item(),
                    "XLNET MET POSITIVE PROBABILITY": predictions[id][3].item(),
                    "XLNET BKG POSITIVE PROBABILITY": predictions[id][4].item(),
                    "XLNET RES POSITIVE PROBABILITY": predictions[id][5].item(),
                    "MET ENSEMBLE CONFIDENCE": final_predictions[id]['FinalPrediction'][1][0],
                    "BKG ENSEMBLE CONFIDENCE": final_predictions[id]['FinalPrediction'][1][1],
                    "RES ENSEMBLE CONFIDENCE": final_predictions[id]['FinalPrediction'][1][2],
                    "FINAL PREDICTION": final_prediction_string(final_predictions[id]['FinalPrediction'][0], final_predictions[id]['FinalPrediction'][1])
                }

        else:
            merged_dict = {}
            for id in self.data:
                merged_dict[id] = {
                    "SECTION": self.data[id]['SECTION'],
                    "CITATION": self.data[id]['CITATION']
                }
                if self.data[id]['SECTION'] == "":
                    merged_dict[id]["SCIBERT MET POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][0].item()
                    merged_dict[id]["SCIBERT BKG POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][1].item()
                    merged_dict[id]["SCIBERT RES POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][2].item()
                    merged_dict[id]["XLNET MET POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][3].item()
                    merged_dict[id]["XLNET BKG POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][4].item()
                    merged_dict[id]["XLNET RES POSITIVE PROBABILITY"] = predictions['NO-SECTIONS'][id][5].item()
                    merged_dict[id]["MET ENSEMBLE CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][0]
                    merged_dict[id]["BKG ENSEMBLE CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][1]
                    merged_dict[id]["RES ENSEMBLE CONFIDENCE"] = final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1][2]
                    merged_dict[id]["FINAL PREDICTION"] = final_prediction_string(final_predictions['NO-SECTIONS'][id]['FinalPrediction'][0], final_predictions['NO-SECTIONS'][id]['FinalPrediction'][1])
                else:
                    merged_dict[id]["SCIBERT MET POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][0].item()
                    merged_dict[id]["SCIBERT BKG POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][1].item()
                    merged_dict[id]["SCIBERT RES POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][2].item()
                    merged_dict[id]["XLNET MET POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][3].item()
                    merged_dict[id]["XLNET BKG POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][4].item()
                    merged_dict[id]["XLNET RES POSITIVE PROBABILITY"] = predictions['SECTIONS'][id][5].item()
                    merged_dict[id]["MET ENSEMBLE CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][0]
                    merged_dict[id]["BKG ENSEMBLE CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][1]
                    merged_dict[id]["RES ENSEMBLE CONFIDENCE"] = final_predictions['SECTIONS'][id]['FinalPrediction'][1][2]
                    merged_dict[id]["FINAL PREDICTION"] = final_prediction_string(final_predictions['SECTIONS'][id]['FinalPrediction'][0], final_predictions['SECTIONS'][id]['FinalPrediction'][1])

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






########### USAGE EXAMPLE ###########

## FARE CHECK CASISTICHE - DONE


"""data = [
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
]"""


"""
data = [
    ('Introduction', "In his 1945 essay 'As We May Think', Vannevar Bush observed how 'publication has been extended far beyond our present ability to make real use of the record' [Bush, 1945]."),
    ('Introduction', "Licklider expanded on this with the vision of a symbiotic relationship between humans and machines. Computers would take care of routine tasks such as storage and retrieval, 'preparing the way for insights and decisions in scientific thinking' [Licklider, 1960]."),
    ('Introduction', 'Computing has indeed revolutionized how research is conducted, but information overload remains an overwhelming problem [Bornmann and Mutz, 2014].'),
    ('Introduction', 'In May 2022, an average of 516 papers per day were submitted to arXiv [arXiv, 2022]. Beyond papers, scientific data is also growing much more quickly than our ability to process it [Marx, 2013]. As of August 2022, the NCBI GenBank contained 1.49 × 1012 nucleotide bases [GenBank, 2022].'),
    ('Our Contribution', 'On reasoning tasks, Galactica beats existing language models on benchmarks such as MMLU and MATH [Hendrycks et al., 2020, 2021].'),
    ('Our Contribution', 'With our reasoning token approach, we outperform Chinchilla on mathematical MMLU with an average score of 41.3% versus 35.7% [Hoffmann et al., 2022]. Our 120B model achieves a score of 20.4% versus PaLM 540B’s 8.8% on MATH [Chowdhery et al., 2022; Lewkowycz et al., 2022].'),
    ('Our Contribution', 'We believe this adds another reasoning method to the deep learning toolkit, alongside the existing chain-of-thought approach that has been well explored recently [Wei et al., 2022; Suzgun et al., 2022].'),
    ('Our Contribution', 'Galactica significantly exceeds the performance of general language models such as the latest GPT-3 in these tasks; on LaTeX equations, it achieves a score of 68.2% versus the latest GPT-3’s 49.0% [Brown et al., 2020].'),
    ('Our Contribution', 'Galactica also performs well in downstream scientific tasks, and we set a new state-of-the-art on several downstream tasks such as PubMedQA [77.6%] and MedMCQA dev [52.9%] [Jin et al., 2019; Pal et al., 2022].'),
    ('Related Work', 'LLMs have achieved breakthrough performance on NLP tasks in recent years. Models are trained with self-supervision on large, general corpuses and they perform well on hundreds of tasks [Brown et al., 2020; Rae et al., 2021; Hoffmann et al., 2022; Black et al., 2022; Zhang et al., 2022; Chowdhery et al., 2022]. This includes scientific knowledge tasks such as MMLU [Hendrycks et al., 2020].'),
    ('Related Work', 'They have the capability to learn in-context through few-shot learning [Brown et al., 2020]. The capability set increases with scale, and recent work has highlighted reasoning capabilities at larger scales with a suitable prompting strategy [Wei et al., 2022; Chowdhery et al., 2022; Kojima et al., 2022; Lewkowycz et al., 2022].'),
    ('Related Work', 'One downside of self-supervision has been the move towards uncurated data. Models may mirror misinformation, stereotypes and bias in the corpus [Sheng et al., 2019; Kurita et al., 2019; Dev et al., 2019; Blodgett et al., 2020; Sheng et al., 2021]. This is undesirable for scientific tasks which value truth.'),
    ('Related Work', 'Uncurated data also means more tokens with limited transfer value for the target use-case; wasting compute budget. For example, the PaLM corpus is 50% social media conversations, which may have limited transfer towards scientific tasks [Chowdhery et al., 2022].'),
    ('Related Work', 'Works such as SciBERT, BioLM and others have shown the benefit of a curated, scientific corpus [Beltagy et al., 2019; Lewis et al., 2020a; Gu et al., 2020; Lo et al., 2019b; Gu et al., 2020; Shin et al., 2020; Hong et al., 2022]. The datasets and models were typically small in scale and scope, much less than corpora for general models.'),
    ('Related Work', 'Beyond scientific text, Transformers for protein sequences and SMILES have shown potential for learning natural representations [Rives et al., 2021; Honda et al., 2019; Irwin et al., 2021; Nijkamp et al., 2022; Lin et al., 2022b].'),
    ('Related Work', "The idea of 'scaling laws' was put forward by Kaplan et al. [2020], who demonstrated evidence that loss scales as a power-law with model size, dataset size, and the amount of training compute."),
    ('Related Work', "The focus was on upstream perplexity, and work by Tay et al. [2022a] showed that this does not always correlate with downstream performance. Hoffmann et al. [2022] presented new analysis taking into account the optimal amount of data, and suggested that existing language models were undertrained: 'Chinchilla scaling laws'."),
    ('Related Work', 'Despite hallucination risks, there is evidence large language models can act as implicit knowledge bases with sufficient capacity [Petroni et al., 2019].'),
    ('Related Work', 'They perform well on knowledge-intensive tasks such as general knowledge [TriviaQA] and specialist knowledge [MMLU] without an external retrieval mechanism [Brown et al., 2020; Hendrycks et al., 2020].'),
    ('Related Work', 'The question of how to update network knowledge remains an active research question [Scialom et al., 2022; Mitchell et al., 2022]. Likewise, the question of how to improve the reliability of generation is an active question [Gao et al., 2022].'),
    ('Related Work', 'Despite these limitations, today’s large models will become cheaper with experience [Hirschmann, 1964], and so a growing proportion of scientific knowledge will enter weight memory as training and re-training costs fall.'),
    ('Related Work', 'Retrieval-augmented models aim to alleviate the shortcomings of weight memory. Examples of such models include RAG, RETRO and Atlas [Lewis et al., 2020b; Borgeaud et al., 2021; Izacard et al., 2022].'),
    ('Dataset', 'The idea that Nature can be understood in terms of an underlying language has a long history [Galilei, 1623; Wigner, 1959; Wheeler, 1990].'),
    ('Dataset', 'In recent years, deep learning has been used to represent Nature, such as proteins and molecules [Jumper et al., 2021; Ross et al., 2021]. Amino acids are an alphabet in which the language of protein structure is written, while atoms and bonds are the language of molecules.'),
    ('Dataset', 'At a higher level, we organize knowledge through natural language, and many works have trained on scientific text [Beltagy et al., 2019; Lewis et al., 2020a; Gu et al., 2020; Lo et al., 2019b].'),
    ('Dataset', 'This is a key question of this work: can we make a working LLM based on a curated, normative paradigm? If true, we could make more purposefully-designed LLMs by having a clear understanding of what enters the corpus, similar to expert systems which had normative standards [Jackson, 1990].'),
    ('3.1 Working Memory Token, <work>', 'A current workaround is using a Transformer’s output context as an external working memory to read from and write to. This is seen in recent work on chain-of-thought prompting [Wei et al., 2022; Suzgun et al., 2022].'),
    ('3.1 Working Memory Token, <work>', 'Prior work has shown that accuracy on tasks like multiplication is proportional to term frequency [Razeghi et al., 2022].'),
    ('3.1 Working Memory Token, <work>', 'Given that classical computers are specialized for tasks like arithmetic, one strategy is to offload these tasks from the neural network to external modules. For example, prior work has looked at the possibilities of external tool augmentation, such as calculators [Thoppilan et al., 2022].'),
    ('3.1 Working Memory Token, <work>', 'Longer term, an architecture change may be needed to support adaptive computation, so machines can have internal working memory on the lines of work such as adaptive computation time and PonderNet [Graves, 2016; Banino et al., 2021].'),
    ('3.2 Prompt Pre-Training', "First, existing work has shown the importance of training token count on performance. The Chinchilla paper derived scaling 'laws' taking into account number of tokens, training a 70bn model for 1.4 trillion tokens [Hoffmann et al., 2022]. They obtained state-of-the-art performance on MMLU, beating much larger models such as Gopher [Rae et al., 2021]."),
    ('3.2 Prompt Pre-Training', 'Separately, research such as FLAN and T0 showed prompt tuning can boost downstream performance [Wei et al., 2021; Sanh et al., 2021; Chung et al., 2022]. Their strategy involved converting tasks to text prompts, using prompt diversity in how the tasks are posed, and then fine-tuning on these prompt datasets.'),
    ('3.2 Prompt Pre-Training', 'And additionally there is the UnifiedQA approach [Khashabi et al., 2020]. In this approach, a T5 model is fine-tuned on question answering datasets, and is shown to boost performance on out-of-domain question answering datasets [Raffel et al., 2020].'),
    ('4.1 Architecture', 'Galactica uses a Transformer architecture in a decoder-only setup [Vaswani et al., 2017], with the following modifications'),
    ('4.1 Architecture', 'GeLU Activation - we use GeLU activations for all model sizes [Hendrycks and Gimpel, 2016].'),
    ('4.1 Architecture', 'No Biases - following PaLM, we do not use biases in any of the dense kernels or layer norms [Chowdhery et al., 2022].'),
    ('4.1 Architecture', 'Learned Positional Embeddings - we use learned positional embeddings for the model. We experimented with ALiBi at smaller scales but did not observe large gains, so we did not use it [Press et al., 2021].'),
    ('4.1 Architecture', 'Vocabulary - we construct a vocabulary of 50k tokens using BPE [Sennrich et al., 2015]. The vocabulary was generated from a randomly selected 2% subset of the training data.'),
    ('4.2 Models', 'We train using AdamW with β1 = 0.9, β2 = 0.95 and weight decay of 0.1 [Loshchilov and Hutter, 2017]. We clip the global norm of the gradient at 1.0, and we use linear decay for learning rate down to 10% of it value.'),
    ('5.1 Repeated Tokens Considered Not Harmful', 'The largest 120B model only begins to overfit at the start of the fifth epoch. This is unexpected as existing research suggests repeated tokens can be harmful on performance [Hernandez et al., 2022].'),
    ('5.1 Repeated Tokens Considered Not Harmful', 'The next question to answer is whether this trend extends to downstream performance and out-of-domain generalization. For this we use a 57 task subset of BIG-bench subset, a general corpus with principally nonscientific tasks and prompt types not included in pre-training [Srivastava et al., 2022].'),
    ('5.2 Knowledge Probes', 'First, we examine how well Galactica absorbs scientific knowledge. We set up several knowledge probe benchmarks, building off the LAMA approach of Petroni et al. [2019].'),
    ('5.2.3 Reasoning', 'We now turn to reasoning capabilities with the <work> token. We start by evaluating on the MMLU mathematics benchmarks, which we report in Table 8 [Hendrycks et al., 2020].'),
    ('5.3 Downstream Scientific NLP', 'On remaining tasks, we achieve state-of-the-art results over fine-tuned models at the time of writing. On PubMedQA, we achieve a score of 77.6% which outperforms the state-of-the-art of 72.2% [Yasunaga et al., 2022].'),
    ('5.3 Downstream Scientific NLP', 'On MedMCQA dev we achieve score of 52.9% versus the state-of-the-art of 41.0% [Gu et al., 2020].'),
    ('5.3 Downstream Scientific NLP', 'For BioASQ and MedQA-USMLE, performance is close to the state-of-the-art performance of fine-tuned models [94.8% and 44.6%] [Yasunaga et al., 2022].'),
    ('5.4.1 Citation Accuracy', 'For dense retriever baselines, we evaluate two different Contriever models [Izacard et al., 2021].'),
    ('5.4.1 Citation Accuracy', 'For dense retriever baselines, we evaluate two different Contriever models [Izacard et al., 2021]. The first is the pre-trained model released by Izacard et al. [2021].'),
    ('5.4.1 Citation Accuracy', 'Retrieval is performed using a FAISS index [Johnson et al., 2019].'),
    ('5.4.2 Citation Distributional Analysis', 'This allows us to assess the model bias towards predicting more popular papers. Specifically, for each context there is a ground truth and predicted reference. We count the number of times each reference appears in our corpus. We then compare the distribution of reference counts between the ground truth references and the predicted references using the Kolmogorov-Smirnov distance [Massey, 1951].'),
    ('5.5 General Capabilities', 'We evaluate on 57 BIG-bench tasks in Table 12 [Srivastava et al., 2022]. The tasks are primarily non-scientific and test general language capability, for example anachronisms, figure of speech and metaphor boolean.'),
    ('5.6.1 IUPAC Name Prediction', 'SMILES is a line notation which represents chemical structure as a sequence of characters [Weininger, 1988].'),
    ('5.6.1 IUPAC Name Prediction', 'The IUPAC nomenclature is a method of naming organic compounds that has a ruleset based on naming the longest chain of carbons connected by single bonds [Favre and Powerll].'),
    ('5.6.1 IUPAC Name Prediction', 'Previous works such as STOUT and Struct2IUPAC have explored the possiblity of using RNNs and Transformers for this task [Rajan et al., 2021; Krasnov et al., 2021].'),
    ('5.6.1 IUPAC Name Prediction', 'To evaluate, we use our compound validation set of 17,052 compounds, and prompt with the SMILES formula and predict the IUPAC name. To calculate accuracy, we use OPSIN to convert the generated IUPAC name to SMILES, canonicalize it and compare with the canonicalized SMILES target [Lowe et al., 2011].'),
    ('5.6.2 MoleculeNet', 'Humans organize knowledge via natural language, and so learning an interface between natural language and scientific modalities like SMILES could be a new tool for navigating the chemical space. We use MoleculeNet classification benchmarks to answer this question, which are summarized in Table 14 [Wu et al., 2017].'),
    ('5.6.2 MoleculeNet', 'We convert training sets to text format and include in pre-training. We evaluate using the splits suggested by the DeepChem library [Ramsundar et al., 2019].'),
    ('5.6.2 MoleculeNet', 'We make sure to Kekulize the SMILES to be consistent with PubChem representations. For evaluation, we use the recommended splits from the DeepChem library [Ramsundar et al., 2019].'),
    ('5.7.1 Sequence Validation Perplexity', 'First, we conduct BLAST on the sequences in the training set and remove all sequences with a sequence identity ≥ 50% with 51 CASP14 target sequences. These are the same test sequences used in ESMFold [Lin et al., 2022b].'),
    ('5.7.3 Protein Function Description', 'As with the keyword prediction task, Galactica appears to be learning based on matching sequences with similar ones it has seen in training, and using this to form a description. This suggests language models for protein sequences could serve as useful alternatives to existing search methods such as BLAST and MMseqs2 [Altschul et al., 1990; Steinegger and Söding, 2017].'),
    ('6.1.1 CrowS-Pairs', "CrowS-Pairs is a collection of 1,508 crowd-sourced pairs of sentences, one which is 'more' stereotyping and one which is 'less' stereotyping, and covers nine characteristics [Nangia et al., 2020]."),
    ('6.1.1 CrowS-Pairs', 'Language models such as OPT use the pushshift.io Reddit corpus as a primary data source, which likely leads the model to learn more discriminatory associations [Zhang et al.,2022].'),
    ('6.1.2 StereoSet', 'StereoSet aims to measure stereotypical biases across profession, religion, gender, and race [Nadeem et al., 2021].'),
    ('6.1.3 Toxicity', 'To measure toxicity we use the RealToxicityPrompts [RTP] benchmark introduced in Gehman et al. [2020].'),
    ('6.1.3 Toxicity', 'We follow the same setup of Zhang et al. [2022] and sample 25 generations of 20 tokens using nucleus sampling [p=0.9] for each of 5000 randomly sampled prompts from RTP. We use the prompts to produce sequences [i.e, continuations] which are then scored by a toxicity classifier provided by Perspective API5'),
    ('6.2 TruthfulQA', 'TruthfulQA is a benchmark that measures answer truthfulness of language model generations [Lin et al., 2022a]. It comprises 817 questions that span health, law, finance and other categories.'),
    ('7.1 Limitations', 'Prompt Pre-Training vs Instruction Tuning We opted for the former in this paper, but ideally we would need to explore what the latter could achieve, along the lines of the recent work of Chung et al. [2022]. A limitation of this work is that we do not perform this direct comparison through ablations, making clear the trade-offs between approaches.'),
    ('7.2 Future Work', 'New Objective Function It is likely further gains can be obtained with mixture-of-denoising training as U-PaLM has recently shown [Tay et al., 2022b; Chung et al., 2022]. We suspect this might be beneficial for the scientific modalities such as protein sequences, where the left-to-right LM objective is quite limiting.'),
    ('7.2 Future Work', 'Extending to Images We cannot capture scientific knowledge adequately without capturing images. This is a natural follow-up project, although it likely requires some architectural modification to make it work well. Existing work such as Alayrac et al. [2022] has shown how to extend LLMs with this modality.'),
]
"""

"""data = [
    ('Introduction', 'This is a citation'),
    ('Introduction', 'This is a background citation'),
    ('Methods', 'Here I use the method of Jhonson et al. (2020)'),
    ('This will be removed because has no citation', ''),
    ('', 'These are the results of my experiment')
]

# '[s]7.7.2. Introduction.[s] [c]This is a citation. I use the method of Jhonson et al. (2020)[c]'

p = Predictor(
    "M",
    "allenai/scibert_scivocab_cased",
    "xlnet/xlnet-base-cased",
    [
        [
            "cic/src/Sections/SciBERT_method_model.pt",
            "cic/src/Sections/SciBERT_background_model.pt",
            "cic/src/Sections/SciBERT_result_model.pt"
        ],
        [
            "cic/src/Sections/XLNet_method_model.pt",
            "cic/src/Sections/XLNet_background_model.pt",
            "cic/src/Sections/XLNet_result_model.pt"
        ]
    ],
    [
        [
            "cic/src/NoSections/NoSec_SciBERT_method_model.pt",
            "cic/src/NoSections/NoSec_SciBERT_background_model.pt",
            "cic/src/NoSections/NoSec_SciBERT_result_model.pt"
        ],
        [
            "cic/src/NoSections/NoSec_XLNet_method_model.pt",
            "cic/src/NoSections/NoSec_XLNet_background_model.pt",
            "cic/src/NoSections/NoSec_XLNet_result_model.pt"
        ]
    ],
    "cic/src/Sections/metaSec_89_46.pth",
    "cic/src/NoSections/metaNoSec_8848.pth",
    data
)

print(p.final_classification())"""



"""
{Must remember to call p.tokenize() before calling p.binary_predictions()
This MATRIOSKA has to be done inside the methods, so that I can call only
the final method of the class and carry out all the operations in a single call.} DONE

REsults of the binary predictors have the following format:

    tensor([0.1181, 0.9395, 0.0094, 0.0584, 0.9844, 0.0011], device='mps:0')

Where:

    SciBERT Method Positive Probability: 0.1181
    SciBERT Background Positive Probability: 0.9395
    SciBERT Result Positive Probability: 0.0094
    XLNet Method Positive Probability: 0.0584
    XLNet Background Positive Probability: 0.9844
    XLNet Result Positive Probability: 0.0011

Thus the structure is: 

    Positive Method probability from SciBERT.
    Positive Background probability from SciBERT.
    Positive Result probability from SciBERT.
    Positive Method probability from XLNet.
    Positive Background probability from XLNet.
    Positive Result probability from XLNet.

    



    [0.1181, 0.9395, 0.0094, 0.0584, 0.9844, 0.0011]
            0      1      2
       - [00.03, 99.91, 00.06]
       - Return -> 1

"""
