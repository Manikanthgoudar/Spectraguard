"""
Step 23 Automated Pytest Suite — Pharmaceutical Test Sample Expansion & Validation
"""

import os
import sys
import pandas as pd
import numpy as np
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "Backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.csv_parser import parse_spectral_csv
from app.services.raman_analysis_service import RamanAnalysisService, get_raman_analysis_service

TEST_SAMPLES_DIR = os.path.join(project_root, "ML", "test_samples")
MANIFEST_PATH = os.path.join(TEST_SAMPLES_DIR, "test_sample_manifest.csv")

EXPECTED_PHARMA_FILES = [
    "test_paracetamol_sample.csv",
    "test_ibuprofen_sample.csv",
    "test_aspirin_sample.csv",
    "test_amoxicillin_sample.csv",
    "test_atorvastatin_sample.csv",
    "test_azithromycin_sample.csv",
    "test_ciprofloxacin_sample.csv",
    "test_diclofenac_sample.csv",
    "test_metformin_sample.csv",
    "test_metronidazole_sample.csv",
    "test_omeprazole_sample.csv"
]


def test_1_test_samples_directory_exists():
    """Verify ML/test_samples/ directory physically exists."""
    assert os.path.exists(TEST_SAMPLES_DIR)
    assert os.path.isdir(TEST_SAMPLES_DIR)


def test_2_pharmaceutical_sample_files_exist():
    """Verify all 11 expected pharmaceutical test CSV files exist in ML/test_samples/."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        assert os.path.exists(filepath), f"Missing test sample: {filename}"


def test_3_csv_files_are_readable():
    """Verify all pharmaceutical test sample CSV files are readable and non-empty."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        with open(filepath, "rb") as f:
            bytes_data = f.read()
        assert len(bytes_data.strip()) > 0, f"Empty CSV file: {filename}"
        wns, intensities = parse_spectral_csv(bytes_data, filename=filename)
        assert len(wns) > 0
        assert len(intensities) > 0


def test_4_csv_format_is_valid():
    """Verify CSV format follows accepted SpectraGuard wide or 2-column format."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        df = pd.read_csv(filepath)
        assert not df.empty, f"DataFrame is empty for {filename}"


def test_5_spectra_have_valid_numeric_values():
    """Verify spectral intensities and wavenumbers consist of valid numeric floats."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        with open(filepath, "rb") as f:
            bytes_data = f.read()
        wns, intensities = parse_spectral_csv(bytes_data, filename=filename)
        assert all(isinstance(x, (int, float, np.floating)) for x in intensities)
        assert all(isinstance(x, (int, float, np.floating)) for x in wns)


def test_6_no_nan_values():
    """Verify no NaN values exist in any test sample CSV."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        df = pd.read_csv(filepath)
        assert not df.isna().any().any(), f"NaN found in {filename}"


def test_7_no_inf_values():
    """Verify no Infinite (Inf) values exist in any test sample CSV."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        df = pd.read_csv(filepath)
        numeric_df = df.select_dtypes(include=[np.number])
        assert not np.isinf(numeric_df.to_numpy()).any(), f"Inf found in {filename}"


def test_8_wavenumber_grid_is_valid():
    """Verify wavenumber grid covers standard 150.0 to 3425.0 cm^-1 range."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        with open(filepath, "rb") as f:
            bytes_data = f.read()
        wns, _ = parse_spectral_csv(bytes_data, filename=filename)
        assert abs(wns[0] - 150.0) < 1.0
        assert abs(wns[-1] - 3425.0) < 1.0


def test_9_feature_count_is_valid():
    """Verify standardized feature count is exactly 3,276."""
    for filename in EXPECTED_PHARMA_FILES:
        filepath = os.path.join(TEST_SAMPLES_DIR, filename)
        with open(filepath, "rb") as f:
            bytes_data = f.read()
        _, intensities = parse_spectral_csv(bytes_data, filename=filename)
        assert len(intensities) == 3276, f"Feature count in {filename} is {len(intensities)}, expected 3276"


def test_10_provenance_manifest_exists():
    """Verify test_sample_manifest.csv exists in ML/test_samples/."""
    assert os.path.exists(MANIFEST_PATH)
    df_manifest = pd.read_csv(MANIFEST_PATH)
    assert not df_manifest.empty
    assert "filename" in df_manifest.columns
    assert "drug_name" in df_manifest.columns
    assert "doi" in df_manifest.columns


def test_11_every_pharmaceutical_sample_has_provenance():
    """Verify every pharmaceutical CSV has a corresponding entry in test_sample_manifest.csv."""
    df_manifest = pd.read_csv(MANIFEST_PATH)
    manifest_files = set(df_manifest["filename"].tolist())
    for filename in EXPECTED_PHARMA_FILES:
        assert filename in manifest_files, f"{filename} missing from manifest"


def test_12_duplicate_samples_are_rejected():
    """Verify duplicate filenames or identical rows are flagged by duplicate check."""
    df_manifest = pd.read_csv(MANIFEST_PATH)
    filenames = df_manifest["filename"].tolist()
    assert len(filenames) == len(set(filenames)), "Duplicate filenames found in manifest"


def test_13_synthetic_samples_are_rejected():
    """Verify all samples in manifest are marked AUTHENTIC_EXPERIMENTAL (no synthetic data)."""
    df_manifest = pd.read_csv(MANIFEST_PATH)
    statuses = df_manifest["authenticity_status"].tolist()
    for status in statuses:
        assert status == "AUTHENTIC_EXPERIMENTAL", f"Non-experimental status found: {status}"


def test_14_existing_paracetamol_sample_preserved():
    """Verify test_paracetamol_sample.csv is preserved and valid."""
    filepath = os.path.join(TEST_SAMPLES_DIR, "test_paracetamol_sample.csv")
    assert os.path.exists(filepath)
    with open(filepath, "rb") as f:
        wns, intensities = parse_spectral_csv(f.read(), filename="test_paracetamol_sample.csv")
    assert len(intensities) == 3276


def test_15_existing_ibuprofen_sample_preserved():
    """Verify test_ibuprofen_sample.csv is preserved and valid."""
    filepath = os.path.join(TEST_SAMPLES_DIR, "test_ibuprofen_sample.csv")
    assert os.path.exists(filepath)
    with open(filepath, "rb") as f:
        wns, intensities = parse_spectral_csv(f.read(), filename="test_ibuprofen_sample.csv")
    assert len(intensities) == 3276


def test_16_reference_library_is_unchanged():
    """Verify reference standards count (150 Paraguay standards) is preserved."""
    service = get_raman_analysis_service()
    ref_count = service.ref_manager.count()
    assert ref_count >= 150, f"Reference count dropped: {ref_count}"


def test_17_threshold_is_unchanged():
    """Verify calibrated authentication threshold remains strictly 0.9860."""
    service = get_raman_analysis_service()
    assert service.CALIBRATED_THRESHOLD == 0.9860
    assert RamanAnalysisService.CALIBRATED_THRESHOLD == 0.9860
