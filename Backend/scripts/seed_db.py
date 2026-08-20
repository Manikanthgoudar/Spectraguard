"""
Seed script: populates the database with mock data.
  - 1 admin user
  - 2 pharmacist users
  - 2 public users
  - 10 reference spectra (realistic Raman-like profiles for common drugs)
  - 8 test records with spectral data and classification results

Run from the Backend folder:
    python scripts/seed_db.py
"""

import sys
import os
import json
import math
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine
from app.models import User, ReferenceSpectrum, Test, SpectraData, Report, ChatMessage
from app.models.user import UserRole
from app.models.test import ClassificationResult
from app.core.security import hash_password
from app.database import Base

# ── Create all tables (idempotent) ────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# ── Spectral Data Generation ──────────────────────────────────────────────────

def generate_wavenumbers(start=400, end=1800, n=200):
    """Generate evenly-spaced Raman wavenumber axis."""
    return [round(start + i * (end - start) / (n - 1), 2) for i in range(n)]


def lorentzian(x, center, width, height):
    """Lorentzian peak function."""
    return height / (1 + ((x - center) / (width / 2)) ** 2)


def generate_drug_spectrum(wavenumbers, peaks, noise_level=0.02, random_seed=None):
    """
    Generate a synthetic Raman spectrum for a drug.
    peaks: list of (center, width, height) tuples.
    """
    if random_seed is not None:
        random.seed(random_seed)

    spectrum = []
    for wn in wavenumbers:
        intensity = sum(lorentzian(wn, c, w, h) for c, w, h in peaks)
        intensity += random.gauss(0, noise_level)
        spectrum.append(max(0.0, round(intensity, 6)))
    return spectrum


# Drug spectral profiles (peak positions characteristic of real Raman spectra)
DRUG_PROFILES = {
    "Paracetamol": [(831, 15, 1.0), (1168, 12, 0.85), (1236, 10, 0.65), (1325, 14, 0.50), (1621, 20, 0.90)],
    "Amoxicillin": [(756, 18, 0.90), (1005, 14, 0.70), (1185, 12, 0.55), (1390, 16, 0.80), (1590, 22, 1.00)],
    "Ibuprofen":   [(837, 16, 1.00), (1186, 13, 0.75), (1462, 15, 0.85), (1608, 18, 0.65), (1720, 20, 0.95)],
    "Metformin":   [(578, 20, 0.80), (876, 18, 1.00), (1171, 15, 0.70), (1382, 14, 0.60), (1578, 20, 0.90)],
    "Atorvastatin":[(492, 22, 0.60), (778, 18, 0.85), (1037, 16, 1.00), (1275, 14, 0.75), (1515, 20, 0.70)],
    "Azithromycin":[(680, 20, 0.75), (921, 17, 0.95), (1125, 15, 0.80), (1288, 18, 1.00), (1467, 22, 0.65)],
    "Omeprazole":  [(615, 18, 0.85), (855, 20, 1.00), (1142, 16, 0.70), (1315, 15, 0.80), (1556, 24, 0.90)],
    "Ciprofloxacin":[(632, 18, 0.90), (878, 16, 0.75), (1110, 14, 1.00), (1342, 18, 0.65), (1622, 22, 0.85)],
    "Metronidazole":[(770, 20, 0.70), (1028, 18, 1.00), (1195, 15, 0.80), (1354, 16, 0.85), (1489, 22, 0.60)],
    "Diclofenac":  [(548, 22, 0.65), (898, 18, 0.90), (1198, 16, 0.80), (1398, 20, 1.00), (1588, 25, 0.75)],
}


