import importlib
import re
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_clutch_package_imports():
    clutch = importlib.import_module("clutch")
    assert Path(clutch.__file__).resolve().parent == PYPROJECT.parent / "clutch"


def test_pyproject_pins_python_floor_and_runtime_deps():
    project = tomllib.loads(PYPROJECT.read_text())["project"]
    assert project["requires-python"] == ">=3.14"
    names = {re.match(r"[A-Za-z0-9._-]+", dep).group().lower() for dep in project["dependencies"]}
    # Section 0 runtime set: exactly these non-stdlib deps, nothing accreted.
    assert names == {"pyyaml", "pydantic", "duckdb"}


def test_pytest_timeout_configuration():
    config = tomllib.loads(PYPROJECT.read_text())
    assert "pytest-timeout==2.5.0" in config["dependency-groups"]["dev"]
    options = config["tool"]["pytest"]["ini_options"]
    assert options["timeout"] == 120
    assert options["timeout_method"] == "thread"
