import os
import unittest
from pathlib import Path

from lxml import etree

from extractor.cex.combined import TEIXMLtoJSONConverter
from extractor.cex.settings import *

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "json_creation")
INPUT_FOLDER = os.path.join(BASE, "input_files")
OUTPUT_FOLDER = os.path.join(BASE, "output_files")

class TestJSONCreation(unittest.TestCase):
    input_file = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_3.grobid.tei.xml")
    output_file = os.path.join(INPUT_FOLDER, "AGR-BIO-SCI_3.json")
    auxiliar_file = SPECIAL_CASES_PATH

    @classmethod
    def setUpClass(cls):
        cls.json_converter = TEIXMLtoJSONConverter(cls.input_file, cls.output_file, cls.auxiliar_file)
        cls.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}


    def test_find_group_references_single(self):
        div = """<div xmlns="http://www.tei-c.org/ns/1.0"><head>INTRODUCTION</head><p>Examples of trait matching include the length of pollinator tongue and corolla depth of flowers <ref type="bibr" coords="2,218,61,247,82,51,59,8,05" target="#b20">(Ibanez 2012)</ref>, biting force of ground beetles and cuticular toughness of prey <ref type="bibr" coords="2,77,95,269,70,87,59,8,05">(Brousseau et al. 2018b</ref>) and lipid content of predatory marine mammals and caloric content of prey <ref type="bibr" coords="2,251,89,280,70,22,21,8,05;2,58,96,291,64,43,26,8,05" target="#b45">(Spitz et al. 2014)</ref>.</p></div>"""
        root = etree.fromstring(div)
        refs_with_following_text = root.xpath(
            "//tei:ref[@type='bibr'][following-sibling::node()[1][self::text()]]",
            namespaces=self.ns
        )
        groups = self.json_converter.find_group_references(root, self.ns, refs_with_following_text)
        groups_text = [[elem.text for elem in sublist] for sublist in groups]

        self.assertTrue('Ibanez 2012' in ''.join(groups_text[0]).strip('()'))
        self.assertTrue('Brousseau et al. 2018b' in ''.join(groups_text[1]).strip('()'))
        self.assertTrue('Spitz et al. 2014' in ''.join(groups_text[2]).strip('()'))

    def test_find_group_references_just_groups(self):
        div="""<div xmlns="http://www.tei-c.org/ns/1.0"><head>INTRODUCTION</head><p>Functional traits are morphological, physiological, phenological, or behavioral characteristics measurable at the individual level that can be related to the fitness of an organism <ref type="bibr" coords="1,115,54,540,93,66,17,8,05" target="#b50">(Violle et al. 2007</ref><ref type="bibr" coords="1,181,71,540,93,64,23,8,05" target="#b38">, Pey et al. 2014)</ref>. Abiotic and biotic environmental characteristics can act as filters selecting individuals based on these characteristics <ref type="bibr" coords="1,260,62,562,81,16,20,8,05;1,65,76,573,81,42,14,8,05" target="#b13">(Diamond 1975</ref><ref type="bibr" coords="1,107,90,573,81,52,78,8,05" target="#b23">, Keddy 1992</ref><ref type="bibr" coords="1,160,68,573,81,58,84,8,05" target="#b43">, Shipley 2010)</ref>.</p></div>
        """
        root = etree.fromstring(div)
        refs_with_following_text = root.xpath(
            "//tei:ref[@type='bibr'][following-sibling::node()[1][self::text()]]",
            namespaces=self.ns
        )
        groups = self.json_converter.find_group_references(root, self.ns, refs_with_following_text)
        groups_text = [[elem.text for elem in sublist] for sublist in groups]

        self.assertTrue('Violle et al. 2007, Pey et al. 2014' in ''.join(groups_text[0]).strip('()'))
        self.assertTrue('Diamond 1975, Keddy 1992, Shipley 2010' in ''.join(groups_text[1]).strip('()'))

    def test_find_group_references_groups_single(self):
        div = """<div xmlns="http://www.tei-c.org/ns/1.0"><head>INTRODUCTION</head><p>Functional traits are morphological, physiological, phenological, or behavioral characteristics measurable at the individual level that can be related to the fitness of an organism <ref type="bibr" coords="1,115,54,540,93,66,17,8,05" target="#b50">(Violle et al. 2007</ref><ref type="bibr" coords="1,181,71,540,93,64,23,8,05" target="#b38">, Pey et al. 2014)</ref>. Examples of trait matching include the length of pollinator tongue and corolla depth of flowers <ref type="bibr" coords="2,218,61,247,82,51,59,8,05" target="#b20">(Ibanez 2012)</ref>, biting force of ground beetles and cuticular toughness of prey <ref type="bibr" coords="2,77,95,269,70,87,59,8,05">(Brousseau et al. 2018b</ref>) and lipid content of predatory marine mammals and caloric content of prey <ref type="bibr" coords="2,251,89,280,70,22,21,8,05;2,58,96,291,64,43,26,8,05" target="#b45">(Spitz et al. 2014)</ref>. Abiotic and biotic environmental characteristics can act as filters selecting individuals based on these characteristics <ref type="bibr" coords="1,260,62,562,81,16,20,8,05;1,65,76,573,81,42,14,8,05" target="#b13">(Diamond 1975</ref><ref type="bibr" coords="1,107,90,573,81,52,78,8,05" target="#b23">, Keddy 1992</ref><ref type="bibr" coords="1,160,68,573,81,58,84,8,05" target="#b43">, Shipley 2010)</ref>.</p></div>
                """
        root = etree.fromstring(div)
        refs_with_following_text = root.xpath(
            "//tei:ref[@type='bibr'][following-sibling::node()[1][self::text()]]",
            namespaces=self.ns
        )
        groups = self.json_converter.find_group_references(root, self.ns, refs_with_following_text)
        groups_text = [[elem.text for elem in sublist] for sublist in groups]


        self.assertTrue('Violle et al. 2007, Pey et al. 2014' in ''.join(groups_text[0]).strip('()'))
        self.assertTrue('Ibanez 2012' in ''.join(groups_text[1]).strip('()'))
        self.assertTrue('Brousseau et al. 2018b' in ''.join(groups_text[2]).strip('()'))
        self.assertTrue('Spitz et al. 2014' in ''.join(groups_text[3]).strip('()'))
        self.assertTrue('Diamond 1975, Keddy 1992, Shipley 2010' in ''.join(groups_text[4]).strip('()'))

    def test_find_group_references_just_one_ref(self):

        div = """<div xmlns="http://www.tei-c.org/ns/1.0"><head>INTRODUCTION</head><p>Examples of trait matching include the length of pollinator tongue and corolla depth of flowers <ref type="bibr" coords="2,218,61,247,82,51,59,8,05" target="#b20">(Ibanez 2012)</ref></p></div>"""
        root = etree.fromstring(div)
        refs_with_following_text = root.xpath(
            "//tei:ref[@type='bibr'][following-sibling::node()[1][self::text()]]",
            namespaces=self.ns
        )
        groups = self.json_converter.find_group_references(root, self.ns, refs_with_following_text)
        groups_text = [[elem.text for elem in sublist] for sublist in groups]

        self.assertTrue('Ibanez 2012' in ''.join(groups_text[0]).strip('()'))
