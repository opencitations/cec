# Citation Extractor and Classifier

The Citation Extractor and Classifier is  a software that performs the automatic annotation of in-text citations in academic papers provided in PDF. 

It is developed within the [GraspOS EU project](https://graspos.eu/). 


It works by applying two steps, described as follows:

- ___PDF Parsing___. The software analyses the PDF paper provided as input and extracts its basic bibliographic metadata, all the bibliographic references with all its metadata marked up, the citation sentences that contain in-text reference pointers , and other structural information such as sections, when possible
- ___Citation Function Classification___. The software uses the output of the previous step to classify the semantics emerging from each citation sentence that will be used for characterising the function of the citation defined by the authors of the citing paper (i.e., the input PDF) by means of the related in-text reference pointer.

Please find more details in the README files of each module: [extractor](extractor/README.md) and [classifier](classifier/README.md).
