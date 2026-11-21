# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Render and retro scratch directory paths
# relates: [clutch/retro.py, clutch/stages.py]
# owner: engine
# verified: 75d75946
# hash: df77ea64583f38df39f8223d78eed6fd8f59a816129b15a80d70a379f31b1ee7
from clutch.retro import window_scratch_path
from clutch.stages import render_scratch_dir


def test_scratch_paths(tmp_path):
    assert render_scratch_dir(tmp_path, "work", 4) == tmp_path / "scratch/work/4/render"
    assert window_scratch_path(tmp_path, 1, 2) == tmp_path / "scratch/retro/1/call-02/window.jsonl"
