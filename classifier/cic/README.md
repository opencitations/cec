<a id="readme-top"></a>

[![Read The Paper](https://img.shields.io/badge/Read_The_Paper-red?style=flat-square)](https://arxiv.org/abs/2407.13329)

<br />
<div align="center">
  <h1 align="center">Citation Extractor and Classifier</h1>
</div>

## About The Project

The Citation Extractor and Classifier (CEC) is a software that performs automatic annotation of in-text citations in academic papers provided in PDF. This page describes the Citation Intent Classifier (CIC) component, which is able to identify the citation intent of one or more citation(s) given as input.

Citations are classified according to the [CiTO ontology](https://sparontologies.github.io/cito/current/cito.html) and four classes are currently recognized: UsesMethodIn, ObtainsBackgroundFrom, UseConclusionsFrom and CitesForInformation.

### Technical Overview

The classification part is carried out by an Ensemble Model, which is a combination of six binary classifiers (in Beta release) and a meta classifier built on top of them.
The meta classifier carries out the voting process and returns the final classification result.
Furthermore, a threshold of 90% confidence has been defined to filter out the results on which the ensemble is not confident enough.

### Key Features
The baseline model surpass the current SOTA Macro-F1 score for the citation intent classification task within the SciCite dataset.

This tool gives you the possibility to classify any number of input sentences given in input in the form of a list of tuples, or as a JSON file. The tool also gives you the possibility to download the results in JSON format.

You have the possibility to select one of three possible working modes:

* With Sections: select this mode if ALL your sentences have also the title of the section in which the citation is contained;
* Without Sections: select this mode if NONE of your sentences contains the title of the section in which the citation is, or if you want to try a classification based on the pure semantic of the sentence at hand;
* Mixed: select this mode if SOME of your sentences have the title of the section in which the citation is contained, and others not. The tool will carry out the entire filtering process and return you the results.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/opencitations/cec.git
   ```
2. Create a python virtual environment (venv)
   ```
   python -m venv <your_venv>
   ```
3. Activate the newly created venv
   ```
   source <your_venv>/bin/activate
   ```
4. Install requirements
   ```
   pip install -r requirements.txt
   ```
5. Run the application
   ```
   python AlphaCIC/main.py
   ```

#### Configuration:
* `PREFIX = /cic/`
* `SRC_PATH = src/`

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Roadmap

- [x] Beta Release:
    - [x] Add structured README.md
    - [x] Add Changelog
    - [x] Improve classifier
    - [x] Publish article
    - [ ] Release new template for the web application
    - [ ] Release API:
        - [ ] Write API:
           - [x] Add support for compressed files and folders
           - [ ] Write Documentation 
           - [ ] Write usage examples
        - [ ] Update base software:
            - [x] Update ensemble models
            - [ ] Add a better threshold definition mechanics

- [x] Alpha Release:
    - [x] Release web application:
        - [x] Design web interface
        - [x] Develop and publish classification model

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## License

Distributed under the ISC License. See [LICENCE](https://github.com/opencitations/cec/blob/main/LICENCE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
