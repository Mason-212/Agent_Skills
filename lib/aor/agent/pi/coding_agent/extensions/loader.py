"""Dynamic extension loader (importlib).

Python port of `vendor/pi-mono-upstream/packages/coding-agent/src/core/extensions/loader.ts`.
Differences:

- Upstream uses a `jiti` TypeScript loader to `import` `.ts` files; we use
  `importlib.util.spec_from_file_location` to load `.py` files directly.
- Each extension module must define a top-level ``register(pi)`` callable.
- Extensions are cached by `(absolute_path, mtime)`; re-calling
  `load_extensions` with an unchanged path is a no-op that reuses the
  prior `Extension` result.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import traceback
import uuid
from dataclasses import dataclass, field

from .types import Extension, ExtensionAPI, ExtensionError


@dataclass
class LoadExtensionsResult:
    extensions: list[Extension] = field(default_factory=list)
    errors: list[ExtensionError] = field(default_factory=list)


_CACHE: dict[str, tuple[float, Extension]] = {}
# Tracks the synthetic ``sys.modules`` name we last assigned to each resolved
# extension path so a reload can purge the previous entry. Without this every
# reload leaks one ``pi_ext_<uuid>`` entry for the lifetime of the process.
_MODULE_NAMES: dict[str, str] = {}


def _expand(path: str) -> str:
    expanded = os.path.expanduser(path.strip())
    return os.path.abspath(expanded)


def _import_module_from_file(resolved: str) -> object:
    prev_name = _MODULE_NAMES.pop(resolved, None)
    if prev_name is not None:
        sys.modules.pop(prev_name, None)
    mod_name = f"pi_ext_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to build import spec for {resolved}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(mod_name, None)
        raise
    _MODULE_NAMES[resolved] = mod_name
    return module


def reload_extension(path: str) -> Extension:
    """Force-reload a single extension, bypassing the mtime cache."""
    resolved = _expand(path)
    if not os.path.isfile(resolved):
        raise FileNotFoundError(resolved)
    module = _import_module_from_file(resolved)
    register = getattr(module, "register", None)
    if not callable(register):
        raise AttributeError(f"extension {resolved} has no top-level `register(pi)` callable")
    api = ExtensionAPI(extension_path=resolved)
    register(api)
    ext = Extension(path=path, resolved_path=resolved, api=api)
    _CACHE[resolved] = (os.path.getmtime(resolved), ext)
    return ext


def load_extensions(paths: list[str]) -> LoadExtensionsResult:
    """Load extensions from a list of file paths.

    Paths may be absolute, `~`-prefixed, or relative to the current
    working directory. Each file must define a top-level
    ``register(pi)`` callable; errors are captured and returned in the
    `errors` list rather than raised so a single bad extension cannot
    break a session.
    """
    result = LoadExtensionsResult()
    for raw in paths:
        resolved = _expand(raw)
        if not os.path.isfile(resolved):
            result.errors.append(ExtensionError(path=raw, error="file does not exist"))
            continue
        try:
            mtime = os.path.getmtime(resolved)
            cached = _CACHE.get(resolved)
            if cached and cached[0] == mtime:
                result.extensions.append(cached[1])
                continue
            ext = reload_extension(resolved)
            result.extensions.append(ext)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(
                ExtensionError(
                    path=raw,
                    error=f"{exc}\n{traceback.format_exc(limit=3)}",
                )
            )
    return result


__all__ = ["LoadExtensionsResult", "load_extensions", "reload_extension"]
