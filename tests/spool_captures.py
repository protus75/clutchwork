# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Read and write spool captures for tests.
# relates: [clutch/evidence/store.py]
# owner: engine
# verified: e3a6f154
# hash: 2307746b41a02d7c4d6901b9eddee6e01f2fa71913c427ed932fbd46bd1726cb
from clutch.evidence.store import CaptureNotFound, CaptureUnreadable, capture_key


def _slot(state_dir, stem, attempt):
    return state_dir / "spools" / stem / str(attempt)


def read_capture(state_dir, spool_stem, attempt, name):
    capture_key(spool_stem, attempt, name)
    path = _slot(state_dir, spool_stem, attempt) / name
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise CaptureNotFound(str(path)) from exc
    except OSError as exc:
        raise CaptureUnreadable(str(path)) from exc


def write_capture(state_dir, spool_stem, attempt, name, data):
    capture_key(spool_stem, attempt, name)
    if not isinstance(data, bytes):
        raise ValueError("capture data must be bytes")
    path = _slot(state_dir, spool_stem, attempt) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def list_captures(state_dir, spool_stem, attempt=None):
    capture_key(spool_stem, 0 if attempt is None else attempt, "x")
    root = _slot(state_dir, spool_stem, 0).parent
    if not root.is_dir():
        return []
    result = []
    for directory in root.iterdir():
        if not directory.is_dir() or not directory.name.isascii() or not directory.name.isdecimal():
            continue
        number = int(directory.name)
        if attempt is not None and number != attempt:
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            name = path.relative_to(directory).as_posix()
            first = name.split("/", 1)[0]
            if "/" not in spool_stem and first.isascii() and first.isdecimal():
                continue
            try:
                capture_key(spool_stem, number, name)
            except ValueError:
                continue
            result.append((number, name))
    return sorted(result)
