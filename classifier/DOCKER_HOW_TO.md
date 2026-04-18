# Classifier with externally mounted models

This guide covers the `opencitations/oc_cec_classifier:1.2.2_V2` image, which does not bundle the ensemble model weights: they must be downloaded separately and mounted into the container.

If you just want to run the classifier without this extra setup, use the `V2_full` image from the [root README](../README.md) instead: that variant already contains the weights.

## Prerequisites

Docker and Docker Compose installed.

## Download the models

Download the V2 model archives from Zenodo:
   - **ModelsWithoutSections (WoS)**: https://doi.org/10.5281/zenodo.14989091
   - **ModelsWithSections (WS)**: https://doi.org/10.5281/zenodo.14989192

## Setup Models Directory

Extract the downloaded archives and create a folder called `models`. Rename the folders "WS" and "WoS" to match this naming convention:

```
├── models
│   ├── ModelsWithoutSections
│   │   ├── FFNN_SciCiteWoS.pth
│   │   ├── WoS_SciBERT_bkg.pt
│   │   ├── WoS_SciBERT_met.pt
│   │   ├── WoS_SciBERT_res.pt
│   │   ├── WoS_XLNet_bkg.pt
│   │   ├── WoS_XLNet_met.pt
│   │   └── WoS_XLNet_res.pt
│   ├── ModelsWithSections
│   │   ├── FFNN_SciCiteWS.pth
│   │   ├── WS_SciBERT_bkg.pt
│   │   ├── WS_SciBERT_met.pt
│   │   ├── WS_SciBERT_res.pt
│   │   ├── WS_XLNet_bkg.pt
│   │   ├── WS_XLNet_met.pt
│   │   └── WS_XLNet_res.pt
```

Now, identify the full path of your `models` folder, as we'll need it for the Docker Compose configuration.

## Create Docker Compose File

Create a file called `docker-compose.yaml`:

```bash
vim docker-compose.yaml
```

Insert the following content:

```yaml
services:
  cic-classifier:
    image: opencitations/oc_cec_classifier:1.2.2_V2
    container_name: cic-classifier
    ports:
      - "5000:5000"
    volumes:
      # Mount local models directory to container
      # Replace with your actual models path (absolute or relative)
      - /your_folder/models:/app/classifier/cic/src/models
    deploy:
      resources:
        limits:
          memory: 32G
        reservations:
          memory: 16G
    restart: unless-stopped
```

Replace `/your_folder/models` with the actual path to your models folder that you noted earlier.

## Start the Container

Run the following command to start Docker Compose:

```bash
docker compose up -d
```

Wait about 10 minutes while it downloads and extracts several gigabytes of data.

## Access the Classifier

Once finished, open your browser and navigate to:

```
http://127.0.0.1:5000/cic/classifier
```