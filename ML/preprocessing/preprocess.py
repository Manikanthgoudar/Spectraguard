"""
Raman Spectral Preprocessing Module - SpectraGuard ML Pipeline (Step 3)

This script performs reproducible Raman spectral preprocessing on raw API compound spectra:
1. Duplicate spectrum detection & removal from working set.
2. Baseline correction using a 5th-degree polynomial fit (with normalized wavenumbers for stability).
3. Standard Normal Variate (SNV) normalization to eliminate additive scatter offsets and multiplicative scaling.
4. Exporting processed features, labels, preprocessing report, and comparison visualization.

Author: Antigravity AI Team / SpectraGuard Project
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class RamanPreprocessor:
    """
    Reusable Raman Spectral Preprocessor class.
    
    Encapsulates polynomial baseline correction and Standard Normal Variate (SNV)
    normalization for processing training sets or single uploaded spectra in production.
    """

    def __init__(self, poly_degree: int = 5):
        """
        Initialize the preprocessor.
        
        Parameters:
        -----------
        poly_degree : int (default=5)
            Polynomial degree for Raman fluorescence baseline estimation.
        """
        self.poly_degree = poly_degree
        self.wavenumbers = None
        self.wn_scaled = None
        self.wn_min = None
        self.wn_max = None

    def fit_wavenumbers(self, feature_cols: list):
        """
        Extract and scale wavenumber values from column names.
        
        Parameters:
        -----------
        feature_cols : list
            List of column names representing Raman shift values (e.g. '150.0' to '3425.0').
        """
        self.wavenumbers = np.array([float(col) for col in feature_cols], dtype=np.float64)
        self.wn_min = float(self.wavenumbers.min())
        self.wn_max = float(self.wavenumbers.max())
        
        # Rescale wavenumbers to interval [-1.0, 1.0] for numerically stable polynomial fitting
        self.wn_scaled = 2.0 * (self.wavenumbers - self.wn_min) / (self.wn_max - self.wn_min) - 1.0

    def remove_duplicates(self, df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
        """
        Remove exact duplicate spectra based solely on intensity feature values.
        Does NOT alter the source dataset file.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input dataframe containing intensity features and labels.
        feature_cols : list
            List of intensity feature column headers.
            
        Returns:
        --------
        pd.DataFrame
            Cleaned dataframe with duplicate rows removed.
        """
        duplicate_mask = df.duplicated(subset=feature_cols, keep='first')
        num_duplicates = duplicate_mask.sum()
        df_clean = df[~duplicate_mask].reset_index(drop=True)
        return df_clean, int(num_duplicates)

    def correct_baseline(self, X: np.ndarray) -> tuple:
        """
        Polynomial baseline correction.
        Fits a 5th-degree polynomial to each spectrum across normalized wavenumbers
        and subtracts the calculated baseline drift.
        
        Parameters:
        -----------
        X : np.ndarray of shape (N, P)
            2D matrix of raw spectral intensities (N spectra, P features).
            
        Returns:
        --------
        tuple (X_corrected, baselines)
            X_corrected : np.ndarray (N, P) - Baseline subtracted spectra.
            baselines : np.ndarray (N, P) - Estimated polynomial baselines.
        """
        if self.wn_scaled is None:
            raise ValueError("Wavenumbers have not been fitted. Call fit_wavenumbers first.")

        # X is (N, P), np.polyfit fits along columns when 2D array is passed (P, N)
        # Fit 5th degree polynomial across normalized wavenumbers for all spectra simultaneously
        coeffs = np.polyfit(self.wn_scaled, X.T, deg=self.poly_degree) # Shape: (poly_degree + 1, N)
        
        # Evaluate baseline using np.polyval (Shape: (P, N)), then transpose to (N, P)
        baselines = np.polyval(coeffs, self.wn_scaled[:, None]).T
        
        # Subtract estimated baseline
        X_corrected = X - baselines
        return X_corrected, baselines

    def normalize_snv(self, X: np.ndarray) -> np.ndarray:
        """
        Standard Normal Variate (SNV) Normalization.
        Standardizes each individual spectrum row-wise to zero mean and unit variance.
        
        Formula: y_snv = (y - mean(y)) / std(y)
        
        Why SNV is chosen for Raman spectra:
        SNV effectively removes multiplicative scaling errors caused by path length / sample thickness /
        focusing variations and eliminates additive background scatter, placing all spectra on a common
        comparable scale without altering spectral peak signatures.
        
        Parameters:
        -----------
        X : np.ndarray of shape (N, P)
            Spectral intensity matrix (raw or baseline-corrected).
            
        Returns:
        --------
        np.ndarray of shape (N, P)
            SNV-normalized spectra.
        """
        means = np.mean(X, axis=1, keepdims=True)
        stds = np.std(X, axis=1, keepdims=True, ddof=1)
        
        # Avoid potential division by zero for flat spectra
        stds[stds == 0.0] = 1.0
        
        X_snv = (X - means) / stds
        return X_snv

    def transform(self, X: np.ndarray, feature_cols: list) -> np.ndarray:
        """
        Apply full preprocessing pipeline to new raw input matrix X.
        
        Parameters:
        -----------
        X : np.ndarray (N, P)
            Raw intensity matrix.
        feature_cols : list
            List of feature column names.
            
        Returns:
        --------
        np.ndarray (N, P)
            Fully preprocessed (baseline corrected + SNV normalized) spectra.
        """
        if self.wavenumbers is None or len(self.wavenumbers) != len(feature_cols):
            self.fit_wavenumbers(feature_cols)
        X_base, _ = self.correct_baseline(X)
        X_snv = self.normalize_snv(X_base)
        return X_snv


def run_preprocessing_pipeline():
    """
    Main function executing Step 3 Raman spectral preprocessing.
    Loads raw CSV, cleans working copy, performs baseline correction & SNV normalization,
    exports processed datasets, report, and comparison figure.
    """
    print("=" * 60)
    print("      SPECTRAGUARD ML - STEP 3 RAMAN PREPROCESSING")
    print("=" * 60)
    
    # Path configuration
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_csv_path = os.path.join(base_dir, "dataset", "raman_spectra_api_compounds.csv")
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    processed_features_path = os.path.join(results_dir, "processed_raman_features.csv")
    processed_labels_path = os.path.join(results_dir, "processed_labels.csv")
    report_path = os.path.join(results_dir, "preprocessing_report.txt")
    plot_path = os.path.join(results_dir, "preprocessing_comparison.png")

    print(f"-> Loading raw dataset from: {raw_csv_path}")
    start_time = time.time()
    raw_df = pd.read_csv(raw_csv_path)
    original_num_spectra = len(raw_df)
    
    # Separate features and label column
    label_col = 'label'
    feature_cols = [c for c in raw_df.columns if c != label_col]
    num_features = len(feature_cols)
    
    print(f"-> Raw dataset loaded: {original_num_spectra} spectra, {num_features} Raman features.")
    
    # Initialize preprocessor
    poly_degree = 5
    preprocessor = RamanPreprocessor(poly_degree=poly_degree)
    preprocessor.fit_wavenumbers(feature_cols)
    
    # Step 1: Remove exact duplicate spectra from working copy only
    clean_df, duplicates_removed = preprocessor.remove_duplicates(raw_df, feature_cols)
    final_num_spectra = len(clean_df)
    print(f"-> Duplicate spectra removed from working set: {duplicates_removed}")
    print(f"-> Working dataset size: {final_num_spectra} spectra.")

    # Extract X (intensities) and y (labels)
    X_raw = clean_df[feature_cols].values.astype(np.float64)
    y = clean_df[label_col].copy()
    
    # Step 2: Baseline Correction
    print(f"-> Performing polynomial baseline correction (Degree={poly_degree})...")
    X_baseline_corrected, baselines = preprocessor.correct_baseline(X_raw)
    
    # Step 3: SNV Normalization
    print("-> Performing Standard Normal Variate (SNV) vector normalization...")
    X_normalized = preprocessor.normalize_snv(X_baseline_corrected)

    # Step 4: Save processed feature matrix and labels separately
    print(f"-> Saving processed features to: {processed_features_path}")
    df_features = pd.DataFrame(X_normalized, columns=feature_cols)
    df_features.to_csv(processed_features_path, index=False)
    
    print(f"-> Saving processed labels to: {processed_labels_path}")
    df_labels = pd.DataFrame({label_col: y})
    df_labels.to_csv(processed_labels_path, index=False)

    # Class distribution calculation
    class_counts = y.value_counts()
    num_classes = len(class_counts)
    
    # Step 5: Save Preprocessing Report
    print(f"-> Generating preprocessing report at: {report_path}")
    report_lines = [
        "========================================================",
        "     SPECTRAGUARD ML - PREPROCESSING REPORT (STEP 3)    ",
        "========================================================",
        "",
        f"Input Dataset Path: ML/dataset/raman_spectra_api_compounds.csv",
        f"Original Number of Spectra: {original_num_spectra}",
        f"Duplicate Spectra Removed (Working Dataset Only): {duplicates_removed}",
        f"Final Number of Spectra: {final_num_spectra}",
        f"Number of Raman Features: {num_features}",
        f"Raman Shift Range: {preprocessor.wn_min:.1f} cm^-1 to {preprocessor.wn_max:.1f} cm^-1",
        f"Baseline Correction Method: Polynomial Baseline Correction (Degree {poly_degree})",
        f"Polynomial Degree: {poly_degree}",
        f"Normalization Method: Standard Normal Variate (SNV)",
        f"Number of Unique Compound Classes: {num_classes}",
        "",
        "--------------------------------------------------------",
        "         CLASS DISTRIBUTION AFTER DUPLICATE REMOVAL     ",
        "--------------------------------------------------------"
    ]
    
    for label, count in class_counts.items():
        pct = (count / final_num_spectra) * 100
        report_lines.append(f" - {label}: {count} samples ({pct:.2f}%)")
        
    report_lines.extend([
        "",
        "========================================================",
        f"Report Generated Successfully in {time.time() - start_time:.2f} seconds.",
        "========================================================"
    ])
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # Step 6: Create Comparison Visualization
    print(f"-> Creating comparison visualization plot at: {plot_path}")
    
    # Select 4 representative spectra from distinct compound classes
    sample_indices = []
    unique_compounds = ['Acetone', 'Ethanol', 'Toluene', 'Cyclohexane']
    for cmp in unique_compounds:
        matches = clean_df.index[clean_df[label_col] == cmp].tolist()
        if matches:
            sample_indices.append(matches[0])
            
    # Fallback if specific classes aren't found
    if len(sample_indices) < 4:
        sample_indices = list(range(4))

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    wavenumbers = preprocessor.wavenumbers

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # Subplot 1: Raw Spectra
    for idx, col in zip(sample_indices, colors):
        compound_name = y.iloc[idx]
        axes[0].plot(wavenumbers, X_raw[idx], label=f"{compound_name} (Raw)", color=col, alpha=0.85, linewidth=1.2)
        axes[0].plot(wavenumbers, baselines[idx], color=col, linestyle='--', alpha=0.5, linewidth=1.0)
    axes[0].set_title("1. Raw Raman Spectra with Estimated 5th-Degree Polynomial Baselines", fontsize=12, fontweight='bold')
    axes[0].set_ylabel("Raw Intensity (a.u.)", fontsize=10)
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].grid(True, linestyle=':', alpha=0.6)

    # Subplot 2: Baseline Corrected Spectra
    for idx, col in zip(sample_indices, colors):
        compound_name = y.iloc[idx]
        axes[1].plot(wavenumbers, X_baseline_corrected[idx], label=f"{compound_name}", color=col, alpha=0.85, linewidth=1.2)
    axes[1].set_title("2. Baseline-Corrected Raman Spectra (Fluorescence Background Removed)", fontsize=12, fontweight='bold')
    axes[1].set_ylabel("Corrected Intensity (a.u.)", fontsize=10)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(True, linestyle=':', alpha=0.6)

    # Subplot 3: SNV Normalized Spectra
    for idx, col in zip(sample_indices, colors):
        compound_name = y.iloc[idx]
        axes[2].plot(wavenumbers, X_normalized[idx], label=f"{compound_name}", color=col, alpha=0.85, linewidth=1.2)
    axes[2].set_title("3. Standard Normal Variate (SNV) Normalized Raman Spectra", fontsize=12, fontweight='bold')
    axes[2].set_xlabel("Raman Shift (cm⁻¹)", fontsize=11, fontweight='bold')
    axes[2].set_ylabel("SNV Intensity (Standardized)", fontsize=10)
    axes[2].legend(loc='upper right', fontsize=9)
    axes[2].grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    elapsed_total = time.time() - start_time

    # Step 7: Print required final summary
    print("\n" + "=" * 60)
    print("STEP 3 PREPROCESSING COMPLETED")
    print("=" * 60)
    print(f"- Number of input spectra: {original_num_spectra}")
    print(f"- Duplicate spectra removed: {duplicates_removed}")
    print(f"- Number of output spectra: {final_num_spectra}")
    print(f"- Number of features: {num_features}")
    print(f"- Number of classes: {num_classes}")
    print(f"- Preprocessing methods used: Polynomial Baseline Correction (Degree 5) + Standard Normal Variate (SNV)")
    print("- Files created:")
    print(f"  1. {os.path.relpath(processed_features_path, base_dir)}")
    print(f"  2. {os.path.relpath(processed_labels_path, base_dir)}")
    print(f"  3. {os.path.relpath(report_path, base_dir)}")
    print(f"  4. {os.path.relpath(plot_path, base_dir)}")
    print(f"  5. ML/preprocessing/preprocess.py")
    print(f"Pipeline executed cleanly in {elapsed_total:.2f} seconds.")
    print("=" * 60)


if __name__ == "__main__":
    run_preprocessing_pipeline()
