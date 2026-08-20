# Raman Spectroscopy Machine Learning Pipeline

This directory contains the machine learning pipeline for Raman spectroscopy analysis within the SpectraGuard project.

## Directory Structure & Guidelines

- **`dataset/`**: Contains the raw Raman dataset (`raman_spectra_api_compounds.csv`).
  - **Important Rule**: The raw dataset in `dataset/` **must not be modified**, edited, or altered in any way.
- **`preprocessing/`**: Contains scripts and functions for data cleaning, spectral normalization, and feature extraction.
- **`models/`**: Dedicated directory for saving and loading trained model artifacts and architectures.
- **`training/`**: Contains model training pipelines, cross-validation scripts, and hyperparameter tuning logic.
- **`results/`**: Reserved for model evaluation metrics, performance plots, confusion matrices, and validation logs.

All preprocessing steps, trained models, training scripts, and results are maintained strictly separately from the raw dataset.
