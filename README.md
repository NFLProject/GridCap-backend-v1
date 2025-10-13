# GridCap Monorepo

GridCap is an NFL fantasy football salary-cap platform. This monorepo contains the FastAPI backend and the Next.js frontend.

## Repository structure

```
gridcap/
  backend/        # FastAPI application
  frontend/       # Next.js 14 client
  render.yaml     # Render deployment config for backend
  vercel.json     # Vercel configuration for frontend
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- pip

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./dev.db"
export JWT_SECRET="change_me"
export FRONTEND_ORIGIN="http://localhost:3000"
uvicorn app:app --reload
```

The API will run on `http://localhost:8000`. Player data seeds automatically on first launch.

## Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local # optional if you create one
# Ensure NEXT_PUBLIC_API_BASE points to your backend (default below)
export NEXT_PUBLIC_API_BASE="http://localhost:8000/api"
npm run dev
```

Access the app at `http://localhost:3000`.

## Running tests

Backend unit and integration tests are handled with `pytest`:

```bash
cd backend
pytest
```

## Deployment

### Backend (Render)

1. Create a new Web Service from the repo root.
2. Use the included `render.yaml` or configure manually:
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `cd backend && uvicorn app:app --host 0.0.0.0 --port 8000`
3. Configure environment variables:
   - `DATABASE_URL=sqlite:////var/data/db.sqlite3`
   - `JWT_SECRET=<secure secret>`
   - `FRONTEND_ORIGIN=https://your-frontend-domain`
4. Attach a persistent disk mounted at `/var/data`.

### Frontend (Vercel)

1. Import the repo into Vercel.
2. Set `NEXT_PUBLIC_API_BASE` to your Render backend URL (e.g. `https://your-backend.onrender.com/api`).
3. Deploy using default Next.js settings.

## Salary cap rules

- Salary cap: $100m
- Squad size: 15 players
- Lineup: 9 starters with captain and vice selected from starters

## API overview

All endpoints are under `/api`. Authenticate using the JWT returned from `/api/auth/login` or `/api/auth/register` via the `Authorization: Bearer <token>` header.

Key endpoints:

- `POST /api/auth/register` — create account
- `POST /api/auth/login` — obtain token
- `GET /api/auth/me` — current user
- `POST /api/leagues/create` — create league
- `POST /api/leagues/join` — join league
- `GET /api/leagues/mine` — list user leagues
- `GET /api/players` — player pool
- `POST /api/squad/save` — save squad of 15 players
- `GET /api/squad` — retrieve saved squad
- `POST /api/lineup/set` — save lineup
- `GET /api/standings/{league_id}` — league standings (placeholder scoring)

## Data seeding

The backend seeds roughly 30 NFL players on startup. Modify `backend/seed_players.py` to adjust the pool.

## Environment variables

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL. Default `sqlite:///./gridcap.db` |
| `JWT_SECRET` | Secret used to sign JWT tokens |
| `FRONTEND_ORIGIN` | Allowed CORS origin for frontend |
| `NEXT_PUBLIC_API_BASE` | Frontend environment, backend base URL including `/api` |

## Notes

- Passwords are hashed with bcrypt.
- JWT tokens expire after 7 days.
- Standings currently return zero points for all teams.
