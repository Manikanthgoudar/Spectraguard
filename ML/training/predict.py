"""
Raman Compound Prediction & Inference Module - SpectraGuard ML Pipeline (Step 4)

This module provides a reusable RamanPredictor class for making compound-identification
predictions on single or batch Raman spectra.

Pipeline Steps:
1. Loads serialized artifacts (raman_scaler.pkl, raman_pca.pkl, raman_svm_model.pkl).
2. Applies Standard Normal Variate (SNV) normalization and baseline correction if raw spectra are provided.
3. Applies StandardScaler transform using parameters fitted during model training.
4. Applies PCA dimensionality reduction using components fitted during model training.
5. Performs SVM prediction and Platt scaling probability estimation.
6. Returns predicted compound name, confidence score (probability), top candidate breakdown, and model status.

Author: Antigravity AI Team / SpectraGuard Project
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd

# Add parent directory to path to allow importing ML.preprocessing.preprocess
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

try:
    from preprocessing.preprocess import RamanPreprocessor
except ImportError:
    RamanPreprocessor = None


class RamanPredictor:
    """
    Reusable Raman Compound Predictor.
    Loads trained Scaler, PCA, and SVM artifacts to perform inference on new Raman spectra.
    """

    def __init__(self, models_dir: str = None):
        """
        Initialize the predictor by loading serialized ML artifacts.
        
        Parameters:
        -----------
        models_dir : str, optional
            Path to directory containing raman_scaler.pkl, raman_pca.pkl, raman_svm_model.pkl.
        """
        if models_dir is None:
            models_dir = os.path.join(base_dir, "models")
            
        self.models_dir = models_dir
        self.scaler_path = os.path.join(models_dir, "raman_scaler.pkl")
        self.pca_path = os.path.join(models_dir, "raman_pca.pkl")
        self.svm_path = os.path.join(models_dir, "raman_svm_model.pkl")
        
        self.scaler = None
        self.pca = None
        self.svm_model = None
        self.is_loaded = False
        
        self.load_artifacts()

    def load_artifacts(self):
        """
        Load scaler, PCA, and SVM objects from disk.
        """
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler artifact not found at: {self.scaler_path}. Run train_model.py first.")
        if not os.path.exists(self.pca_path):
            raise FileNotFoundError(f"PCA artifact not found at: {self.pca_path}. Run train_model.py first.")
        if not os.path.exists(self.svm_path):
            raise FileNotFoundError(f"SVM artifact not found at: {self.svm_path}. Run train_model.py first.")
            
        # Model serialization loading explanation:
        # joblib.load restores the exact fitted state of StandardScaler (mean, std), PCA (components, mean),
        # and SVM (support vectors, Platt probability parameters) from training, ensuring zero data leakage.
        self.scaler = joblib.load(self.scaler_path)
        self.pca = joblib.load(self.pca_path)
        self.svm_model = joblib.load(self.svm_path)
        self.is_loaded = True
        print(f"[RamanPredictor] Successfully loaded model artifacts from {self.models_dir}")

    def predict(self, spectrum: np.ndarray, feature_cols: list = None, is_preprocessed: bool = True) -> dict:
        """
        Predict compound identity and confidence for a single input Raman spectrum.
        
        Parameters:
        -----------
        spectrum : np.ndarray
            1D array of shape (P,) or 2D array of shape (1, P) representing Raman spectrum.
        feature_cols : list, optional
            List of wavenumber column headers required if raw preprocessing is requested.
        is_preprocessed : bool (default=True)
            Set to True if spectrum has already undergone SNV normalization (as in Step 3 output).
            Set to False if raw intensities are passed.
            
        Returns:
        --------
        dict
            Dictionary containing:
            - status: 'SUCCESS' or 'ERROR'
            - predicted_compound: str
            - confidence: float (0.0 to 1.0)
            - confidence_percentage: str
            - top_candidates: list of dicts with top predicted compounds and probabilities
            - model_status: dict describing loaded artifacts
        """
        if not self.is_loaded:
            return {
                "status": "ERROR",
                "error_message": "Model artifacts are not loaded.",
                "predicted_compound": None,
                "confidence": 0.0,
                "model_status": "NOT_LOADED"
            }
            
        try:
            # Ensure spectrum is 2D numpy array of shape (1, P)
            X_input = np.asarray(spectrum, dtype=np.float64)
            if X_input.ndim == 1:
                X_input = X_input.reshape(1, -1)
                
            # If input is raw spectrum, apply baseline correction & SNV normalization
            if not is_preprocessed:
                if RamanPreprocessor is None:
                    raise ImportError("RamanPreprocessor module could not be imported for raw preprocessing.")
                if feature_cols is None:
                    raise ValueError("feature_cols must be provided when is_preprocessed=False.")
                preprocessor = RamanPreprocessor(poly_degree=5)
                X_input = preprocessor.transform(X_input, feature_cols)

            # 1. Apply StandardScaler transform (fitted during training)
            X_scaled = self.scaler.transform(X_input)
            
            # 2. Apply PCA dimensionality reduction (fitted during training)
            X_pca = self.pca.transform(X_scaled)
            
            # 3. Perform SVM Prediction and Platt Probability Estimation
            pred_class = self.svm_model.predict(X_pca)[0]
            
            # Check if probability estimation is supported by SVM model
            if hasattr(self.svm_model, "predict_proba"):
                probs = self.svm_model.predict_proba(X_pca)[0]
                classes = self.svm_model.classes_
                
                # Pair classes with probabilities and sort descending
                class_prob_pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
                top_class, top_prob = class_prob_pairs[0]
                
                top_candidates = [
                    {"compound": str(c), "probability": float(p), "percentage": f"{p * 100:.2f}%"}
                    for c, p in class_prob_pairs[:5]
                ]
                confidence = float(top_prob)
            else:
                pred_class = str(pred_class)
                confidence = 1.0
                top_candidates = [{"compound": pred_class, "probability": 1.0, "percentage": "100.00%"}]
                
            return {
                "status": "SUCCESS",
                "predicted_compound": str(pred_class),
                "confidence": confidence,
                "confidence_percentage": f"{confidence * 100:.2f}%",
                "top_candidates": top_candidates,
                "model_status": {
                    "scaler": "LOADED",
                    "pca": "LOADED",
                    "pca_components": int(self.pca.n_components_),
                    "svm": "LOADED",
                    "classifier_type": "SVC-RBF"
                }
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error_message": str(e),
                "predicted_compound": None,
                "confidence": 0.0,
                "model_status": "INFERENCE_FAILED"
            }


def main_demo():
    """
    Demonstration and self-test for RamanPredictor.
    Loads 5 sample test spectra from processed_raman_features.csv and runs inference.
    """
    print("=" * 65)
    print("      SPECTRAGUARD ML - STEP 4 PREDICTION INFERENCE DEMO")
    print("=" * 65)
    
    results_dir = os.path.join(base_dir, "results")
    features_path = os.path.join(results_dir, "processed_raman_features.csv")
    labels_path = os.path.join(results_dir, "processed_labels.csv")
    
    if not os.path.exists(features_path) or not os.path.exists(labels_path):
        print("Features or labels CSV files not found. Cannot run demo.")
        return

    predictor = RamanPredictor()
    
    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)
    
    sample_indices = [0, 500, 1200, 2000, 3000]
    
    print("\nRunning inference on 5 sample test spectra:\n")
    for idx in sample_indices:
        if idx >= len(df_features):
            continue
        spectrum = df_features.iloc[idx].values
        actual_label = df_labels.iloc[idx]['label']
        
        res = predictor.predict(spectrum, is_preprocessed=True)
        
        print(f"Sample #{idx}:")
        print(f"  - Actual Compound:    {actual_label}")
        print(f"  - Predicted Compound: {res['predicted_compound']}")
        print(f"  - Confidence:         {res['confidence_percentage']}")
        print(f"  - Status:             {res['status']}")
        print(f"  - Top 3 Candidates:")
        for cand in res['top_candidates'][:3]:
            print(f"      * {cand['compound']}: {cand['percentage']}")
        print("-" * 55)


if __name__ == "__main__":
    main_demo()
