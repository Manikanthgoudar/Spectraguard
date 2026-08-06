import os
import warnings
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
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-pro",
]


def get_gemini_reply(prompt: str, history: list = None) -> str:
    """Generates a reply using Gemini API with automatic model fallback."""
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "").strip()

    if api_key:
        try:
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
                    logger.warning(f"Model {model_name} failed: {model_err}")
                    continue
        except Exception as e:
            logger.error(f"Gemini API configuration/generation error: {e}")

    # Domain-specific fallback reply if Gemini API key is absent or quota limited
    q = prompt.lower().trim() if hasattr(prompt, 'trim') else prompt.lower().strip()

    if "genuine" in q or "authentic" in q:
        return (
            "A sample is classified as **Genuine** when its cosine similarity against the reference spectrum is ≥ 97% (0.970). "
            "This confirms that the spectral fingerprint matches the authenticated reference compound, verifying both the presence "
            "and proper ratio of the Active Pharmaceutical Ingredient (API)."
        )
    if "counterfeit" in q or "fake" in q:
        return (
            "A **Potentially Counterfeit** result is returned when the cosine similarity falls below 85% (< 0.850). "
            "This indicates missing diagnostic peaks, significant wavenumber shifts, or foreign spectral artifacts. "
            "**Action:** Quarantine the batch immediately, log the serial number, and send a sample for confirmatory HPLC / LC-MS analysis."
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
            "• Formula: Sim(A, B) = (A · B) / (||A|| × ||B||)\n\n"
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
    if "hello" in q or "hi" in q or "hey" in q:
        return (
            "Hello! I am your SpectraGuard AI Assistant. How can I assist you today with pharmaceutical testing, "
            "Raman spectral analysis, or spectral matching?"
        )

    return (
        f"Regarding '{prompt}': I am ready to assist with spectral analysis, cosine similarity calculation, "
        "or pharmaceutical verification rules."
    )
