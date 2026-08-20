# SpectraGuard Real Reference-Derived Integration Test Sample Library

This directory contains real reference-derived sample CSV files for all 11 active pharmaceutical drugs in the SpectraGuard reference database.

> [!IMPORTANT]
> **Provenance & Usage Disclaimer**:
> These CSV files are reference-derived integration test samples created by exporting existing validated Raman reference spectra from MySQL. They are used to verify the end-to-end application pipeline and are not independent validation samples. No synthetic spectra, noise, or peak modifications were applied.

---

## Directory Structure & Available Samples

| Drug Name | Sample CSV Path | Source Reference ID | Dataset / Provenance |
| :--- | :--- | :--- | :--- |
| **Acetylsalicylic Acid** | `sample_test/acetylsalicylic_acid/sample_acetylsalicylic_acid.csv` | `REF-PARAGUAY-ASA-001` | Paraguay OTC Reference |
| **Amoxicillin** | `sample_test/amoxicillin/sample_amoxicillin.csv` | `REF-STEP21-AMOX-001` | Validated Amoxicillin Standard |
| **Atorvastatin** | `sample_test/atorvastatin/sample_atorvastatin.csv` | `REF-STEP21-ATOR-001` | Validated Atorvastatin Standard |
| **Azithromycin** | `sample_test/azithromycin/sample_azithromycin.csv` | `REF-STEP21-AZITH-001` | Validated Azithromycin Standard |
| **Ciprofloxacin** | `sample_test/ciprofloxacin/sample_ciprofloxacin.csv` | `REF-STEP21-CIPRO-001` | Validated Ciprofloxacin Standard |
| **Diclofenac** | `sample_test/diclofenac/sample_diclofenac.csv` | `REF-STEP21-DICLO-001` | Validated Diclofenac Standard |
| **Ibuprofen** | `sample_test/ibuprofen/sample_ibuprofen.csv` | `REF-PARAGUAY-IBU-001` | Paraguay OTC Reference |
| **Metformin** | `sample_test/metformin/sample_metformin.csv` | `REF-STEP21-METF-001` | Validated Metformin Standard |
| **Metronidazole** | `sample_test/metronidazole/sample_metronidazole.csv` | `REF-STEP21-METRO-001` | Validated Metronidazole Standard |
| **Omeprazole** | `sample_test/omeprazole/sample_omeprazole.csv` | `REF-STEP21-OMEP-001` | Validated Omeprazole Standard |
| **Paracetamol** | `sample_test/paracetamol/sample_paracetamol.csv` | `REF-PARAGUAY-PARA-001` | Paraguay OTC Reference |

---

## How to Test via Flutter UI / Backend API

### 1. Auto Identification Mode
1. Open the **Upload Spectra** screen in the SpectraGuard Flutter application.
2. Select any CSV sample file from `sample_test/<drug_name>/sample_<drug_name>.csv`.
3. Leave target drug set to **Auto Identification**.
4. Tap **Run Analysis**.
5. **Expected Result**: System automatically detects target drug with similarity score >= 0.9860 (`AUTHENTIC_REFERENCE_MATCH`).

### 2. Selected Drug Verification Mode
1. Select target drug (e.g., *Acetylsalicylic Acid*).
2. Upload corresponding sample CSV (`sample_test/acetylsalicylic_acid/sample_acetylsalicylic_acid.csv`).
3. Tap **Run Analysis**.
4. **Expected Result**: `AUTHENTIC_REFERENCE_MATCH` with similarity score >= 0.9860.
5. Next, try uploading the *Acetylsalicylic Acid* CSV while selecting a different target drug (e.g., *Azithromycin*).
6. **Expected Result**: System returns `UNKNOWN` (unmatched spectral profile), preventing false authentication.
