import ast
from pathlib import Path


def test_no_raw_path_mkdir_or_unlink_in_seam_users():
    for name in ("enginelog.py", "journal.py", "stages.py"):
        tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch" / name).read_text())
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        assert not [call for call in calls if call.attr == "unlink"], name
        assert not [call for call in calls if call.attr == "mkdir" and not (isinstance(call.value, ast.Attribute) and call.value.attr in {"fs", "_fs"})], name
