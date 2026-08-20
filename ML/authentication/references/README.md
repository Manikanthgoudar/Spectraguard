# SpectraGuard Pharmaceutical Raman Reference Data Layer

## 1. Overview

This directory (`ML/authentication/references/`) is reserved exclusively for storing **verified authentic pharmaceutical Raman reference standards**.

A **Pharmaceutical Reference Spectrum** is a high-resolution, standardized Raman spectral measurement obtained from a certified authentic pharmaceutical drug sample under controlled laboratory conditions.

---

## 2. Strict Requirements & Constraints

> [!CAUTION]
> **PROHIBITION OF SYNTHETIC OR FABRICATED DATA**
> - Reference files MUST NOT be created from invented, random, mock, or synthetic values.
> - Filenames, solvent spectra, or mock backend upload samples MUST NEVER be presented as authentic pharmaceutical references.
> - Any reference file submitted without verified source/provenance metadata WILL BE REJECTED by the validation engine.

---

## 3. Reference CSV Technical Specifications

### A. Spectral Feature Vector
- **Feature Count**: Exactly **3,276** wavenumber intensity features.
- **Wavenumber Range**: Spanning from **150.0 cm⁻¹** to **3425.0 cm⁻¹** (inclusive) in 1.0 cm⁻¹ uniform intervals.
- **Feature Ordering**: Strictly ascending order (`150.0, 151.0, 152.0, ... , 3425.0`).
- **Data Values**: Non-negative finite floating-point numbers. No `NaN`, `null`, `inf`, or string values allowed in spectral channels.

### B. Preprocessing Compatibility
All reference spectra must be compatible with the official SpectraGuard preprocessing pipeline:
1. **5th-Degree Polynomial Baseline Subtraction** (fluorescence background removal).
2. **Standard Normal Variate (SNV) Normalization** (scatter correction and scaling).

---

## 4. Required Provenance & Metadata Specifications

Each reference entry MUST be accompanied by structured provenance metadata.

### Mandatory Metadata Fields:
1. `reference_id`: Unique identifier string (e.g. `REF-PARACETAMOL-USP-2026`).
2. `drug_name`: Official international nonproprietary name (INN) of the active ingredient (e.g. `Paracetamol`).
3. `manufacturer`: Name of the pharmaceutical manufacturer or certified reference provider (e.g. `USP / EP Reference Standards`).
4. `dosage_form`: Physical dosage form (e.g. `Tablet 500mg`, `Oral Powder`, `API Bulk`).
5. `source`: Name of accredited laboratory or institution supplying the reference (e.g. `Central Quality Control Lab`).
6. `source_url`: URL, DOI, or official document registry link verifying the origin.
7. `collection_date`: Date of acquisition (`YYYY-MM-DD`).
8. `spectrometer_information`: Model and specifications of spectrometer used (e.g. `785nm Portable Raman Spectrometer`).
9. `laser_wavelength`: Excitation laser wavelength (e.g. `785 nm`).
10. `preprocessing_method`: Preprocessing applied prior to storage (e.g. `SNV + 5th Polynomial Baseline`).
11. `notes`: Additional notes or batch identification numbers.

---

## 5. Directory Structure & Files

- `README.md`: Technical specification document (this file).
- `reference_metadata_template.csv`: Standardized metadata template CSV.
- `validate_reference.py`: Automatic verification & validation engine for reference datasets.
