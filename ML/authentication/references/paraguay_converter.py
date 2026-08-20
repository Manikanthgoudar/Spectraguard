"""
Paraguay OTC Raman Dataset Converter & Reference Integration Pipeline - SpectraGuard ML

Converts raw Raman spectra from the official Paraguay OTC dataset (Zenodo record 11106420)
into the SpectraGuard standardized reference format:
- Grid: 150.0 to 3425.0 cm⁻¹ (1.0 cm⁻¹ step spacing, 3,276 uniform intensity features)
- Baseline Correction: 5th-degree polynomial fit
- Normalization: Standard Normal Variate (SNV)
- Provenance & Metadata: Full preservation of drug identity, brand/trademark codes, instrument info, and DOI.
- Unmeasured Region Handling: Zero-padding for 3200.0-3425.0 cm⁻¹ to avoid peak fabrication.
- Reference Status: Labeled strictly as AUTHENTIC_REFERENCE.
"""

import os
import sys

# Ensure project root (spectra directory) is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

from ML.preprocessing.preprocess import RamanPreprocessor
from ML.authentication.references.validate_reference import ReferenceValidator


class ParaguayOTCConverter:
    """
    Conversion engine for the Paraguay OTC Raman Spectroscopy Dataset.
    """

    TARGET_START_WN = 150.0
    TARGET_END_WN = 3425.0
    TARGET_N_FEATURES = 3276

    def __init__(self, raw_dir: str):
        self.raw_dir = raw_dir
        self.target_wavenumbers = np.linspace(
            self.TARGET_START_WN, self.TARGET_END_WN, self.TARGET_N_FEATURES, dtype=np.float64
        )
        self.feature_cols = [f"{wn:.1f}" for wn in self.target_wavenumbers]

    def _load_raw_drug_file(
        self,
        drug_filename: str,
        trademark_filename: str,
        drug_name: str,
        id_prefix: str
    ) -> List[Dict[str, Any]]:
        """
        Load and parse a drug's intensity spreadsheet and trademark mapping file.
        """
        drug_path = os.path.join(self.raw_dir, drug_filename)
        trademark_path = os.path.join(self.raw_dir, trademark_filename)

        if not os.path.exists(drug_path) or not os.path.exists(trademark_path):
            raise FileNotFoundError(f"Missing raw data files: {drug_path} or {trademark_path}")

        df_drug = pd.read_excel(drug_path)
        df_trademark = pd.read_excel(trademark_path)

        # First column is 'Raman Shift'
        shift_col = df_drug.columns[0]
        raw_shifts = df_drug[shift_col].to_numpy(dtype=np.float64)

        # Remaining columns are spectra
        spec_cols_drug = [c for c in df_drug.columns if c != shift_col]
        spec_cols_trade = [c for c in df_trademark.columns if c != shift_col]

        records = []
        for i in range(len(spec_cols_drug)):
            col_d = spec_cols_drug[i]
            col_t = spec_cols_trade[i] if i < len(spec_cols_trade) else "N/A"
            
            raw_intensities = df_drug[col_d].to_numpy(dtype=np.float64)

            # Clean brand code (strip trailing .1, .2 pandas suffixes if present)
            brand_code = col_t.split('.')[0] if '.' in col_t and col_t.split('.')[0].replace('-', '').isalnum() else col_t

            ref_id = f"REF-PARAGUAY-{id_prefix}-{i+1:03d}"

            records.append({
                "reference_id": ref_id,
                "drug_name": drug_name,
                "brand_or_trademark": brand_code,
                "original_col_name": col_d,
                "raw_shifts": raw_shifts,
                "raw_intensities": raw_intensities,
            })

        return records

    def resample_spectrum(self, raw_shifts: np.ndarray, raw_intensities: np.ndarray) -> np.ndarray:
        """
        Resample raw spectrum to SpectraGuard grid (150.0 to 3425.0 cm⁻¹, 3,276 points).
        
        Linear interpolation is applied within the measured range (148.32 - 3199.44 cm⁻¹).
        The unmeasured high-wavenumber region (3200.0 - 3425.0 cm⁻¹) is set to 0.0 to avoid
        fabricating unmeasured spectral peaks.
        """
        max_measured_wn = float(raw_shifts.max())

        # Interpolate within measured range
        resampled = np.interp(
            self.target_wavenumbers,
            raw_shifts,
            raw_intensities,
            left=raw_intensities[0],   # Flat boundary below 148.32 cm⁻¹ (small 1.68 cm⁻¹ gap)
            right=0.0                  # Zero padding above 3199.44 cm⁻¹
        )

        # Explicitly zero out any wavenumbers > max_measured_wn
        unmeasured_mask = self.target_wavenumbers > max_measured_wn
        resampled[unmeasured_mask] = 0.0

        return resampled

    def process_and_convert(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute full extraction, grid resampling, baseline correction, and SNV normalization.
        """
        drug_configs = [
            ("Paracetamol.xlsx", "Paracetamol-trademark.xlsx", "Paracetamol", "PARA"),
            ("Ibuprofen.xlsx", "Ibuprofen-trademark.xlsx", "Ibuprofen", "IBU"),
            ("Acetylsalicylic-acid.xlsx", "Acetylsalicylic-acid-trademark.xlsx", "Acetylsalicylic Acid", "ASA"),
        ]

        all_raw_records = []
        for d_file, t_file, d_name, prefix in drug_configs:
            recs = self._load_raw_drug_file(d_file, t_file, d_name, prefix)
            all_raw_records.extend(recs)

        print(f"-> Extracted {len(all_raw_records)} raw spectral records from Paraguay files.")

        # Step 1: Resample all spectra to target grid
        X_resampled = np.zeros((len(all_raw_records), self.TARGET_N_FEATURES), dtype=np.float64)
        for idx, rec in enumerate(all_raw_records):
            X_resampled[idx] = self.resample_spectrum(rec["raw_shifts"], rec["raw_intensities"])

        # Step 2: Preprocess using SpectraGuard RamanPreprocessor (5th degree poly baseline + SNV)
        preprocessor = RamanPreprocessor(poly_degree=5)
        preprocessor.fit_wavenumbers(self.feature_cols)

        # Baseline correction
        X_baseline_subtracted, _ = preprocessor.correct_baseline(X_resampled)

        # SNV normalization
        X_snv = preprocessor.normalize_snv(X_baseline_subtracted)

        # Step 3: Build DataFrame with Metadata and Feature Columns
        meta_rows = []
        for idx, rec in enumerate(all_raw_records):
            meta = {
                "reference_id": rec["reference_id"],
                "drug_name": rec["drug_name"],
                "brand_or_trademark": rec["brand_or_trademark"],
                "source": "National University of Asunción (FACEN / FP-UNA), Paraguay",
                "source_url": "https://zenodo.org/records/11106420",
                "doi": "10.5281/zenodo.11106420",
                "spectrometer_information": "BWTEK iRaman 785s Portable Spectrometer",
                "laser_wavelength": "785 nm",
                "laser_power": "50%",
                "exposure_time": "1.0s x 10 accumulations",
                "acquisition_date": "2024-04-05",
                "license": "CC BY 4.0",
                "sample_status": "AUTHENTIC_REFERENCE",
                "reference_status": "ACTIVE",
                "preprocessing_method": "5th-Degree Polynomial Baseline Subtraction + SNV Normalization",
                "out_of_range_handling": "Zero-padded unmeasured region (3200.0-3425.0 cm⁻¹)"
            }
            meta_rows.append(meta)

        df_meta = pd.DataFrame(meta_rows)
        df_feats = pd.DataFrame(X_snv, columns=self.feature_cols)

        df_full = pd.concat([df_meta, df_feats], axis=1)

        summary = {
            "total_spectra": len(df_full),
            "spectra_per_drug": df_full["drug_name"].value_counts().to_dict(),
            "spectra_per_brand": df_full["brand_or_trademark"].value_counts().to_dict(),
            "target_n_features": self.TARGET_N_FEATURES,
            "target_wavenumber_range": [self.TARGET_START_WN, self.TARGET_END_WN]
        }

        return df_full, summary


def run_paraguay_conversion():
    """
    Run conversion pipeline and export paraguay_otc_reference.csv.
    """
    print("=" * 70)
    print("      PARAGUAY OTC RAMAN DATASET CONVERSION & INTEGRATION      ")
    print("=" * 70)

    raw_dir = os.path.join(current_dir, "raw", "paraguay_otc")
    output_csv = os.path.join(current_dir, "paraguay_otc_reference.csv")

    converter = ParaguayOTCConverter(raw_dir)
    df_converted, summary = converter.process_and_convert()

    print(f"-> Exporting converted reference dataset to: {output_csv}")
    df_converted.to_csv(output_csv, index=False)

    print("\n" + "=" * 70)
    print("CONVERSION SUMMARY:")
    print(f"  - Total spectra converted: {summary['total_spectra']}")
    for drug, count in summary['spectra_per_drug'].items():
        print(f"    * {drug}: {count} spectra")
    print(f"  - Wavenumber grid: {summary['target_wavenumber_range'][0]} to {summary['target_wavenumber_range'][1]} cm^-1")
    print(f"  - Feature count per spectrum: {summary['target_n_features']}")
    print("=" * 70)


if __name__ == "__main__":
    run_paraguay_conversion()
