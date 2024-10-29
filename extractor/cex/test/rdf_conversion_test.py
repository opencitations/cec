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
    input_file = os.path.join(INPUT_FOLDER, "PHY-AST_95.grobid.tei.xml")
    mapping_file = os.path.join(INPUT_FOLDER, "mapping_file.json")

    @classmethod
    def setUpClass(cls):
        # Use your RDF conversion class to convert TEI XML to RDF
        rdf_converter = TEIXMLtoRDFConverter(cls.input_file)
        rdf_converter2 = TEIXMLtoRDFConverter(cls.input_file, cls.mapping_file)
        cls.graph_set = rdf_converter.convert_to_rdf()
        cls.graph_set2 = rdf_converter2.convert_to_rdf()

    def test_verify_doi_main_br(self):
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        ids = main_br.get_identifiers()
        self.assertTrue(len(ids) == 1)
        self.assertTrue(ids[0].get_literal_value() == "10.1364/oe.27.031465")

    def test_validate_br_hierarchy(self):
        """
        Validate the hierarchy of the bibliographic entities (article -> issue -> volume -> journal).
        """
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        issue = main_br.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/JournalIssue') in issue.get_types())
        self.assertTrue(issue.get_number() == "22")

        volume = issue.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/JournalVolume') in volume.get_types())
        self.assertTrue(volume.get_number() == "27")

        journal = volume.get_is_part_of()
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/fabio/Journal') in journal.get_types())
        self.assertTrue(journal.get_identifiers()[0].get_literal_value() == "1094-4087")

    def test_check_publications_in_listBibl(self):

        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        be = main_br.get_contained_in_reference_lists()
        self.assertTrue(len(be) == 35)

    def test_check_has_citation_relation(self):
        """Check that the relation has_citation is instantiated only one time even if a br is cited more than one time
        in the same article"""
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        citations = main_br.get_citations()
        count_doi = 0
        for el in citations:
            for id_x in el.get_identifiers():
                if id_x.get_literal_value() == "10.1364/optica.2.000980":
                    count_doi += 1
        self.assertTrue(count_doi == 1)

    def test_check_citations(self):
        """Check that a citation is created for each reference pointer -> I'm referring to b10 (doi: "10.1364/optica.2.000980"), that is cited two times
        in the text, so I need to check that there are two citations with the same citing and cited entity"""
        citations = self.graph_set.get_ci()
        set_citing_entity = set()
        list_cited_entities = list()
        for cit in citations:
            citing_ent = cit.get_citing_entity()
            set_citing_entity.add(citing_ent)
            cited_ent = cit.get_cited_entity()
            if cited_ent.get_identifiers():
                doi_cited_ent = cited_ent.get_identifiers()[0].get_literal_value()
                if doi_cited_ent == "10.1364/optica.2.000980":
                    list_cited_entities.append(doi_cited_ent)
        list_cit_ent = list(set_citing_entity)
        self.assertTrue(list_cit_ent[0].get_identifiers()[0].get_literal_value() == "10.1364/oe.27.031465")
        self.assertTrue(len(list_cited_entities) == 2)

    def test_check_sections_titles(self):
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        titles = []
        for section in sections:
            titles.append(section.get_title())
        self.assertTrue(titles == ["Introduction", "Cavity design", "Laser performance in continuous wave and modelocked operation", "Conclusion and outlook"])


    def test_check_sections_titles_with_alignment(self):
        main_br = self.graph_set2.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        titles = []
        for section in sections:
            titles.append(section.get_title())
        self.assertTrue(
            titles == ["Introduction", "Cavity design", "Laser performance in continuous wave and modelocked operation",
                       "Conclusion and outlook"])

    def test_check_sections_types(self):
        main_br = self.graph_set.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        rhetorical_types = set()
        for section in sections:
            if len(section.get_types())== 3:
                type = section.get_types()[2]
                rhetorical_types.add(type)
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/deo/Introduction') in rhetorical_types and rdflib.term.URIRef('http://purl.org/spar/deo/Conclusion') not in rhetorical_types)


    def test_check_sections_types_with_alignment(self):
        main_br = self.graph_set2.get_entity(URIRef("https://w3id.org/oc/cex/br/1"))
        sections = main_br.get_contained_discourse_elements()
        rhetorical_types = set()
        for section in sections:
            if len(section.get_types())== 3:
                type = section.get_types()[2]
                rhetorical_types.add(type)
        self.assertTrue(rdflib.term.URIRef('http://purl.org/spar/deo/Introduction') and rdflib.term.URIRef('http://purl.org/spar/deo/Conclusion') in rhetorical_types)


if __name__ == "__main__":
    test = TestRDFConversion()
    test.setUpClass()
