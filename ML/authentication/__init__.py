"""
SpectraGuard Pharmaceutical Raman Reference & Authentication Layer
"""

from .reference_manager import ReferenceRecord, ReferenceManager
from .authentication_result import ComparisonStatus, AuthenticationResult
from .authenticator import RamanAuthenticator

__all__ = [
    "ReferenceRecord",
    "ReferenceManager",
    "ComparisonStatus",
    "AuthenticationResult",
    "RamanAuthenticator"
]
