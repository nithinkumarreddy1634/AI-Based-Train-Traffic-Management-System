# Setup & Installation Guide

**Project**: Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control  
**Phase**: Phase 12 Production Readiness & Final Integration  
**Status**: Verified Academic Simulation & Decision-Support Prototype  

---

## 1. System Requirements

### Hardware Prerequisites
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher (Quad-core recommended).
- **Memory**: Minimum 4 GB RAM (8 GB recommended for concurrent simulation & ML inference).
- **Storage**: 1 GB free disk space.

### Software Prerequisites
- **Python**: Version 3.10 to 3.14+
- **Node.js**: Version 18.0+ (with npm 9+)
- **Git**: Version 2.30+
- **Web Browser**: Google Chrome, Mozilla Firefox, or Microsoft Edge (modern Chromium).

---

## 2. Repository & Workspace Setup

Clone the repository and enter the project root directory:

```bash
git clone <repository-url>
cd "Maximizing Section Throughput Using Al- Powered Precise Train Traffic Control"
```

---

## 3. Environment Configuration

Copy the sample environment template to `.env`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

### Configuration Variables (`.env`)
```ini
# Project Metadata
PROJECT_NAME="Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control"
PROJECT_PHASE="Phase 12: Production Readiness & Final Integration"
API_VERSION=1.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Backend Server Binding
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///./train_control.db

# Simulation Engine & ML Artifacts
SIMULATION_SPEED=1.0
ML_MODEL_PATH=ml/saved_models/delay_prediction_model.pkl

# Frontend Integration & CORS
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
```

> **Security Note**: Never commit `.env` to version control. The `.gitignore` file is preconfigured to exclude all `.env` files and SQLite `.db` databases.

---

## 4. Backend Setup & Startup

### Step 4.1: Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4.2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4.3: Initialize and Deterministically Seed the Database
Populate the railway infrastructure, rolling stock fleet, and benchmark scenarios:

```bash
python -m data.seed --seed 42
```
*Optional: To reset and wipe the database before seeding, pass `--reset`:*
```bash
python -m data.seed --seed 42 --reset
```

### Step 4.4: Launch the FastAPI Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend server is accessible at:
- **API Root**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Technical Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health Probe**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 5. Frontend Setup & Startup

Open a new terminal window in the project root:

```bash
cd frontend
```

### Step 5.1: Install Node Dependencies
```bash
npm install
```

### Step 5.2: Start Vite Development Server
```bash
npm run dev
```

The application will launch on:
- **Operations Control Center**: [http://localhost:5173](http://localhost:5173)

### Step 5.3: Production Build (Optional)
To verify or compile a production bundle:
```bash
npm run build
```
The compiled assets will be placed in `frontend/dist/`.

---

## 6. Running Automated Tests

Ensure your virtual environment is active, then execute:

```bash
pytest tests/ -v
```

All 120+ tests covering Phases 1 through 12 will execute and report a 100% pass rate.

To run only the end-to-end pipeline test:
```bash
pytest tests/test_phase12_end_to_end.py -v
```

---

## 7. Troubleshooting & FAQ

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Port 8000 already in use** | An existing background server is running | Kill the existing process: `Get-Process python \| Stop-Process` on Windows, or specify `--port 8001`. |
| **CORS connection error in frontend** | Backend is not running or origin mismatch | Ensure backend is active on `http://127.0.0.1:8000` and verify `ALLOWED_ORIGINS` in `.env`. |
| **ML Model Unavailable notice** | Model artifacts missing from `ml/saved_models/` | Run `python -m ml.models.train_model` to train and serialize the model. |
| **PowerShell script execution disabled** | Windows security policy restricts scripts | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell before activating `.venv`. |
| **Database table locked** | Concurrent SQLite writes from multiple processes | The connection engine sets `check_same_thread=False` and uses WAL mode; avoid accessing `train_control.db` in external DB editors during simulation. |

