"""Signature-checked, configurable fake for the Git seam."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared fake for the Git seam: each method checks its arguments against its signature, records the call, and returns a per-method override (value, exception or callback) or a default
# relates: [clutch/git.py, tests/unit/test_git_fake.py, tests/integration/test_git_fake_adoption.py]
# owner: engine
# verified: bc0baafb
# hash: 1c06b2fc5cb012adc93c8818f1ba11e84d11205c7cd5855e41f48536d97f3269

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from pathlib import Path


def _method(default):
    def decorate(signature):
        @wraps(signature)
        async def call(self, *args, **kwargs):
            inspect.signature(signature).bind(self, *args, **kwargs)
            self.calls.append((signature.__name__, args, kwargs))
            value = self._overrides.get(signature.__name__, default)
            if isinstance(value, BaseException):
                raise value
            if callable(value):
                value = value(*args, **kwargs)
                if inspect.isawaitable(value):
                    value = await value
            return value

        return call

    return decorate


class GitFake:
    def __init__(self, **overrides):
        allowed = {name for name in vars(type(self)) if not name.startswith("_")} | {"_run"}
        unknown = overrides.keys() - allowed
        if unknown:
            raise TypeError(f"Unknown GitFake overrides: {sorted(unknown)}")
        self._overrides = overrides
        self.calls = []
        self._main_write = asyncio.Lock()
        self._commit_lock = asyncio.Lock()

    def main_write(self) -> asyncio.Lock:
        self.calls.append(("main_write", (), {}))
        value = self._overrides.get("main_write", self._main_write)
        if isinstance(value, BaseException):
            raise value
        return value() if callable(value) else value

    @_method("")
    async def _run(self, dir: Path, *args: str) -> str:
        pass

    @_method(None)
    async def init(self, dir: Path, *, branch: str) -> None:
        pass

    @_method("")
    async def status_porcelain(self, dir: Path, *args: str) -> str:
        pass

    @_method((lambda *args, **kwargs: []))
    async def ls_files(self, dir: Path) -> list[str]:
        pass

    @_method("")
    async def tree_id(self, dir: Path, index: Path) -> str:
        pass

    @_method((lambda *args, **kwargs: []))
    async def tree_changes(self, dir: Path, before: str, after: str) -> list[str]:
        pass

    @_method("")
    async def rev_parse(self, dir: Path, rev: str) -> str:
        pass

    @_method("")
    async def merge_base(self, dir: Path, a: str, b: str) -> str:
        pass

    @_method((lambda dir: dir / ".git"))
    async def git_common_dir(self, dir: Path) -> Path:
        pass

    @_method((lambda *args, **kwargs: []))
    async def diff_names(self, dir: Path, base: str, stem: str) -> list[str]:
        pass

    @_method("")
    async def diff(self, dir: Path, base: str, stem: str) -> str:
        pass

    @_method("")
    async def diff_stat(self, dir: Path, base: str, stem: str) -> str:
        pass

    @_method(None)
    async def add(self, dir: Path, paths: Sequence[str]) -> None:
        pass

    @_method("")
    async def commit(self, dir: Path, message: str, *, only: Sequence[str] = ()) -> str:
        pass

    @_method("")
    async def commit_edit(self, dir: Path, message: str, *, only: Sequence[str], edit: Callable[[], Awaitable[None]]) -> str:
        pass

    @_method(None)
    async def previous_release_tag(self, dir: Path) -> str | None:
        pass

    @_method((lambda *args, **kwargs: []))
    async def merged_subjects(self, dir: Path, since: str | None) -> list[str]:
        pass

    @_method((lambda *args, **kwargs: []))
    async def merged_tickets(self, dir: Path) -> list[tuple[str, str]]:
        pass

    @_method((lambda *args, **kwargs: []))
    async def ticket_touches(self, dir: Path) -> list[tuple[str, str, list[str]]]:
        pass

    @_method(None)
    async def tag(self, dir: Path, name: str, message: str, target: str) -> None:
        pass

    @_method(None)
    async def branch_delete(self, dir: Path, name: str) -> None:
        pass

    @_method(None)
    async def worktree_add(self, dir: Path, path: Path, branch: str, start: str) -> None:
        pass

    @_method(None)
    async def worktree_attach(self, dir: Path, path: Path, branch: str) -> None:
        pass

    @_method(None)
    async def worktree_add_detached(self, dir: Path, path: Path, rev: str) -> None:
        pass

    @_method(None)
    async def worktree_remove(self, dir: Path, path: Path) -> None:
        pass

    @_method(None)
    async def worktree_prune(self, dir: Path) -> None:
        pass

    @_method(None)
    async def rebase(self, dir: Path, onto: str) -> None:
        pass

    @_method(None)
    async def restore(self, dir: Path, paths: Sequence[str], *, source: str) -> None:
        pass

    @_method(None)
    async def rebase_stop_at_conflict(self, dir: Path, onto: str) -> None:
        pass

    @_method((lambda *args, **kwargs: []))
    async def conflicted_paths(self, dir: Path) -> list[str]:
        pass

    @_method(None)
    async def rebase_continue(self, dir: Path) -> None:
        pass

    @_method("")
    async def merge_squash(self, dir: Path, branch: str, message: str) -> str:
        pass

    @_method(None)
    async def push(self, dir: Path, remote: str, branch: str) -> None:
        pass

    @_method("")
    async def describe(self, dir: Path) -> str:
        pass

    @_method((lambda *args, **kwargs: []))
    async def first_parent_squashes(self, dir: Path, app_commit: str) -> list[dict]:
        pass
