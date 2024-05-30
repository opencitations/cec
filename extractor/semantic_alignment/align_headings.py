#!/usr/bin/env python3
import json
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
    nlp = load_model('en_core_web_lg')
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)


# Load JSON file
def load_json(file_path):
    if file_path.endswith(".json"):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data


# Align section titles based on semantic similarity
def align_sections(json_data, reference_titles):
    aligned_titles = {}
    section_titles = set()

    # First, iterate through json_data to collect all unique section titles
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        section_titles.add(section_title)

    # List to store all (section_title, ref_title, similarity_score) tuples
    similarity_scores = []

    for section_title in section_titles:
        for ref_title in reference_titles:
            similarity_score = calculate_similarity(section_title.lower(), ref_title.lower())
            similarity_scores.append((section_title, ref_title, similarity_score))

    # Sort the list based on similarity scores in descending order
    similarity_scores.sort(key=lambda x: x[2], reverse=True)

    used_reference_titles = set()

    for section_title, ref_title, score in similarity_scores:
        if section_title not in aligned_titles and ref_title not in used_reference_titles and score > 0.7:
            aligned_titles[section_title] = ref_title
            used_reference_titles.add(ref_title)
    return aligned_titles


def build_output_file(aligned_titles, json_data, output_path):
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        if section_title in aligned_titles:
            json_data[section]['ALIGNED SECTION'] = aligned_titles[section_title]
    try:
        with open(output_path, 'w', encoding="utf-8") as file:
            json.dump(json_data, file, indent=4)
        print("The output file has been correctly generated")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


def run(input_zip_or_json, headings_list, json_output):
    json_data = load_json(input_zip_or_json)
    aligned_titles = align_sections(json_data, headings_list)
    build_output_file(aligned_titles, json_data, json_output)





