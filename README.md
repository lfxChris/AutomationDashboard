# Automation Dashboard

TV-friendly status board for healthchecks.io automations.

- **Frontend**: Vue 3 + Vite (`frontend-vue/`), deployed to GitHub Pages.
- **Backend**: FastAPI (`backend/`), deployed to Render. Talks to the healthchecks.io API and enriches each check with `last_run_age`, `next_expected_relative`, formatted period/grace, etc.

## Local dev

### Backend

```powershell
cd backend
Copy-Item .env.example .env   # then fill in HC_API_KEY
..\.venv\Scripts\python -m pip install -r requirements.txt
..\.venv\Scripts\python -m uvicorn app:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

### Frontend

```powershell
cd frontend-vue
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. By default it calls `http://127.0.0.1:8000/checks`. To point it elsewhere, create `frontend-vue/.env` with `VITE_API_URL=https://your-backend-url`.

## Deployment

### Backend (Render)

1. New > Web Service > connect this repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Environment variables:
   - `HC_API_KEY` = your healthchecks.io read-only API key
   - `ALLOWED_ORIGINS` = your GitHub Pages URL, e.g. `https://<user>.github.io`

### Frontend (GitHub Pages)

1. Repo Settings > Pages > Source: **GitHub Actions**.
2. Repo Settings > Secrets and variables > Actions > **Variables**:
   - `VITE_BASE` = `/<repo-name>/` (e.g. `/AutomationDashboard/`)
   - `VITE_API_URL` = `https://<your-render-app>.onrender.com`
3. Push to `main` — `.github/workflows/deploy-pages.yml` builds and publishes.
