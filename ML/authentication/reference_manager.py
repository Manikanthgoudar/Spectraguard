"""
Pharmaceutical Raman Reference Spectrum Manager - SpectraGuard ML

Provides clean data structures and a management interface for storing, loading,
and retrieving pharmaceutical reference spectra used in spectral similarity evaluation.
"""

import numpy as np
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field


@dataclass
class ReferenceRecord:
    """
    Data structure for a single pharmaceutical reference spectrum.
    
    Attributes:
    -----------
    drug_name : str
        Name of the pharmaceutical drug or compound (e.g., 'Paracetamol', 'Ibuprofen').
    reference_id : str
        Unique identifier for the reference spectrum (e.g., 'REF-PARA-001').
    raman_features : np.ndarray
        Numeric array containing preprocessed intensity features (length 3,276).
    wavenumbers : np.ndarray
        Numeric array containing corresponding wavenumber values in cm⁻¹ (length 3,276).
    preprocessing_metadata : Dict[str, Any]
        Metadata detailing preprocessing steps applied (e.g., baseline correction, SNV).
    source_information : Dict[str, Any]
        Origin metadata (laboratory, spectrometer instrument, purity, supplier).
    reference_status : str
        Current status of the reference record ('ACTIVE', 'ARCHIVED', 'DRAFT').
    """
    drug_name: str
    reference_id: str
    raman_features: np.ndarray
    wavenumbers: np.ndarray
    preprocessing_metadata: Dict[str, Any] = field(default_factory=dict)
    source_information: Dict[str, Any] = field(default_factory=dict)
    reference_status: str = "ACTIVE"

    def __post_init__(self):
        """Validate feature dimensions and array types."""
        self.raman_features = np.asarray(self.raman_features, dtype=np.float64)
        self.wavenumbers = np.asarray(self.wavenumbers, dtype=np.float64)
        
        if self.raman_features.ndim != 1:
            self.raman_features = self.raman_features.flatten()
            
        if self.wavenumbers.ndim != 1:
            self.wavenumbers = self.wavenumbers.flatten()
            
        if len(self.raman_features) != len(self.wavenumbers):
            raise ValueError(
                f"Dimension mismatch between raman_features ({len(self.raman_features)}) "
                f"and wavenumbers ({len(self.wavenumbers)})."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary summary of the reference record (excluding raw vectors)."""
        return {
            "drug_name": self.drug_name,
            "reference_id": self.reference_id,
            "feature_count": len(self.raman_features),
            "wavenumber_range": [float(self.wavenumbers[0]), float(self.wavenumbers[-1])],
            "preprocessing_metadata": self.preprocessing_metadata,
            "source_information": self.source_information,
            "reference_status": self.reference_status
        }


class ReferenceManager:
    """
    In-memory registry and repository manager for pharmaceutical reference spectra.
    """

    def __init__(self):
        self._references_by_id: Dict[str, ReferenceRecord] = {}
        self._references_by_drug: Dict[str, List[str]] = {}

    def add_reference(self, record: ReferenceRecord) -> None:
        """
        Register a new reference record.
        
        Parameters:
        -----------
        record : ReferenceRecord
            The reference record instance to register.
        """
        if not isinstance(record, ReferenceRecord):
            raise TypeError("Expected a ReferenceRecord instance.")
            
        ref_id = record.reference_id
        if ref_id in self._references_by_id:
            raise ValueError(f"Duplicate reference ID '{ref_id}' already exists in repository.")

        drug_key = record.drug_name.strip().lower()
        
        self._references_by_id[ref_id] = record
        
        if drug_key not in self._references_by_drug:
            self._references_by_drug[drug_key] = []
        if ref_id not in self._references_by_drug[drug_key]:
            self._references_by_drug[drug_key].append(ref_id)

    def get_available_drug_names(self) -> List[str]:
        """
        Retrieve a sorted list of unique active pharmaceutical drug names
        currently registered in the reference database.
        """
        active_drugs = set()
        for record in self._references_by_id.values():
            if record.reference_status == "ACTIVE" and record.drug_name:
                active_drugs.add(record.drug_name.strip())
        return sorted(list(active_drugs))

    def get_reference_by_id(self, reference_id: str) -> Optional[ReferenceRecord]:
        """Retrieve a reference record by its unique reference_id."""
        return self._references_by_id.get(reference_id)

    def get_reference_by_drug(self, drug_name: str) -> Optional[ReferenceRecord]:
        """
        Retrieve the latest active reference record for a target drug name.
        
        Parameters:
        -----------
        drug_name : str
            Name of the drug or compound.
            
        Returns:
        --------
        Optional[ReferenceRecord]
            The matching active reference record, or None if not found.
        """
        drug_key = drug_name.strip().lower()
        ref_ids = self._references_by_drug.get(drug_key, [])
        
        for ref_id in reversed(ref_ids):
            record = self._references_by_id[ref_id]
            if record.reference_status == "ACTIVE":
                return record
                
        return None

    def get_active_references_for_drug(self, drug_name: str) -> List[ReferenceRecord]:
        """
        Retrieve all active reference records registered for a target drug name.
        """
        drug_key = drug_name.strip().lower()
        ref_ids = self._references_by_drug.get(drug_key, [])
        records = []
        for ref_id in ref_ids:
            record = self._references_by_id.get(ref_id)
            if record and record.reference_status == "ACTIVE":
                records.append(record)
        return records

    def get_all_active_references(self) -> List[ReferenceRecord]:
        """
        Retrieve all registered active reference records across all compounds.
        """
        return [
            rec for rec in self._references_by_id.values()
            if rec.reference_status == "ACTIVE"
        ]

    def has_reference_for_drug(self, drug_name: str) -> bool:
        """Check if an active reference exists for a target drug name."""
        return len(self.get_active_references_for_drug(drug_name)) > 0

    def list_references(self) -> List[Dict[str, Any]]:
        """List summary info of all registered reference records."""
        return [record.to_dict() for record in self._references_by_id.values()]

    def count(self) -> int:
        """Return total count of registered reference records."""
        return len(self._references_by_id)

