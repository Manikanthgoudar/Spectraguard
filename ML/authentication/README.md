# SpectraGuard Pharmaceutical Raman Authentication Architecture

## 1. Overview & Architectural Role

The **SpectraGuard** system employs a multi-tiered approach for analyzing Raman spectra of chemical and pharmaceutical substances.

### Distinction Between Compound Identification & Product Authentication

1. **Compound Identification Layer (Existing ML Model)**
   - **Role**: Predicts which of the 32 known chemical compound classes a given spectrum belongs to (e.g., Acetone, Cyclohexane, Toluene, Paracetamol).
   - **Mechanism**: A 32-class Support Vector Machine (SVM) operating on 43 PCA components extracted from 3,276 preprocessed wavenumber features.
   - **Scope**: Identifies *chemical identity only*. It does **NOT** evaluate product purity, formulation accuracy, batch authenticity, or Genuine vs. Counterfeit status.

2. **Pharmaceutical Reference & Authentication Layer (New Layer)**
   - **Role**: Compares a high-resolution, processed Raman spectrum against an authentic reference standard for a specific target drug formulation.
   - **Mechanism**: Calculates a quantitative spectral similarity score (Cosine Similarity) between the preprocessed test spectrum vector and a registered authentic reference spectrum vector.
   - **Scope**: Measures physical/spectral fidelity against known reference standards to establish a baseline for verification.

---

## 2. End-to-End Authentication Architecture Pipeline

```
┌─────────────────────────────────────────┐
│     Uploaded Raw Raman Spectrum         │
│     (CSV with Wavenumber & Intensity)   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│       Spectral Preprocessing            │
│  - Polynomial Baseline Correction (5th) │
│  - Standard Normal Variate (SNV)        │
│  - Resampling to 3,276 Wavenumbers      │
│    (150.0 cm⁻¹ to 3425.0 cm⁻¹)          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│     Compound Identification Layer       │
│  - StandardScaler & PCA Transform       │
│  - 32-Class SVM Classifier              │
│  - Predicted Compound & Confidence      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│   Pharmaceutical Reference Comparison   │
│  - Retrieve Reference Standard Vector   │
│  - Feature Range & Order Validation     │
│  - Compute Spectral Similarity Score    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│       Spectral Similarity Score         │
│  - Cosine Similarity Metric [0.0 - 1.0] │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│       Authentication Decision           │
│  (Requires Empirical Decision Boundary   │
│   Fitted on Genuine vs Counterfeit Data)│
└─────────────────────────────────────────┘
```

---

## 3. Stages of the Pipeline

1. **Uploaded Raman Spectrum**: Input file containing spectral data points across wavenumber ranges.
2. **Same Preprocessing**: Apply identical preprocessing (5th-degree polynomial baseline subtraction, Standard Normal Variate SNV scaling, and feature alignment to 3,276 channels from 150.0 to 3425.0 cm⁻¹).
3. **Compound Identification**: Pass through scaler, PCA, and 32-class SVM model to determine chemical compound class and confidence score.
4. **Pharmaceutical Reference Comparison**: Fetch the verified reference spectral vector for the target drug from `ReferenceManager` and pass through `RamanAuthenticator`.
5. **Similarity / Anomaly Score**: Calculate Cosine Similarity metric quantifying spectral shape and peak ratio correlation between test and reference spectrum.
6. **Authentication Decision**: Compare the raw score against statistically validated boundaries once a verified dataset containing both authentic drugs and confirmed counterfeit formulations is collected.

---

## 4. Key Design Principles & Safeguards

- **No Fabricated Labels**: Genuine vs. Counterfeit labels are strictly prohibited without an empirical reference dataset of real vs. fake drug samples.
- **Raw Similarity Scoring**: The engine outputs pure numerical similarity scores alongside strict comparison statuses (`MATCH_COMPUTED`, `REFERENCE_NOT_AVAILABLE`, `INVALID_INPUT`).
- **Feature Preservation**: All spectral vectors must maintain exact length (3,276 channels) and wavenumber order (150.0 cm⁻¹ to 3425.0 cm⁻¹).
