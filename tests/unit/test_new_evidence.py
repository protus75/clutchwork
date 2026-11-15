from pathlib import Path

import pytest

from clutch.__main__ import _new
from clutch.runner import Refusal


def test_bug_requires_evidence_before_io():
    with pytest.raises(Refusal, match="--evidence"):
        _new(Path("/nonexistent-repo"), "fix-thing", "bug")


def test_feature_rejects_evidence_before_io():
    with pytest.raises(Refusal, match="evidence is for bug tickets"):
        _new(Path("/nonexistent-repo"), "add-thing", "feature", ("x.txt",))
