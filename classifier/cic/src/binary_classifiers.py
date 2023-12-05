from src.metaclassifiers import *
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class EnsembleClassifier:
    def __init__(self, model_ckp, state_dict_paths_list, id2label, label2id):
        """
        To initialize the classifier, we need to provide the following:
            - model_ckp: the checkpoint of the model used to fine-tune
            - state_dict_paths_list: a list of paths to the state_dict of each model in the ensemble.
                                        The order of the paths must be the same as the order of the models in the ensemble.
                                        Here it is important to follow the following order:
                                            1. Background model
                                            2. Method model
                                            3. Result model
            - metaclassifier_state_dict_path: the path to the state_dict of the metaclassifier
            - id2label: id2label dictionary
            - label2id: label2id dictionary
        """
        self.model_ckp = model_ckp
        self.state_dict_paths_list = state_dict_paths_list
        self.id2label = id2label
        self.label2id = label2id
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_ckp)
        self.device = self.retrieve_device()
        self.models = self.load_fine_tuned_model()
        self.background_model = self.models[0]
        self.method_model = self.models[1]
        self.result_model = self.models[2]

    def retrieve_device(self):
        """
        Retrieve the device on which to run the model.
        """

        if torch.cuda.is_available():
            device = torch.device("cuda")
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
        return device

    def load_fine_tuned_model(self):
        """
        Load the fine-tuned models specific to this case.
        """

        background_state_dict_path = self.state_dict_paths_list[0]
        background_model = AutoModelForSequenceClassification.from_pretrained(
            self.model_ckp, num_labels=2, id2label=self.id2label, label2id=self.label2id
        )
        background_model.load_state_dict(torch.load(background_state_dict_path, map_location=self.device))
        background_model = background_model.to(self.device).eval()


        method_state_dict_path = self.state_dict_paths_list[1]
        method_model = AutoModelForSequenceClassification.from_pretrained(
            self.model_ckp, num_labels=2, id2label=self.id2label, label2id=self.label2id
        )
        method_model.load_state_dict(torch.load(method_state_dict_path, map_location=self.device))
        method_model = method_model.to(self.device).eval()

        result_state_dict_path = self.state_dict_paths_list[2]
        result_model = AutoModelForSequenceClassification.from_pretrained(
            self.model_ckp, num_labels=2, id2label=self.id2label, label2id=self.label2id
        )
        result_model.load_state_dict(torch.load(result_state_dict_path, map_location=self.device))
        result_model = result_model.to(self.device).eval()

        return (background_model, method_model, result_model)

    def load_metaclassifier(self):
        """
        Load the CNN metaclassifier.
        """
        metaclassifier = SectionsMetaClassifierCNN()  # create instance of CNN_1d metaclassifier
        metaclassifier.load_state_dict(torch.load(self.metaclassifier_state_dict_path))
        metaclassifier = metaclassifier.to(self.device).eval()
        return metaclassifier
