import json
import re


import spacy
from lxml import etree


from extractor.cex.settings import *


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
            print("Model not found. Installing en_core_web_trf model")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        nlp = self.customize_tokenizer(nlp)
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def build_dict_ref_citkey(self, xml, ns):
        refs = xml.xpath(".//tei:div/tei:p/tei:ref[@type='bibr']", namespaces=ns)
        return {ref: f"cit{i + 1}" for i, ref in enumerate(refs)}

    def find_sentences_in_div(self, div, dict_to_check, ns):
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
            cleaned_text = re.sub('\s+', ' ', cleaned_text)
            cleaned_text = re.sub(r'\s+([,;.])', r'\1', cleaned_text)  # Remove spaces before punctuation
            # Remove unnecessary whitespaces inside parentheses
            cleaned_text = re.sub(r'\(\s*(.*?)\s*\)', r'(\1)', cleaned_text)
            return self.test_model_segmentation(cleaned_text)
        return []

    def find_sentences_in_div_superscripts(self, div, dict_to_check, ns):
        sentences_to_modify = self.find_sentences_in_div(div, dict_to_check, ns)
        for i, sentence in enumerate(sentences_to_modify):
            if i > 0:
                # Check if the citation is at the start of the sentence and preceding sentence ends with a period
                preceding_sentence = sentences_to_modify[i-1]
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

    def extract_last_head(self, head, has_n_attribute, has_roman_numeration):
        if head is None:
            return None

        head_text = (head.text or "").strip()
        if has_n_attribute and 'n' in head.attrib:
            return head_text
        elif has_roman_numeration:
            pattern = r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+'
            return re.sub(pattern, "", head_text).strip()
        return head_text

    def get_text_before_ref(self, ref, ns):
        preceding_text = ref.xpath('preceding-sibling::text()', namespaces=ns)
        text_before_ref = " ".join(preceding_text).strip() if preceding_text else ""
        text_before_ref = re.sub(r'^[^\w\s]+', '', text_before_ref)
        sentences = self.test_model_segmentation(text_before_ref)
        text_before_ref = sentences[-1].strip() if sentences else ""
        return text_before_ref

    def are_intext_reference_pointers_apexes(self, xml, ns):
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
                preceding_text = self.get_text_before_ref(ref, ns)
                if preceding_text.endswith('.'):
                    list_words = preceding_text.strip().split(' ')
                    ending_word = list_words[-1]
                    if ending_word not in special_cases:
                        preceding_texts.append(preceding_text)

            if len(preceding_texts) > total_refs/5:
                return True
        return False

    def convert_to_json(self):
        #try to differentiate numerical in text pointers from strings
        tree = etree.parse(self.xml_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # Precompute common elements
        ref_citkey_dict = self.build_dict_ref_citkey(tree, ns)
        head_elements = root.findall(".//tei:div/tei:head", namespaces=ns)
        has_n_attribute = any("n" in head.attrib for head in head_elements)
        roman_pattern = r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*\s+'
        has_roman_numeration = any(re.search(roman_pattern, (head.text or "").strip()) for head in head_elements)

        superscipts = self.are_intext_reference_pointers_apexes(tree, ns)

        # Initialize storage for citations
        citations = {}
        for div in root.findall(".//tei:div", namespaces=ns):
            head = div.find("./tei:head", namespaces=ns)
            last_head = self.extract_last_head(head, has_n_attribute, has_roman_numeration)

            if superscipts:
                sentences = self.find_sentences_in_div_superscripts(div, ref_citkey_dict, ns)
            else:
                sentences = self.find_sentences_in_div(div, ref_citkey_dict, ns)

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
                            citation_text = re.sub(r'\s+', ' ', processed_sentence)
                            citation_text = re.sub(r'\s+([,;.])', r'\1', citation_text)
                            citations[cit] = {
                                "SECTION": last_head,
                                "CITATION": citation_text,
                                "REFERENCE": ref_text
                            }

        # Save results to JSON
        with open(self.output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(citations, json_file, indent=2, ensure_ascii=False)


xml_file = "/home/marta/Scrivania/lavoro/ENE_EV12/ENE_EV12.grobid.tei.xml"
out_json = "/home/marta/Scrivania/lavoro/ENE_EV12/ENE_EV122.json"
xml_file_superscript = "/home/marta/Scaricati/processed_pdfs_1732793644.860334/HEA-PRO_EV15_1732793618.623148/HEA-PRO_EV15.grobid.tei.xml"
xml_file_superscript2 = "/home/marta/Scrivania/lavoro/DEN_EV9_1732963593.030276/DEN_EV9.grobid.tei.xml"
out_json2 = "/home/marta/Scrivania/lavoro/DEN_EV9.json"
aux = SPECIAL_CASES_PATH

tree = etree.parse(xml_file_superscript)
root = tree.getroot()
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

my_class = TEIXMLtoJSONConverter(xml_file_superscript2, out_json2, aux)
print(my_class.convert_to_json())