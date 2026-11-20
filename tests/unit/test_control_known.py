"""Inbox owners must supply the admission stem rule at construction."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Inbox owners must supply the admission stem rule at construction.
# relates: [clutch/control.py, clutch/daemon.py]
# owner: engine
# verified: 0a308920
# hash: bc2c89af733b6aa24a03653f0b9d5589377ccbc8bb41a0f89e3b3636d3748bcb

import pytest

from clutch.control import ControlInbox
from clutch.daemon import PauseConsumer


def test_inbox_requires_known():
    with pytest.raises(TypeError, match="known"):
        ControlInbox(journal=None, lifecycle_id="life", holds=lambda: set(), apply=lambda _: None, files=lambda: (), read=lambda _: b"")


def test_pause_consumer_requires_and_forwards_known():
    args = dict(journal=None, lifecycle_id="life", state_dir=None, fs=None, sleep=None, files=lambda: (), read=lambda _: b"")
    with pytest.raises(TypeError, match="known"):
        PauseConsumer(**args)
    consumer = PauseConsumer(**args, known=lambda stem: stem == "x")
    assert consumer.inbox.known("x") is True
    assert consumer.inbox.known("y") is False
