"""add_reference_metadata_and_test_fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extended reference spectra metadata ───────────────────────────────────
    op.add_column('reference_spectra', sa.Column('generic_name', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('brand_name', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('strength', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('dosage_form', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('reference_spectra', sa.Column('uses', sa.Text(), nullable=True))
    op.add_column('reference_spectra', sa.Column('storage_conditions', sa.String(length=500), nullable=True))
    op.add_column('reference_spectra', sa.Column('license_number', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('wavenumber_range', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('num_measurements', sa.Integer(), nullable=True))
    op.add_column('reference_spectra', sa.Column('similarity_threshold', sa.Float(), nullable=True))
    op.add_column('reference_spectra', sa.Column('spectrum_info', sa.Text(), nullable=True))

    # ── Extended test fields ───────────────────────────────────────────────────
    op.add_column('tests', sa.Column('strength', sa.String(length=100), nullable=True))
    op.add_column('tests', sa.Column('dosage_form', sa.String(length=100), nullable=True))
    op.add_column('tests', sa.Column('manufacturing_date', sa.String(length=50), nullable=True))
    op.add_column('tests', sa.Column('cosine_similarity', sa.Float(), nullable=True))
    op.add_column('tests', sa.Column('euclidean_distance', sa.Float(), nullable=True))
    op.add_column('tests', sa.Column('risk_level', sa.String(length=50), nullable=True))
    op.add_column('tests', sa.Column('peak_match_count', sa.Integer(), nullable=True))
    op.add_column('tests', sa.Column('peak_difference_summary', sa.Text(), nullable=True))
    op.add_column('tests', sa.Column('ai_explanation', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove test fields
    op.drop_column('tests', 'ai_explanation')
    op.drop_column('tests', 'peak_difference_summary')
    op.drop_column('tests', 'peak_match_count')
    op.drop_column('tests', 'risk_level')
    op.drop_column('tests', 'euclidean_distance')
    op.drop_column('tests', 'cosine_similarity')
    op.drop_column('tests', 'manufacturing_date')
    op.drop_column('tests', 'dosage_form')
    op.drop_column('tests', 'strength')

    # Remove reference fields
    op.drop_column('reference_spectra', 'spectrum_info')
    op.drop_column('reference_spectra', 'similarity_threshold')
    op.drop_column('reference_spectra', 'num_measurements')
    op.drop_column('reference_spectra', 'wavenumber_range')
    op.drop_column('reference_spectra', 'license_number')
    op.drop_column('reference_spectra', 'storage_conditions')
    op.drop_column('reference_spectra', 'uses')
    op.drop_column('reference_spectra', 'description')
    op.drop_column('reference_spectra', 'country')
    op.drop_column('reference_spectra', 'dosage_form')
    op.drop_column('reference_spectra', 'strength')
    op.drop_column('reference_spectra', 'brand_name')
    op.drop_column('reference_spectra', 'generic_name')
