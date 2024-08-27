# CHANGELOG.md

## Beta (unreleased)

Citation Intent Classifier - Features & products:

  - add API support -> possibility to classify compressed archives and files
  - extended pool of models and revised classifier -> [Description](https://arxiv.org/abs/2407.13329)
  - add demo in the web application home page -> [CIC](http://137.204.64.4:81/cic/start)
  
Citation Extractor - Features & products:
  - add API support -> possibility to extract citations from compressed archives and single PDFs
  - add module for extraction and semantic alignment of section titles
  - add production of a JSON-LD file

## Alpha (2024-02-08)

Citation Intent Classifier - Features & products:

  - released web application -> [CIC](http://137.204.64.4:81/cic/)
  - ensemble model with 3 base LMs
  
Citation Extractor - Features & products:

  - released web application -> [CEX](http://137.204.64.4:81/cex/)
  - use of the GROBID Python Client with the configuration "processFulltextDocument" and the trained citation model "model5.wapiti" -> [trained GROBID citation models](https://doi.org/10.5281/zenodo.10529709)
