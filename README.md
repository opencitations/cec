# Citation Extractor and Classifier

The Citation Extractor and Classifier is  a software that performs the automatic annotation of in-text citations in academic papers provided in PDF. 

It is developed within the [GraspOS EU project](https://graspos.eu/). 


It works by applying two steps, described as follows:

- ___PDF Parsing___. The software analyses the PDF paper provided as input and extracts its basic bibliographic metadata, all the bibliographic references with all its metadata marked up, the citation sentences that contain in-text reference pointers , and other structural information such as sections, when possible
- ___Citation Function Classification___. The software uses the output of the previous step to classify the semantics emerging from each citation sentence that will be used for characterising the function of the citation defined by the authors of the citing paper (i.e., the input PDF) by means of the related in-text reference pointer.

Please find more details in the README files of each module: [extractor](extractor/README.md) and [classifier](classifier/README.md).


# Docker Compose
Ready-to-use Docker setup. No expertise required.

Create `docker-compose.yaml`:
```yaml
services:
  grobid:
    image: opencitations/grobid-cec:1.0.0
    container_name: grobid
    init: true
    ports:
      - "8070:8070"
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4'
        reservations:
          memory: 8G
          cpus: '2'
    restart: unless-stopped

  extractor:
    image: opencitations/oc_cec_extractor:1.0.4
    container_name: cec_extractor
    init: true
    ports:
      - "5001:5001"
    environment:
      - GROBID_URL=http://grobid:8070
    restart: unless-stopped
    depends_on:
      - grobid

  cic-classifier:
    image: opencitations/oc_cec_classifier:V2_full
    container_name: cic-classifier
    ports:
      - "5000:5000"
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 4G
    restart: unless-stopped
```

**Adjust CPU and RAM based on your hardware.**

## Commands
```bash
docker compose up -d      # Run the docker-compose.yaml
docker compose down       # Stop all the containers
docker compose restart    # Restart all
```

## Services

- Classifier: http://localhost:5000/cic
- Extractor: http://localhost:5001/cex