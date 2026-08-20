"""
Authentication Result Data Structure - SpectraGuard ML

Defines structured comparison result types and status enumerations for the
pharmaceutical Raman reference authentication layer.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ComparisonStatus(str, Enum):
    """
    Allowed comparison status values for reference authentication decision logic.
    
    CRITICAL POLICY RULE:
    Genuine and Counterfeit labels are strictly prohibited at this layer
    because the available open datasets do not contain verified counterfeit samples.
    Low similarity scores must be categorized as UNKNOWN, never COUNTERFEIT.
    """
    AUTHENTIC_REFERENCE_MATCH = "AUTHENTIC_REFERENCE_MATCH"
    UNKNOWN = "UNKNOWN"
    REFERENCE_NOT_AVAILABLE = "REFERENCE_NOT_AVAILABLE"
    INVALID_INPUT = "INVALID_INPUT"
    MATCH_COMPUTED = "MATCH_COMPUTED"  # Maintained for backward compatibility


@dataclass
class AuthenticationResult:
    """
    Structured result returned by the RamanAuthenticator engine.
    
    Attributes:
    -----------
    drug_name : str
        Name of the target drug or compound being evaluated.
    similarity_score : Optional[float]
        Raw numerical similarity score (Cosine Similarity in range [0.0, 1.0]).
        None if status is REFERENCE_NOT_AVAILABLE or INVALID_INPUT.
    reference_id : Optional[str]
        Identifier of the pharmaceutical reference spectrum record used.
        None if reference was not found or input was invalid.
    comparison_status : ComparisonStatus
        Status enum value: AUTHENTIC_REFERENCE_MATCH, UNKNOWN,
        REFERENCE_NOT_AVAILABLE, or INVALID_INPUT.
    similarity_method : str
        The spectral similarity calculation algorithm used ('cosine_similarity').
    details : Dict[str, Any]
        Context dictionary containing threshold, decision details, metadata, etc.
    """
    drug_name: str
    similarity_score: Optional[float]
    reference_id: Optional[str]
    comparison_status: ComparisonStatus
    similarity_method: str = "cosine_similarity"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result object to dictionary format."""
        return {
            "drug_name": self.drug_name,
            "similarity_score": self.similarity_score,
            "reference_id": self.reference_id,
            "comparison_status": self.comparison_status.value if isinstance(self.comparison_status, ComparisonStatus) else str(self.comparison_status),
            "similarity_method": self.similarity_method,
            "details": self.details
        }

    def __post_init__(self):
        """Ensure comparison_status is a valid ComparisonStatus enum value."""
        if isinstance(self.comparison_status, str):
            try:
                self.comparison_status = ComparisonStatus(self.comparison_status)
            except ValueError:
                raise ValueError(
                    f"Invalid status '{self.comparison_status}'. Must be one of: "
                    f"{[e.value for e in ComparisonStatus]}"
                )
