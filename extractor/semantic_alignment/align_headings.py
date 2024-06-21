#!/usr/bin/env python3
import json
import re
import spacy
import zipfile
from scipy.optimize import linear_sum_assignment
import numpy as np


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
def align_sections(json_data, reference_titles, predefined_mappings):
    section_titles = set()
    aligned_titles = {}
    used_reference_indices = set()

    # First, iterate through json_data to collect all unique section titles
    for section in json_data:
        section_title = json_data[section].get('SECTION', [])
        section_titles.add(section_title)

    section_titles = list(section_titles)
    n_sections = len(section_titles)
    n_references = len(reference_titles)

    # Check for keyword-based mappings
    for section in section_titles:
        lower_section = section.lower()
        for keyword, reference in predefined_mappings.items():
            if keyword in lower_section:
                if reference in reference_titles:
                    aligned_titles[section] = reference
                    used_reference_indices.add(reference_titles.index(reference))
                    break  # Exit the loop once a match is found


    # Determine the size of the square cost matrix
    size = max(n_sections, n_references)
    # Create the cost matrix and initialize with large negative values for dummy entries
    cost_matrix = np.full((size, size), 0, dtype=np.float64)

    # Fill the cost matrix with actual similarity scores
    for i in range(n_sections):
        for j in range(n_references):
            if section_titles[i] not in aligned_titles and j not in used_reference_indices:
                similarity_score = calculate_similarity(section_titles[i].lower(), reference_titles[j].lower())
                if similarity_score > 0.7:
                    cost_matrix[i, j] = -similarity_score  # Negative because we want to maximize similarity

    # Apply the Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    for row, col in zip(row_ind, col_ind):
        if (row < n_sections and col < n_references and cost_matrix[row, col] != 0
                and section_titles[row] not in aligned_titles):
            aligned_titles[section_titles[row]] = reference_titles[col]

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


def run(input_zip_or_json, headings_list, json_output, predefined_mappings_file):
    json_data = load_json(input_zip_or_json)
    predefined_mappings = load_json(predefined_mappings_file)
    aligned_titles = align_sections(json_data, headings_list, predefined_mappings)
    build_output_file(aligned_titles, json_data, json_output)





