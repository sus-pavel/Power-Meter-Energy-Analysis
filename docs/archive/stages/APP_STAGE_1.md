# App Stage 1: v0.2.0-app-core

Stage 1 introduces the application backend foundation without changing the research prototype pipeline.

## Implemented

- FastAPI application shell at `backend.app.main:app`.
- SQLite initialization for `users`, `devices`, `device_registers`, and `audit_log`.
- Local password hashing.
- HMAC JWT authentication.
- Role-based permission checks.
- Default admin user creation when the user table is empty.
- Device CRUD API.
- Register map CRUD API.
- Safe Modbus probe placeholder.
- Health endpoint.
- Minimal dashboard summary endpoint.
- Basic admin user management API.

## Run

Install dependencies, then start the app backend:

```bash
uvicorn backend.app.main:app --reload
```

Open:

- API health: `http://127.0.0.1:8000/api/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

The app database is created at `data/powermeter_app.db`.

## Default Admin

On first startup, if no users exist, the backend creates:

- username: `admin`
- password: `admin`
- role: `admin`

Warning: change this password before any real use. The default is only for local prototype startup.

## API Endpoints

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/users`
- `POST /api/users`
- `GET /api/users/{user_id}`
- `PUT /api/users/{user_id}`
- `DELETE /api/users/{user_id}`
- `GET /api/devices`
- `POST /api/devices`
- `GET /api/devices/{device_id}`
- `PUT /api/devices/{device_id}`
- `DELETE /api/devices/{device_id}`
- `GET /api/devices/{device_id}/registers`
- `POST /api/devices/{device_id}/registers`
- `PUT /api/devices/{device_id}/registers/{register_id}`
- `DELETE /api/devices/{device_id}/registers/{register_id}`
- `POST /api/devices/{device_id}/probe`
- `GET /api/dashboard/summary`

Use the token from `/api/auth/login` as a bearer token:

```http
Authorization: Bearer <token>
```

## Known Limitations

- Logout is client-side only because Stage 1 uses stateless JWTs.
- The JWT secret defaults to a local development value. Set `POWERMETER_JWT_SECRET` for real use.
- Device probing is a placeholder and does not open network connections.
- No frontend or desktop wrapper is included in Stage 1.
- Audit log entries are written for create, update, and delete operations, but no audit viewing endpoint exists yet.

## Stage 2 Plan

Stage 2 will implement Modbus Device Discovery and Register Probe:

- scan IP range;
- check port `502`;
- test Modbus TCP connection;
- scan `unit_id` range;
- safely probe registers;
- save discovered candidates;
- add discovered device to the managed device list.
