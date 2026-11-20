import pytest
from pydantic import ValidationError

from clutch.config import Meta, MetaPath


def test_default_and_closed_kind():
    assert Meta().paths == []
    with pytest.raises(ValidationError):
        MetaPath(root="docs/", kind="unknown")
