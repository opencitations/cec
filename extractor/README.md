# Citation Extractor (cex) [Version: Alpha]

## Get started:
**Note all operations must be done as root `su`**

### Init Grobid
* Clone the Grobid repo (https://github.com/kermitt2/grobid.git) into `cex/src/`
* Update the directory with the corresponding model from `extractor/cex/src/train_data`: (1) `grobid-home/models/citation`, (2) `grobid-trainer/resources/dataset/citation`
* run grobid `./gradlew run`

### Prepare/Run the python service
* create a python virtual env `python -m venv <your_venv>`
* activate venv: `source <your_venv>/bin/activate`
* install libs: `cd cex | pip -r requirements.txt`
* run the app: `python main.py`

**Configuration:**
To change the `PREFIX` variables go to **cex/main.py**
Default is set to `PREFIX = /cex/`
