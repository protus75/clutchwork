"""Local version bumps and annotated release tags; publishing is separate."""

from collections.abc import Mapping
from pathlib import Path

from clutch.changelog import insert_section
from clutch.config import Config
from clutch.git import Git, GitError
from clutch.journal import EventType
from clutch.providers import child_env
from clutch.runner import Refusal
from clutch.seams import FileSystem, ProcessExec

UV_TIMEOUT_S = 60.0
BUILD_TIMEOUT_S = 600.0
PUBLISH_TIMEOUT_S = 600.0


async def release(repo: Path, git: Git, exec_: ProcessExec, fs: FileSystem, env: Mapping[str, str], part: str, today: str) -> tuple[str, str]:
    dirty = await git.status_porcelain(repo, "--", "pyproject.toml", "uv.lock", "CHANGELOG.md")
    if dirty:
        raise Refusal(f"uncommitted version files: {dirty.strip()}", "commit or restore pyproject.toml, uv.lock and CHANGELOG.md before release")
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
    previous = await git.previous_release_tag(repo)
    subjects = await git.merged_subjects(repo, previous)
    rc, _, err = await exec_.run(["uv", "version", "--bump", part], cwd=repo, env=env, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version bump failed (rc {rc}): {lines[-1] if lines else ''}", "restore pyproject.toml and uv.lock before retrying release")
    path = repo / "CHANGELOG.md"
    try:
        existing = fs.read_bytes(path).decode("utf-8")
    except FileNotFoundError:
        existing = None
    fs.write(path, insert_section(existing, version, today, subjects).encode("utf-8"))
    message = f"release: {version}"
    sha = await git.commit(repo, message, only=["pyproject.toml", "uv.lock", "CHANGELOG.md"])
    await git.tag(repo, tag, message, sha)
    return version, sha


async def publishable(repo: Path, git: Git, env: Mapping[str, str], config: Config) -> None:
    token_name = config.release.pypi_token
    if config.release.publish and not env.get(token_name):
        raise Refusal(f"{token_name} is unset or empty", f"export {token_name} with a PyPI token or set release.publish: false to build without uploading")
    dirty = await git.status_porcelain(repo, "--untracked-files=no")
    if dirty.strip():
        raise Refusal(f"uncommitted tracked files: {dirty.strip()}", "commit or restore them, then retry clutch publish")


def journal_release(journal, version, sha) -> None:
    journal.append(EventType.SIGNAL, {"signal": "release", "version": version, "tag": f"v{version}", "commit": sha})


async def publish(repo: Path, git: Git, exec_: ProcessExec, fs: FileSystem, env: Mapping[str, str], config: Config) -> tuple[str, list[Path], bool]:
    await publishable(repo, git, env, config)
    token_name = config.release.pypi_token
    child = child_env(env, config)
    rc, out, err = await exec_.run(["uv", "version", "--short"], cwd=repo, env=child, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch publish")
    version = out.strip()
    tag = f"v{version}"
    head = await git.rev_parse(repo, "HEAD")
    try:
        tagged = await git.rev_parse(repo, f"refs/tags/{tag}^{{commit}}")
    except GitError:
        tagged = None
    if tagged != head:
        raise Refusal(f"tag {tag} is missing or not on HEAD", "run clutch release --minor or clutch release --patch to tag the version at HEAD, then retry clutch publish")
    dist = config.state_dir / "dist"
    rc, _, err = await exec_.run(["uv", "build", "--clear", "-o", str(dist)], cwd=repo, env=child, timeout=BUILD_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv build failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch publish")
    artifacts = [dist / name for name in sorted(fs.entries(dist)) if name.endswith((".whl", ".tar.gz"))]
    if not artifacts:
        raise Refusal("uv build produced no artifacts", "fix the build, then retry clutch publish")
    if not config.release.publish:
        return version, artifacts, False
    rc, _, err = await exec_.run(["uv", "publish", *map(str, artifacts)], cwd=repo, env={**child, "UV_PUBLISH_TOKEN": env[token_name]}, timeout=PUBLISH_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv publish failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch publish")
    return version, artifacts, True
