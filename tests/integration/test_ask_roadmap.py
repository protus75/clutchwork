# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the roadmap prompt prints the packaged type/roadmap facet and wrapped host notes without creating the roadmap or state
# relates: [clutch/__main__.py, clutch/ask.py, clutch/runner.py, clutch/specs/__init__.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: af6ce3dea81b43d0eef9159cc012b77262dc05cb4787b297de23ab7c146de7e6
import pytest
import yaml

from clutch import ask, specs
from clutch.__main__ import main
from clutch.runner import SPECS_DIR
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


def test_roadmap_resources_and_read_only_host(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state") + '\nask_notes: "host guidance"\n')
    facet = (SPECS_DIR / "doc/facets/type/roadmap.md").read_text()
    metadata = yaml.safe_load(facet.split("---", 2)[1])
    assert metadata["facet"] == "type/roadmap"  # A different facet identity is not the roadmap Type.
    assert metadata["version"] == "1.0" and metadata["applies_to"] == ["create", "derive"]  # A stale version or missing operation is incompatible.
    assert main(["prompt", "roadmap"], cwd=tmp_path) == 0  # A missing ticket or source tree must not refuse.
    output = capsys.readouterr().out
    assert facet in output  # A copied or omitted body is not the packaged facet.
    assert specs.data_open("host_notes") + "\nhost guidance\n" + specs.data_close("host_notes") in output  # Raw host notes without the data wrapper are unsafe.
    assert not (tmp_path / "docs/roadmap.md").exists()  # Rendering must not create the roadmap.
    assert not (tmp_path / "custom/state").exists()  # Rendering must not create state.
