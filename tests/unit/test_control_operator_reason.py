# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test control operator reason
# relates: [clutch/control.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: 433dc84579da67fd6b21786651543eca1db66bc1d002fcc98dee6f51e5a75c76
import json
from pathlib import PurePath
from types import SimpleNamespace

import pytest

from clutch import control
from clutch.journal import EventType

BASE = dict(request_id="request-1", lifecycle_id="life", verb="reject", stem="sample", hold_id=None, actor="operator")


def test_request_shapes_and_publication():
    assert control.validate_request({**BASE, "operator_reason": "x"}, "request-1.json").operator_reason == "x"
    assert control.validate_request(BASE, "request-1.json").operator_reason is None
    for value in ({**BASE, "verb": "confirm", "operator_reason": "x"}, {**BASE, "operator_reason": ""}, {**BASE, "operator_reason": 2}):
        with pytest.raises(ValueError):
            control.validate_request(value, "request-1.json")
    writes = []
    control.publish_request(PurePath("state"), control.AdmissionRequest(**BASE), SimpleNamespace(publish=lambda path, data: writes.append(json.loads(data))))
    assert writes == [BASE]


def test_decision_shapes():
    body = dict(kind=control.CONTROL_DECISION, decision="accepted", reason="matching admission", **BASE)

    def event(value):
        return SimpleNamespace(type=EventType.SIGNAL, ticket=None, key=None, body=value)

    assert list(control.decisions([event(body)]))[0].body == body
    with_reason = {**body, "operator_reason": "x"}
    assert list(control.decisions([event(with_reason)]))[0].body == with_reason
    with pytest.raises(ValueError):
        list(control.decisions([event({**body, "extra": "x"})]))
