import unittest
import subprocess
import os
import time
from itertools import count
from lib2to3.fixes.fix_imports import MAPPING
from pathlib import Path
import os

import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
from extractor.cex.combined import TEIXMLtoRDFConverter, PDFProcessor
import requests
from rdflib import Graph, URIRef
from oc_ocdm import Storer

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "rdf_conversion")
INPUT_FOLDER = os.path.join(BASE, "input_files")


class TestRDFConversion(unittest.TestCase):
    input_file = os.path.join(INPUT_FOLDER, "VET_107.grobid.tei.xml")
    json_file = os.path.join(INPUT_FOLDER, "VET_107.json")
    target_dict_vet107 = {'cit1': 'b0', 'cit2': 'b1', 'cit3': 'b2', 'cit4': 'b3', 'cit5': 'b4', 'cit6': 'b5', 'cit7': 'b6', 'cit8': 'b7', 'cit10': 'b9', 'cit11': 'b10', 'cit12': 'b11', 'cit13': 'b12', 'cit14': 'b13', 'cit15': 'b3', 'cit16': 'b14', 'cit17': 'b15', 'cit18': 'b16', 'cit19': 'b17', 'cit20': 'b18', 'cit21': 'b19', 'cit22': 'b20', 'cit23': 'b21', 'cit24': 'b22', 'cit25': 'b23', 'cit26': 'b24', 'cit27': 'b25', 'cit28': 'b3', 'cit29': 'b26', 'cit30': 'b27', 'cit31': 'b2', 'cit32': 'b2', 'cit33': 'b11', 'cit34': 'b12', 'cit35': 'b7', 'cit36': 'b13', 'cit37': 'b28', 'cit38': 'b2', 'cit39': 'b29', 'cit40': 'b12', 'cit41': 'b2', 'cit42': 'b0', 'cit43': 'b2', 'cit44': 'b30'}
    input_file2 = os.path.join(INPUT_FOLDER, "PHY-AST_95.grobid.tei.xml")
    json_file2 = os.path.join(INPUT_FOLDER, "PHY-AST_95.json")
    target_dict_phyast95 = {'cit1': 'b0', 'cit2': 'b1', 'cit3': 'b2', 'cit4': 'b3', 'cit5': 'b4', 'cit6': 'b5', 'cit7': 'b2', 'cit8': 'b6', 'cit9': 'b4', 'cit10': 'b5', 'cit11': 'b7', 'cit12': 'b8', 'cit13': 'b9', 'cit14': 'b10', 'cit15': 'b10', 'cit16': 'b11', 'cit17': 'b12', 'cit18': 'b13', 'cit19': 'b14', 'cit20': 'b15', 'cit21': 'b16', 'cit22': 'b17', 'cit23': 'b9', 'cit24': 'b18', 'cit25': 'b17', 'cit26': 'b19', 'cit27': 'b20', 'cit28': 'b21', 'cit29': 'b22', 'cit30': 'b18', 'cit31': 'b19', 'cit32': 'b20', 'cit33': 'b23', 'cit34': 'b15', 'cit35': 'b16', 'cit36': 'b17', 'cit37': 'b18', 'cit38': 'b19', 'cit39': 'b20', 'cit40': 'b21', 'cit41': 'b22', 'cit42': 'b23', 'cit43': 'b24', 'cit44': 'b25', 'cit45': 'b9', 'cit46': 'b26', 'cit47': 'b24', 'cit48': 'b27', 'cit49': 'b9', 'cit50': 'b28', 'cit51': 'b18', 'cit52': 'b23', 'cit53': 'b26', 'cit54': 'b19', 'cit55': 'b29', 'cit56': 'b26', 'cit57': 'b29', 'cit58': 'b30', 'cit59': 'b31', 'cit60': 'b26', 'cit61': 'b32', 'cit62': 'b27', 'cit63': 'b33', 'cit64': 'b31', 'cit65': 'b33', 'cit66': 'b18', 'cit67': 'b23', 'cit68': 'b26', 'cit69': 'b34', 'cit70': 'b28'}
    @classmethod
    def setUpClass(cls):
        # Use your RDF conversion class to convert TEI XML to RDF
        rdf_converter = TEIXMLtoRDFConverter(cls.input_file, cls.json_file, cls.target_dict_vet107)
        cls.graph_set = rdf_converter.convert_to_rdf()
        rdf_converter2 = TEIXMLtoRDFConverter(cls.input_file2, cls.json_file2, cls.target_dict_phyast95)
        cls.graph_set2 = rdf_converter2.convert_to_rdf()

    def test_verify_doi_main_br(self):
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        ids = main_br.get_identifiers()
        self.assertTrue(len(ids) == 1)
        self.assertTrue(ids[0].get_literal_value() == "10.1177/1098612x18810933")

    def test_validate_br_hierarchy(self):
        """
        Validate the hierarchy of the bibliographic entities (article -> issue -> volume -> journal).
        """
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        issue = main_br.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/JournalIssue') in issue.get_types())
        self.assertTrue(issue.get_number() == "10")

        volume = issue.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/JournalVolume') in volume.get_types())
        self.assertTrue(volume.get_number() == "21")

        journal = volume.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/Journal') in journal.get_types())
        self.assertTrue(["1098-612X", "1532-2750"] == [el.get_literal_value() for el in journal.get_identifiers()])

    def test_check_publications_in_listBibl(self):

        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        be = main_br.get_contained_in_reference_lists()
        self.assertTrue(len(be) == 31)

    def test_check_has_citation_relation(self):
        """Check that the relation has_citation is instantiated only one time even if a br is cited more than one time
        in the same article"""
        main_br = self.graph_set2.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        citations = main_br.get_citations()
        count_doi = 0
        for el in citations:
            for id_x in el.get_identifiers():
                if id_x.get_literal_value() == "10.1364/ol.43.006037":
                    count_doi += 1
        self.assertTrue(count_doi == 1)

    def test_check_citations(self):
        """Check that a citation is created for each reference pointer -> I'm referring to b10 (doi: "10.1364/optica.2.000980"), that is cited two times
        in the text, so I need to check that there are two citations with the same citing and cited entity"""
        citations = self.graph_set2.get_ci()
        set_citing_entity = set()
        list_cited_entities = list()
        for cit in citations:
            citing_ent = cit.get_citing_entity()
            set_citing_entity.add(citing_ent)
            cited_ent = cit.get_cited_entity()
            if cited_ent.get_title():
                title = cited_ent.get_title()
                if title == "Compact extreme ultraviolet source at megahertz pulse repetition rate with a low-noise ultrafast thin-disk laser oscillator":
                    list_cited_entities.append(cited_ent)
        list_cit_ent = list(set_citing_entity)
        self.assertTrue(list_cit_ent[0].get_identifiers()[0].get_literal_value() == "10.1364/oe.27.031465")
        self.assertTrue(len(list_cited_entities) == 2)

    def test_check_sections_titles(self):
        main_br = self.graph_set2.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        titles = []
        for section in sections:
            titles.append(section.get_title())
        self.assertTrue(titles == ["Introduction", "Cavity design", "Laser performance in continuous wave and modelocked operation", "Conclusion and outlook"])

    def test_check_sections_types(self):
        main_br = self.graph_set2.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        rhetorical_types = set()
        for section in sections:
            if len(section.get_types())== 3:
                type = section.get_types()[2]
                rhetorical_types.add(type)
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/deo/Introduction') in rhetorical_types and rdflib.term.URIRef('http://purl.org/spar/deo/Conclusion') in rhetorical_types)

    #check citations' identifiers
    def test_check_citations_id(self):
        citations = self.graph_set2.get_ci()
        ids = list()
        for cit in citations:
            cit_ids = cit.get_identifiers()
            if cit_ids:
                ids.append(cit_ids[0].get_literal_value())
                if cit_ids[0].get_literal_value() == "cit5":
                    id_cited = cit.get_cited_entity().get_identifiers()[0].get_literal_value()
                    self.assertTrue(id_cited == "10.1364/oe.23.021064")
        expected_ids = [f"cit{num}" for num in range(1, 71)]

        self.assertTrue(ids == expected_ids)


    #check what happens if the target reference is not found in the tei-xml: the citation is created without the cited entity
    def test_check_citations_no_target(self):
        citations = self.graph_set.get_ci()
        for cit in citations:
            cit_ids = cit.get_identifiers()
            if cit_ids:
                if cit_ids[0].get_literal_value() == "cit9":
                    cited_ent = cit.get_cited_entity()
                    self.assertTrue(cited_ent is None)




if __name__ == "__main__":
    test = TestRDFConversion()
    test.setUpClass()
