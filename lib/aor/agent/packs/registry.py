"""Convention-based domain pack discovery and loading.

A pack is any directory under the configured packs root that exposes a
``create_pack(workspace_dir: Path) -> BoundDomainPack`` factory in its
``__init__.py``.

Example layout::

    agents/packs/
        tabicl/
            __init__.py    # exposes create_pack(workspace_dir) -> BoundDomainPack
            ...
        moirai/
            __init__.py
            ...
"""

from __future__ import annotations

import importlib
from pathlib import Path

from agent.packs.base import BoundDomainPack

DEFAULT_WORKSPACE_ROOT = Path("/var/edc/packs")
DEFAULT_PACKS_PACKAGE = "agents.packs"


class PackLoadError(RuntimeError):
    """Raised when a pack cannot be discovered or loaded."""


def _is_valid_pack_id(pack_id: str) -> bool:
    """Pack ids must be valid Python identifiers so they can form module paths.

    `discover()` and `load()` share this rule so directories that pass
    discovery never fail at import time on the module-name level.
    """
    return bool(pack_id) and pack_id.isidentifier() and not pack_id.startswith("_")


def _validate_packs_root(packs_root: Path) -> None:
    """Raise PackLoadError if `packs_root` is not an existing directory."""
    if not packs_root.exists():
        raise PackLoadError(f"packs_root does not exist: {packs_root}")
    if not packs_root.is_dir():
        raise PackLoadError(f"packs_root is not a directory: {packs_root}")


class PackRegistry:
    """Discovers and loads packs by directory convention.

    Discovery rule: any subdirectory of ``packs_root`` that contains an
    ``__init__.py`` is treated as a pack candidate. The directory name is the
    pack id.

    Loading rule: ``load(pack_id)`` imports ``{packs_package}.{pack_id}`` and
    invokes ``create_pack(workspace_dir)`` on the resulting module.
    """

    def __init__(
        self,
        *,
        packs_root: Path | None = None,
        packs_package: str = DEFAULT_PACKS_PACKAGE,
        workspace_root: Path | None = None,
    ) -> None:
        if packs_root is not None:
            _validate_packs_root(packs_root)
        self._packs_root = packs_root
        self._packs_package = packs_package
        self._workspace_root = workspace_root or DEFAULT_WORKSPACE_ROOT

    @property
    def workspace_root(self) -> Path:
        return Path(self._workspace_root)

    def discover(self, packs_root: Path | None = None) -> list[str]:
        """Return pack ids discovered under ``packs_root``.

        A directory qualifies as a pack if it has an ``__init__.py`` and its
        name is a valid pack id (Python identifier, not underscore-prefixed).
        Order is sorted by id for deterministic iteration.
        """
        root = packs_root if packs_root is not None else self._packs_root
        if root is None:
            raise PackLoadError(
                "PackRegistry has no packs_root configured; pass one to "
                "discover() or to PackRegistry(packs_root=...)."
            )
        _validate_packs_root(root)

        pack_ids: list[str] = []
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            if not _is_valid_pack_id(entry.name):
                continue
            if not (entry / "__init__.py").exists():
                continue
            pack_ids.append(entry.name)
        pack_ids.sort()
        return pack_ids

    async def load(
        self,
        pack_id: str,
        *,
        workspace_root: Path | None = None,
    ) -> BoundDomainPack:
        """Load a pack by id and return an unopened instance.

        The caller is responsible for ``await pack.open()`` and
        ``await pack.close()``. Story 3/6 introduces the Session that owns
        that lifecycle; until then callers must do it themselves.

        Raises:
            PackLoadError: if the pack module cannot be imported or does not
                expose a callable ``create_pack`` factory.
        """
        if not _is_valid_pack_id(pack_id):
            raise PackLoadError(f"invalid pack_id: {pack_id!r}")

        module_name = f"{self._packs_package}.{pack_id}"
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise PackLoadError(
                f"could not import pack module {module_name!r}: {exc}"
            ) from exc

        factory = getattr(module, "create_pack", None)
        if factory is None or not callable(factory):
            raise PackLoadError(
                f"pack module {module_name!r} does not expose a callable "
                f"`create_pack(workspace_dir)` factory"
            )

        workspace_dir = self._ensure_workspace(pack_id, workspace_root)

        try:
            pack = factory(workspace_dir)
        except Exception as exc:
            raise PackLoadError(
                f"pack factory {module_name}.create_pack raised {type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(pack, BoundDomainPack):
            raise PackLoadError(
                f"pack factory {module_name}.create_pack returned "
                f"{type(pack).__name__}, expected a BoundDomainPack subclass"
            )
        return pack

    def _ensure_workspace(
        self,
        pack_id: str,
        workspace_root: Path | None,
    ) -> Path:
        root = workspace_root or self._workspace_root
        workspace_dir = root / pack_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir
