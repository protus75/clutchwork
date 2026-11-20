# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test new evidence
# relates: [clutch/__main__.py, clutch/runner.py]
# owner: engine
# verified: 9a610809
# hash: 9e16d490cd4cc11e12c702612f4d583aa26c26f148186549ec2968c5d9a91214
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
