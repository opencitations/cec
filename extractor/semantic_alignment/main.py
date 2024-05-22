import json
import os
import re
import spacy
import zipfile


# Load SpaCy model
def load_model(model):
    try:
        nlp = spacy.load(model)
    except OSError:
        print("Model not found. Installing ...")
        spacy.cli.download(model)
        nlp = spacy.load(model)
    return nlp


# Function to calculate semantic similarity between two texts
def calculate_similarity(text1, text2):
    nlp = load_model('en_core_web_md')
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)


# Load JSON file
def load_json(file_path):
    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_content = zip_ref.namelist()
            for el in zip_content:
                if el.endswith(".json"):
                    with zip_ref.open(el) as file:
                        data = json.load(file)
                        return data
    elif file_path.endswith(".json"):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data


# Align section titles based on semantic similarity
def align_sections(json_data, reference_titles):
    roman_number = r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.*'
    section_number = r'^[1-9]+\.*'
    aligned_titles = {}
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        if section_title not in aligned_titles:
            if re.search(section_number, section_title):
                pattern = re.compile(section_number)
                match = pattern.search(section_title)
                if match:
                    match = match.group()
                    section_title = section_title.replace(match, "").strip()
            elif re.search(roman_number, section_title):
                pattern = re.compile(roman_number)
                match = pattern.search(section_title)
                if match:
                    match = match.group()
                    section_title = section_title.replace(match, "").strip()
            best_match = None
            best_score = 0.7
            for ref_title in reference_titles:
                similarity_score = calculate_similarity(section_title, ref_title)
                if similarity_score > best_score:
                    best_score = similarity_score
                    best_match = ref_title
                if best_match is not None:
                    aligned_titles[json_data[section].get('SECTION', [])] = best_match
    return aligned_titles


def build_output_file(aligned_titles, json_data, output_path):
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        if section_title in aligned_titles:
            json_data[section]['ALIGNED HEADING'] = aligned_titles[section_title]
    try:
        with open(output_path, 'w') as file:
            json.dump(json_data, file, indent=4)
        print("The output file has been correctly generated")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


# Example usage
if __name__ == "__main__":
    zip_file = '' # output of the extractor
    reference_titles = ["Introduction", "Related Works", "Methods and Materials", "Results", "Discussion", "Conclusion"]
    output_file = '' # path to the file to save the results

    json_data = load_json(zip_file)
    aligned_titles = align_sections(json_data, reference_titles)
    build_output_file(aligned_titles, json_data, output_file)

