# Step 15 Audit: SpectraGuard Pharmaceutical Reference Database Architecture

## 1. Overview & Audit Objectives
This document presents the detailed architectural audit of the pharmaceutical reference data pipeline in SpectraGuard, identifying current reference datasets, database models, ML reference manager mechanics, backend API endpoints, and Flutter frontend selection components.

---

## 2. Detailed Audit Findings

### 2.1 Current Reference Data & Database Structures
- **ML Authentic Reference Standard File**: `ML/authentication/references/paraguay_otc_reference.csv`
  - Total Reference Spectra: **150**
  - Current Reference Drugs: **3** (Paracetamol: 50, Ibuprofen: 50, Acetylsalicylic Acid: 50)
  - Features per Spectrum: **3,276** (Resampled to uniform grid 150.0–3425.0 cm⁻¹)
  - Preprocessing: 5th-Degree Polynomial Baseline Correction + Standard Normal Variate (SNV) Normalization
  - Provenance: National University of Asunción (FACEN / FP-UNA), Paraguay (Zenodo DOI: 10.5281/zenodo.11106420)
- **Database Schema**: `reference_spectra` table (`Backend/app/models/reference_spectra.py`)
  - Columns: `id`, `drug_name`, `generic_name`, `brand_name`, `strength`, `dosage_form`, `manufacturer`, `country`, `description`, `uses`, `storage_conditions`, `license_number`, `batch_reference`, `wavenumber_data` (JSON), `intensity_data` (JSON), `wavenumber_range`, `num_measurements`, `similarity_threshold`, `spectrum_info`, `source`, `added_by`, `created_at`.
- **In-Memory ML Reference Repository**: `ReferenceManager` (`ML/authentication/reference_manager.py`)
  - Loads reference spectra from `paraguay_otc_reference.csv` into `ReferenceRecord` dataclass objects on service initialization.
  - Maintains indexes by `reference_id` and normalized `drug_name`.

### 2.2 Metadata & Drug Naming Conventions
- **Reference Record Metadata**:
  - `reference_id`: Unique identifier (e.g. `REF-PARAGUAY-PARA-001`, `REF-PARAGUAY-IBU-001`, `REF-PARAGUAY-ASA-001`).
  - `drug_name`: INN drug name string (e.g., `Paracetamol`, `Ibuprofen`, `Acetylsalicylic Acid`).
  - `source_information`: Dict storing source URL, DOI, brand/trademark code, spectrometer info (`BWTEK iRaman 785s`).
  - `reference_status`: `ACTIVE` (or `ARCHIVED` / `DRAFT`).
- **Drug Name Normalization**:
  - `RamanAnalysisService.normalize_drug_name()` in `Backend/app/services/raman_analysis_service.py` uses `DRUG_NAME_MAPPING` dictionary to normalize common synonyms/aliases (e.g. `acetaminophen` -> `Paracetamol`, `aspirin` -> `Acetylsalicylic Acid`, `ibu` -> `Ibuprofen`).

### 2.3 Reference Retrieval & Authentication Mechanics
- **Active Reference Selection**:
  - `ReferenceManager.get_active_references_for_drug(drug_name)` queries all records with matching normalized drug name and `reference_status == 'ACTIVE'`.
- **Similarity Evaluation**:
  - `RamanAuthenticator.compare_with_reference()` computes raw Cosine Similarity between the preprocessed input spectrum (3,276 features) and all active candidate reference spectra for the target drug.
  - Returns the highest similarity candidate score and reference ID.
- **Authentication Decision Policy**:
  - Threshold: Strictly `0.9860` (calibrated in Step 11).
  - Score $\ge 0.9860 \implies$ `AUTHENTIC_REFERENCE_MATCH`
  - Score $< 0.9860 \implies$ `UNKNOWN`
  - No active reference found for target drug $\implies$ `REFERENCE_NOT_AVAILABLE`
  - Input invalid / missing $\implies$ `INVALID_INPUT`

### 2.4 API Request & Routing Flow
- **Endpoint**: `POST /api/analyze-raman` (`Backend/app/routers/raman_analysis.py`)
  - Form parameters: `file` (CSV bytes) and optional `drug_name` (string).
  - Delegates execution to `RamanAnalysisService.analyze_raman_spectrum(content, drug_name)`.
- **Existing Reference API Endpoints**:
  - `GET /reference`: Paginated list of reference spectra stored in database `reference_spectra` table.
  - Currently missing: Dedicated lightweight public endpoint `GET /reference/drugs` returning all unique active reference drug names directly from the active ML `ReferenceManager` / DB repository.

### 2.5 Hardcoded Restrictions Identified
1. **Frontend Flutter App** (`Frontend/spectra_app/lib/features/spectra/screens/upload_spectra_screen.dart`):
   - `_availableReferenceStandards` contains hardcoded list: `['Paracetamol', 'Ibuprofen', 'Acetylsalicylic Acid (Aspirin)']`.
   - Dropdown menu items and ChoiceChips render from this fixed list.
   - Text fields and default mode hardcoded to `'Paracetamol'`.
2. **Custom Drug Name Field Usage**:
   - The UI includes a "Custom" mode allowing manual input. However, if a user enters a drug without an active reference standard (e.g., `Amoxicillin`), the backend correctly returns `REFERENCE_NOT_AVAILABLE`. The audit confirms the backend does not fabricate or match invalid reference standards, but the frontend needs dynamic drug list fetching so users select active available standards.

---

## 3. Plan for Step 15 Reference Database Expansion
1. **Backend Dynamic Endpoint**: Implement `GET /reference/drugs` (or `GET /api/reference/drugs`) returning the list of active drugs currently registered in the reference manager / reference database.
2. **Reference Management Extension**: Ensure `ReferenceManager` exposes `get_available_drug_names()` dynamically.
3. **Reference Import Mechanism**: Extend reference data importer/loader to support registering additional authentic reference spectra with full 3,276-feature grid and metadata validation.
4. **Flutter Dynamic UI**: Update `UploadSpectraScreen` to fetch active drugs from `GET /reference/drugs` on load, showing a loading indicator, handling errors gracefully, and dynamically populating the dropdown / choice chips.
5. **Preservation**: Retain the 150 Paraguay OTC reference spectra, 0.9860 threshold, cosine similarity calculation, and UNKNOWN / REFERENCE_NOT_AVAILABLE policy.
