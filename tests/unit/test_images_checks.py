import builtins
import importlib
import sys
from io import BytesIO
from unittest.mock import patch

import pytest

from clutch import images


def test_import_is_lazy():
    names = ("PIL", "numpy", "skimage", "imagehash", "cv2", "open_clip", "torch")
    before = {name for name in sys.modules if name.split(".")[0] in names}
    real_import = builtins.__import__

    def checked_import(name, *args, **kwargs):
        assert name.split(".")[0] not in names
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=checked_import):
        importlib.reload(images)
    assert {name for name in sys.modules if name.split(".")[0] in names} == before


@pytest.fixture
def pictures(tmp_path):
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng  # deterministic, independent textures
    base = Image.fromarray(rng(12).integers(0, 256, (256, 256, 3), dtype=np.uint8))
    insert = Image.fromarray(rng(23).integers(0, 256, (96, 96, 3), dtype=np.uint8))
    other = Image.fromarray(rng(34).integers(0, 256, (256, 256, 3), dtype=np.uint8))
    edited = base.copy()
    edited.paste(insert, (80, 80))
    paths = {}
    for name, image in (("base", base), ("insert", insert), ("other", other), ("edited", edited), ("solid", Image.new("RGB", (64, 64), "red"))):
        paths[name] = tmp_path / f"{name}.png"
        image.save(paths[name])
    return paths


def test_no_inputs_and_blank(pictures, tmp_path):
    import numpy as np
    from PIL import Image

    noise = tmp_path / "noise.png"
    Image.fromarray(np.random.default_rng(1).integers(0, 256, (64, 64, 3), dtype=np.uint8)).save(noise)
    assert images.judge(noise, []) == []
    assert any("not-blank" in message for message in images.judge(pictures["solid"], []))


@pytest.mark.parametrize("contents", [None, b"", b"not an image"])
def test_bad_artifact_names_path(tmp_path, contents):
    path = tmp_path / "bad.png"
    if contents is not None:
        path.write_bytes(contents)
    failures = images.judge(path, [])
    assert failures and all(str(path) in message for message in failures)
    assert any(("exists" if contents is None else "decode") in message for message in failures)


def test_copy_and_preservation(pictures, tmp_path):
    copy = tmp_path / "copy.png"
    copy.write_bytes(pictures["base"].read_bytes())
    assert any("not-a-copy" in message for message in images.judge(copy, [pictures["base"]]))
    edited = images.judge(pictures["edited"], [pictures["base"]])
    assert not any("not-a-copy" in message or ": preservation check" in message for message in edited)
    replaced = images.judge(pictures["other"], [pictures["base"]])
    assert any(": preservation check" in message for message in replaced)
    assert not any("not-a-copy" in message for message in replaced)
    assert any("not-a-copy" in message for message in images.judge(pictures["insert"], [pictures["base"], pictures["insert"]]))


def test_presence_and_combined(pictures):
    assert images.judge(pictures["edited"], [pictures["base"], pictures["insert"]]) == []
    failures = images.judge(pictures["base"], [pictures["base"], pictures["insert"]])
    assert any(": presence check" in message and str(pictures["insert"]) in message for message in failures)


def test_missing_extra(pictures):
    with patch.object(images, "_load", side_effect=ImportError):
        failures = images.judge(pictures["edited"], [])
    assert len(failures) == 1 and "clutchwork[images]" in failures[0]


def test_previews_are_png_and_do_not_write(pictures, tmp_path):
    from PIL import Image

    before = set(tmp_path.iterdir())
    for result in (images.side_by_side([pictures["base"], pictures["edited"]]), images.heatmap(pictures["base"], pictures["edited"])):
        assert isinstance(result, bytes)
        with Image.open(BytesIO(result)) as image:
            assert image.format == "PNG"
    assert set(tmp_path.iterdir()) == before


def test_dimensions(pictures, tmp_path):
    from PIL import Image

    with Image.open(pictures["base"]) as source:
        small = tmp_path / "small.png"
        wide = tmp_path / "wide.png"
        source.resize((16, 16)).save(small)
        source.resize((400, 32)).save(wide)
    assert any(": dimensions/aspect" in message for message in images.judge(small, []))
    assert any(": dimensions/aspect" in message for message in images.judge(wide, []))
