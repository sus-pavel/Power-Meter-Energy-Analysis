from __future__ import annotations

import logging
import os
import sys

import uvicorn

from backend.app.core.desktop_paths import configure_desktop_environment


def configure_logging(log_path: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def main() -> None:
    paths = configure_desktop_environment()
    configure_logging(str(paths.backend_log_path))
    logging.getLogger(__name__).info(
        "Starting PowerMeter backend in desktop mode on 127.0.0.1:%s with database %s",
        os.getenv("POWERMETER_PORT", "8765"),
        os.getenv("POWERMETER_DB_PATH"),
    )
    from backend.app.main import app

    uvicorn.run(
        app,
        host=os.getenv("POWERMETER_HOST", "127.0.0.1"),
        port=int(os.getenv("POWERMETER_PORT", "8765")),
        log_config=None,
    )


if __name__ == "__main__":
    main()
