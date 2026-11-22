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

from clutch.evidence.schema import Attempt, End, Start
from clutch.seams import FileSystem


class SkipRecord:
    """A record version whose major version is not understood."""


class CaptureNotFound(LookupError):
    """No pointer exists for the requested capture."""


class CaptureUnreadable(Exception):
    """A capture pointer or its blob cannot be read."""


SKIP = SkipRecord()
_STEM = re.compile(r"[a-z0-9][a-z0-9_-]{1,127}\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}\Z")
_REF = re.compile(r"sha256:[0-9a-f]{64}\Z")


def capture_key(spool_stem, attempt, name):
    """Map a spool slot to a validated evidence capture key."""
    if not isinstance(spool_stem, str) or spool_stem.count("/") > 1:
        raise ValueError("invalid spool stem")
    parts = spool_stem.split("/")
    stem = parts[0]
    if not _STEM.fullmatch(stem):
        raise ValueError("invalid spool stem")
    if len(parts) == 2 and not re.fullmatch(r"(?:0|[1-9][0-9]{0,8})", parts[1]):
        raise ValueError("invalid run sequence")
    if type(attempt) is not int or attempt < 0:
        raise ValueError("invalid attempt")
    if not isinstance(name, str) or not _NAME.fullmatch(name) or re.match(r"run-[0-9]+/", name):
        raise ValueError("invalid capture name")
    if len(parts) == 2:
        name = f"run-{parts[1]}/{name}"
    if not _NAME.fullmatch(name):
        raise ValueError("invalid capture name")
    return stem, attempt, name


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

    def _capture_path(self, stem: str, attempt: int, name: str) -> Path:
        self._validate_capture(stem, attempt, name)
        return self.root / "captures" / stem / str(attempt) / (quote(name, safe="") + ".json")

    @staticmethod
    def _validate_capture(stem, attempt=None, name=None):
        if not isinstance(stem, str) or not _STEM.fullmatch(stem):
            raise ValueError("invalid stem")
        if attempt is not None and (type(attempt) is not int or attempt < 0):
            raise ValueError("invalid attempt")
        if name is not None and (not isinstance(name, str) or not _NAME.fullmatch(name)):
            raise ValueError("invalid capture name")

    def put_capture(self, stem: str, attempt: int, name: str, data: bytes) -> None:
        # A missing required value is invalid even though listing accepts None.
        if attempt is None or name is None:
            raise ValueError("attempt and name are required")
        path = self._capture_path(stem, attempt, name)
        ref = self.put_blob(data)
        self.fs.write(path, json.dumps({"schema": "clutch.evidence.capture/1.0", "blob": ref}).encode())

    def get_capture(self, stem: str, attempt: int, name: str) -> bytes:
        if attempt is None or name is None:
            raise ValueError("attempt and name are required")
        path = self._capture_path(stem, attempt, name)
        try:
            raw = self.read_bytes(path)
        except FileNotFoundError as exc:
            raise CaptureNotFound(str(path)) from exc
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("pointer is not an object")
            schema, ref = data.get("schema"), data.get("blob")
            if not isinstance(schema, str) or not re.fullmatch(r"clutch\.evidence\.capture/1\.\d+", schema):
                raise ValueError("invalid capture schema")
            if not isinstance(ref, str) or not _REF.fullmatch(ref):
                raise ValueError("invalid capture blob")
            return self.get_blob(ref)
        except (ValueError, UnicodeError, FileNotFoundError, zstd.ZstdError) as exc:
            raise CaptureUnreadable(str(path)) from exc

    def captures(self, stem: str, attempt: int | None = None) -> list[tuple[int, str]]:
        self._validate_capture(stem, attempt)
        root = self.root / "captures" / stem
        result = []
        for directory in self.fs.entries(root):
            if not directory.isascii() or not directory.isdecimal() or int(directory) < 0:
                continue
            number = int(directory)
            if attempt is not None and number != attempt:
                continue
            for entry in self.fs.entries(root / directory):
                name = unquote(entry[:-5]) if entry.endswith(".json") else ""
                if _NAME.fullmatch(name):
                    result.append((number, name))
        return sorted(result)

    def _record_path(self, key: str, kind: str) -> Path:
        if kind not in ("start", "end"):
            raise ValueError("record kind must be start or end")
        return self.root / "calls" / quote(key, safe="") / (kind + ".json")

    def write_record(self, key: str, kind: str, data: dict, *, replace: bool = False) -> None:
        model = {"start": Start, "end": End}.get(kind)
        if model is None:
            raise ValueError("record kind must be start or end")
        record = model.model_validate(data)
        (self.fs.write if replace else self.fs.publish)(self._record_path(key, kind), record.model_dump_json(by_alias=True).encode())

    def read_record(self, key: str, kind: str) -> BaseModel | SkipRecord:
        path = self._record_path(key, kind)
        data = json.loads(self.read_bytes(path))
        match = re.fullmatch(r"clutch\.evidence\.call/(\d+)\.(\d+)", data["schema"])
        if not match or match.group(1) != "1":
            return SKIP
        data["schema"] = "clutch.evidence.call/1.0"
        model = {"start": Start, "end": End}[kind]
        return model.model_validate(_ignore_unknown(model, data))

    def write_normalized(self, key: str, normalizer_id: str, view: dict) -> None:
        path = self._record_path(key, "start").parent / "normalized" / (quote(normalizer_id, safe="") + ".json")
        self.fs.write(path, self.redact(json.dumps(view)).encode())

    def read_normalized(self, key: str) -> tuple[list[dict], int]:
        """Return understood views and the count skipped for unknown versions."""
        directory = self._record_path(key, "start").parent / "normalized"
        views = []
        skipped = 0
        for name in self.fs.entries(directory):
            if not name.endswith(".json"):
                continue
            view = json.loads(self.read_bytes(directory / name))
            match = re.fullmatch(r"clutch\.evidence\.events/(\d+)\.(\d+)", view["schema"])
            if not match or match.group(1) != "1":
                skipped += 1
                continue
            views.append(view)
        return views, skipped

    def write_attempt(self, data: dict) -> None:
        record = Attempt.model_validate(data)
        path = self.root / "attempts" / record.stem / str(record.run_seq) / f"{record.attempt}.json"
        self.fs.publish(path, self.redact(record.model_dump_json(by_alias=True)).encode())

    def read_attempt(self, stem: str, run_seq: int, attempt: int) -> Attempt | SkipRecord:
        path = self.root / "attempts" / stem / str(run_seq) / f"{attempt}.json"
        data = json.loads(self.read_bytes(path))
        match = re.fullmatch(r"clutch\.evidence\.attempt/(\d+)\.(\d+)", data["schema"])
        if not match or match.group(1) != "1":
            return SKIP
        data["schema"] = "clutch.evidence.attempt/1.0"
        return Attempt.model_validate(_ignore_unknown(Attempt, data))

    def attempts(self) -> list[tuple[str, int, int]]:
        root = self.root / "attempts"
        return sorted(
            (stem, int(run), int(name[:-5]))
            for stem in self.fs.entries(root)
            for run in self.fs.entries(root / stem)
            if run.isdecimal()
            for name in self.fs.entries(root / stem / run)
            if name.endswith(".json") and name[:-5].isdecimal()
        )

    def call_keys(self, prefix: str) -> list[str]:
        return sorted(key for entry in self.fs.entries(self.root / "calls") if (key := unquote(entry)).startswith(prefix))

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
        captures = self.root / "captures"
        for stem in self.fs.entries(captures):
            for attempt in self.fs.entries(captures / stem):
                for name in self.fs.entries(captures / stem / attempt):
                    if name.endswith(".json"):
                        counts.update(_refs(json.loads(self.read_bytes(captures / stem / attempt / name))))
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
