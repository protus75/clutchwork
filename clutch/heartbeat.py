"""Serve refreshes the heartbeat file each healthy loop."""

from pathlib import Path

from clutch.seams import FileSystem


class Heartbeat:
    def __init__(self, *, state_dir: Path, fs: FileSystem) -> None:
        self.path, self.fs = state_dir / "heartbeat", fs

    def refresh(self) -> None:
        self.fs.write(self.path, b"")
