#!/usr/bin/env python3
import json
import re
import spacy
import zipfile
from scipy.optimize import linear_sum_assignment
import numpy as np
from collections import defaultdict, deque
from extractor.cex.settings import *
from concurrent.futures import ProcessPoolExecutor, as_completed


# Load SpaCy model
def load_model(model):
    try:
        nlp = spacy.load(model)
    except OSError:
        print("Model not found. Installing ...")
        spacy.cli.download(model)
        nlp = spacy.load(model)
    return nlp


nlp = load_model('en_core_web_lg')
# Function to calculate semantic similarity between two texts
def calculate_similarity(text1, text2):
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)

# Load JSON file
def load_json(file_path):
    if str(file_path).endswith(".json"):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data

def compute_similarity(section, reference):
    return section, reference, calculate_similarity(section.lower(), reference.lower())

# Align section titles based on semantic similarity
def align_sections(json_data, reference_titles, predefined_mappings):
    section_titles = set()
    aligned_titles = defaultdict(list)

    # First, iterate through json_data to collect all unique section titles
    for section in json_data:
        section_title = json_data[section].get('SECTION', '')
        section_titles.add(section_title)

    section_titles = list(section_titles)

    # Check for keyword-based mappings
    used_references = set()
    for section in section_titles:
        lower_section = section.lower()
        for keyword, reference in predefined_mappings.items():
            if keyword in lower_section:
                for single_reference in reference:
                    if single_reference in reference_titles and single_reference not in used_references:
                        aligned_titles[section].append(single_reference)
                        used_references.add(single_reference)

    available_titles = set(reference_titles) - used_references

    # Use ProcessPoolExecutor to parallelize similarity calculations
    similarity_scores = []
    with ProcessPoolExecutor() as executor:
        futures = []
        for section in section_titles:
            for reference in available_titles:
                futures.append(executor.submit(compute_similarity, section, reference))

        for future in as_completed(futures):
            section, reference, score = future.result()
            if score > 0.8:
                similarity_scores.append((section, reference, score))

    # Sort similarity scores in descending order
    similarity_scores.sort(key=lambda x: x[2], reverse=True)

    # Assign sections to references
    used_references = set()
    for section, reference, score in similarity_scores:
        if reference not in used_references:
            aligned_titles[section].append(reference)
            used_references.add(reference)

    return aligned_titles


# Build output file with aligned sections
def build_output_file(aligned_titles, json_data, output_path):
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        if section_title in aligned_titles:
            json_data[section]['ALIGNED SECTION'] = aligned_titles[section_title]
    try:
        with open(output_path, 'w', encoding="utf-8") as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
        print("The output file has been correctly generated")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


def build_mapping_file(aligned_titles, output_path):
    # Convert dictionary to JSON string
    json_data = json.dumps(aligned_titles, indent=4)

    # Save JSON string to a file
    with open(output_path, "w") as json_file:
        json_file.write(json_data)


# Main function to run the alignment process
def run(input_zip_or_json, headings_list, json_output, mapping_output, predefined_mappings_file=PREDEFINED_MAPPINGS_PATH):
    json_data = load_json(input_zip_or_json)
    predefined_mappings = load_json(predefined_mappings_file)
    aligned_titles = align_sections(json_data, headings_list, predefined_mappings)
    build_mapping_file(aligned_titles, mapping_output)
    build_output_file(aligned_titles, json_data, json_output)