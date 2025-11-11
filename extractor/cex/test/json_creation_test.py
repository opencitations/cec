import json
import os
import re
import unittest
from pathlib import Path

from html5lib.constants import namespaces
from lxml import etree
from spacy.lang.am.examples import sentences

from combined import TEIXMLtoJSONConverter
from settings import *
import shutil

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "json_creation")
INPUT_FOLDER = os.path.join(BASE, "input_files")
OUTPUT_FOLDER = os.path.join(BASE, "output_files")

class TestJSONCreation(unittest.TestCase):
    input_file = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_3.grobid.tei.xml")
    input_file2 = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_EV1.grobid.tei.xml")
    input_file3 = os.path.join(INPUT_FOLDER, "NOTES-8.grobid.tei.xml")
    input_file4 = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_4.grobid.tei.xml")
    input_file5 = os.path.join(INPUT_FOLDER, "ART-HUM_5.grobid.tei.xml")
    input_file6 = os.path.join(INPUT_FOLDER, "ENE_46.xml")
    output_file = os.path.join(OUTPUT_FOLDER, "AGR-BIO-SCI_3.json")
    output_file2 = os.path.join(OUTPUT_FOLDER, "AGR-BIO-SCI_EV1.json")
    output_file3 = os.path.join(OUTPUT_FOLDER, "NOTES-8.json")
    output_file4 = os.path.join(OUTPUT_FOLDER, "AGR-BIO-SCI_4.json")
    output_file5 = os.path.join(OUTPUT_FOLDER, "ART-HUM_5.json")
    output_file6 = os.path.join(OUTPUT_FOLDER, "ENE_46.json")
    auxiliar_file = SPECIAL_CASES_PATH

    @classmethod
    def setUpClass(cls):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        cls.json_converter = TEIXMLtoJSONConverter(cls.input_file, cls.output_file, cls.auxiliar_file, False)
        cls.json_converter2 = TEIXMLtoJSONConverter(cls.input_file2, cls.output_file2, cls.auxiliar_file, False)
        cls.json_converter3 = TEIXMLtoJSONConverter(cls.input_file3, cls.output_file3, cls.auxiliar_file, False)
        cls.json_converter4 = TEIXMLtoJSONConverter(cls.input_file4, cls.output_file4, cls.auxiliar_file, False)
        cls.json_converter5 = TEIXMLtoJSONConverter(cls.input_file5, cls.output_file5, cls.auxiliar_file, False)
        cls.json_converter6 = TEIXMLtoJSONConverter(cls.input_file6, cls.output_file6, cls.auxiliar_file, False)
        cls.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    @classmethod
    def tearDownClass(cls):
        # Clean up test directories after all tests
        shutil.rmtree(OUTPUT_FOLDER, ignore_errors=True)


    def test_citation_text_more_ref_not_in_a_group(self):
        self.json_converter2.convert_to_json()
        with open(self.output_file2, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            citation_text = data["cit1"]["CITATION"]
            self.assertTrue("(Martínez-Paredes et al., 2012)" in citation_text)
            self.assertTrue("(Rommers et al., 2004)" in citation_text)
            self.assertTrue("(Viudes- de-Castro et al., 1991; Rosell, 2000)" in citation_text)

    def test_citation_footnote(self):
        self.json_converter3.convert_to_json()
        with open(self.output_file3, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            self.assertTrue(
         any(entry.get("CITATION") == 'For a design process that prioritizes exact optimisation, see [15].'
        for entry in data.values()))
            
    def test_figure_caption_deduplication(self):
        self.json_converter4.convert_to_json()
        with open(self.output_file4, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        all_figure_captions = [entry["CITATION"] for entry in data.values() if entry.get("SECTION") == "Figure Caption"]
        self.assertTrue(len(all_figure_captions) == 1)

    def test_untitled_sections(self):
        self.json_converter5.convert_to_json()
        with open(self.output_file5, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        all_sections = set([entry['SECTION'] for entry in data.values()])
        self.assertTrue('Section Untitled 1' in all_sections and 'Section Untitled 2' in all_sections)

    def test_sentence_with_formulas(self):
        self.json_converter6.convert_to_json()
        with open(self.output_file6, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)


if __name__ == "__main__":
    unittest.main()

