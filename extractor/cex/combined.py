
import os
from extractor.cex.grobid_client.grobid_client import GrobidClient
from lxml import etree
import json
import re
import spacy
from oc_ocdm import Storer
from oc_ocdm.graph import GraphSet
from oc_ocdm.graph.entities import Identifier
from oc_ocdm.support import create_date
from datetime import datetime
import uuid
from extractor.cex.settings import SPECIAL_CASES_PATH


class TEIXMLtoJSONConverter:
    def __init__(self, xml_file, output_json_file, auxiliar_file):
        self.xml_file = xml_file
        self.output_json_file = output_json_file
        self.auxiliar_file = auxiliar_file

    def customize_tokenizer(self, nlp):
        with open(self.auxiliar_file, 'r') as file:
            special_cases = json.load(file)
        for word, tokens in special_cases.items():
            nlp.tokenizer.add_special_case(word, tokens)
        return nlp

    def test_model_segmentation(self, text):
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Model not found. Installing en_core_web_sm model")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        nlp = self.customize_tokenizer(nlp)
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def get_text_before_ref(self, ref, ns):
        preceding_text = ref.xpath('preceding-sibling::text()', namespaces=ns)
        text_before_ref = " ".join(preceding_text).strip() if preceding_text else ""
        text_before_ref = re.sub(r'^[^\w\s]+', '', text_before_ref)
        sentences = self.test_model_segmentation(text_before_ref)
        text_before_ref = sentences[-1].strip() if sentences else ""
        return text_before_ref

    def get_text_after_ref(self, ref, ns):
        following_text = ref.xpath('following-sibling::text()', namespaces=ns)
        text_after_ref = " ".join(following_text).strip() if following_text else ""
        sentences = self.test_model_segmentation(text_after_ref)
        text_after_ref = sentences[0].strip() if sentences else ""
        return text_after_ref

    def convert_to_json(self):
        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        citations = {}
        last_head = None
        citation_id = 1

        head_elements = root.findall(".//tei:div/tei:head", namespaces=ns)
        has_n_attribute = any("n" in head.attrib for head in head_elements)
        roman_numbers_pattern = r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*(?:\.[A-Z0-9]+\.*)*\s+'
        has_roman_numeration = any(re.search(roman_numbers_pattern, head.text.strip() if head.text else "") for head
                                   in head_elements)
        head_n_attribute = sum("n" in head.attrib for head in head_elements)
        head_no_n_attribute = sum("n" not in head.attrib for head in head_elements)
        for div in root.findall(".//tei:div", namespaces=ns):
            head = div.find("./tei:head", namespaces=ns)

            if head is not None:
                head_text = head.text.strip() if head.text else ""
                if head_n_attribute > head_no_n_attribute:
                    if has_n_attribute:
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
                elif has_roman_numeration:
                    if re.search(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+', head_text):
                        pattern = re.compile(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+')
                        match = pattern.search(head_text)
                        if match:
                            match = match.group().strip()
                            last_head = head_text.replace(match, "")
                else:
                    last_head = head_text

                '''if last_head is not None and all(keyword not in head_text for keyword in ["Introduction", "Related Works", "Material", "Methods" (methods and materials), "Results", "Discussion", "Conclusion"]):
                    head_text = last_head'''

                refs = div.findall(".//tei:p/tei:ref[@type='bibr']", namespaces=ns)

                for ref in refs:
                    text_before_ref = self.get_text_before_ref(ref, ns)
                    ref_text = ref.text.strip() if ref.text else ""
                    text_after_ref = self.get_text_after_ref(ref, ns)
                    combined_text = f"{text_before_ref} {ref_text} {text_after_ref}"

                    citation_key = f"cit{citation_id}"

                    if citation_key not in citations:
                        citations[citation_key] = {
                            "SECTION": last_head,
                            "CITATION": ""
                        }

                    citations[citation_key]["CITATION"] += combined_text + " "

                    citation_id += 1

        for citation in citations.values():
            citation["CITATION"] = citation["CITATION"].strip()

        with open(self.output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(citations, json_file, indent=2, ensure_ascii=False)


class TEIXMLtoRDFConverter:

    def __init__(self, xml_file, output_rdf_file):
        self.xml_file = xml_file
        self.output_turtle_file = output_rdf_file

    def create_unique_uri(self, base_uri, prefix):
        return f"{base_uri}{prefix}/{uuid.uuid4()}"

    def convert_to_rdf(self):

        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        base_uri = "https://w3id.org/oc/cex/"

        cex_graphset = GraphSet(base_uri)

        # Extract br metadata from the xml-tei using XPath
        doi_elements = root.xpath('//tei:idno[@type="DOI"]', namespaces=ns)
        title_elements = root.xpath('//tei:title[@level="a"]', namespaces=ns)
        authors = root.xpath('//tei:fileDesc//tei:author', namespaces=ns)
        pub_date = root.xpath('//tei:publicationStmt/tei:date[@type="published"]/@when', namespaces=ns)
        publisher = root.xpath('//tei:publicationStmt/tei:publisher', namespaces=ns)

        if doi_elements:
            doi = doi_elements[0].text
            br_uri = self.create_unique_uri(base_uri, "br")
            br = cex_graphset.add_br(br_uri)

            id_uri = self.create_unique_uri(base_uri, "id")
            br_id = cex_graphset.add_id(id_uri)

            br_id.create_doi(doi)

            br.has_identifier(br_id)
            if title_elements:
                br.has_title(title_elements[0].text)
            if pub_date:
                # Convert the string to a datetime object
                date_obj = datetime.strptime(pub_date[0], "%Y-%m-%d")

                # Convert to ISO 8601 format
                iso_format = date_obj.isoformat()
                br.has_pub_date(iso_format)

            for author in authors:
                forename_elements = author.xpath('.//tei:forename', namespaces=ns)
                surname_elements = author.xpath('.//tei:surname', namespaces=ns)
                orcid_elements = author.xpath('.//tei:idno[@type="ORCID"]', namespaces=ns)
                orcid = orcid_elements[0].text

                ra = cex_graphset.add_ra(f"https://w3id.org/oc/cex/br/{orcid}")

                orcid_uri = self.create_unique_uri(base_uri, "id")
                ra_id = cex_graphset.add_id(orcid_uri)
                ra_id.create_orcid(orcid)
                ra.has_identifier(ra_id)
                ra.has_given_name(forename_elements[0].text)
                ra.has_family_name(surname_elements[0].text)

        # Create Storer instances
        my_graph_storer = Storer(cex_graphset)
        my_graph_storer.store_graphs_in_file(self.output_turtle_file)


class PDFProcessor:
    def __init__(self, input_pdf_path="/Users/olga/Downloads/AGR-BIO-SCI_2.pdf", output_tei_path="output",
                 output_json_path="output", config_path="config.json", auxiliar_file=SPECIAL_CASES_PATH):
        self.client = GrobidClient(config_path=config_path)
        self.input_pdf_path = input_pdf_path
        self.output_tei_path = output_tei_path
        self.output_json_path = output_json_path
        self.auxiliar_file = auxiliar_file

    def process_pdf(self, consolidate_citations=True, consolidate_header=True, tei_coordinates=True, force=True):
        input_pdf_path = [self.input_pdf_path]
        output_tei_path = self.output_tei_path

        self.client.process("processFulltextDocument", input_path=input_pdf_path, output=output_tei_path,
                            consolidate_citations=consolidate_citations, consolidate_header=consolidate_header,
                            tei_coordinates=tei_coordinates, force=force)

        basename = os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".grobid.tei.xml"
        xml_file_path = os.path.join(output_tei_path, basename)
        output_json_name = self.output_json_path + os.path.sep + os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".json"

        tei_to_json_converter = TEIXMLtoJSONConverter(xml_file=xml_file_path, output_json_file=output_json_name,
                                                      auxiliar_file=self.auxiliar_file)

        tei_to_json_converter.convert_to_json()

        output_turtle_name = self.output_json_path + "//" + os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".ttl"
        tei_to_rdf_converter = TEIXMLtoRDFConverter(xml_file=xml_file_path, output_rdf_file=output_turtle_name)
        tei_to_rdf_converter.convert_to_rdf()

        folder_path = 'output'
        files = []
        for entry in os.scandir(folder_path):
            if entry.is_file():
                files.append(entry.name)
        for file in files:
            os.remove(os.path.join(folder_path, file))

    def create_xml_tei(self, consolidate_citations=True, consolidate_header=True, tei_coordinates=True, force=True):
        input_pdf_path = [self.input_pdf_path]
        output_tei_path = self.output_tei_path

        self.client.process("processFulltextDocument", input_path=input_pdf_path, output=output_tei_path,
                            consolidate_citations=consolidate_citations, consolidate_header=consolidate_header,
                            tei_coordinates=tei_coordinates, force=force)

        basename = os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".grobid.tei.xml"
        xml_file_path = os.path.join(output_tei_path, basename)
        return input_pdf_path, xml_file_path

    def create_json(self, input_pdf_path, xml_file_path):
        output_json_name = self.output_json_path + os.path.sep + os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".json"

        tei_to_json_converter = TEIXMLtoJSONConverter(xml_file=xml_file_path, output_json_file=output_json_name,
                                                      auxiliar_file=self.auxiliar_file)

        tei_to_json_converter.convert_to_json()

    def create_rdf(self, input_pdf_path, xml_file_path):
        output_turtle_name = self.output_json_path + os.path.sep + os.path.basename(input_pdf_path[0]).split(".pdf")[
            0] + ".ttl"
        tei_to_rdf_converter = TEIXMLtoRDFConverter(xml_file=xml_file_path, output_rdf_file=output_turtle_name)
        tei_to_rdf_converter.convert_to_rdf()


if __name__ == '__main__':
    pdf_processor = PDFProcessor()
    pdf_processor.process_pdf()


