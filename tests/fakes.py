"""Small in-memory implementations of the engine's test seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Small in-memory implementations of the engine's test seams.
# relates: [clutch/journal.py]
# owner: clutch/journal.py
# verified: d7719818
# hash: 1b1ae30e696dd8f8d696995f708f10f169381ff68b7431308ce9543a90e493f7

import asyncio
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from clutch.journal import EVENT_VERSIONS, Event, render_ts


class FakeClock:
    def __init__(self, now=None):
        self.now = now if now is not None else datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


class FakeExec:
    def __init__(self, result=(0, "", "")):
        self.result = result
        self.calls = []

    async def run(self, argv, *, cwd, env, timeout, stdin_path=None):
        self.calls.append(list(argv))
        return self.result


class FakeFileSystem:
    def __init__(self):
        self.files = {}
        self.directories = set()

    def mkdir(self, path):
        path = Path(path)
        self.directories.update((path, *path.parents))

    def remove(self, path):
        self.files.pop(Path(path), None)

    def entries(self, path):
        path = Path(path)
        return sorted(p.name for p in self.files.keys() | self.directories if p.parent == path and p != path)

    def publish(self, path, data):
        if Path(path) in self.files:
            raise FileExistsError(path)
        self.write(path, data)

    def write(self, path, data):
        path = Path(path)
        self.mkdir(path.parent)
        self.files[path] = data

    def replace(self, src, dst):
        self.files[Path(dst)] = self.files.pop(Path(src))

    def read_bytes(self, path):
        try:
            return self.files[Path(path)]
        except KeyError:
            raise FileNotFoundError(path) from None

    def size(self, path):
        return len(self.read_bytes(path))


class FakeJournal:
    def __init__(self, clock=None):
        self.clock = clock if clock is not None else FakeClock()
        self.events = []

    def append(self, type, body, *, ticket=None, key=None):
        event = Event(EVENT_VERSIONS[type], type, render_ts(self.clock()), ticket, key, body)
        self.events.append(event)
        return event

    def read(self):
        return list(self.events)


class FakeGit:
    def __init__(self, results=None):
        self.results = {} if results is None else results
        self.calls = []

    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self.results[name]

        return call


async def turn():
    # Yield through callbacks without a wall-clock sleep or a timer.
    future = asyncio.get_running_loop().create_future()
    asyncio.get_running_loop().call_soon(future.set_result, None)
    await future


async def until(predicate, clock, step, *, timeout=60):
    deadline = time.monotonic() + timeout
    n = 0
    while time.monotonic() < deadline:
        if predicate():
            return
        if n % 20 == 0:
            clock.advance(step)
        await turn()
        n += 1
    raise AssertionError("predicate did not become true before timeout")