def main():
    db = SessionLocal()

    print("[+] Starting database seeding...")

    # ── Clear existing data (order matters due to FK constraints) ─────────────
    print("  Clearing existing seed data...")
    db.query(Report).delete()
    db.query(SpectraData).delete()
    db.query(Test).delete()
    db.query(ReferenceSpectrum).delete()
    db.query(ChatMessage).delete()
    db.query(User).delete()
    db.commit()

    # ── Users ─────────────────────────────────────────────────────────────────
    print("  Creating users...")
    users = [
        User(
            full_name="Dr. Admin User",
            email="admin@spectraguard.com",
            password_hash=hash_password("Admin@1234"),
            phone="+1-555-0100",
            role=UserRole.admin,
            organization="SpectraGuard HQ",
            designation="System Administrator",
            city="New York",
        ),
        User(
            full_name="Dr. Sarah Chen",
            email="sarah.chen@pharmacy.com",
            password_hash=hash_password("Pharma@1234"),
            phone="+1-555-0101",
            role=UserRole.pharmacist,
            organization="City Pharmacy Network",
            license_number="PH-2024-001",
            designation="Senior Pharmacist",
            city="Los Angeles",
        ),
        User(
            full_name="Dr. James Okonkwo",
            email="j.okonkwo@pharmacy.com",
            password_hash=hash_password("Pharma@5678"),
            phone="+1-555-0102",
            role=UserRole.pharmacist,
            organization="MediCare Pharmacy",
            license_number="PH-2024-002",
            designation="Chief Pharmacist",
            city="Chicago",
        ),
        User(
            full_name="Agent Maria Lopez",
            email="m.lopez@fda.gov",
            password_hash=hash_password("Invest@1234"),
            phone="+1-555-0103",
            role=UserRole.investigator,
            organization="FDA Drug Enforcement",
            license_number="INV-2024-001",
            designation="Field Investigator",
            city="Washington DC",
        ),
        User(
            full_name="Public User",
            email="user@example.com",
            password_hash=hash_password("User@1234"),
            phone="+1-555-0104",
            role=UserRole.public,
            city="Seattle",
        ),
    ]

    for u in users:
        db.add(u)
    db.flush()
    print(f"    [OK] {len(users)} users created")

    # ── Reference Spectra ──────────────────────────────────────────────────────
    print("  Creating reference spectra...")
    wavenumbers = generate_wavenumbers(400, 1800, 200)
    admin_id = users[0].id

    references = []
    manufacturers = [
        "PharmaCorp International",
        "BioSynth Laboratories",
        "MediGen Pharma",
        "GlobalRx Solutions",
        "NovaMed Industries",
    ]

    for i, (drug_name, peaks) in enumerate(DRUG_PROFILES.items()):
        intensity = generate_drug_spectrum(wavenumbers, peaks, noise_level=0.01, random_seed=i)
        ref = ReferenceSpectrum(
            drug_name=drug_name,
            manufacturer=manufacturers[i % len(manufacturers)],
            batch_reference=f"REF-{drug_name[:3].upper()}-2024-{i+1:03d}",
            wavenumber_data=json.dumps(wavenumbers),
            intensity_data=json.dumps(intensity),
            source="WHO Pharmaceutical Reference Standards",
            added_by=admin_id,
        )
        db.add(ref)
        references.append((ref, drug_name, peaks))

    db.flush()
    print(f"    [OK] {len(references)} reference spectra created")

    # ── Tests + Spectra Data ───────────────────────────────────────────────────
    print("  Creating test records and spectral data...")
    test_users = [users[1], users[2], users[3], users[4]]

    test_configs = [
        # (user_idx, drug_name, noise_level, result, days_ago)
        (0, "Paracetamol",   0.015, ClassificationResult.genuine,               7),
        (0, "Ibuprofen",     0.900, ClassificationResult.potentially_counterfeit, 5),
        (1, "Amoxicillin",   0.020, ClassificationResult.genuine,               3),
        (1, "Metformin",     0.400, ClassificationResult.requires_verification,  2),
        (2, "Atorvastatin",  0.018, ClassificationResult.genuine,               1),
        (2, "Azithromycin",  0.800, ClassificationResult.potentially_counterfeit, 4),
        (3, "Omeprazole",    0.022, ClassificationResult.genuine,               6),
        (3, "Ciprofloxacin", 0.300, ClassificationResult.requires_verification,  1),
    ]

    ref_map = {drug: (ref_obj, peaks) for ref_obj, drug, peaks in references}

    for cfg in test_configs:
        user_idx, drug_name, noise, result, days_ago = cfg
        test_user = test_users[user_idx]
        ref_obj, peaks = ref_map[drug_name]

        # Generate uploaded spectrum with the specified noise level
        intensity = generate_drug_spectrum(
            wavenumbers, peaks, noise_level=noise, random_seed=user_idx * 100
        )

        confidence_map = {
            ClassificationResult.genuine: round(random.uniform(97.5, 99.8), 2),
            ClassificationResult.requires_verification: round(random.uniform(85.0, 96.9), 2),
            ClassificationResult.potentially_counterfeit: round(random.uniform(40.0, 84.9), 2),
        }

        test = Test(
            user_id=test_user.id,
            drug_name=drug_name,
            batch_number=f"BATCH-{drug_name[:3].upper()}-{random.randint(1000, 9999)}",
            manufacturer=ref_obj.manufacturer,
            expiry_date=f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            uploaded_csv_path=f"uploads/{test_user.id}/{drug_name.lower()}_spectrum.csv",
            classification_result=result,
            confidence_score=confidence_map[result],
            matched_reference_id=ref_obj.id,
            tested_at=datetime.utcnow() - timedelta(days=days_ago),
        )
        db.add(test)
        db.flush()

        spectra = SpectraData(
            test_id=test.id,
            wavenumber_data=json.dumps(wavenumbers),
            intensity_data=json.dumps(intensity),
        )
        db.add(spectra)

    db.commit()
    print(f"    [OK] {len(test_configs)} tests + spectral data records created")

    # ── Sample CSV Files ───────────────────────────────────────────────────────
    print("  Creating sample CSV files for demo...")
    os.makedirs("sample_data", exist_ok=True)

    # Genuine samples (low noise — should classify as genuine)
    for i, (drug_name, peaks) in enumerate(DRUG_PROFILES.items()):
        intensity = generate_drug_spectrum(wavenumbers, peaks, noise_level=0.015, random_seed=42 + i)
        csv_path = f"sample_data/{drug_name.lower().replace(' ', '_')}_genuine.csv"
        with open(csv_path, "w") as f:
            f.write("wavenumber,intensity\n")
            for wn, it in zip(wavenumbers, intensity):
                f.write(f"{wn},{it}\n")
        print(f"    [OK] {csv_path}")

    # Counterfeit samples (high noise — should classify as counterfeit/requires verification)
    counterfeit_drugs = ["Paracetamol", "Amoxicillin", "Ibuprofen"]
    for i, drug_name in enumerate(counterfeit_drugs):
        peaks = DRUG_PROFILES[drug_name]
        intensity = generate_drug_spectrum(wavenumbers, peaks, noise_level=1.2, random_seed=99 + i)
        csv_path = f"sample_data/{drug_name.lower().replace(' ', '_')}_counterfeit.csv"
        with open(csv_path, "w") as f:
            f.write("wavenumber,intensity\n")
            for wn, it in zip(wavenumbers, intensity):
                f.write(f"{wn},{it}\n")
        print(f"    [OK] {csv_path}")

    # Borderline samples (medium noise — should classify as requires_verification)
    borderline_drugs = ["Metformin", "Ciprofloxacin"]
    for i, drug_name in enumerate(borderline_drugs):
        peaks = DRUG_PROFILES[drug_name]
        intensity = generate_drug_spectrum(wavenumbers, peaks, noise_level=0.35, random_seed=200 + i)
        csv_path = f"sample_data/{drug_name.lower().replace(' ', '_')}_borderline.csv"
        with open(csv_path, "w") as f:
            f.write("wavenumber,intensity\n")
            for wn, it in zip(wavenumbers, intensity):
                f.write(f"{wn},{it}\n")
        print(f"    [OK] {csv_path}")

    db.close()

    print("\n[+] Database seeding complete!")
    print("\n[+] Seeded Credentials:")
    print("  Admin:        admin@spectraguard.com     / Admin@1234")
    print("  Pharmacist 1: sarah.chen@pharmacy.com    / Pharma@1234")
    print("  Pharmacist 2: j.okonkwo@pharmacy.com     / Pharma@5678")
    print("  Investigator: m.lopez@fda.gov             / Invest@1234")
    print("  Public:       user@example.com            / User@1234")
    print("\n[+] Run the API:  uvicorn app.main:app --reload")
    print("[+] API Docs:     http://localhost:8000/docs")


if __name__ == "__main__":
    main()
