import json
import os
import re
import unittest
from pathlib import Path

from html5lib.constants import namespaces
from lxml import etree
from spacy.lang.am.examples import sentences

from extractor.cex.combined import TEIXMLtoJSONConverter
from extractor.cex.settings import *

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "json_creation")
INPUT_FOLDER = os.path.join(BASE, "input_files")
OUTPUT_FOLDER = os.path.join(BASE, "output_files")

class TestJSONCreation(unittest.TestCase):
    input_file = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_3.grobid.tei.xml")
    input_file2 = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_EV1.grobid.tei.xml")
    output_file = os.path.join(OUTPUT_FOLDER, "AGR-BIO-SCI_3.json")
    output_file2 = os.path.join(OUTPUT_FOLDER, "AGR-BIO-SCI_EV1.json")
    auxiliar_file = SPECIAL_CASES_PATH

    @classmethod
    def setUpClass(cls):
        cls.json_converter = TEIXMLtoJSONConverter(cls.input_file, cls.output_file, cls.auxiliar_file, False)
        cls.json_converter2 = TEIXMLtoJSONConverter(cls.input_file2, cls.output_file2, cls.auxiliar_file, False)
        cls.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def test_citation_text_more_ref_not_in_a_group(self):
        self.json_converter2.convert_to_json()
        with open(self.output_file2, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            citation_text = data["cit1"]["CITATION"]
            self.assertTrue("(Martínez-Paredes et al., 2012)" in citation_text)
            self.assertTrue("(Rommers et al., 2004)" in citation_text)
            self.assertTrue("(Viudes- de-Castro et al., 1991; Rosell, 2000)" in citation_text)

    def test_citation_text_end_sentence(self):
        self.json_converter2.convert_to_json()
        with open(self.output_file2, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            citation_text = data["cit5"]["CITATION"]
            print(citation_text)

