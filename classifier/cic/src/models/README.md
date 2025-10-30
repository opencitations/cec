### 📂 Model Directory Structure

This directory must contain the following two subfolders:

1. `ModelsWithoutSections/`  
2. `ModelsWithSections/`  

---

### 📦 Downloading the Pretrained Models

You can download the pretrained model archives from Zenodo:

- **ModelsWithoutSections (WoS)** → [https://doi.org/10.5281/zenodo.14989091](https://doi.org/10.5281/zenodo.14989091)  
- **ModelsWithSections (WS)** → [https://doi.org/10.5281/zenodo.14989192](https://doi.org/10.5281/zenodo.14989192)

---

### 🧭 Installation Instructions

1. **Download** both ZIP files from the links above.  
2. **Extract** each archive on your machine.  
3. **Move the extracted model files** into the correct directories:
   - Files from the *WoS* archive → move into `ModelsWithoutSections/`  
   - Files from the *WS* archive → move into `ModelsWithSections/`  

> ⚠️ **Important:**  
> Do **not** move the entire `WoS` or `WS` folders themselves.  
> Only the **model files inside** these folders (e.g., `.pt`, `.pth`) should be placed directly into the corresponding directories.

---

### ✅ Final Structure

```bash
models/
├── ModelsWithoutSections/
│   ├── FFNN_SciCiteWoS.pth
│   ├── WoS_SciBERT_bkg.pt
│   ├── WoS_SciBERT_met.pt
│   ├── WoS_SciBERT_res.pt
│   ├── WoS_XLNet_bkg.pt
│   ├── WoS_XLNet_met.pt
│   └── WoS_XLNet_res.pt
└── ModelsWithSections/
    ├── FFNN_SciCiteWS.pth
    ├── WS_SciBERT_bkg.pt
    ├── WS_SciBERT_met.pt
    ├── WS_SciBERT_res.pt
    ├── WS_XLNet_bkg.pt
    ├── WS_XLNet_met.pt
    └── WS_XLNet_res.pt
```