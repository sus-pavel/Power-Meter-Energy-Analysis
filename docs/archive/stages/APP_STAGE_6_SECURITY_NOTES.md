# Stage 6 Security Notes

Stage 6 is local-first macOS desktop packaging. It does not add cloud services, Docker, auto-update, Developer ID signing, or notarization.

## Local Binding

The packaged backend binds only to:

```text
127.0.0.1
```

Desktop mode must not bind to `0.0.0.0`.

## Local Secrets

If `POWERMETER_JWT_SECRET` is not set in desktop mode, the backend creates a local secret at:

```text
~/Library/Application Support/PowerMeter/config/jwt_secret
```

The generated secret is outside the repository and outside the `.app` bundle.

## Database Location

The desktop SQLite database is stored at:

```text
~/Library/Application Support/PowerMeter/app.sqlite
```

Runtime databases must not be stored inside the repository or the app bundle.

## Credentials and Logs

The backend must not log passwords, JWT tokens, or future Modbus credentials. Stage 6 keeps JWT storage behavior unchanged from the React app; tokens remain in frontend local storage.

## First-Run Admin

If no users exist, the app creates:

```text
admin / admin
```

The UI flags this account with a warning until the password is changed. A dedicated first-run password-change screen is deferred to Stage 6.1.
