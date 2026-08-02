"""Resolve the Salesforce Eng AI Model Gateway base URL.

This is the single seam between the deployment environment and
`models_catalog.catalog`. Callers must not read these env vars directly;
all gateway URL resolution goes through `resolve_gateway_base_url()`.

Resolution order (highest priority first):

1. ``ENG_AI_MODEL_GW_URL`` env var -- full URL override. Ops can point
   a running service at any endpoint (including a local mitmproxy or a
   sandbox) without a code change.

2. TODO(gateway-url): per-environment derivation for dev/stage/prod.
   We currently only know the preprod hostname shape
   (``devx-preprod.aws-esvc1-useast2``); the production and staging
   hostnames are not yet available in this repo. When they are, this
   module should grow a lookup that mirrors
   ``aip_model_store_client.url_utils.derive_aip_model_store_url_from_env``
   -- likely keyed on ``P_FALCON_INSTANCE`` for consistency. Until then,
   deployed pods must set ``ENG_AI_MODEL_GW_URL`` explicitly, and we
   emit a ``UserWarning`` when a deployed environment is detected
   without an override so the misconfiguration is loud.

3. Local-dev default: the devx-preprod URL. This keeps laptop workflows
   (unit tests, notebooks, ad-hoc scripts) working with zero setup, the
   same way they do today.

Future work hook: a separate workstream is planned to route LLM calls
via an internal path (not direct HTTPS). That path should flow through
this same resolver so the public surface
(``resolve_gateway_base_url()``) stays stable and there is one place
to reason about how the Gateway endpoint is chosen.
"""

from __future__ import annotations

import os
import warnings

_OVERRIDE_ENV = "ENG_AI_MODEL_GW_URL"
_DEPLOYMENT_HINT_ENV = "P_FALCON_INSTANCE"

# Local-dev default. See TODO(gateway-url) in the module docstring for
# how this should evolve when non-preprod URLs are known.
_LOCAL_DEV_DEFAULT = (
    "https://eng-ai-model-gateway.sfproxy.devx-preprod.aws-esvc1-useast2.aws.sfdc.cl"
)


def resolve_gateway_base_url() -> str:
    """Return the Gateway base URL for the current process.

    Called once, eagerly, at ``catalog.py`` import time. If the process
    changes ``os.environ`` after import, the change will not be picked
    up -- matching the lifecycle of every other `Model` field in the
    static catalog.
    """
    explicit = os.environ.get(_OVERRIDE_ENV, "").strip()
    if explicit:
        return explicit

    # Heuristic: if a deployment hint is present, we are almost certainly
    # running in a pod rather than on a developer laptop. Falling back to
    # the preprod URL there is a misconfiguration, so make it visible.
    if os.environ.get(_DEPLOYMENT_HINT_ENV, "").strip():
        warnings.warn(
            "Falling back to the preprod Salesforce AI Model Gateway URL "
            f"because {_OVERRIDE_ENV} is unset while {_DEPLOYMENT_HINT_ENV} "
            "indicates a deployed environment. Set "
            f"{_OVERRIDE_ENV} explicitly, or add per-environment "
            "derivation here (see TODO(gateway-url) in _gateway_url.py).",
            stacklevel=2,
        )

    return _LOCAL_DEV_DEFAULT


__all__ = ["resolve_gateway_base_url"]
