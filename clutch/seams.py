"""Injectable seams: engine code never calls these raw."""

import asyncio
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from clutch.evidence.schema import Rusage

Clock = Callable[[], datetime]
# Every timed wait races its work against this to a clock-derived deadline, so tests wait zero wall-clock.
Sleep = Callable[[float], Awaitable[None]]


def spawn_detached(argv: Sequence[str], *, cwd: Path, env: Mapping[str, str], output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a") as stream:
        child = subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True, stdin=subprocess.DEVNULL, stdout=stream, stderr=stream)
    return child.pid


def child_exit(pid: int) -> int | None:
    try:
        waited, status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return None
    return os.waitstatus_to_exitcode(status) if waited else None


@runtime_checkable
class ProcessExec(Protocol):
    async def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float | None,
        stdin_path: Path | None = None,
    ) -> tuple[int, str, str]: ...


@runtime_checkable
class ReplaceExec(Protocol):
    async def replace(self, argv: Sequence[str], *, cwd: Path, env: Mapping[str, str]) -> int: ...


@runtime_checkable
class GroupExec(ProcessExec, Protocol):
    """Publish spawn groups and optionally deliver stdout lines synchronously, including the EOF tail.

    A failed line consumer stops delivery, not capture: drain and reap, then raise its first
    exception with (stdout, stderr) in `process_capture`. An intervening unwind keeps its
    exception type and carries the capture; any consumer failure is its cause and carries it too.
    """

    async def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float | None,
        stdin_path: Path | None = None,
        on_spawn: Callable[[int], None] | None = None,
        on_stdout_line: Callable[[str], None] | None = None,
        on_rusage: Callable[["Rusage"], None] | None = None,
    ) -> tuple[int, str, str]: ...

    def kill_group(self, pgid: int) -> None:
        """Signal-not-reap: returns once the group is SIGKILLed; the spawner's `run` still reaps."""
        ...


class ExecutableNotFound(Exception):
    """argv[0] does not resolve: a config/setup refusal, never a raw FileNotFoundError."""

    def __init__(self, binary: str) -> None:
        super().__init__(f"executable not found: {binary!r} (install it or fix PATH in the child env)")
        self.binary = binary


@runtime_checkable
class Notifications(Protocol):
    async def notify(self, argv: Sequence[str]) -> dict[str, str | int]: ...


class NotificationFailed(Exception):
    """Delivery did not complete; repair the command and retry the pending evidence."""


class CommandNotifications:
    def __init__(self, exec_: ProcessExec, *, cwd: Path, env: Mapping[str, str], timeout: float, scrub: Callable[[str], str]) -> None:
        self.exec_, self.cwd, self.env = exec_, cwd, env
        self.timeout, self.scrub = timeout, scrub

    async def notify(self, argv: Sequence[str]) -> dict[str, str | int]:
        if not argv or isinstance(argv, str) or any(not isinstance(p, str) or "\0" in p for p in argv) or not argv[0].strip():
            raise ValueError("notify needs a nonempty argv list with a nonblank executable and no NULs")
        try:
            rc, out, err = await self.exec_.run(list(argv), cwd=self.cwd, env=self.env, timeout=self.timeout)
        except (ExecutableNotFound, TimeoutError, OSError) as exc:
            raise NotificationFailed(self.scrub(f"notify failed: {exc}; install/fix notify argv or PATH and retry pending evidence")) from None
        out, err = self.scrub(out), self.scrub(err)
        if rc != 0:
            raise NotificationFailed(f"notify exited {rc}: {out[-2000:]} {err[-2000:]}; make notify exit 0 and retry pending evidence")
        return {"rc": rc, "stdout": out, "stderr": err}


