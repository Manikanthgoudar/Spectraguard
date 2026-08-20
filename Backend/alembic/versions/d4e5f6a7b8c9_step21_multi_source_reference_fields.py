"""step21_multi_source_reference_fields

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extended multi-source reference fields
    op.add_column('reference_spectra', sa.Column('dataset_id', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('dataset_name', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('source_institution', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('reference_spectra', sa.Column('doi', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('license', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('sample_type', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('spectral_range_original', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('spectral_resolution_original', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('laser_wavelength', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('spectrometer', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('original_filename', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('original_sample_id', sa.String(length=100), nullable=True))
    op.add_column('reference_spectra', sa.Column('preprocessing_method', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('missing_range', sa.String(length=255), nullable=True))
    op.add_column('reference_spectra', sa.Column('sample_status', sa.String(length=50), nullable=True, server_default="AUTHENTIC"))
    op.add_column('reference_spectra', sa.Column('reference_status', sa.String(length=50), nullable=True, server_default="ACTIVE"))


def downgrade() -> None:
    op.drop_column('reference_spectra', 'reference_status')
    op.drop_column('reference_spectra', 'sample_status')
    op.drop_column('reference_spectra', 'missing_range')
    op.drop_column('reference_spectra', 'preprocessing_method')
    op.drop_column('reference_spectra', 'original_sample_id')
    op.drop_column('reference_spectra', 'original_filename')
    op.drop_column('reference_spectra', 'spectrometer')
    op.drop_column('reference_spectra', 'laser_wavelength')
    op.drop_column('reference_spectra', 'spectral_resolution_original')
    op.drop_column('reference_spectra', 'spectral_range_original')
    op.drop_column('reference_spectra', 'sample_type')
    op.drop_column('reference_spectra', 'license')
    op.drop_column('reference_spectra', 'doi')
    op.drop_column('reference_spectra', 'source_url')
    op.drop_column('reference_spectra', 'source_institution')
    op.drop_column('reference_spectra', 'dataset_name')
    op.drop_column('reference_spectra', 'dataset_id')
