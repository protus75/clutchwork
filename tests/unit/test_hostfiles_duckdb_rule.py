from clutch.hostfiles import CORE_TEMPLATE


def test_duckdb_rule_is_unique_and_in_engine_conduct():
    lines = CORE_TEMPLATE.splitlines()
    matches = [index for index, line in enumerate(lines) if b"DuckDB, never SQLite" in line]
    assert len(matches) == 1
    assert matches[0] > lines.index(b"## Engine conduct")


def test_core_template_fits_shared_cap():
    assert len(CORE_TEMPLATE) <= 8192
