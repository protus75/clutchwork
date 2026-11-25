"""Local version bumps and annotated release tags; publishing is separate."""

import json
from collections.abc import Mapping
from fnmatch import fnmatchcase
from pathlib import Path

from clutch.antigravity import PLUGIN_NAME, portable_bundle_files
from clutch.changelog import insert_section
from clutch.config import Config
from clutch.git import Git, GitError
from clutch.journal import EventType
from clutch.providers import child_env
from clutch.runner import Refusal
from clutch.seams import ExecutableNotFound, FileSystem, ProcessExec

UV_TIMEOUT_S = 60.0
BUILD_TIMEOUT_S = 600.0
PUBLISH_TIMEOUT_S = 600.0


async def release(repo: Path, git: Git, exec_: ProcessExec, fs: FileSystem, env: Mapping[str, str], part: str, today: str) -> tuple[str, str]:
    logo = None
    try:
        manifest = json.loads(fs.read_bytes(repo / "plugin.json"))
        if isinstance(manifest, dict) and manifest.get("name") == PLUGIN_NAME:
            logo = fs.read_bytes(repo / "clutch/assets/logo.png")
    except OSError, ValueError, UnicodeDecodeError:
        pass
    paths = ["pyproject.toml", "uv.lock", "CHANGELOG.md"]
    if logo is not None:
        paths.extend(sorted(portable_bundle_files(version_str="", logo_bytes=logo)))
    dirty = await git.status_porcelain(repo, "--", *paths)
    if dirty:
        remedy = "commit or restore pyproject.toml, uv.lock and CHANGELOG.md"
        if logo is not None:
            remedy += " and the Antigravity plugin bundle"
        raise Refusal(f"uncommitted version files: {dirty.strip()}", remedy + " before release bump")
    rc, out, err = await exec_.run(["uv", "version", "--bump", part, "--dry-run", "--short"], cwd=repo, env=env, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version dry run failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry release bump")
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
        raise Refusal(f"uv version bump failed (rc {rc}): {lines[-1] if lines else ''}", "restore pyproject.toml and uv.lock before retrying release bump")
    path = repo / "CHANGELOG.md"
    try:
        existing = fs.read_bytes(path).decode("utf-8")
    except FileNotFoundError:
        existing = None
    fs.write(path, insert_section(existing, version, today, subjects).encode("utf-8"))
    if logo is not None:
        for rel, data in portable_bundle_files(version_str=version, logo_bytes=logo).items():
            fs.write(repo / rel, data)
    message = f"release: {version}"
    sha = await git.commit(repo, message, only=paths)
    await git.tag(repo, tag, message, sha)
    return version, sha


async def publishable(repo: Path, git: Git, env: Mapping[str, str], config: Config) -> None:
    token_name = config.release.pypi_token
    if config.release.publish and not env.get(token_name):
        raise Refusal(f"{token_name} is unset or empty", f"export {token_name} with a PyPI token or set release.publish: false to build without uploading")
    dirty = await git.status_porcelain(repo, "--untracked-files=no")
    if dirty.strip():
        raise Refusal(f"uncommitted tracked files: {dirty.strip()}", "commit or restore them, then retry clutch release publish")


def journal_release(journal, version, sha) -> None:
    journal.append(EventType.SIGNAL, {"signal": "release", "version": version, "tag": f"v{version}", "commit": sha})


async def publish(repo: Path, git: Git, exec_: ProcessExec, fs: FileSystem, env: Mapping[str, str], config: Config) -> tuple[str, list[Path], bool]:
    await publishable(repo, git, env, config)
    token_name = config.release.pypi_token
    child = child_env(env, config)
    child.pop("UV_PUBLISH_TOKEN", None)
    rc, out, err = await exec_.run(["uv", "version", "--short"], cwd=repo, env=child, timeout=UV_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv version failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch release publish")
    version = out.strip()
    tag = f"v{version}"
    head = await git.rev_parse(repo, "HEAD")
    try:
        tagged = await git.rev_parse(repo, f"refs/tags/{tag}^{{commit}}")
    except GitError:
        tagged = None
    if tagged != head:
        raise Refusal(f"tag {tag} is missing or not on HEAD", "run clutch release bump --minor or clutch release bump --patch to tag the version at HEAD, then retry clutch release publish")
    for argv in config.release.pre_build:
        try:
            rc, _, _ = await exec_.run(argv, cwd=repo, env=child, timeout=BUILD_TIMEOUT_S)
        except (TimeoutError, ExecutableNotFound) as exc:
            raise Refusal(f"release.pre_build command {argv[0]} failed: {type(exc).__name__}", "fix the pre-build command, then retry clutch release publish") from exc
        if rc:
            raise Refusal(f"release.pre_build command {argv[0]} failed (rc {rc})", "fix the pre-build command, then retry clutch release publish")
    dist = config.state_dir / "dist"
    rc, _, err = await exec_.run(["uv", "build", "--clear", "-o", str(dist)], cwd=repo, env=child, timeout=BUILD_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv build failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch release publish")
    artifacts = [dist / name for name in sorted(fs.entries(dist)) if name.endswith((".whl", ".tar.gz"))]
    if not artifacts:
        raise Refusal("uv build produced no artifacts", "fix the build, then retry clutch release publish")
    if not config.release.publish:
        return version, artifacts, False
    rc, _, err = await exec_.run(["uv", "publish", *map(str, artifacts)], cwd=repo, env={**child, "UV_PUBLISH_TOKEN": env[token_name]}, timeout=PUBLISH_TIMEOUT_S)
    if rc:
        lines = [line for line in err.splitlines() if line.strip()]
        raise Refusal(f"uv publish failed (rc {rc}): {lines[-1] if lines else ''}", "fix the uv error, then retry clutch release publish")
    return version, artifacts, True


async def run_packages(repo: Path, exec_: ProcessExec, fs: FileSystem, env: Mapping[str, str], config: Config) -> list[str]:
    if not config.release.packages:
        return []
    lines = []
    for package in config.release.packages:
        try:
            pattern = Path(package.kept)
            before = set(fs.entries(repo / pattern.parent))
            rc, _, _ = await exec_.run(package.argv, cwd=repo, env=child_env(env, config), timeout=BUILD_TIMEOUT_S)
            if rc:
                lines.append(f"package: {package.argv[0]} failed (rc {rc})")
                continue
            after = set(fs.entries(repo / pattern.parent))
            kept = sorted(name for name in after - before if fnmatchcase(name, pattern.name))
            lines.extend(f"package: kept {pattern.parent / name}" for name in kept)
            if not kept:
                lines.append(f"package: nothing kept for {package.kept}")
        except TimeoutError:
            lines.append(f"package: {package.argv[0]} failed (timeout)")
        except ExecutableNotFound:
            lines.append(f"package: {package.argv[0]} failed (not found)")
        except Exception as exc:
            lines.append(f"package: {package.argv[0]} failed ({type(exc).__name__})")
    return lines
