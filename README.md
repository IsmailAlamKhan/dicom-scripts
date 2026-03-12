# 🏥 DICOM Scripts
A collection of Python scripts for working with DICOM medical imaging files — extract institution metadata, modify institution names, and create brand-new anonymized studies with consistent UID mappings.
---
## 📋 Table of Contents
- [Overview](#overview)
- [Scripts](#scripts)
  - [extract\\_institution\\_names.py](#1-extract_institution_namespy)
  - [add\\_institution\\_names.py](#2-add_institution_namespy)
  - [create\\_new\\_study.py](#3-create_new_studypy)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Output Files](#output-files)
- [Notes](#notes)
---
## Overview
These scripts use the [`pydicom`](https://pydicom.github.io/) library to read, modify, and write DICOM (`.dcm`) files. They are designed for use cases such as:
- Auditing institution metadata across a DICOM dataset
- Anonymizing or relabeling DICOM files for testing or transfer
- Creating fresh DICOM studies with new UIDs while preserving structural relationships
All scripts support processing both **single files** and **entire directory trees**.
---
## Scripts
### 1. `extract_institution_names.py`
Scans DICOM files and extracts the `InstitutionName` tag (DICOM tag `0008,0080`) along with the `StudyInstanceUID`.
**What it does:**
- Walks through a directory recursively to find all `.dcm` files
- Reads each file and pulls out the institution name and study UID
- Prints a summary of all unique institutions found
- Saves results to a timestamped CSV file
**Output CSV columns:** `id`, `institution_name`, `error`
---
### 2. `add_institution_names.py`
Adds or overwrites the `InstitutionName` tag in DICOM files. Also re-assigns Patient IDs, Study UIDs, Series UIDs, SOP Instance UIDs, and accession numbers to anonymize the data.
**What it does:**
- Sets a custom institution name across all processed files
- Generates new, consistent Patient IDs and Study UIDs (maintaining relationships within a study)
- Generates new unique Series and SOP Instance UIDs per file
- Optionally creates `.backup_*` copies of original files before modifying
- Optionally reorganizes output into a new directory structure: `output_dir/[StudyInstanceUID]/[filename].dcm`
- Saves a detailed modification log to a timestamped CSV file
**Output CSV columns:** `original_file_path`, `new_file_path`, `status`, `original_institution`, `new_institution`, `backup_path`, `error`
---
### 3. `create_new_study.py`
Creates a completely new DICOM study from existing files, reassigning all identifiers while preserving the hierarchical structure (Study → Series → Instance).
**What it does:**
- Assigns a new Institution Name and Patient Name/ID
- Generates one new `StudyInstanceUID` shared across all files
- Maps each original `SeriesInstanceUID` to a new consistent UID (preserving series groupings)
- Generates a new unique `SOPInstanceUID` per instance
- Updates Study/Series dates and times to the current datetime
- Randomizes `StudyID` and `AccessionNumber`
- Organizes output as: `output_dir/[StudyUID]/[SeriesUID]/IMG#####.dcm`
- Saves a CSV processing log and a plain-text UID mapping file
**Output files:**
- `new_study_log_<timestamp>.csv` — per-file processing results
- `uid_mapping_<timestamp>.txt` — full mapping of original → new UIDs
---
## Requirements
- Python 3.7+
- [`pydicom`](https://pydicom.github.io/) >= 2.3.0
---
## Installation
1. **Clone the repository:**
```bash
   git clone https://github.com/IsmailAlamKhan/dicom-scripts.git
   cd dicom-scripts
```
2. **Install dependencies:**
```bash
   pip install -r requirements.txt
```
---
## Usage
Each script is run interactively from the command line. Simply execute the script and follow the prompts.
```bash
# Extract institution names from DICOM files
python extract_institution_names.py
# Add or modify institution names
python add_institution_names.py
# Create a new anonymized study
python create_new_study.py
```
Each script will ask you to:
1. Choose between processing a **single file** or a **directory**
2. Provide the file/directory path
3. Confirm before making any changes
---
## Output Files
| Script | Output |
|---|---|
| `extract_institution_names.py` | `institution_names_<timestamp>.csv` |
| `add_institution_names.py` | `institution_modification_log_<timestamp>.csv` + optional `.backup_*` files |
| `create_new_study.py` | `new_study_log_<timestamp>.csv` + `uid_mapping_<timestamp>.txt` |
---
## Notes
- All scripts use `force=True` when reading DICOM files, so they can handle non-standard or partially malformed files.
- Original transfer syntax is preserved when saving files.
- The `create_new_study.py` script maintains **consistent UID mappings** — files belonging to the same original series
