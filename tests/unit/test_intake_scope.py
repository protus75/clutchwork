# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test intake scope
# relates: [clutch/tickets.py]
# owner: clutch/tickets.py
# verified: 0a308920
# hash: 316c61643df777e1fc917cdd6081a7f6f05ceba63a8a86832f6a14a180854774
import inspect

from clutch import tickets


def test_stems_is_a_required_keyword():
    parameter = inspect.signature(tickets.intake).parameters["stems"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
