# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: context suggest query over index tables
# relates: [clutch/__main__.py]
# owner: engine
# verified: be8ec7c3
# hash: 46df290eb4379175fe90f38e5efde93cdeb2f635e50f431aa2d6742b19aeede6
import duckdb

from clutch.context import suggest


def test_suggest_filters_and_ranking():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE files (path VARCHAR, kind VARCHAR, purpose VARCHAR, relates VARCHAR, owner VARCHAR, hash VARCHAR, size BIGINT)")
    conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR, tokens BIGINT)")
    conn.execute("CREATE TABLE touches (ticket VARCHAR, commit_sha VARCHAR, path VARCHAR)")
    paths = ["clutch/index.py", "clutch/merge.py", "clutch/skip.py", "tickets/no.md", "box:one"]
    conn.executemany("INSERT INTO files (path) VALUES (?)", [(p,) for p in paths])
    conn.executemany(
        "INSERT INTO touches VALUES (?, ?, ?)",
        [
            (t, sha, p)
            for t, sha, p in [
                ("a", "1", "clutch/index.py"),
                ("a", "1", "clutch/merge.py"),
                ("a", "2", "clutch/merge.py"),
                ("b", "3", "clutch/index.py"),
                ("b", "3", "clutch/merge.py"),
                ("c", "4", "clutch/merge.py"),
                ("demo", "5", "clutch/index.py"),
                ("demo", "5", "clutch/skip.py"),
                ("a", "1", "tickets/no.md"),
                ("a", "1", "missing.py"),
            ]
        ],
    )
    conn.executemany(
        "INSERT INTO chunks VALUES (?, ?, ?, ?)",
        [
            ("clutch/index.py", "clutch/index.py::build", "index build", 2),
            ("clutch/index.py", "clutch/index.py::index_build", "index only", 1),
            ("tickets/no.md", "tickets/no.md#build", "index build", 2),
            ("box:one", "box:one#build", "index build", 2),
        ],
    )
    files, sections = suggest(conn, "demo", ["clutch/index.py"], [], "`index.build` and `clutch/index.py`")
    assert files == [("clutch/merge.py", "changed with clutch/index.py in 2 past tickets")]
    assert sections == [("clutch/index.py::build", "matches build, index")]
    assert suggest(conn, "demo", ["clutch/index.py"], ["clutch/merge.py::name", "clutch/index.py::build"], "`index.build`") == ([], [])
    assert suggest(conn, "demo", ["clutch/index.py"], [], "index build")[1] == []
    conn.close()


def test_caps_ties_and_reasons():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE files (path VARCHAR)")
    conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR)")
    conn.execute("CREATE TABLE touches (ticket VARCHAR, commit_sha VARCHAR, path VARCHAR)")
    conn.executemany("INSERT INTO files VALUES (?)", [(f"file{i}",) for i in range(7)])
    conn.executemany("INSERT INTO touches VALUES (?, ?, ?)", [("a", "sha", p) for p in ["fence-b", "fence-a"] + [f"file{i}" for i in range(7)]] + [("b", "sha", p) for p in ["fence-b", "file6"]])
    conn.executemany("INSERT INTO chunks VALUES (?, ?, ?)", [(f"file{i}", f"file{i}#section", "alpha bravo charlie delta echo foxtrot") for i in range(7)])
    files, sections = suggest(conn, "demo", ["fence-b", "fence-a"], [], "`alpha bravo charlie delta echo foxtrot`")
    assert files == [("file6", "changed with fence-b in 2 past tickets")] + [(f"file{i}", "changed with fence-a in 1 past tickets") for i in range(4)]
    assert sections == [(f"file{i}#section", "matches alpha, bravo, charlie, delta, echo") for i in range(5)]
    conn.close()