class SubprocessExec:
    """Real process-exec seam: every child in its own process group, every kill a group kill."""

    async def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float | None,
        stdin_path: Path | None = None,
        on_spawn: Callable[[int], None] | None = None,
        on_stdout_line: Callable[[str], None] | None = None,
        on_rusage: Callable[["Rusage"], None] | None = None,
    ) -> tuple[int, str, str]:
        if shutil.which(argv[0], path=env.get("PATH", "")) is None:
            raise ExecutableNotFound(argv[0])
        # Unbounded callers stream through inherited stdio; their out/err come back empty.
        stream = None if timeout is None else subprocess.PIPE
        with open(stdin_path, "rb") if stdin_path else open(os.devnull, "rb") as stdin:
            proc = await _spawn(
                argv,
                cwd=cwd,
                env=dict(env),
                stdin=stdin,
                stdout=stream,
                stderr=stream,
                start_new_session=True,
            )
            proc._clutch_wait = asyncio.create_task(_reap(proc, on_rusage))
            proc._clutch_pipes = []
            readers: list[asyncio.Task] = []
            stdout, stderr = bytearray(), bytearray()
            consumer_error: BaseException | None = None

            def deliver(line: str) -> None:
                nonlocal consumer_error
                if consumer_error is None and on_stdout_line is not None:
                    try:
                        on_stdout_line(line)
                    except BaseException as exc:
                        consumer_error = exc

            try:
                if stream is not None:
                    for pipe in (proc.stdout, proc.stderr):
                        reader = asyncio.StreamReader()
                        connecting = asyncio.create_task(asyncio.get_running_loop().connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), pipe))
                        try:
                            await asyncio.shield(connecting)
                        except BaseException:
                            await connecting
                            proc._clutch_pipes.append(reader)
                            raise
                        proc._clutch_pipes.append(reader)
                if on_spawn is not None:
                    on_spawn(proc.pid)  # start_new_session: the child's pid IS its pgid
                async with asyncio.timeout(timeout):
                    if stream is None:
                        await asyncio.shield(proc._clutch_wait)
                        out, err = b"", b""
                    else:
                        readers = [
                            asyncio.create_task(_read_pipe(proc._clutch_pipes[0], stdout, deliver if on_stdout_line is not None else None)),
                            asyncio.create_task(_read_pipe(proc._clutch_pipes[1], stderr)),
                            asyncio.ensure_future(asyncio.shield(proc._clutch_wait)),
                        ]
                        out, err, _ = await asyncio.gather(*readers)
            except BaseException as exc:
                # Timeout and outer cancellation alike: grandchildren must not outlive the call.
                for reader in readers:
                    reader.cancel()
                await asyncio.gather(*readers, return_exceptions=True)
                remaining_out, remaining_err = await _kill_and_wait(proc)
                stdout.extend(remaining_out or b"")
                stderr.extend(remaining_err or b"")
                capture = (stdout.decode(errors="replace"), stderr.decode(errors="replace"))
                exc.process_capture = capture
                if consumer_error is not None:
                    consumer_error.process_capture = capture
                    # Cancellation/timeout still owns the unwind; keep the consumer failure visible.
                    raise exc from consumer_error
                raise
            if consumer_error is not None:
                consumer_error.process_capture = (stdout.decode(errors="replace"), stderr.decode(errors="replace"))
                raise consumer_error
        return proc.returncode or 0, (out or b"").decode(errors="replace"), (err or b"").decode(errors="replace")

    async def replace(self, argv: Sequence[str], *, cwd: Path, env: Mapping[str, str]) -> int:
        if shutil.which(argv[0], path=env.get("PATH", "")) is None:
            raise ExecutableNotFound(argv[0])
        sys.stdout.flush()
        sys.stderr.flush()
        os.chdir(cwd)
        os.execvpe(argv[0], argv, dict(env))

    def kill_group(self, pgid: int) -> None:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def rusage_figures(ru) -> "Rusage":
    from clutch.evidence.schema import Rusage

    return Rusage(user_s=ru.ru_utime, sys_s=ru.ru_stime, max_rss_kb=ru.ru_maxrss)


def reap_outcome(status, ru, on_rusage) -> int:
    code = os.waitstatus_to_exitcode(status)
    if on_rusage is not None:
        on_rusage(rusage_figures(ru))
    return code


async def _spawn(argv, **kwargs):
    return subprocess.Popen(argv, **kwargs)


async def _reap(proc, on_rusage):
    loop = asyncio.get_running_loop()
    ready = loop.create_future()
    fd = os.pidfd_open(proc.pid)
    try:
        loop.add_reader(fd, lambda: not ready.done() and ready.set_result(None))
        await ready
        _, status, ru = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        return reap_outcome(status, ru, on_rusage)
    finally:
        loop.remove_reader(fd)
        os.close(fd)


async def _kill_and_wait(proc) -> tuple[bytes | None, bytes | None]:
    SubprocessExec().kill_group(proc.pid)
    # Drain after failed/cancelled readers while the child is reaped.
    for pipe in (proc.stdout, proc.stderr)[len(proc._clutch_pipes) :]:
        if pipe is not None:
            reader = asyncio.StreamReader()
            await asyncio.get_running_loop().connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), pipe)
            proc._clutch_pipes.append(reader)
    drained = await asyncio.gather(*(_read_pipe(pipe, bytearray()) for pipe in proc._clutch_pipes))
    await asyncio.shield(proc._clutch_wait)
    return tuple(drained) if drained else (None, None)


async def _read_pipe(
    pipe: asyncio.StreamReader,
    captured: bytearray,
    on_line: Callable[[str], None] | None = None,
) -> bytes:
    pending = bytearray()
    while chunk := await pipe.read(65536):
        captured.extend(chunk)
        if on_line is not None:
            pending.extend(chunk)
            while (end := pending.find(b"\n")) >= 0:
                line = bytes(pending[: end + 1])
                del pending[: end + 1]
                on_line(line.decode(errors="replace"))
    if pending and on_line is not None:
        on_line(pending.decode(errors="replace"))
    return bytes(captured)


@runtime_checkable
class FileSystem(Protocol):
    def mkdir(self, path: Path) -> None: ...

    def remove(self, path: Path) -> None: ...

    def entries(self, path: Path) -> list[str]:
        """Sorted names directly inside a directory, or an empty list if absent."""
        ...

    def publish(self, path: Path, data: bytes) -> None:
        """Durable atomic publication; an existing destination is never overwritten."""
        ...

    def write(self, path: Path, data: bytes) -> None:
        """Atomic: temp file, fsync, rename."""
        ...

    def replace(self, src: Path, dst: Path) -> None: ...

    def read_bytes(self, path: Path) -> bytes: ...

    def size(self, path: Path) -> int: ...


class LocalFileSystem:
    def mkdir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def remove(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def entries(self, path: Path) -> list[str]:
        try:
            return sorted(os.listdir(path))
        except FileNotFoundError:
            return []

    def publish(self, path: Path, data: bytes) -> None:
        # Sync every ancestor edge, including directories another publisher just created.
        path.parent.mkdir(parents=True, exist_ok=True)
        for directory in (path.parent, *path.parent.parents):
            self._sync_directory(directory)
        fd, name = tempfile.mkstemp(prefix=".control-", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # link is atomic and refuses an existing name, unlike rename/replace.
            os.link(temporary, path)
            temporary.unlink()
            self._sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _sync_directory(path: Path) -> None:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def replace(self, src: Path, dst: Path) -> None:
        os.replace(src, dst)

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def size(self, path: Path) -> int:
        return path.stat().st_size
