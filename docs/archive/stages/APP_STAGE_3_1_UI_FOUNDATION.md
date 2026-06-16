# App Stage 3.1: UI Foundation

Stage 3.1 introduces the first React application shell for PowerMeter. It does not implement discovery execution, candidate review, device editing, realtime charts, DRPI, SSA, or desktop packaging.

## Frontend Architecture

The frontend lives in `frontend/` and uses:

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- TailwindCSS
- lucide-react

Source layout:

```text
frontend/src/
  app/
  api/
  auth/
  layouts/
  pages/
  components/
  hooks/
  types/
  routes/
  styles/
```

## Auth Flow

The login page calls `POST /api/auth/login` and stores the returned JWT in local storage. `AuthContext` loads the current user with `GET /api/auth/me`, exposes `login`, `logout`, `current user`, and role state, and clears the session on API `401` responses.

## Routing

- `/` redirects to `/dashboard` when authenticated.
- `/` redirects to `/login` when unauthenticated.
- `/login` is public.
- `/dashboard`, `/devices`, `/discovery`, `/analytics`, and `/admin` are protected.
- `/403`, `/404`, `/500`, and `/401` error screens are available.

## Permissions

Navigation and protected routes use role-aware rules:

- `guest`: Dashboard
- `analyst`: Dashboard, Analytics
- `chief_engineer`: Dashboard, Devices, Discovery, Analytics
- `admin`: Dashboard, Devices, Discovery, Analytics, Administration

## UI Structure

The app shell uses a compact industrial layout:

- top bar with logo, current user, role, logout;
- left sidebar navigation;
- dense page content region;
- reusable page header, status cards, loading, empty, error, role badge, and user menu components.

## API Integrations

Implemented integrations:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/dashboard/summary`
- `GET /api/devices`

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Run

Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Future Stages

Stage 3.2 can build directly on this shell:

- device list and editor;
- discovery scan form;
- scan job progress;
- candidate review;
- probe results;
- promotion workflow;
- register map editor.
