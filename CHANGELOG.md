# CHANGELOG.md

## Beta (unreleased)

Citation Intent Classifier - Features & products:
  - extended pool of base models and revised/improved classifier -> [Description](https://arxiv.org/abs/2407.13329)
  - add demo in the web application home page -> [CIC](http://137.204.64.4:81/cic/start)
  
Citation Extractor - Features & products:
  - use of [Spacy](https://spacy.io) tokenizer (model [en_core_web_sm](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.7.1)) for the segmentation and recognition of citation sentences
  - add module for extraction and semantic alignment of section titles

## Alpha (2024-02-08)

Citation Intent Classifier - Features & products:

  - released web application -> [CIC](http://137.204.64.4:81/cic/)
  - ensemble model with 3 base LMs
  
Citation Extractor - Features & products:

  - released web application -> [CEX](http://137.204.64.4:81/cex/)
  - use of the GROBID Python Client with the configuration "processFulltextDocument" and the trained citation model "model5.wapiti" -> [trained GROBID citation models](https://doi.org/10.5281/zenodo.10529709)
  - use of regex for the segmentation and recognition of citation sentences 
