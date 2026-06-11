"""Load a user-submitted policy file into a uniform callable.

Accepts any of these conventions in the submitted ``.py`` file:
  * a ``Policy`` class with ``act(obs)`` and optional ``reset()``
  * a module-level ``policy(obs)`` function
  * a ``build_policy()`` factory returning a callable (optionally with ``reset()``)

Returns a `LoadedPolicy` whose ``__call__(obs)`` is what the simulator drives, and
whose ``reset()`` is invoked by the engine before every rollout so stateful
policies start clean.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable


class LoadedPolicy:
    def __init__(self, fn: Callable[[dict], Any], reset: Callable[[], None] | None,
                 policy_id: str, source_path: str):
        self._fn = fn
        self._reset = reset
        self.policy_id = policy_id
        self.source_path = source_path

    def reset(self) -> None:
        if self._reset is not None:
            self._reset()

    def __call__(self, obs: dict) -> Any:
        return self._fn(obs)


def load_policy(path: str | Path, policy_id: str | None = None) -> LoadedPolicy:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"policy file not found: {path}")

    mod_name = f"taco_submitted_policy_{abs(hash(str(path))) % (10 ** 8)}"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import policy module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)

    pid = policy_id or path.stem

    # 1) a Policy class
    cls = getattr(module, "Policy", None)
    if isinstance(cls, type):
        inst = cls()
        act = getattr(inst, "act", None) or getattr(inst, "__call__", None)
        if act is None:
            raise TypeError("Policy class must define act(obs) or __call__(obs)")
        reset = getattr(inst, "reset", None)
        name = getattr(inst, "name", pid)
        return LoadedPolicy(act, reset, str(name), str(path))

    # 2) build_policy() factory
    builder = getattr(module, "build_policy", None)
    if callable(builder):
        obj = builder()
        if hasattr(obj, "act"):
            return LoadedPolicy(obj.act, getattr(obj, "reset", None),
                                str(getattr(obj, "name", pid)), str(path))
        if callable(obj):
            return LoadedPolicy(obj, getattr(obj, "reset", None), pid, str(path))

    # 3) module-level policy(obs)
    fn = getattr(module, "policy", None)
    if callable(fn):
        return LoadedPolicy(fn, getattr(module, "reset", None), pid, str(path))

    raise TypeError(
        "submitted policy must define one of: a `Policy` class with act(obs), a "
        "`build_policy()` factory, or a module-level `policy(obs)` function"
    )
