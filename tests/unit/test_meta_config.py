# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test meta config
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 9a610809
# hash: c2832ac7273ad7cfdda16fedd4bad58e38f70b3f6ac003ae25fd2c9c47fbfbfa
import pytest
from pydantic import ValidationError

from clutch.config import Meta, MetaPath


def test_default_and_closed_kind():
    assert Meta().paths == []
    with pytest.raises(ValidationError):
        MetaPath(root="docs/", kind="unknown")
