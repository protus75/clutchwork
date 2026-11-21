# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Read and write spool captures for tests.
# relates: [clutch/evidence/store.py]
# owner: engine
# verified: 5e952a0e
# hash: cafb048d751ad63a222ad8d863c52f328b40e1d0ee01c97c859357b6ce0a6683
from clutch.evidence.store import CaptureNotFound, CaptureUnreadable, capture_key


def _slot(state_dir, stem, attempt):
    return state_dir / "spools" / stem / str(attempt)


def read_capture(state_dir, spool_stem, attempt, name, *, fs=None):
    capture_key(spool_stem, attempt, name)
    path = _slot(state_dir, spool_stem, attempt) / name
    try:
        return path.read_bytes() if fs is None else fs.read_bytes(path)
    except FileNotFoundError as exc:
        raise CaptureNotFound(str(path)) from exc
    except OSError as exc:
        raise CaptureUnreadable(str(path)) from exc


def write_capture(state_dir, spool_stem, attempt, name, data, *, fs=None):
    capture_key(spool_stem, attempt, name)
    if not isinstance(data, bytes):
        raise ValueError("capture data must be bytes")
    path = _slot(state_dir, spool_stem, attempt) / name
    if fs is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    else:
        fs.write(path, data)


def _capture_name(spool_stem, attempt, name):
    first = name.split("/", 1)[0]
    if "/" not in spool_stem and first.isascii() and first.isdecimal():
        return False
    try:
        capture_key(spool_stem, attempt, name)
    except ValueError:
        return False
    return True


def list_captures(state_dir, spool_stem, attempt=None, *, fs=None):
    capture_key(spool_stem, 0 if attempt is None else attempt, "x")
    root = _slot(state_dir, spool_stem, 0).parent
    if fs is not None:

        def walk(path):
            try:
                children = fs.entries(path)
            except NotADirectoryError:
                children = []
            if children:
                for child in children:
                    yield from walk(path / child)
            else:
                try:
                    fs.read_bytes(path)
                except OSError:
                    return
                yield path

        result = []
        for entry in fs.entries(root):
            if not entry.isascii() or not entry.isdecimal():
                continue
            number = int(entry)
            if attempt is not None and number != attempt:
                continue
            directory = root / entry
            for path in walk(directory):
                name = path.relative_to(directory).as_posix()
                if _capture_name(spool_stem, number, name):
                    result.append((number, name))
        return sorted(result)
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
            if _capture_name(spool_stem, number, name):
                result.append((number, name))
    return sorted(result)
