"""Evidence persistence through the injected filesystem seam."""

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable
from compression import zstd
from pathlib import Path
from urllib.parse import quote, unquote

from pydantic import BaseModel

from clutch.evidence.schema import End, Start
from clutch.seams import FileSystem


class SkipRecord:
    """A record version whose major version is not understood."""


SKIP = SkipRecord()
_REF = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _refs(value: object) -> set[str]:
    if isinstance(value, str):
        return {value} if _REF.fullmatch(value) else set()
    if isinstance(value, dict):
        return set().union(*(_refs(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_refs(v) for v in value))
    return set()


def _ignore_unknown(model: type[BaseModel], data: dict) -> dict:
    """Strip future optional fields recursively before strict validation."""
    result = {}
    for name, field in model.model_fields.items():
        key = field.alias or name
        if key not in data:
            continue
        value = data[key]
        annotation = field.annotation
        if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
            value = _ignore_unknown(annotation, value)
        else:
            for item in getattr(annotation, "__args__", ()):
                if isinstance(item, type) and issubclass(item, BaseModel) and isinstance(value, dict):
                    value = _ignore_unknown(item, value)
                    break
        result[key] = value
    return result


class EvidenceStore:
    def __init__(self, state_dir: Path, fs: FileSystem, read_bytes: Callable[[Path], bytes], size: Callable[[Path], int], redact: Callable[[str], str]):
        self.root = state_dir / "evidence"
        self.fs = fs
        self.read_bytes = read_bytes
        self.size = size
        self.redact = redact

    def _blob_path(self, ref: str) -> Path:
        if not _REF.fullmatch(ref):
            raise ValueError("invalid blob reference")
        digest = ref[7:]
        return self.root / "blobs" / digest[:2] / digest

    def put_blob(self, data: bytes) -> str:
        try:
            data = self.redact(data.decode("utf-8")).encode("utf-8")
        except UnicodeDecodeError:
            pass
        ref = "sha256:" + hashlib.sha256(data).hexdigest()
        path = self._blob_path(ref)
        if path.name in self.fs.entries(path.parent):
            return ref
        try:
            self.fs.publish(path, zstd.compress(data))
        except FileExistsError:
            pass
        return ref

    def get_blob(self, ref: str) -> bytes:
        return zstd.decompress(self.read_bytes(self._blob_path(ref)))

    def _record_path(self, key: str, kind: str) -> Path:
        if kind not in ("start", "end"):
            raise ValueError("record kind must be start or end")
        return self.root / "calls" / quote(key, safe="") / (kind + ".json")

    def write_record(self, key: str, kind: str, data: dict) -> None:
        model = {"start": Start, "end": End}.get(kind)
        if model is None:
            raise ValueError("record kind must be start or end")
        record = model.model_validate(data)
        self.fs.publish(self._record_path(key, kind), record.model_dump_json(by_alias=True).encode())

    def read_record(self, key: str, kind: str) -> BaseModel | SkipRecord:
        path = self._record_path(key, kind)
        data = json.loads(self.read_bytes(path))
        match = re.fullmatch(r"clutch\.evidence\.call/(\d+)\.(\d+)", data["schema"])
        if not match or match.group(1) != "1":
            return SKIP
        data["schema"] = "clutch.evidence.call/1.0"
        model = {"start": Start, "end": End}[kind]
        return model.model_validate(_ignore_unknown(model, data))

    def latest_stdout(self, prefix: str) -> str:
        calls = self.root / "calls"
        records = []
        for entry in self.fs.entries(calls):
            key = unquote(entry)
            if key.startswith(prefix) and "end.json" in self.fs.entries(calls / entry):
                record = self.read_record(key, "end")
                if record is not SKIP:
                    records.append((record.clock.wall_end, entry, record))
        if not records:
            return ""
        record = max(records, key=lambda item: item[:2])[2]
        try:
            return self.get_blob(record.raw.stdout).decode(errors="replace")
        except FileNotFoundError:
            return ""

    def prune(self, max_bytes: int) -> None:
        blobs = self.root / "blobs"
        paths = [blobs / prefix / name for prefix in self.fs.entries(blobs) for name in self.fs.entries(blobs / prefix)]
        sizes = {"sha256:" + path.name: self.size(path) for path in paths}
        total = sum(sizes.values())
        if total <= max_bytes:
            return
        calls = self.root / "calls"
        records = []
        counts: Counter[str] = Counter()
        for key in self.fs.entries(calls):
            directory = calls / key
            refs: set[str] = set()
            end = None
            for name in self.fs.entries(directory):
                if name == "normalized":
                    for view in self.fs.entries(directory / name):
                        refs.update(_refs(json.loads(self.read_bytes(directory / name / view))))
                elif name.endswith(".json"):
                    data = json.loads(self.read_bytes(directory / name))
                    refs.update(_refs(data))
                    if name == "end.json":
                        end = data
            counts.update(refs)
            if end is not None:
                records.append((end["clock"]["wall_end"], key, refs, _refs(end)))
        for _, _, refs, eligible in sorted(records):
            counts.subtract(refs)
            for ref in sorted(eligible):
                if counts[ref] == 0 and ref in sizes:
                    self.fs.remove(self._blob_path(ref))
                    total -= sizes.pop(ref)
                    if total <= max_bytes:
                        return
