import os
import logging
import warnings
import concurrent.futures
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from app.config import settings
from app.core.logging_config import logger

SYSTEM_INSTRUCTION = (
    "You are SpectraGuard AI, an expert AI assistant specializing in pharmaceutical drug authentication, "
    "Raman spectroscopy analysis, spectral cosine similarity matching, peak divergence analysis, and regulatory compliance. "
    "Provide clear, professional, concise, and accurate explanations. Use markdown formatting where helpful."
)

CANDIDATE_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-2.0-flash-exp",
]


def _call_gemini_with_timeout(api_key: str, prompt: str, timeout_seconds: float = 3.5) -> str:
    """Calls Gemini API inside a worker thread bounded by a strict timeout."""
    def _worker():
        genai.configure(api_key=api_key)
        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_INSTRUCTION,
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as model_err:
                logger.warning(f"Gemini model '{model_name}' attempt failed: {model_err}")
                continue
        raise RuntimeError("All candidate Gemini models failed or timed out.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_worker)
        return future.result(timeout=timeout_seconds)


def get_gemini_reply(prompt: str, history: list = None) -> str:
    """Generates a reply using Gemini API with automatic model fallback and strict timeout."""
    api_key = (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()

    if api_key and api_key.startswith("AIza") and len(api_key) > 20:
        try:
            return _call_gemini_with_timeout(api_key, prompt, timeout_seconds=3.5)
        except concurrent.futures.TimeoutError:
            logger.warning("Gemini API call timed out after 3.5s. Falling back to local AI engine.")
        except Exception as e:
            logger.warning(f"Gemini API error ({e}). Falling back to local AI engine.")

    # ── Domain-Specific AI Fallback Engine ──────────────────────────────────────
    return _domain_fallback_reply(prompt)


def _domain_fallback_reply(prompt: str) -> str:
    q = prompt.lower().strip()

    if "genuine" in q or "authentic" in q:
        return (
            "A sample is classified as **Genuine** when its cosine similarity against the reference spectrum is ≥ 97% (0.970). "
            "This confirms that the spectral fingerprint matches the authenticated reference compound, verifying both the presence "
            "and proper ratio of the Active Pharmaceutical Ingredient (API)."
        )
    if "counterfeit" in q or "fake" in q or "suspect" in q:
        return (
            "A **Potentially Counterfeit** result is returned when the cosine similarity falls below 85% (< 0.850). "
            "This indicates missing diagnostic peaks, significant wavenumber shifts, or foreign spectral artifacts.\n\n"
            "**Action Protocol:**\n"
            "1. Quarantine the batch immediately.\n"
            "2. Log serial numbers and lot information.\n"
            "3. Submit a sample for confirmatory HPLC / LC-MS analysis."
        )
    if "borderline" in q or "verification" in q or "verify" in q:
        return (
            "A **Requires Verification** result (85% – 97% similarity) is borderline. "
            "This may stem from minor excipient variations, batch-to-batch manufacturing shifts, or early sample degradation. "
            "We recommend secondary laboratory verification (HPLC or dissolution testing) before releasing the lot."
        )
    if "cosine" in q or "similarity" in q:
        return (
            "Cosine similarity calculates the dot product of normalized spectral vectors:\n"
            "• **Formula**: Sim(A, B) = (A · B) / (||A|| × ||B||)\n\n"
            "A score of 1.000 means identical spectra. SpectraGuard thresholds:\n"
            "• **≥ 0.970**: Genuine\n"
            "• **0.850 – 0.969**: Requires Verification\n"
            "• **< 0.850**: Potentially Counterfeit"
        )
    if "raman" in q or "spectroscop" in q:
        return (
            "Raman Spectroscopy is a high-precision, non-destructive optical technique. "
            "When monochromatic laser light interacts with molecular bonds, inelastic scattering (Raman shift) occurs. "
            "The resulting wavenumber spectrum (cm⁻¹) acts as a unique chemical fingerprint capable of identifying APIs and excipients in seconds."
        )
    if "upload" in q or "csv" in q:
        return (
            "To run a test, navigate to **Upload Spectra** and select a CSV file. Format requirement:\n"
            "• Column 1: Wavenumber (cm⁻¹)\n"
            "• Column 2: Intensity (arbitrary units)\n"
            "SpectraGuard automatically performs baseline correction, noise filtering, and intensity normalization."
        )
    if "report" in q or "pdf" in q:
        return (
            "PDF reports can be downloaded from any Test Details screen. Reports contain:\n"
            "1. Classification status & risk assessment\n"
            "2. Match score & cosine similarity breakdown\n"
            "3. High-resolution spectral overlay charts\n"
            "4. Prominent peak alignment tables (cm⁻¹ shifts)\n"
            "5. AI diagnostic rationale & regulatory compliance stamps"
        )
    if "metformin" in q:
        return (
            "**Metformin HCl** is an antidiabetic agent with characteristic Raman peaks at ~735 cm⁻¹, ~938 cm⁻¹, and ~1060 cm⁻¹. "
            "SpectraGuard compares uploaded spectral scans against authenticated reference samples to ensure active API concentration."
        )
    if "amoxicillin" in q:
        return (
            "**Amoxicillin** is a broad-spectrum beta-lactam antibiotic. Key Raman diagnostic bands appear around ~850 cm⁻¹, ~1240 cm⁻¹, and ~1600 cm⁻¹. "
            "Spectral degradation or peak attenuation indicates sub-potent or counterfeit formulations."
        )
    if "hello" in q or "hi" in q or "hey" in q or "greetings" in q:
        return (
            "Hello! I am your **SpectraGuard AI Assistant**. How can I assist you today with pharmaceutical testing, "
            "Raman spectral analysis, cosine similarity thresholds, or test reporting?"
        )
    if "help" in q or "what can you" in q or "capability" in q:
        return (
            "I can assist you with:\n"
            "• **Classification**: Genuine vs Counterfeit thresholds\n"
            "• **Spectral Math**: Cosine similarity & peak prominence\n"
            "• **Preprocessing**: Baseline correction & SNR analysis\n"
            "• **App Usage**: Uploading CSVs & exporting PDF reports\n"
            "• **Protocols**: Quarantine steps & regulatory reporting"
        )

    return (
        f"Regarding '**{prompt}**': I am ready to assist with pharmaceutical verification, "
        "spectral cosine similarity, Raman peak matching, or quarantine protocol rules. "
        "Type **help** to see all available topics."
    )

