# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for dev._resolve_node_modules worktree fallback and for the esbuild path, NODE_PATH env and missing-esbuild error in dev.build_ui_bundle.
# relates: [dev.py]
# owner: dev.py
# verified: 1fc28917
# hash: 6277f5b94f585d839c186c76d3583100011028cc61f168c9afaab0c65029d636
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import dev


def file(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def setup_worktree(tmp_path, relative=False):
    main, root = tmp_path / "main", tmp_path / "wt"
    gitdir = main / ".git/worktrees/wt"
    gitdir.mkdir(parents=True)
    file(main / "node_modules/.bin/esbuild")
    pointer = os.path.relpath(gitdir, root) if relative else str(gitdir)
    file(root / ".git", f"  gitdir: {pointer}  \n")
    return main, root


@pytest.mark.parametrize("relative", [False, True])
def test_worktree_pointer(tmp_path, relative):
    main, root = setup_worktree(tmp_path, relative)
    assert dev._resolve_node_modules(root) == main / "node_modules"  # Reject the missing worktree copy.


def test_local_precedes_worktree(tmp_path):
    main, root = setup_worktree(tmp_path)
    file(root / "node_modules/.bin/esbuild")
    assert dev._resolve_node_modules(root) == root / "node_modules"  # Reject the available main copy.


@pytest.mark.parametrize("kind", ["missing_esbuild", "missing_git", "directory", "other_pointer", "unreadable"])
def test_no_fallback(tmp_path, kind):
    main, root = setup_worktree(tmp_path)
    if kind == "missing_esbuild":
        (main / "node_modules/.bin/esbuild").unlink()
    elif kind == "missing_git":
        (root / ".git").unlink()
    elif kind == "directory":
        (root / ".git").unlink()
        (root / ".git").mkdir()
    elif kind == "other_pointer":
        (root / ".git").write_text(f"gitdir: {main / '.git/other/wt'}\n")
    if kind == "unreadable":
        with patch.object(Path, "read_text", side_effect=OSError("unreadable")):
            assert dev._resolve_node_modules(root) == root / "node_modules"  # Reject propagating the read error.
    else:
        assert dev._resolve_node_modules(root) == root / "node_modules"  # Reject an invalid fallback.


@pytest.mark.parametrize("local", [False, True])
def test_builder_environment(tmp_path, local):
    main, root = setup_worktree(tmp_path)
    for name in ("vscode-clutchwork/media/view.css", "clutch/ui/dashboard.css", "vscode-clutchwork/media/ticket-lifecycle.svg", "clutch/ui/app.js"):
        file(root / name, "asset")
    if local:
        file(root / "node_modules/.bin/esbuild")
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="bundle", stderr=""))
    dev.build_ui_bundle(root, run_cmd=runner)
    args, kwargs = runner.call_args
    expected = root if local else main
    assert args[0][0] == str(expected / "node_modules/.bin/esbuild")  # Reject the other checkout's executable.
    if local:
        assert "env" not in kwargs  # Reject a changed local runner signature.
    else:
        assert kwargs["env"]["NODE_PATH"] == str(main / "node_modules")  # Reject missing or local package lookup.


def test_missing_esbuild_reports_error(tmp_path):
    root = tmp_path / "wt"
    for name in ("vscode-clutchwork/media/view.css", "clutch/ui/dashboard.css", "vscode-clutchwork/media/ticket-lifecycle.svg", "clutch/ui/app.js"):
        file(root / name, "asset")

    def missing(*args, **kwargs):
        raise FileNotFoundError("esbuild")

    with pytest.raises(RuntimeError, match="ui-bundle: missing source or esbuild"):
        dev.build_ui_bundle(root, run_cmd=missing)  # Reject a changed missing-executable error.
