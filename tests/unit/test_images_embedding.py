# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test images embedding
# relates: [clutch/images.py, clutch/stages.py]
# owner: engine
# verified: 0a308920
# hash: c91edf4cbf48b0a0ab213f5c8616e8496e57636fea28c4e659d3eb2698ab597e
import sys
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image

from clutch import images, stages


@pytest.fixture
def pictures(tmp_path):
    base = Image.fromarray(np.random.default_rng(12).integers(0, 256, (270, 270, 3), dtype=np.uint8))
    insert = Image.fromarray(np.random.default_rng(23).integers(0, 256, (90, 90, 3), dtype=np.uint8))
    edited = base.copy()
    edited.paste(insert, (90, 90))
    paths = []
    for name, image in (("base", base), ("insert", insert), ("edited", edited)):
        path = tmp_path / f"{name}.png"
        image.save(path)
        paths.append(path)
    return paths


def test_embedding_views_and_default(pictures, monkeypatch):
    base, insert, edited = pictures
    calls = []

    def embed(views):
        calls.append(views)
        return np.array([[1.0, 0.0]] + [[1.0, 0.0] if np.array_equal(np.asarray(view), np.asarray(views[0])) else [0.0, 1.0] for view in views[1:]])

    monkeypatch.setattr(images, "_embedder", lambda: embed)
    assert images.judge(edited, [base, insert], embedding=True) == []
    assert len(calls[0]) == 11 and calls[0][5].size == (90, 90)
    monkeypatch.setattr(images, "_embedder", lambda: lambda views: np.array([[1.0, 0.0]] + [[0.0, 1.0]] * 10))
    failures = images.judge(edited, [base, insert], embedding=True)
    assert len(failures) == 1 and str(insert) in failures[0] and "presence check failed" in failures[0] and "(embedding)" in failures[0]
    monkeypatch.setattr(images, "_embedder", Mock(side_effect=AssertionError("default must use ORB")))
    assert images.judge(edited, [base, insert]) == []
    monkeypatch.setattr(images, "_embedder", Mock(side_effect=ImportError))
    failures = images.judge(edited, [base, insert], embedding=True)
    assert len(failures) == 1 and "clutchwork[images-embed]" in failures[0]


def test_gate_uses_declared_presence(pictures, tmp_path, monkeypatch):
    base, insert, edited = pictures
    monkeypatch.setattr(images, "_embedder", lambda: lambda views: np.array([[1.0, 0.0]] + [[0.0, 1.0]] * 10))
    render = {"artifact": [edited.name], "input": [base.name, insert.name], "presence": ["embedding"]}
    item = stages.Evidence(
        stem="work", head_sha="abc", claimed="ok", scope_fence=[], inserted_lines=0, verification=[], run_record=None, changed_files=[], is_graphics=True, render_dir=str(tmp_path), render=render
    )
    report = stages.ImageQualityGate().check(item, tmp_path)
    assert report.verdict == "fail" and "(embedding)" in report.findings[0].message
    del render["presence"]
    report = stages.ImageQualityGate().check(item.model_copy(update={"render": render}), tmp_path)
    assert report.verdict == "pass" and not report.findings
    monkeypatch.setattr(images, "_embedder", Mock(side_effect=ImportError))
    render["presence"] = ["embedding"]
    report = stages.ImageQualityGate().check(item.model_copy(update={"render": render}), tmp_path)
    assert "clutchwork[images-embed]" in report.findings[0].paved_road


def test_loader_normalizes_with_fake_modules(monkeypatch):
    class Tensor:
        def __init__(self, data):
            self.data = np.asarray(data)

        def norm(self, dim, keepdim):
            return np.linalg.norm(self.data, axis=dim, keepdims=keepdim)

        def __truediv__(self, divisor):
            return Tensor(self.data / divisor)

    model = SimpleNamespace(eval=Mock(), encode_image=lambda batch: Tensor(batch))
    create = Mock(return_value=(model, None, lambda image: image))
    monkeypatch.setitem(sys.modules, "open_clip", SimpleNamespace(create_model_and_transforms=create))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(no_grad=nullcontext, stack=lambda items: items))
    result = images._embedder()([[3.0, 4.0], [5.0, 12.0]])
    assert np.allclose(result.data, [[0.6, 0.8], [5 / 13, 12 / 13]], atol=1e-6)
    assert model.eval.call_count == 1 and create.call_count == 1
