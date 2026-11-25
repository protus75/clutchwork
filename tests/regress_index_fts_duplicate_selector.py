# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression probe that runs an index FTS query against duplicate markdown heading selectors and reports pass, defect, or error as JSON
# relates: [clutch/index.py, clutch/seams.py]
# owner: engine
# verified: a5276361
# hash: 5dbf51cde7f977e9a2993404f92bf2f8e57cf16a18c481a9145f24f57b16b6a3
import asyncio
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

import duckdb

from clutch import index
from clutch.seams import LocalFileSystem


def main():
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b"# Top\n## Engine conduct\nengine behavior\n## Engine conduct\nengine process\n"
            (root / "doc.md").write_bytes(data)
            conn = duckdb.connect(str(root / "index.duckdb"))
            conn.execute("LOAD fts")
            conn.execute("CREATE TABLE files (path VARCHAR, kind VARCHAR, purpose VARCHAR, relates VARCHAR, owner VARCHAR)")
            conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR, tokens BIGINT)")
            conn.execute("INSERT INTO files VALUES ('doc.md', '', '', '[]', '')")
            conn.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?)", index._extract("doc.md", data)[4])
            conn.execute("PRAGMA create_fts_index('chunks', 'selector', 'text', overwrite=1)")
            conn.close()

            class Creator:
                def load(self, conn, kind):
                    conn.execute("LOAD fts")
                    return []

            config = NS(state_dir=root, index=NS(embed=None))
            result = asyncio.run(index.query(config, root, "engine", fs=LocalFileSystem(), exec_=None, env={}, creator=Creator()))
            if result.outcome == "found":
                result_name, code = "pass", 0
            elif result.outcome == "index_unreadable" and any("More than one row returned" in finding for finding in result.findings):
                result_name, code = "defect", 1
            else:
                result_name, code = "error", 2
    except Exception:
        result_name, code = "error", 2
    print(json.dumps({"regression_result": result_name}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
