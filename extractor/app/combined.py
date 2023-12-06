
import os

from grobid_client.grobid_client import GrobidClient
from lxml import etree
import json
import re


class TEIXMLtoJSONConverter:
    def __init__(self, xml_file, output_json_file):
        self.xml_file = xml_file
        self.output_json_file = output_json_file

    def get_text_before_ref(self, ref, ns):
        preceding_text = ref.xpath('preceding-sibling::text()', namespaces=ns)
        text_before_ref = " ".join(preceding_text).strip() if preceding_text else ""
        text_before_ref = re.sub(r'^[^\w\s]+', '', text_before_ref)
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text_before_ref)
        text_before_ref = sentences[-1].strip() if sentences else ""
        return text_before_ref

    def get_text_after_ref(self, ref, ns):
        following_text = ref.xpath('following-sibling::text()', namespaces=ns)
        text_after_ref = " ".join(following_text).strip() if following_text else ""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text_after_ref)
        text_after_ref = sentences[0].strip() if sentences else ""
        return text_after_ref

    def convert_to_json(self):
        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        citations = {}
        last_head = None
        citation_id = 1

        for div in root.findall(".//tei:div", namespaces=ns):
            head = div.find("./tei:head", namespaces=ns)

            if head is not None:
                head_text = head.text.strip() if head.text else ""

                if last_head is not None and all(keyword not in head_text for keyword in ["Introduction", "Material", "Methods", "Results", "Discussion", "Conclusion"]):
                    head_text = last_head

                refs = div.findall(".//tei:p/tei:ref[@type='bibr']", namespaces=ns)

                for ref in refs:
                    text_before_ref = self.get_text_before_ref(ref, ns)
                    ref_text = ref.text.strip() if ref.text else ""
                    text_after_ref = self.get_text_after_ref(ref, ns)
                    combined_text = f"{text_before_ref} {ref_text} {text_after_ref}"

                    citation_key = f"cit{citation_id}"

                    if citation_key not in citations:
                        citations[citation_key] = {
                            "SECTION": head_text,
                            "CITATION": ""
                        }

                    citations[citation_key]["CITATION"] += combined_text + " "

                    citation_id += 1

                last_head = head_text

        for citation in citations.values():
            citation["CITATION"] = citation["CITATION"].strip()

        with open(self.output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(citations, json_file, indent=2, ensure_ascii=False)

class PDFProcessor:
    def __init__(self, input_pdf_path="/Users/olga/Downloads/AGR-BIO-SCI_2.pdf", output_tei_path="output", output_json_path="output", config_path="./config.json"):
        self.client = GrobidClient(config_path=config_path)
        self.input_pdf_path = input_pdf_path
        self.output_tei_path = output_tei_path
        self.output_json_path = output_json_path

    def process_pdf(self, consolidate_citations=True, consolidate_header=True, tei_coordinates=True, force=True):
        input_pdf_path = [self.input_pdf_path]
        output_tei_path = self.output_tei_path
        self.client.process("processFulltextDocument", input_path=input_pdf_path, output=output_tei_path,
                            consolidate_citations=consolidate_citations, consolidate_header=consolidate_header,
                            tei_coordinates=tei_coordinates, force=force)

        basename = os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".grobid.tei.xml"
        xml_file_path = os.path.join(output_tei_path, basename)
        output_json_name = self.output_json_path + "//" + os.path.basename(input_pdf_path[0]).split(".pdf")[0] + ".json"

        tei_to_json_converter = TEIXMLtoJSONConverter(xml_file=xml_file_path, output_json_file=output_json_name)
        tei_to_json_converter.convert_to_json()

        folder_path = 'output'
        files = []
        for entry in os.scandir(folder_path):
            if entry.is_file():
                files.append(entry.name)
        for file in files:
            os.remove(os.path.join(folder_path, file))

if __name__ == '__main__':
    pdf_processor = PDFProcessor()
    pdf_processor.process_pdf()


