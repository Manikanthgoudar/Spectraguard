import logging
from sqlalchemy import text, inspect
from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate():
    inspector = inspect(engine)
    existing_cols = [c["name"] for c in inspector.get_columns("reference_spectra")]
    logger.info(f"Existing columns in reference_spectra: {existing_cols}")

    new_cols = [
        ("dataset_id", "VARCHAR(100) NULL"),
        ("dataset_name", "VARCHAR(255) NULL"),
        ("source_institution", "VARCHAR(255) NULL"),
        ("source_url", "VARCHAR(500) NULL"),
        ("doi", "VARCHAR(255) NULL"),
        ("license", "VARCHAR(100) NULL"),
        ("sample_type", "VARCHAR(100) NULL"),
        ("spectral_range_original", "VARCHAR(100) NULL"),
        ("spectral_resolution_original", "VARCHAR(100) NULL"),
        ("laser_wavelength", "VARCHAR(100) NULL"),
        ("spectrometer", "VARCHAR(255) NULL"),
        ("original_filename", "VARCHAR(255) NULL"),
        ("original_sample_id", "VARCHAR(100) NULL"),
        ("preprocessing_method", "VARCHAR(255) NULL"),
        ("missing_range", "VARCHAR(255) NULL"),
        ("sample_status", "VARCHAR(50) NULL DEFAULT 'AUTHENTIC'"),
        ("reference_status", "VARCHAR(50) NULL DEFAULT 'ACTIVE'"),
    ]

    with engine.begin() as conn:
        for col_name, col_def in new_cols:
            if col_name not in existing_cols:
                logger.info(f"Adding column '{col_name}' to MySQL table 'reference_spectra'...")
                try:
                    conn.execute(text(f"ALTER TABLE reference_spectra ADD COLUMN {col_name} {col_def}"))
                    logger.info(f"Successfully added column '{col_name}'")
                except Exception as e:
                    logger.error(f"Failed to add column '{col_name}': {e}")
            else:
                logger.info(f"Column '{col_name}' already exists.")

if __name__ == "__main__":
    migrate()
