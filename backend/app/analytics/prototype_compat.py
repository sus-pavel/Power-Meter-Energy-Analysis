from __future__ import annotations

import types
import sys
from pathlib import Path
from typing import Any

from backend.app.core.config import BASE_DIR


_CACHE: dict[str, types.ModuleType] = {}


def load_prototype_module(relative_path: str, module_name: str) -> types.ModuleType:
    """Load prototype source in Python 3.9 without changing prototype files."""
    if module_name in _CACHE:
        return _CACHE[module_name]
    path = BASE_DIR / relative_path
    source = Path(path).read_text(encoding="utf-8")
    source = source.replace("@dataclass(slots=True)", "@dataclass")
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    _CACHE[module_name] = module
    return module


def prototype_drpi_engine() -> Any:
    return load_prototype_module("core/drpi_engine.py", "powermeter_prototype_drpi")


def prototype_ssa_engine() -> Any:
    return load_prototype_module("core/ssa_engine.py", "powermeter_prototype_ssa")
