
import os
import shutil
import traceback

from html5lib.constants import namespaces
from oc_ocdm.graph.entities.bibliographic import DiscourseElement

from extractor.cex.grobid_client.grobid_client import GrobidClient
from lxml import etree
import json
import re
import spacy
from oc_ocdm import Storer
from oc_ocdm.graph import GraphSet
from datetime import datetime
from rdflib import URIRef
import uuid
from extractor.cex.semantic_alignment.align_headings import run
from extractor.cex.settings import *


class TEIXMLtoJSONConverter:
    def __init__(self, xml_file, output_json_file, auxiliar_file, create_rdf):
        self.xml_file = xml_file
        self.output_json_file = output_json_file
        self.auxiliar_file = auxiliar_file
        self.create_rdf = create_rdf
        self.output_target_file = output_json_file.replace(".json", "_target.json")

    def customize_tokenizer(self, nlp):
        with open(self.auxiliar_file, 'r') as file:
            special_cases = json.load(file)
        for word, tokens in special_cases.items():
            nlp.tokenizer.add_special_case(word, tokens)
        return nlp

    def protect_formulas(self, text, formula_map):
        """Sostituisce le formule matematiche con segnaposti unici"""
        formula_pattern = r'([a-zA-Z]\s*=\s*-?\d+(\.\d+)?([eE][-+]?\d+)?)'  # Cattura es. 'w = -1'

        def replace_formula(match):
            key = f"FORMULA{len(formula_map)}"
            formula_map[key] = match.group(0)
            return key  # Sostituisce la formula con un segnaposto

        return re.sub(formula_pattern, replace_formula, text)

    def restore_formulas(self, sentences, formula_map):
        """Ripristina le formule originali nei testi segmentati"""
        return [self.replace_back(sentence, formula_map) for sentence in sentences]

    def replace_back(self, sentence, formula_map):
        """Sostituisce i segnaposti con le formule originali"""
        for key, formula in formula_map.items():
            sentence = sentence.replace(key, formula)
        return sentence

    def test_model_segmentation(self, text, formula_map):
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Model not found. Installing en_core_web_trf model")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        nlp = self.customize_tokenizer(nlp)
        protected_text = self.protect_formulas(text, formula_map)  # Protegge le formule
        doc = nlp(protected_text)
        sentences = [sent.text.strip() for sent in doc.sents]
        return self.restore_formulas(sentences, formula_map)  # Ripristina le formule

    def build_dict_ref_citkey(self, xml, ns):
        refs = xml.xpath(".//tei:div/tei:p/tei:ref[@type='bibr']", namespaces=ns)
        refs_in_notes = xml.xpath(".//tei:note//tei:ref[@type='bibr']", namespaces=ns)
        refs_in_figures = xml.xpath(".//tei:figure/tei:figDesc/tei:ref[@type='bibr']", namespaces = ns)
        if refs_in_notes:
            refs = refs + refs_in_notes
        if refs_in_figures:
            refs = refs + refs_in_figures
        return {ref: f"cit{i + 1}" for i, ref in enumerate(refs)}

    def find_sentences_in_div(self, div, dict_to_check, ns, formula_map):
        # Extract all text from the <div> tag, including references
        text_to_segment = div.xpath(""".//tei:p/text() | .//tei:p/tei:ref""", namespaces=ns)
        processed_text = []
        for elem in text_to_segment:
            if isinstance(elem, etree._Element):  # <ref> tags
                if elem.tag == f"{{{ns['tei']}}}ref" and elem.get("type") == "bibr" and elem in dict_to_check:
                    processed_text.append(dict_to_check[elem])
                else:
                    if elem.text:
                        processed_text.append(elem.text)
            elif elem:  # Regular text
                processed_text.append(elem)

        if processed_text:
            # Combine and clean text
            cleaned_text = ' '.join(processed_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = re.sub(r'\s+([,;.])', r'\1', cleaned_text)  # Remove spaces before punctuation
            # Remove unnecessary whitespaces inside parentheses
            cleaned_text = re.sub(r'\(\s*(.*?)\s*\)', r'(\1)', cleaned_text)
            return self.test_model_segmentation(cleaned_text, formula_map)
        return []

    def find_sentences_in_div_superscripts(self, div, dict_to_check, ns, formula_map):
        sentences_to_modify = self.find_sentences_in_div(div, dict_to_check, ns, formula_map)
        for i, sentence in enumerate(sentences_to_modify):
            if i > 0:
                # Check if the citation is at the start of the sentence and preceding sentence ends with a period
                preceding_sentence = sentences_to_modify[i-1]
                # this will match also following citations at the beginning of the sentence
                cit_el = re.search(r"^(cit\d+\s*)+", sentence)
                if cit_el and sentences_to_modify[i-1].endswith('.'):
                    cit_el_text = cit_el.group()
                    new_preceding_sentence = "%s %s" % (preceding_sentence, cit_el_text)
                    new_sentence = sentence.replace(cit_el_text, '')
                    sentences_to_modify[i] = new_sentence
                    sentences_to_modify[i-1] = new_preceding_sentence.strip()
        return sentences_to_modify

    # Function to replace matches
    def replace_citations(self, sentence, ref_citkey_dict):
        inverted_dict = {v: k for k, v in ref_citkey_dict.items()}  # Citkey to <ref> lookup
        citations = re.findall(r"cit\d+", sentence)
        for cit in citations:
            ref = inverted_dict.get(cit)
            if ref is not None:
                ref_text = ref.text.strip() if ref.text else ""
                sentence = sentence.replace(cit, ref_text)
        return sentence

    def get_text_before_ref(self, ref, ns, formula_map):
        preceding_text = ref.xpath('preceding-sibling::text()', namespaces=ns)
        text_before_ref = " ".join(preceding_text).strip() if preceding_text else ""
        text_before_ref = re.sub(r'^[^\w\s]+', '', text_before_ref)
        sentences = self.test_model_segmentation(text_before_ref, formula_map)
        text_before_ref = sentences[-1].strip() if sentences else ""
        return text_before_ref

    def are_intext_reference_pointers_apexes(self, xml, ns, formula_map):
        refs = xml.xpath(".//tei:div/tei:p/tei:ref[@type='bibr']", namespaces=ns)
        numbers = 0
        with open(self.auxiliar_file, 'r') as file:
            special_cases = json.load(file)
        total_refs = len([ref for ref in refs if ref.text])
        for ref in refs:
            ref_text = ref.text.strip() if ref.text else ""

            # Remove all characters except letters (a-z, A-Z) and digits (0-9)
            cleaned_text = re.sub(r"[^a-zA-Z0-9]", "", ref_text)

            # Check if the cleaned text contains only digits
            if cleaned_text.isdigit():
                numbers += 1

        if numbers > total_refs/2:
            # check if intext reference pointers are superscript
            # get the text preceding the intext reference pointers
            # Loop through each reference and extract preceding text
            preceding_texts = []
            for ref in refs:
                preceding_text = self.get_text_before_ref(ref, ns, formula_map)
                if preceding_text.endswith('.'):
                    list_words = preceding_text.strip().split(' ')
                    ending_word = list_words[-1]
                    if ending_word not in special_cases:
                        preceding_texts.append(preceding_text)

            if len(preceding_texts) > total_refs/5:
                return True
        return False

    def clean_section_title(self, title):
        if title is not None:
            title = title.strip()
            # Check if the title starts with a non-alphanumeric character
            while title and not re.match(r"^[a-zA-Z0-9]", title[0]):
                title = title[1:]  # Remove the first character
            return title.strip()  # Otherwise, return the cleaned title
        else:
            return title
    
    def find_sentences_in_figure(self, figure, dict_to_check, ns, formula_map):
        # Extract all text from the <div> tag, including references
        text_to_segment = figure.xpath(""".//tei:figDesc/text() | .//tei:figDesc/tei:ref""", namespaces=ns)
        processed_text = []
        for elem in text_to_segment:
            if isinstance(elem, etree._Element):  # <ref> tags
                if elem.tag == f"{{{ns['tei']}}}ref" and elem.get("type") == "bibr" and elem in dict_to_check:
                    processed_text.append(dict_to_check[elem])
                else:
                    if elem.text:
                        processed_text.append(elem.text)
            elif elem:  # Regular text
                processed_text.append(elem)

        if processed_text:
            # Combine and clean text
            cleaned_text = ' '.join(processed_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = re.sub(r'\s+([,;.])', r'\1', cleaned_text)  # Remove spaces before punctuation
            # Remove unnecessary whitespaces inside parentheses
            cleaned_text = re.sub(r'\(\s*(.*?)\s*\)', r'(\1)', cleaned_text)
            
            return self.test_model_segmentation(cleaned_text, formula_map)
            
        return []

    def convert_to_json(self):
        #try to differentiate numerical in text pointers from strings
        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        formula_map = {}
        last_head = None

        # Precompute common elements
        ref_citkey_dict = self.build_dict_ref_citkey(tree, ns)
        head_elements = root.findall(".//tei:div/tei:head", namespaces=ns)
        has_n_attribute = any("n" in head.attrib for head in head_elements)
        roman_pattern = r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+'
        has_roman_numeration = any(re.search(roman_pattern, (head.text or "").strip()) for head in head_elements)
        head_n_attribute = sum("n" in head.attrib for head in head_elements)
        head_no_n_attribute = sum("n" not in head.attrib for head in head_elements)
        head_roman = sum(
            1 for head in head_elements if re.search(roman_pattern, (head.text or "").strip())
        )
        head_no_roman = sum(
            1 for head in head_elements if not re.search(roman_pattern, (head.text or "").strip())
        )

        # Find notes with in-text reference pointers
        notes_text_with_refs = set()
        refs_in_notes = root.findall(".//tei:note//tei:ref[@type='bibr']", namespaces=ns)
        if refs_in_notes:
            for ref in refs_in_notes:
                note = ref.xpath("./ancestor::tei:note[1]", namespaces=ns)[0]  # Move up to the <note> parent
                xml_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
                notes_text_with_refs.add(xml_id)

        superscipts = self.are_intext_reference_pointers_apexes(tree, ns, formula_map)

        if self.create_rdf:
            target = dict()

        # Initialize storage for citations
        citations = {}
        for div in root.findall(".//tei:div", namespaces=ns):

            formula_map = {}

            head = div.find("./tei:head", namespaces=ns)
            if head is not None:
                head_text = head.text.strip() if head.text else ""
                if has_n_attribute:
                    if head_n_attribute >= (head_no_n_attribute+head_n_attribute)/2:
                        if 'n' in head.attrib:
                            n = head.get("n")
                            n_parts = n.split(".")
                            if '' in n_parts:
                                n_parts.remove('')
                            if len(n_parts) == 1:
                                if re.search(r'\b\d+(\.\d+)+\b', head_text):
                                    split_string = re.split(r'\b\d+(\.\d+)+\b', head_text)
                                    split_string = [substring.strip() for substring in split_string]
                                    last_head = split_string[0].strip()
                                else:
                                    last_head = head_text
                    else:
                        last_head=head_text
                elif has_roman_numeration:
                    if head_roman >= (head_no_roman+head_roman)/2:
                        if re.search(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+', head_text):
                            pattern = re.compile(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+')
                            match = pattern.search(head_text)
                            if match:
                                match = match.group().strip()
                                last_head = head_text.replace(match, "")
                    else:
                        last_head=head_text
                else:
                    last_head = head_text

            if superscipts:
                sentences = self.find_sentences_in_div_superscripts(div, ref_citkey_dict, ns, formula_map)
            else:
                sentences = self.find_sentences_in_div(div, ref_citkey_dict, ns, formula_map)

            # Checks if any foot-type references in the div match the set of known notes containing citations.
            # If they match, extracts additional sentences from those notes.
            if notes_text_with_refs:
                notes_text_in_div = [note.text for note in div.findall(".//tei:ref[@type='foot']", namespaces=ns)]
                if notes_text_in_div:
                    for el in list(notes_text_with_refs):
                        if el in notes_text_in_div:
                            note_with_refs = root.find(f""".//tei:note[@xml:id="{el}"]""", namespaces={
                                                        "tei": "http://www.tei-c.org/ns/1.0",
                                                        "xml": "http://www.w3.org/XML/1998/namespace"
                                                        })
                            sentences += self.find_sentences_in_div(note_with_refs, ref_citkey_dict, ns, formula_map)
            
            # Replaces citation placeholders (cit1, cit2, etc.) with resolved reference data.
            if sentences:
                processed_sentences = {
                    sentence: self.replace_citations(sentence, ref_citkey_dict)
                    for sentence in sentences if "cit" in sentence
                }

                for i, (sentence, processed_sentence) in enumerate(processed_sentences.items()):
                    for cit in re.findall(r"cit\d+", sentence):
                        ref = next((k for k, v in ref_citkey_dict.items() if v == cit), None)
                        if ref is not None:
                            ref_text = ref.text.strip() if ref.text else ""
                            citation_text = re.sub(r'/s+', ' ', processed_sentence)
                            citation_text = re.sub(r'/s+([,;.])', r'\1', citation_text)
                            citations[cit] = {
                                "SECTION": self.clean_section_title(last_head),
                                "CITATION": citation_text,
                                "REFERENCE": ref_text
                            }
                            if self.create_rdf:
                                target_attr = ref.get("target")  # Extract the target attribute
                                if target_attr:
                                    target[cit] = target_attr.replace('#','')
            
        #references in figures
        sentences_from_figures = set()
        
        figs_with_refs = list()
        seen_coords = set()
        refs_in_figs = root.findall(".//tei:figure//tei:ref[@type='bibr']", namespaces=ns)
        if refs_in_figs:
            for ref in refs_in_figs:
                fig = ref.xpath("./ancestor::tei:figure[1]", namespaces=ns)[0]  # Move up to the <figure> parent
                
                # Get the coords attribute (or default to None)
                coords = fig.get("coords")

                # Skip if we've already seen this coords value
                if coords in seen_coords:
                    continue

                # Otherwise, record it
                seen_coords.add(coords)
                figs_with_refs.append(fig)
        
        for fig in figs_with_refs:
            sentences_from_figures.update(set(self.find_sentences_in_figure(fig, ref_citkey_dict, ns, formula_map)))

        sentences_from_figures_list = list(sentences_from_figures)
     
        if sentences_from_figures_list:
            processed_sentences = {
                sentence: self.replace_citations(sentence, ref_citkey_dict)
                for sentence in sentences_from_figures_list if "cit" in sentence
            }

            for i, (sentence, processed_sentence) in enumerate(processed_sentences.items()):
                for cit in re.findall(r"cit\d+", sentence):
                    ref = next((k for k, v in ref_citkey_dict.items() if v == cit), None)
                    if ref is not None:
                        ref_text = ref.text.strip() if ref.text else ""
                        citation_text = re.sub(r'\s+', ' ', processed_sentence)
                        citation_text = re.sub(r'\s+([,;.])', r'\1', citation_text)
                        citations[cit] = {
                            "SECTION": "Figure Caption",
                            "CITATION": citation_text,
                            "REFERENCE": ref_text
                        }
                        if self.create_rdf:
                            target_attr = ref.get("target")  # Extract the target attribute
                            if target_attr:
                                target[cit] = target_attr.replace('#', '')


        # Save results to JSON
        with open(self.output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(citations, json_file, indent=2, ensure_ascii=False)

        if self.create_rdf:
            return target

class TEIXMLtoRDFConverter:

    def __init__(self, xml_file, json_file, target_dict):
        self.xml_file = xml_file
        self.json_file = json_file
        self.target_dict = target_dict

    def create_unique_uri(self, base_uri, prefix):
        unique_uri = f"{base_uri}{prefix}/{uuid.uuid4()}"
        return URIRef(unique_uri)

    def create_main_br(self, xml_string, cex_graphset, base_uri):

        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        doi_elements = xml_string.xpath('.//tei:idno[@type="DOI"]', namespaces=ns)
        arxiv_elements = xml_string.xpath('.//tei:idno[@type="arXiv"]', namespaces=ns)
        title_elements = xml_string.xpath('.//tei:titleStmt//tei:title[@level="a"]', namespaces=ns)
        authors = xml_string.xpath('.//tei:author', namespaces=ns)
        pub_date = xml_string.xpath('.//tei:publicationStmt/tei:date[@type="published"]/@when', namespaces=ns)
        publisher = xml_string.xpath('.//tei:publicationStmt/tei:publisher', namespaces=ns)
        issn = xml_string.xpath('.//tei:monogr/tei:idno[@type="ISSN"]', namespaces=ns)
        eissn = xml_string.xpath('.//tei:monogr/tei:idno[@type="eISSN"]', namespaces=ns)
        issn.extend(eissn)
        journal_title = xml_string.xpath('.//tei:monogr/tei:title[@level="j"]', namespaces=ns)
        series_title = xml_string.xpath('.//tei:monogr/tei:title[@level="s"]', namespaces=ns)
        # <title level="m"> for non journal bibliographical item holding the cited article, e.g. conference proceedings title.
        other_title = xml_string.xpath('.//tei:monogr/tei:title[@level="m"]', namespaces=ns)
        issue_n = xml_string.xpath('.//tei:biblScope[@unit="issue"]', namespaces=ns)
        volume_n = xml_string.xpath('.//tei:biblScope[@unit="volume"]', namespaces=ns)
        pages = xml_string.xpath('.//tei:biblScope[@unit="page"]', namespaces=ns)

        br_uri = self.create_unique_uri(base_uri, "br")
        br = cex_graphset.add_br(br_uri)

        if doi_elements:
            id_uri = self.create_unique_uri(base_uri, "id")
            br_id = cex_graphset.add_id(id_uri)
            doi = doi_elements[0].text
            br_id.create_doi(doi)
            br.has_identifier(br_id)

        if arxiv_elements:
            id_uri2 = self.create_unique_uri(base_uri, "id")
            br_id2 = cex_graphset.add_id(id_uri2)
            arxiv = arxiv_elements[0].text
            br_id2.create_arxiv(arxiv)
            br.has_identifier(br_id2)

        if title_elements:
            br.has_title(title_elements[0].text)
        if pub_date:
            # Convert the string to a datetime object
            date_obj = datetime.strptime(pub_date[0], "%Y-%m-%d")

            # Convert to ISO 8601 format
            iso_format = date_obj.isoformat()
            br.has_pub_date(iso_format)

        if authors:
            for author in authors:
                ra_author_uri = self.create_unique_uri(base_uri, "ra")
                forename_elements = author.xpath('.//tei:forename', namespaces=ns)
                surname_elements = author.xpath('.//tei:surname', namespaces=ns)
                orcid_elements = author.xpath('.//tei:idno[@type="ORCID"]', namespaces=ns)

                ra_author = cex_graphset.add_ra(ra_author_uri)
                if orcid_elements:
                    orcid = orcid_elements[0].text
                    orcid_uri = self.create_unique_uri(base_uri, "id")
                    ra_id = cex_graphset.add_id(orcid_uri)
                    ra_id.create_orcid(orcid)
                    ra_author.has_identifier(ra_id)

                if forename_elements:
                    ra_author.has_given_name(forename_elements[0].text)
                if surname_elements:
                    ra_author.has_family_name(surname_elements[0].text)
                if forename_elements and surname_elements:
                    ra_author.has_name("%s %s" % (forename_elements[0].text, surname_elements[0].text))
                ar_author_uri = self.create_unique_uri(base_uri, prefix="ar")
                ar_author = cex_graphset.add_ar(ar_author_uri)
                ar_author.create_author()
                ar_author.is_held_by(ra_author)
                br.has_contributor(ar_author)

        if publisher:
            ra_publisher_uri = self.create_unique_uri(base_uri, "ra")
            publisher_name = publisher[0].text
            ra_publisher = cex_graphset.add_ra(ra_publisher_uri)
            if publisher_name is not None:
                ra_publisher.has_name(publisher_name)
            ar_publisher_uri = self.create_unique_uri(base_uri, prefix="ar")
            ar_publisher = cex_graphset.add_ar(ar_publisher_uri)
            ar_publisher.create_publisher()
            ar_publisher.is_held_by(ra_publisher)
            br.has_contributor(ar_publisher)

        if journal_title:
            br.create_journal_article()
            if issue_n:
                br_issue_uri = self.create_unique_uri(base_uri, prefix="br")
                issue = cex_graphset.add_br(br_issue_uri)
                issue.create_issue()
                issue.has_number(issue_n[0].text)

            if volume_n:
                br_volume_uri = self.create_unique_uri(base_uri, prefix="br")
                volume = cex_graphset.add_br(br_volume_uri)
                volume.create_volume()
                volume.has_number(volume_n[0].text)

            br_journal_uri = self.create_unique_uri(base_uri, "br")
            journal = cex_graphset.add_br(br_journal_uri)
            journal.create_journal()
            journal.has_title(journal_title[0].text)
            if issn:
                for el in issn:
                    id_uri = self.create_unique_uri(base_uri, "id")
                    journal_id = cex_graphset.add_id(id_uri)
                    journal_id.create_issn(el.text)
                    journal.has_identifier(journal_id)

            if issue_n and volume_n:
                br.is_part_of(issue)
                issue.is_part_of(volume)
                volume.is_part_of(journal)
            elif issue_n:
                br.is_part_of(issue)
                issue.is_part_of(journal)
            elif volume_n:
                br.is_part_of(volume)
                volume.is_part_of(journal)
            else:
                br.is_part_of(journal)

        if series_title:
            br_series_uri = self.create_unique_uri(base_uri, "br")
            series = cex_graphset.add_br(br_series_uri)
            series.create_series()
            series.has_title(series_title[0].text)
            br.is_part_of(series)

        if other_title:
            br_monograph_uri = self.create_unique_uri(base_uri, "br")
            monograph = cex_graphset.add_br(br_monograph_uri)
            monograph.create_monograph()
            monograph.has_title(other_title[0].text)
            br.is_part_of(monograph)

        if pages:
            start_page = pages[0].get("from")
            ending_page = pages[0].get("to")
            re_uri = self.create_unique_uri(base_uri, prefix="re")
            res_emb = cex_graphset.add_re(re_uri)
            if start_page and ending_page:
                res_emb.has_starting_page(start_page)
                res_emb.has_ending_page(ending_page)
            elif start_page:
                res_emb.has_starting_page(start_page)
                res_emb.has_ending_page(start_page)
            elif not start_page and not ending_page:
                res_emb.has_starting_page(pages[0].text)
                res_emb.has_ending_page(pages[0].text)
            br.has_format(res_emb)

        return br

    def create_cited_entity(self, xml_string, cex_graphset, base_uri):

        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        doi_elements = xml_string.xpath('.//tei:idno[@type="DOI"]', namespaces=ns)
        arxiv_elements = xml_string.xpath('.//tei:idno[@type="arXiv"]', namespaces=ns)
        title_elements = xml_string.xpath('.//tei:title[@level="a"]', namespaces=ns)
        authors = xml_string.xpath('.//tei:author', namespaces=ns)
        pub_date = xml_string.xpath('.//tei:monogr/tei:date[@type="published"]/@when', namespaces=ns)
        publisher = xml_string.xpath('.//tei:monogr/tei:publisher', namespaces=ns)
        issn = xml_string.xpath('.//tei:monogr/tei:idno[@type="ISSN"]', namespaces=ns)
        eissn = xml_string.xpath('.//tei:monogr/tei:idno[@type="eISSN"]', namespaces=ns)
        issn.extend(eissn)
        journal_title = xml_string.xpath('.//tei:monogr/tei:title[@level="j"]', namespaces=ns)
        series_title = xml_string.xpath('.//tei:monogr/tei:title[@level="s"]', namespaces=ns)
        # <title level="m"> for non journal bibliographical item holding the cited article, e.g. conference proceedings title.
        other_title = xml_string.xpath('.//tei:monogr/tei:title[@level="m"]', namespaces=ns)
        issue_n = xml_string.xpath('.//tei:biblScope[@unit="issue"]', namespaces=ns)
        volume_n = xml_string.xpath('.//tei:biblScope[@unit="volume"]', namespaces=ns)
        pages = xml_string.xpath('.//tei:biblScope[@unit="page"]', namespaces=ns)


        br_uri = self.create_unique_uri(base_uri, "br")
        br = cex_graphset.add_br(br_uri)

        if doi_elements:
            id_uri = self.create_unique_uri(base_uri, "id")
            br_id = cex_graphset.add_id(id_uri)
            doi = doi_elements[0].text
            br_id.create_doi(doi)
            br.has_identifier(br_id)

        if arxiv_elements:
            id_uri2 = self.create_unique_uri(base_uri, "id")
            br_id2 = cex_graphset.add_id(id_uri2)
            arxiv = arxiv_elements[0].text
            br_id2.create_arxiv(arxiv)
            br.has_identifier(br_id2)

        if title_elements:
            br.has_title(title_elements[0].text)
        if pub_date:
            # Convert the string to a datetime object
            date_obj = datetime.strptime(pub_date[0], "%Y-%m-%d")

            # Convert to ISO 8601 format
            iso_format = date_obj.isoformat()
            br.has_pub_date(iso_format)

        if authors:
            for author in authors:
                ra_author_uri = self.create_unique_uri(base_uri, "ra")
                forename_elements = author.xpath('.//tei:forename', namespaces=ns)
                surname_elements = author.xpath('.//tei:surname', namespaces=ns)
                orcid_elements = author.xpath('.//tei:idno[@type="ORCID"]', namespaces=ns)

                ra_author = cex_graphset.add_ra(ra_author_uri)
                if orcid_elements:
                    orcid = orcid_elements[0].text
                    orcid_uri = self.create_unique_uri(base_uri, "id")
                    ra_id = cex_graphset.add_id(orcid_uri)
                    ra_id.create_orcid(orcid)
                    ra_author.has_identifier(ra_id)
                if forename_elements:
                    ra_author.has_given_name(forename_elements[0].text)
                if surname_elements:
                    ra_author.has_family_name(surname_elements[0].text)
                if forename_elements and surname_elements:
                    ra_author.has_name("%s %s" % (forename_elements[0].text, surname_elements[0].text))
                ar_author_uri = self.create_unique_uri(base_uri, prefix="ar")
                ar_author = cex_graphset.add_ar(ar_author_uri)
                ar_author.create_author()
                ar_author.is_held_by(ra_author)
                br.has_contributor(ar_author)

        if publisher:
            ra_publisher_uri = self.create_unique_uri(base_uri, "ra")
            publisher_name = publisher[0].text
            ra_publisher = cex_graphset.add_ra(ra_publisher_uri)
            ra_publisher.has_name(publisher_name)
            ar_publisher_uri = self.create_unique_uri(base_uri, prefix="ar")
            ar_publisher = cex_graphset.add_ar(ar_publisher_uri)
            ar_publisher.create_publisher()
            ar_publisher.is_held_by(ra_publisher)
            br.has_contributor(ar_publisher)

        if journal_title:
            br.create_journal_article()
            if issue_n:
                br_issue_uri = self.create_unique_uri(base_uri, prefix="br")
                issue = cex_graphset.add_br(br_issue_uri)
                issue.create_issue()
                issue.has_number(issue_n[0].text)

            if volume_n:
                br_volume_uri = self.create_unique_uri(base_uri, prefix="br")
                volume = cex_graphset.add_br(br_volume_uri)
                volume.create_volume()
                volume.has_number(volume_n[0].text)

            br_journal_uri = self.create_unique_uri(base_uri, "br")
            journal = cex_graphset.add_br(br_journal_uri)
            journal.create_journal()
            journal.has_title(journal_title[0].text)
            if issn:
                for el in issn:
                    id_uri = self.create_unique_uri(base_uri, "id")
                    journal_id = cex_graphset.add_id(id_uri)
                    journal_id.create_issn(el.text)
                    journal.has_identifier(journal_id)

            if issue_n and volume_n:
                br.is_part_of(issue)
                issue.is_part_of(volume)
                volume.is_part_of(journal)
            elif issue_n:
                br.is_part_of(issue)
                issue.is_part_of(journal)
            elif volume_n:
                br.is_part_of(volume)
                volume.is_part_of(journal)
            else:
                br.is_part_of(journal)

        if series_title:
            br_series_uri = self.create_unique_uri(base_uri, "br")
            series = cex_graphset.add_br(br_series_uri)
            series.create_series()
            series.has_title(series_title[0].text)
            br.is_part_of(series)

        if other_title:
            br_monograph_uri = self.create_unique_uri(base_uri, "br")
            monograph = cex_graphset.add_br(br_monograph_uri)
            monograph.create_monograph()
            monograph.has_title(other_title[0].text)
            br.is_part_of(monograph)

        if pages:
            start_page = pages[0].get("from")
            ending_page = pages[0].get("to")
            re_uri = self.create_unique_uri(base_uri, prefix="re")
            res_emb = cex_graphset.add_re(re_uri)
            if start_page and ending_page:
                res_emb.has_starting_page(start_page)
                res_emb.has_ending_page(ending_page)
            elif start_page:
                res_emb.has_starting_page(start_page)
                res_emb.has_ending_page(start_page)
            elif not start_page and not ending_page:
                res_emb.has_starting_page(pages[0].text)
                res_emb.has_ending_page(pages[0].text)
            br.has_format(res_emb)

        return br

    def assign_rhetoric_type(self, de: DiscourseElement, title) -> None:
        if title == "Introduction":
            de.create_introduction()
        elif title == "Related Work":
            de.create_related_work()
        elif title == "Methods":
            de.create_methods()
        elif title == "Materials":
            de.create_materials()
        elif title == "Results":
            de.create_results()
        elif title == "Discussion":
            de.create_discussion()
        elif title == "Conclusion":
            de.create_conclusion()

    def search_be(self, cex_graphset: GraphSet, my_xmlid):
        all_be = cex_graphset.get_be()
        for el in all_be:
            id = el.get_identifiers()
            if id:
                xmlid = id[0].get_literal_value()
                if xmlid == my_xmlid:
                    return el

    def search_cited_br_through_be(self, cex_graphset, my_xmlid):
        all_be = cex_graphset.get_be()
        for el in all_be:
            id = el.get_identifiers()
            if id:
                xmlid = id[0].get_literal_value()
                if xmlid == my_xmlid:
                    cited_br = el.get_referenced_br()
                    return cited_br

    def convert_to_rdf(self):

        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        base_uri = "https://w3id.org/oc/cex/"

        cex_graphset = GraphSet(base_uri)

        # Extract br metadata from the xml-tei using XPath
        main_br = root.xpath('//tei:fileDesc', namespaces=ns)
        # cited entities contained in the bibliography
        cited_entities = root.xpath('//tei:biblStruct[ancestor::tei:listBibl]', namespaces=ns)
        main_br_obj = self.create_main_br(main_br[0], cex_graphset, base_uri)
        for cited in cited_entities:
            # create a bibliographic reference for each element in the bibliography and link it to the main br
            be_uri = self.create_unique_uri(base_uri, "be")
            be = cex_graphset.add_be(be_uri)
            be_xmlid_text = cited.get('{http://www.w3.org/XML/1998/namespace}id')
            if be_xmlid_text:
                be_xmlid_uri = self.create_unique_uri(base_uri, "id")
                be_xmlid = cex_graphset.add_id(be_xmlid_uri)
                be_xmlid.create_xmlid(be_xmlid_text)
                be.has_identifier(be_xmlid)

            cited_br_obj = self.create_cited_entity(cited, cex_graphset, base_uri)
            be.references_br(cited_br_obj)
            main_br_obj.contains_in_reference_list(be)

        #load the json to create citations
        with open(self.json_file, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

            sections_created = dict()

            #each el contains 3/4 keys: section, citation, reference, aligned section
            for citation_key in json_data:

                el = json_data[citation_key]

                # section title
                if el.get('SECTION'):
                    head_title = el['SECTION']

                    #create section if not already created
                    if head_title not in sections_created:

                        de_uri = self.create_unique_uri(base_uri, "de")
                        de = cex_graphset.add_de(de_uri)
                        de.create_section()
                        de.has_title(head_title)

                        #rhetoric types
                        if el.get('ALIGNED SECTION'):
                            head = el['ALIGNED SECTION']
                            if type(head) is list:
                                for ret_el in head:
                                    self.assign_rhetoric_type(de, ret_el)
                            else:
                                self.assign_rhetoric_type(de, head)
                        else:
                            if el.get('SECTION'):
                                head = el['SECTION']
                                if head.lower() in ["introduction", "related work", "methods", "materials", "results",
                                                        "discussion", "conclusion"]:
                                    self.assign_rhetoric_type(de, head)

                        sections_created[head_title] = de
                        main_br_obj.contains_discourse_element(de)

                if el.get('REFERENCE'):
                    reference_pointer_uri = self.create_unique_uri(base_uri, "rp")
                    reference_pointer = cex_graphset.add_rp(reference_pointer_uri)
                    reference_pointer.has_content(el['REFERENCE'][0])
                    if el.get('SECTION'):
                        current_de = sections_created[el['SECTION']]
                        current_de.is_context_of_rp(reference_pointer)
                    ref_target = self.target_dict.get(citation_key)
                    if ref_target:
                        be_obtained = self.search_be(cex_graphset, ref_target)
                        if be_obtained:
                            reference_pointer.denotes_be(be_obtained)

                ci_uri = self.create_unique_uri(base_uri, prefix="ci")
                citation = cex_graphset.add_ci(ci_uri)
                citation_key_uri = self.create_unique_uri(base_uri, "id")
                citation_key_id = cex_graphset.add_id(citation_key_uri)
                citation_key_id.create_xpath(citation_key)
                citation.has_identifier(citation_key_id)
                citation.has_citing_entity(main_br_obj)
                if ref_target:
                    cited_entity = self.search_cited_br_through_be(cex_graphset, ref_target)
                    if cited_entity:
                        citation.has_cited_entity(cited_entity)
                        #link the cited entity to the main br
                        if cited_entity not in main_br_obj.get_citations():
                            #has_citation: Setter method corresponding to the ``cito:cites`` RDF predicate.
                            main_br_obj.has_citation(cited_entity)
                cit_pub_date = main_br_obj.get_pub_date()
                if cit_pub_date:
                    citation.has_citation_creation_date(cit_pub_date)

        return cex_graphset


class PDFProcessor:
    def __init__(self, input_pdf_path="/Users/olga/Downloads/AGR-BIO-SCI_2.pdf", output_tei_path="output",
                 output_json_path="output", config_path=CONFIG_PATH, auxiliar_file=SPECIAL_CASES_PATH):
        self.client = GrobidClient(config_path=CONFIG_PATH)
        self.input_pdf_path = input_pdf_path
        self.output_tei_path = output_tei_path
        self.output_json_path = output_json_path
        self.auxiliar_file = auxiliar_file
        current_datetime = datetime.now()
        timestamp = current_datetime.timestamp()
        pdf_filename = os.path.basename(self.input_pdf_path)
        output_intermediate_dir = os.path.join(output_tei_path, f"{pdf_filename.replace('.pdf', '')}_{timestamp}")
        os.makedirs(output_intermediate_dir, exist_ok=True)
        os.chmod(output_intermediate_dir, 0o777)
        self.output_intermediate_dir = output_intermediate_dir

    def validate_file_list(self, file_list):
        # Required file types and their initial counts
        required_counts = {'.xml': 0, '.json': 0, '.jsonld': 0}

        # Check each file in the list
        for file in file_list:
            ext = file.lower().rsplit('.', 1)[-1]  # Extract file extension and make it lowercase
            ext = '.' + ext
            if ext in required_counts:
                required_counts[ext] += 1
            else:
                return False  # A file with an unexpected extension is found

        # Ensure each required file type is present exactly once
        return all(count == 1 for count in required_counts.values()) and len(file_list) == 3

    def process_pdf(self, align_headings=False, create_rdf=False):
        input_pdf_path = [self.input_pdf_path]
        output = self.output_tei_path
        pdf_filename = os.path.basename(input_pdf_path[0])
        manifest_info = {"filename": pdf_filename}
        current_stage = "Initializing PDF processor"
        generated_xml = False

        try:
            # grobid extraction
            current_stage = "Generating TEI/XML file"
            input_pdf_path, output_tei_path = self.create_xml_tei()
            generated_xml = True

        except Exception as e:
            current_datetime = datetime.now()
            timestamp = current_datetime.timestamp()
            error_log_path = os.path.join(self.output_intermediate_dir, f"error_log_{timestamp}.json")
            with open(error_log_path, 'w') as error_file:
                json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                           "traceback": traceback.format_exc()}, error_file, indent=4)

        if generated_xml:
            try:
                # citations' context + section heading
                current_stage = "Generating JSON file"
                target_dict = self.create_json(input_pdf_path, output_tei_path, create_rdf)
                # aligning headings
                if align_headings:
                    current_stage = "Aligning headings"
                    json_files = [el for el in os.listdir(self.output_intermediate_dir) if
                                  el.endswith(".json") and el.startswith(str(pdf_filename).replace(".pdf", ""))]
                    if json_files:
                        json_file_path = os.path.join(self.output_intermediate_dir, json_files[0])
                        try:
                            run(json_file_path,
                                ["Introduction", "Related Work", "Methods", "Materials", "Results", "Discussion", "Conclusion"],
                                json_file_path, str(PREDEFINED_MAPPINGS_PATH))
                        except Exception as e:
                            current_datetime = datetime.now()
                            timestamp = current_datetime.timestamp()
                            error_log_path = os.path.join(self.output_intermediate_dir, f"error_log_{timestamp}.json")
                            with open(error_log_path, 'w') as error_file:
                                json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                                           "traceback": traceback.format_exc()}, error_file, indent=4)
            except Exception as e:
                current_datetime = datetime.now()
                timestamp = current_datetime.timestamp()
                error_log_path = os.path.join(self.output_intermediate_dir, f"error_log_{timestamp}.json")
                with open(error_log_path, 'w') as error_file:
                    json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                               "traceback": traceback.format_exc()}, error_file, indent=4)
            if create_rdf:
                try:
                    # rdf creation
                    current_stage = "Generating RDF file"
                    self.create_rdf(input_pdf_path, output_tei_path, target_dict)

                except Exception as e:
                    current_datetime = datetime.now()
                    timestamp = current_datetime.timestamp()
                    error_log_path = os.path.join(self.output_intermediate_dir, f"error_log_{timestamp}.json")
                    with open(error_log_path, 'w') as error_file:
                        json.dump({"error": str(e), "timestamp": timestamp, "current_stage": current_stage,
                                   "traceback": traceback.format_exc()}, error_file, indent=4)

        single_pdf = os.path.join(output, "single_pdf")
        shutil.copytree(self.output_intermediate_dir, single_pdf)
        processing_outputs = os.listdir(single_pdf)
        files = dict()
        status = "error"
        if self.validate_file_list(processing_outputs):
            status = "success"
        just_error_logs = all(el.startswith('error_log') for el in processing_outputs)

        if just_error_logs:
            files['errors'] = [el for el in processing_outputs if el.startswith('error_log')]
        else:
            for el in processing_outputs:
                if el.endswith('.tei.xml'):
                    files["tei"] = {'status': 'processed', 'file': el}
                if el.endswith('.json') and not el.startswith('error_log'):
                    files["json"] = {'status': 'processed', 'file': el}
                if create_rdf:
                    if el.endswith('.jsonld'):
                        files["rdf"] = {'status': 'processed', 'file': el}
                if el.startswith('error_log'):
                    status = "partial processing"
                    log_file_path = os.path.join(single_pdf, el)
                    with open(log_file_path, 'r') as file:
                        data = json.load(file)
                        stage = data['current_stage']
                        if 'TEI/XML' in stage:
                            files["tei"] = {'status': 'error', 'error': data['error'], 'file': el}

                        if 'JSON' in stage or 'headings' in stage:
                            files["json"] = {'status': 'error', 'error': data['error'], 'file': el}

                        if 'RDF' in stage:
                            files["rdf"] = {'status': 'error', 'error': data['error'], 'file': el}

        manifest_info["status"] = status
        manifest_info["output_directory"] = os.path.basename(self.output_intermediate_dir)
        manifest_info["files"] = files

        shutil.rmtree(single_pdf)

        return manifest_info


    def create_xml_tei(self, consolidate_citations=True, consolidate_header=True, tei_coordinates=True, force=True):
        input_pdf_path = [self.input_pdf_path]
        output_tei_path = self.output_intermediate_dir

        self.client.process("processFulltextDocument", input_path=input_pdf_path, output=output_tei_path,
                            consolidate_citations=consolidate_citations, consolidate_header=consolidate_header,
                            tei_coordinates=tei_coordinates, force=force)

        basename = os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".grobid.tei.xml"
        xml_file_path = os.path.join(output_tei_path, basename)
        return input_pdf_path, xml_file_path

    def create_json(self, input_pdf_path, xml_file_path, create_rdf):
        output_json_name = self.output_intermediate_dir + os.path.sep + os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".json"

        tei_to_json_converter = TEIXMLtoJSONConverter(xml_file=xml_file_path, output_json_file=output_json_name,
                                                      auxiliar_file=self.auxiliar_file, create_rdf=create_rdf)

        target = tei_to_json_converter.convert_to_json()
        if target:
            return target

    def create_rdf(self, input_pdf_path, xml_file_path, target_dict):
        output_jsonld_name = self.output_intermediate_dir + os.path.sep + os.path.basename(input_pdf_path[0]).split(".pdf")[
            0] + ".jsonld"
        output_json_name = self.output_intermediate_dir + os.path.sep + \
                           os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".json"

        tei_to_rdf_converter = TEIXMLtoRDFConverter(xml_file=xml_file_path, json_file=output_json_name, target_dict=target_dict)

        cex_graphset = tei_to_rdf_converter.convert_to_rdf()

        storer = Storer(cex_graphset, output_format="json-ld")
        storer.store_graphs_in_file(output_jsonld_name)



if __name__ == '__main__':
    pdf_processor = PDFProcessor()
    pdf_processor.process_pdf()

