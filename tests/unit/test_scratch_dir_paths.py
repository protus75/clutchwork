from clutch.retro import window_scratch_path
from clutch.stages import render_scratch_dir


def test_scratch_paths(tmp_path):
    assert render_scratch_dir(tmp_path, "work", 4) == tmp_path / "scratch/work/4/render"
    assert window_scratch_path(tmp_path, 1, 2) == tmp_path / "scratch/retro/1/call-02/window.jsonl"
