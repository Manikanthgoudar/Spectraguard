"""
Raman Compound Classification Model Training - SpectraGuard ML Pipeline (Step 4)

This script trains and evaluates a Raman compound-identification classifier:
1. Loads preprocessed Raman feature vectors (SNV-normalized) and compound labels.
2. Performs a stratified train/test split (80% training, 20% testing).
3. Fits a StandardScaler and PCA dimensionality reduction ONLY on training data to prevent data leakage.
4. Trains an RBF-kernel Support Vector Machine (SVM) classifier on PCA-transformed training data.
5. Evaluates model performance on the untouched test set (Accuracy, Macro/Weighted Precision, Recall, F1-score).
6. Exports confusion matrix plot, PCA visualization plot, classification report, and overall evaluation text report.
7. Serializes trained Scaler, PCA, and SVM model artifacts into ML/models/ for inference.

IMPORTANT:
- This model is exclusively a Raman compound-identification classifier.
- It does NOT generate or predict Genuine/Counterfeit labels.
- It does NOT generate synthetic data or modify raw source CSV files.

Author: Antigravity AI Team / SpectraGuard Project
"""

import os
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)


def train_raman_classifier():
    """
    Executes Step 4 model training, evaluation, artifact serialization,
    and report generation.
    """
    print("=" * 65)
    print("     SPECTRAGUARD ML - STEP 4 MODEL TRAINING & EVALUATION")
    print("=" * 65)
    
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # Path Setup
    # -------------------------------------------------------------------------
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    models_dir = os.path.join(base_dir, "models")
    
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    features_path = os.path.join(results_dir, "processed_raman_features.csv")
    labels_path = os.path.join(results_dir, "processed_labels.csv")
    
    scaler_save_path = os.path.join(models_dir, "raman_scaler.pkl")
    pca_save_path = os.path.join(models_dir, "raman_pca.pkl")
    svm_save_path = os.path.join(models_dir, "raman_svm_model.pkl")
    
    confusion_matrix_path = os.path.join(results_dir, "confusion_matrix.png")
    pca_vis_path = os.path.join(results_dir, "pca_visualization.png")
    class_report_path = os.path.join(results_dir, "classification_report.txt")
    eval_summary_path = os.path.join(results_dir, "model_evaluation.txt")
    
    # -------------------------------------------------------------------------
    # 1. Load Processed Dataset
    # -------------------------------------------------------------------------
    print(f"-> Loading processed features from: {features_path}")
    print(f"-> Loading processed labels from:   {labels_path}")
    
    df_features = pd.read_csv(features_path)
    df_labels = pd.read_csv(labels_path)
    
    X = df_features.values.astype(np.float64)
    y = df_labels['label'].values
    
    num_samples, num_features = X.shape
    unique_classes = np.unique(y)
    num_classes = len(unique_classes)
    
    print(f"-> Dataset Loaded Successfully: {num_samples} samples, {num_features} Raman features, {num_classes} compound classes.")
    
    # -------------------------------------------------------------------------
    # 2. Stratified Train/Test Split (Data Leakage Prevention)
    # -------------------------------------------------------------------------
    # Train/test split explanation:
    # We use an 80/20 train/test split with stratify=y to ensure that every single compound class
    # maintains an identical proportion in both the training set (80%) and testing set (20%).
    # Fixed random_state=42 guarantees 100% reproducible splits across runs.
    test_size_ratio = 0.20
    random_seed = 42
    
    print(f"-> Performing Stratified Train/Test Split ({int((1-test_size_ratio)*100)}% Train / {int(test_size_ratio*100)}% Test, random_state={random_seed})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size_ratio,
        random_state=random_seed,
        stratify=y
    )
    
    num_train = len(X_train)
    num_test = len(X_test)
    print(f"   - Training set size: {num_train} samples")
    print(f"   - Testing set size:  {num_test} samples")
    
    # -------------------------------------------------------------------------
    # 3. Standard Feature Scaling (Fitted STRICTLY on Training Data)
    # -------------------------------------------------------------------------
    # Data leakage prevention:
    # Scaler standardizes each feature to mean 0 and variance 1.
    # We fit the scaler ONLY on X_train. X_test is transformed using the parameters (mean, std)
    # computed from X_train, ensuring no information from test set bleeds into preprocessing.
    print("-> Fitting StandardScaler on training set...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # -------------------------------------------------------------------------
    # 4. PCA Dimensionality Reduction (Fitted STRICTLY on Training Data)
    # -------------------------------------------------------------------------
    # Principal Component Analysis (PCA) explanation:
    # Raman spectra contain 3,276 wavenumber features, many of which are highly correlated.
    # PCA transforms high-dimensional features into linearly uncorrelated principal components.
    # We set n_components=0.95 to retain 95% of cumulative explained variance while reducing
    # feature dimensionality significantly to prevent overfitting and speed up training.
    # Data leakage prevention: PCA is fit ONLY on X_train_scaled and then transforms X_test_scaled.
    variance_threshold = 0.95
    print(f"-> Fitting PCA (Explained Variance Threshold = {variance_threshold * 100:.1f}%) on training data...")
    
    pca = PCA(n_components=variance_threshold, random_state=random_seed)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)
    
    num_components = pca.n_components_
    explained_variance_total = np.sum(pca.explained_variance_ratio_) * 100
    print(f"   - Selected PCA components: {num_components}")
    print(f"   - Cumulative explained variance: {explained_variance_total:.2f}%")
    
    # -------------------------------------------------------------------------
    # 5. Train Support Vector Machine (SVM) Classifier
    # -------------------------------------------------------------------------
    # SVM Explanation:
    # Support Vector Classifier (SVC) with Radial Basis Function (RBF) kernel projects data into a high-dimensional
    # space to find optimal hyperplanes separating compound classes.
    # Setting class_weight='balanced' automatically adjusts weights inversely proportional to class frequencies.
    # Setting probability=True fits Platt scaling probability calibration so the model outputs true compound confidence probabilities.
    print("-> Training RBF Support Vector Machine (SVM) Classifier...")
    svm_model = SVC(
        kernel='rbf',
        C=10.0,
        gamma='scale',
        class_weight='balanced',
        probability=True,
        random_state=random_seed
    )
    
    svm_model.fit(X_train_pca, y_train)
    print("   - SVM model training completed successfully.")
    
    # -------------------------------------------------------------------------
    # 6. Model Evaluation on Untouched Test Set
    # -------------------------------------------------------------------------
    # Evaluation Metrics Explanation:
    # - Accuracy: Overall fraction of correct compound predictions.
    # - Macro Metrics (Precision, Recall, F1): Calculate metrics independently for each class and average them equally,
    #   giving equal importance to all compound classes regardless of sample size.
    # - Weighted Metrics (Precision, Recall, F1): Calculate metrics for each class weighted by class frequency.
    print("-> Evaluating model performance on untouched test set...")
    y_pred = svm_model.predict(X_test_pca)
    
    accuracy = accuracy_score(y_test, y_pred)
    
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='macro'
    )
    weighted_prec, weighted_rec, weighted_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='weighted'
    )
    
    print("\n---------------------------------------------------------")
    print("               MODEL PERFORMANCE METRICS                 ")
    print("---------------------------------------------------------")
    print(f"   - Accuracy:           {accuracy * 100:.2f}% ({accuracy:.4f})")
    print(f"   - Macro Precision:    {macro_prec * 100:.2f}% ({macro_prec:.4f})")
    print(f"   - Macro Recall:       {macro_rec * 100:.2f}% ({macro_rec:.4f})")
    print(f"   - Macro F1-Score:     {macro_f1 * 100:.2f}% ({macro_f1:.4f})")
    print(f"   - Weighted Precision: {weighted_prec * 100:.2f}% ({weighted_prec:.4f})")
    print(f"   - Weighted Recall:    {weighted_rec * 100:.2f}% ({weighted_rec:.4f})")
    print(f"   - Weighted F1-Score:  {weighted_f1 * 100:.2f}% ({weighted_f1:.4f})")
    print("---------------------------------------------------------\n")
    
    # -------------------------------------------------------------------------
    # 7. Generate & Save Confusion Matrix Plot
    # -------------------------------------------------------------------------
    print(f"-> Generating confusion matrix plot: {confusion_matrix_path}")
    labels_sorted = sorted(list(unique_classes))
    cm = confusion_matrix(y_test, y_pred, labels=labels_sorted)
    
    plt.figure(figsize=(16, 14))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('SpectraGuard Raman Classifier - Confusion Matrix (Test Set)', fontsize=14, fontweight='bold', pad=15)
    plt.colorbar(shrink=0.8)
    
    tick_marks = np.arange(len(labels_sorted))
    plt.xticks(tick_marks, labels_sorted, rotation=90, fontsize=8)
    plt.yticks(tick_marks, labels_sorted, fontsize=8)
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            if val > 0:
                plt.text(j, i, str(val),
                         horizontalalignment="center",
                         verticalalignment="center",
                         color="white" if val > thresh else "black",
                         fontsize=7, fontweight='bold')
                         
    plt.ylabel('True Compound Label', fontsize=11, fontweight='bold')
    plt.xlabel('Predicted Compound Label', fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(confusion_matrix_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------------------
    # 8. Generate & Save PCA 2D Class Distribution Visualization
    # -------------------------------------------------------------------------
    print(f"-> Generating 2D PCA class distribution visualization: {pca_vis_path}")
    plt.figure(figsize=(13, 10))
    
    for idx, cls in enumerate(labels_sorted):
        mask = (y_test == cls)
        plt.scatter(
            X_test_pca[mask, 0],
            X_test_pca[mask, 1],
            label=cls,
            alpha=0.8,
            edgecolors='k',
            linewidths=0.3,
            s=40
        )
        
    pc1_var = pca.explained_variance_ratio_[0] * 100
    pc2_var = pca.explained_variance_ratio_[1] * 100
    
    plt.title(f'Raman Spectral Features - PCA Space Distribution (PC1 vs PC2)\nTotal Variance Explained by 2 Components: {pc1_var + pc2_var:.2f}%', fontsize=13, fontweight='bold')
    plt.xlabel(f'Principal Component 1 ({pc1_var:.2f}% Variance)', fontsize=11, fontweight='bold')
    plt.ylabel(f'Principal Component 2 ({pc2_var:.2f}% Variance)', fontsize=11, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(pca_vis_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------------------
    # 9. Save Detailed Classification Report
    # -------------------------------------------------------------------------
    print(f"-> Writing classification report to: {class_report_path}")
    cls_report_text = classification_report(y_test, y_pred, target_names=labels_sorted, digits=4)
    with open(class_report_path, "w", encoding="utf-8") as f:
        f.write("=========================================================================\n")
        f.write("     SPECTRAGUARD ML - STEP 4 CLASSIFICATION REPORT (TEST SET)          \n")
        f.write("=========================================================================\n\n")
        f.write(cls_report_text)
        f.write("\n")
        
    # -------------------------------------------------------------------------
    # 10. Save Overall Model Evaluation Summary
    # -------------------------------------------------------------------------
    print(f"-> Writing overall model evaluation summary to: {eval_summary_path}")
    eval_summary_lines = [
        "=========================================================================",
        "     SPECTRAGUARD ML - MODEL TRAINING & EVALUATION REPORT (STEP 4)       ",
        "=========================================================================",
        "",
        "1. MODEL ARCHITECTURE & PIPELINE SUMMARY",
        "-------------------------------------------------------------------------",
        " - Model Purpose: Raman Spectral Compound Identification Classifier",
        " - Feature Preprocessing: SNV Vector Normalization (Step 3)",
        " - Feature Scaling: StandardScaler (Fit on Train Set Only)",
        " - Dimensionality Reduction: Principal Component Analysis (PCA)",
        "   * Cumulative Variance Threshold: 95.0%",
        f"   * Selected Principal Components: {num_components}",
        f"   * Actual Explained Variance: {explained_variance_total:.2f}%",
        " - Classifier: Support Vector Machine (SVC)",
        "   * Kernel: RBF (Radial Basis Function)",
        "   * Regularization Parameter (C): 10.0",
        "   * Gamma: scale",
        "   * Class Weight: balanced",
        "   * Probability Estimation: Enabled (Platt Scaling)",
        "",
        "2. DATASET SPLIT & DATA LEAKAGE SAFEGUARDS",
        "-------------------------------------------------------------------------",
        f" - Total Samples Loaded: {num_samples}",
        f" - Number of Unique Compound Classes: {num_classes}",
        f" - Input Feature Dimensions: {num_features} Raman Wavenumbers",
        " - Train/Test Split: 80% Training / 20% Testing (Stratified)",
        f"   * Training Samples: {num_train}",
        f"   * Testing Samples:  {num_test}",
        "   * Random Seed: 42",
        " - Data Leakage Prevention Measures:",
        "   * Train/test split was performed prior to any scaling or PCA.",
        "   * StandardScaler was fit strictly on X_train, then applied to transform X_test.",
        "   * PCA model was fit strictly on scaled X_train, then applied to transform X_test.",
        "   * Model evaluation was conducted exclusively on the untouched test set.",
        "",
        "3. PERFORMANCE EVALUATION ON UNTOUCHED TEST SET",
        "-------------------------------------------------------------------------",
        f" - Accuracy:           {accuracy * 100:.2f}% ({accuracy:.4f})",
        f" - Macro Precision:    {macro_prec * 100:.2f}% ({macro_prec:.4f})",
        f" - Macro Recall:       {macro_rec * 100:.2f}% ({macro_rec:.4f})",
        f" - Macro F1-Score:     {macro_f1 * 100:.2f}% ({macro_f1:.4f})",
        f" - Weighted Precision: {weighted_prec * 100:.2f}% ({weighted_prec:.4f})",
        f" - Weighted Recall:    {weighted_rec * 100:.2f}% ({weighted_rec:.4f})",
        f" - Weighted F1-Score:  {weighted_f1 * 100:.2f}% ({weighted_f1:.4f})",
        "",
        "4. MODEL SERIALIZATION & SAVED ARTIFACTS",
        "-------------------------------------------------------------------------",
        f" - Scaler Artifact:     ML/models/raman_scaler.pkl",
        f" - PCA Artifact:        ML/models/raman_pca.pkl",
        f" - SVM Model Artifact:  ML/models/raman_svm_model.pkl",
        f" - Confusion Matrix:    ML/results/confusion_matrix.png",
        f" - PCA Scatter Plot:    ML/results/pca_visualization.png",
        f" - Classification Rep:  ML/results/classification_report.txt",
        "",
        "=========================================================================",
        f"Report Generated Successfully in {time.time() - start_time:.2f} seconds.",
        "========================================================================="
    ]
    
    with open(eval_summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(eval_summary_lines))
        
    # -------------------------------------------------------------------------
    # 11. Model Serialization (Saving Scaler, PCA, and SVM)
    # -------------------------------------------------------------------------
    # Serialization Explanation:
    # Model serialization saves trained python object state into binary files via joblib.
    # In production/inference, predict.py loads these saved objects to apply exact training
    # scaling and transformation without retraining or exposing test data.
    print(f"-> Saving StandardScaler object to: {scaler_save_path}")
    joblib.dump(scaler, scaler_save_path)
    
    print(f"-> Saving PCA object to:           {pca_save_path}")
    joblib.dump(pca, pca_save_path)
    
    print(f"-> Saving trained SVM model to:    {svm_save_path}")
    joblib.dump(svm_model, svm_save_path)
    
    elapsed = time.time() - start_time
    
    # -------------------------------------------------------------------------
    # 12. Final Execution Summary Output
    # -------------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("STEP 4 MODEL TRAINING COMPLETED")
    print("=" * 65)
    print(f"- Number of training samples: {num_train}")
    print(f"- Number of test samples: {num_test}")
    print(f"- Number of classes: {num_classes}")
    print(f"- PCA components: {num_components}")
    print(f"- Accuracy: {accuracy:.4f}")
    print(f"- Macro F1: {macro_f1:.4f}")
    print(f"- Weighted F1: {weighted_f1:.4f}")
    print("- Location of saved model files:")
    print(f"  1. {os.path.relpath(scaler_save_path, base_dir)}")
    print(f"  2. {os.path.relpath(pca_save_path, base_dir)}")
    print(f"  3. {os.path.relpath(svm_save_path, base_dir)}")
    print("- Location of evaluation files:")
    print(f"  1. {os.path.relpath(confusion_matrix_path, base_dir)}")
    print(f"  2. {os.path.relpath(pca_vis_path, base_dir)}")
    print(f"  3. {os.path.relpath(class_report_path, base_dir)}")
    print(f"  4. {os.path.relpath(eval_summary_path, base_dir)}")
    print(f"Model training and evaluation pipeline executed in {elapsed:.2f} seconds.")
    print("=" * 65)


if __name__ == "__main__":
    train_raman_classifier()
