# Security Policy

PowerMeter App v0.2.0 is a local-first macOS beta. It is intended for trusted local machines and trusted local networks.

## Supported Version

Security fixes are tracked against the current app fork beta line:

```text
PowerMeter App v0.2.x
```

## Reporting Issues

Please do not publish sensitive security issues with real network details, device addresses, credentials, or site names. Open a private report with:

- affected version or commit;
- operating system;
- whether the issue affects backend, frontend, desktop packaging, or Modbus discovery;
- sanitized logs;
- steps to reproduce;
- expected and actual behavior.

## Local Security Model

- The packaged backend binds to `127.0.0.1`.
- Runtime data is stored under `~/Library/Application Support/PowerMeter/`.
- The desktop shell launches and terminates only the backend process it created.
- Port `8765` conflicts are reported instead of killing unknown processes.
- Production secrets must not be committed to the repository.

For implementation notes, see [docs/SECURITY_NOTES.md](docs/SECURITY_NOTES.md).
