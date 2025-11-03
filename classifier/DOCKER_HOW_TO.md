# How to Use the Classifier with Docker Compose

## Prerequisites

First, make sure you have Docker and Docker Compose installed on your system.

## Download Models

Download the models from here (make sure to select **VERSION 2**):
   - **Ensemble Model Without Section Titles**: [EnsIntWos](https://doi.org/10.5281/zenodo.11652578)
   - **Ensemble Model With Section Titles**: [EnsIntWS](https://doi.org/10.5281/zenodo.11653642)

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
    image: opencitations/oc_cec_classifier:1.2.1_V2
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