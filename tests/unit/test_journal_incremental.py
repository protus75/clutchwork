# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test journal incremental
# relates: [clutch/journal.py]
# owner: clutch/journal.py
# verified: 0a308920
# hash: 2666c2a3edbe3c98f500b72b97b496191b9ce937ae18231ab14ba4fae43bc057
from pathlib import Path

import pytest

from clutch.journal import JournalCorruption, _parse_complete_lines

LINE = b'{"v":1,"type":"timer_armed","ts":"2026-08-04T12:00:00+00:00","ticket":null,"key":null,"body":{"n":7}}'


def test_complete_lines_and_offset():
    events, offset, count = _parse_complete_lines(Path("segment"), LINE + b"\n" + LINE[:12], 42, 3)
    assert [e.body for e in events] == [{"n": 7}]
    assert offset == 42 + len(LINE) + 1
    assert count == 4
    events, next_offset, count = _parse_complete_lines(Path("segment"), LINE[:12], offset, count)
    assert events == []
    assert next_offset == offset
    assert count == 4
    events, next_offset, count = _parse_complete_lines(Path("segment"), LINE + b"\n", offset, count)
    assert events[0].body == {"n": 7}
    assert next_offset == offset + len(LINE) + 1
    assert count == 5


def test_error_line_uses_prior_count():
    with pytest.raises(JournalCorruption, match=r"segment: line 5:"):
        _parse_complete_lines(Path("segment"), LINE + b"\nbad\n", 9, 3)
