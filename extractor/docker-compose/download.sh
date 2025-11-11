#!/bin/bash

# Insert this script in the same folder as docker-compose.yml and run it to download the models

#ENVs
CITATION_MODEL_URL='https://zenodo.org/records/10529709/files/trained%20models.zip?download=1'
CITATION_MODEL_SUBDIR='trained models'
CITATION_MODEL_VERSION='model2.wapiti'
SEGMENTATION_MODEL_URL='https://zenodo.org/records/17549454/files/grobid_trained_segmentation_models.zip?download=1'
SEGMENTATION_MODEL_VERSION='model5.wapiti'

#------------------------------------------------------------------



#creating folder
mkdir ./citation_model
mkdir ./segmentation_model

#download citation model
wget -O citation.zip ${CITATION_MODEL_URL}
unzip citation.zip -d ./citation_folder
cp "./citation_folder/${CITATION_MODEL_SUBDIR}/${CITATION_MODEL_VERSION}" ./citation_model/model.wapiti
rm -rf ./citation.zip
rm -rf ./citation_folder


#download segmentation model
wget -O segmentation.zip ${SEGMENTATION_MODEL_URL}
unzip segmentation.zip -d segment_folder
cp "./segment_folder/${SEGMENTATION_MODEL_VERSION}" ./segmentation_model/model.wapiti
rm -rf ./segmentation.zip
rm -rf ./segment_folder