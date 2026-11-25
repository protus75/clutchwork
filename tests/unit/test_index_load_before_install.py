"""Extension loading uses installed extensions before attempting installation."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests checking that default_creator.load tries LOAD first, then INSTALL and a second LOAD, and reports each failure path.
# relates: [clutch/index.py]
# owner: clutch/index.py
# verified: 01d081d3
# hash: 6edd981550c57bfe9680413dde782747f812c4f57babbe2697e0031601e57e36

import duckdb
import pytest

from clutch.index import default_creator


class Connection:
    def __init__(self, failures):
        self.calls = []
        self.failures = failures

    def execute(self, sql):
        self.calls.append(sql)
        if len(self.calls) in self.failures:
            raise duckdb.Error(self.failures[len(self.calls)])


@pytest.mark.parametrize(
    ("failures", "calls", "result"),
    [
        ({}, ["LOAD fts"], []),
        ({1: "missing"}, ["LOAD fts", "INSTALL fts", "LOAD fts"], []),
        ({1: "missing", 2: "install failed"}, ["LOAD fts", "INSTALL fts"], ["fts unavailable: install failed"]),
        ({1: "missing", 3: "retry failed"}, ["LOAD fts", "INSTALL fts", "LOAD fts"], ["fts unavailable: retry failed"]),
    ],
)
def test_load(failures, calls, result):
    conn = Connection(failures)
    assert default_creator.load(conn, "fts") == result
    assert conn.calls == calls
