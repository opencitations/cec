# GROBID with custom models

Setup to run GROBID with custom citation and segmentation models.

## Quick start

Just use the bash script that download the models automatically:
```bash
# First download the models
bash ./download.sh
```
The directory structure after running the script:
├─ docker-compose/
   │  ├─ docker-compose.yaml
   │  ├─ citation_model/
   │  │  └─ model.wapiti
   │  └─ segmentation_model/
   │     └─ model.wapiti

Now we can start the docker compose file:
```bash
# Then start GROBID
docker compose up -d
```

GROBID will be available at `http://localhost:8070`

## Using different models

If you want to use different models, edit the variables at the top of `download.sh`:
```bash
CITATION_MODEL_URL='https://zenodo.org/records/10529709/files/trained%20models.zip?download=1'
CITATION_MODEL_SUBDIR='trained models'
CITATION_MODEL_VERSION='model2.wapiti'
SEGMENTATION_MODEL_URL='https://zenodo.org/records/17549454/files/grobid_trained_segmentation_models.zip?download=1'
SEGMENTATION_MODEL_VERSION='model5.wapiti'
```

Change the URLs and file names to match your models, then run the script.

## What it does

The `download.sh` script downloads two models from Zenodo:
- **Citation model** (model2.wapiti) - for citation extraction
- **Segmentation model** (model5.wapiti) - for document segmentation

Models are extracted from zip files and copied to the right folders that get mounted in the container.



## Useful commands
```bash
# Start in background
docker compose up -d

# Check logs
docker compose logs -f

# Stop everything
docker compose down
```

