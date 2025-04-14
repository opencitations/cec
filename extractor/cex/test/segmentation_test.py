import os
import unittest
from pathlib import Path
from lxml import etree


from extractor.cex.combined import TEIXMLtoJSONConverter

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "segmentation")
INPUT_DIR = os.path.join(BASE, "input")
OUTPUT_DIR = os.path.join(BASE, "output")



class TestSegmentation(unittest.TestCase):
    input_file = os.path.join(INPUT_DIR, "PHY-AST_EV24.grobid.tei.xml")
    output_json = os.path.join(OUTPUT_DIR, "PHY-AST_EV24.json")
    auxiliar_file = os.path.join(BASE, 'special_cases.json')

    @classmethod
    def setUpClass(cls):
        cls.json_converter = TEIXMLtoJSONConverter(cls.input_file, cls.output_json, cls.auxiliar_file, False)

    def test_find_sentences(self):
        # try to differentiate numerical in text pointers from strings

        tree = etree.parse(self.input_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        ref_citkey_dict = self.json_converter.build_dict_ref_citkey(tree, ns)
        sentences = []
        for div in root.findall(".//tei:div", namespaces=ns):
            formula_map = {}
            sentences += self.json_converter.find_sentences_in_div(div, ref_citkey_dict, ns, formula_map)

