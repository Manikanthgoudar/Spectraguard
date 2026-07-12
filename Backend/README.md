# SpectraGuard Backend API

AI-based pharmaceutical authentication system using Raman spectroscopy.  
Built with **FastAPI + MySQL + SQLAlchemy + scikit-learn**.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- MySQL 8.0+ (running locally or via Docker)
- pip

### 2. Install Dependencies
```bash
cd Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
copy .env.example .env
# Edit .env — set your MySQL credentials
```

Key `.env` values:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=spectraguard
JWT_SECRET_KEY=change-this-in-production
```

### 4. Create MySQL Database
```sql
CREATE DATABASE spectraguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. Seed with Mock Data
```bash
python scripts/seed_db.py
```

Seeded accounts:

| Role         | Email                       | Password     |
|--------------|-----------------------------|--------------|
| Admin        | admin@spectraguard.com      | Admin@1234   |
| Pharmacist   | sarah.chen@pharmacy.com     | Pharma@1234  |
| Pharmacist   | j.okonkwo@pharmacy.com      | Pharma@5678  |
| Investigator | m.lopez@fda.gov             | Invest@1234  |
| Public       | user@example.com            | User@1234    |

### 7. Run the API
```bash
python run.py
# or
uvicorn app.main:app --reload
```

API available at: http://localhost:8000  
Swagger UI:       http://localhost:8000/docs  
ReDoc:            http://localhost:8000/redoc  

---

## Project Structure

```
Backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, routers
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models/              # ORM models (User, Test, ReferenceSpectrum, ...)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # Route handlers (auth, spectra, classify, ...)
│   ├── services/
│   │   ├── classification.py   # AI classification engine
│   │   ├── csv_parser.py       # CSV upload + validation
│   │   └── report_generator.py # PDF report generation
│   └── core/
│       ├── security.py      # JWT + bcrypt
│       ├── dependencies.py  # Auth guards (get_current_user, require_admin)
│       └── logging_config.py
├── alembic/                 # Database migrations
├── scripts/
│   └── seed_db.py           # Mock data seeder
├── requirements.txt
├── .env                     # Local config (not committed)
└── run.py                   # Dev server entrypoint
```

---

## API Endpoints

### Authentication
| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| POST   | /auth/signup          | Register (role-based staged signup)  |
| POST   | /auth/login           | Login → JWT access + refresh tokens  |
| POST   | /auth/refresh-token   | Refresh access token                 |
| GET    | /auth/me              | Current user profile                 |

### Spectrum Upload
| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| POST   | /spectra/upload           | Upload CSV, creates test record    |
| GET    | /spectra/sample-datasets  | List demo sample CSVs              |
| GET    | /spectra/{test_id}        | Get parsed spectral data           |

### AI Classification
| Method | Endpoint                              | Description                        |
|--------|---------------------------------------|------------------------------------|
| POST   | /classify/{test_id}                   | Run AI classification              |
| GET    | /classify/reference-matches/{test_id} | Top-N reference matches            |

### Tests
| Method | Endpoint          | Description                          |
|--------|-------------------|--------------------------------------|
| GET    | /tests            | List tests (with filters)            |
| GET    | /tests/{test_id}  | Full test detail                     |
| DELETE | /tests/{test_id}  | Delete a test                        |

### Reference Database (Admin)
| Method | Endpoint            | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | /reference          | List all reference spectra           |
| POST   | /reference          | Add new reference (admin only)       |
| PUT    | /reference/{id}     | Update reference (admin only)        |
| DELETE | /reference/{id}     | Remove reference (admin only)        |

### Reports
| Method | Endpoint                      | Description                      |
|--------|-------------------------------|----------------------------------|
| POST   | /reports/generate/{test_id}   | Generate PDF report              |
| GET    | /reports/{test_id}            | Download PDF report              |

### Admin Dashboard
| Method | Endpoint         | Description                          |
|--------|------------------|--------------------------------------|
| GET    | /admin/stats     | Aggregate statistics                 |
| GET    | /admin/users     | List/filter all users                |
| PATCH  | /admin/users/{id}| Update user role/status              |

---

## AI Classification Logic

1. **Upload** — CSV parsed, wavenumber + intensity arrays stored in DB  
2. **Preprocess** — Sort by wavenumber → resample to 512-point grid (cubic interpolation) → Savitzky-Golay smoothing → rubber-band baseline correction → L2 normalisation  
3. **Compare** — Compute cosine similarity + Euclidean distance against every entry in `reference_spectra`  
4. **Classify**:
   - Cosine similarity ≥ 0.97 → **Genuine**  
   - Cosine similarity < 0.85 → **Potentially Counterfeit**  
   - 0.85–0.97 → **Requires Further Verification**  
5. **Store** — Result, confidence score, and best-matched reference ID saved to test record  

---

## CSV Format

Uploaded files must have at minimum two columns:

```csv
wavenumber,intensity
400.0,0.0512
402.5,0.0634
...
```

Accepted column aliases:
- **Wavenumber**: `wavenumber`, `wavenumbers`, `raman_shift`, `raman shift`, `wave`, `cm-1`, `cm_1`
- **Intensity**: `intensity`, `intensities`, `counts`, `signal`, `absorbance`

Minimum 10 data rows required.
