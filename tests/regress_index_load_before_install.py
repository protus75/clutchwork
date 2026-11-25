"""Reproduce an unnecessary install in a read-only home directory."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Regression script checking that default_creator.load tries LOAD before INSTALL, so an already-installed extension still loads when the home directory is read-only.
# relates: [clutch/index.py]
# owner: clutch/index.py
# verified: 01d081d3
# hash: 2a98d8861c1ffd032ef9cc840953751d4e91dce064d21a4e665dbf9f91e44e46

import json
import sys

import duckdb

from clutch.index import default_creator


class Connection:
    def __init__(self):
        self.calls = []

    def execute(self, sql):
        self.calls.append(sql)
        if sql == "INSTALL fts":
            raise duckdb.IOException("Failed to create directory in read-only home")
        if sql != "LOAD fts":
            raise ValueError(sql)


def main():
    conn = Connection()
    try:
        result = default_creator.load(conn, "fts")
        if result == [] and conn.calls == ["LOAD fts"]:
            outcome, code = "pass", 0
        elif conn.calls == ["INSTALL fts"] and result == ["fts unavailable: Failed to create directory in read-only home"]:
            outcome, code = "defect", 1
        else:
            outcome, code = "error", 2
    except Exception:
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
