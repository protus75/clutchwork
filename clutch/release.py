"""Local version bumps and annotated release tags; publishing is separate."""

from collections.abc import Mapping
from pathlib import Path

from clutch.git import Git, GitError
from clutch.runner import Refusal
from clutch.seams import ProcessExec

UV_TIMEOUT_S = 60.0


async def release(repo: Path, git: Git, exec_: ProcessExec, env: Mapping[str, str], part: str) -> tuple[str, str]:
    dirty = await git.status_porcelain(repo, "--", "pyproject.toml", "uv.lock")
    if dirty:
        raise Refusal(f"uncommitted version files: {dirty.strip()}", "commit or restore pyproject.toml and uv.lock before release")
    rc, out, err = await exec_.run(["uv", "version", "--bump", part, "--dry-run", "--short"], cwd=repo, env=env, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version dry run failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry release")
    version = out.strip()
    tag = f"v{version}"
    try:
        await git.rev_parse(repo, f"refs/tags/{tag}")
    except GitError:
        pass
    else:
        raise Refusal(f"tag {tag} already exists", "choose a version whose release tag does not exist")
    rc, _, err = await exec_.run(["uv", "version", "--bump", part], cwd=repo, env=env, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version bump failed (rc {rc}): {lines[-1] if lines else ''}", "restore pyproject.toml and uv.lock before retrying release")
    message = f"release: {version}"
    sha = await git.commit(repo, message, only=["pyproject.toml", "uv.lock"])
    await git.tag(repo, tag, message, sha)
    return version, sha
