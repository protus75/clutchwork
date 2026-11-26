# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the extension snapshot has one provider-install entry per provider adapter plus an update-all entry, and that each argv parses as a provider install command
# relates: [clutch/__main__.py, clutch/observe.py, clutch/providers.py]
# owner: engine
# verified: 69d790e1
# hash: 4ffd636ce936b4720be823831cc236e73f96b92d126f5a8d19be71891188fd0f
from clutch.__main__ import _parser
from clutch.observe import extension_fields
from clutch.providers import ADAPTERS


def test_provider_installs(tmp_path):
    entries = extension_fields(tmp_path)["providerInstalls"]
    names = [name for name in sorted(ADAPTERS) if ADAPTERS[name].PACKAGE is not None]
    assert len(entries) == len(names) + 1
    assert [entry["argv"] for entry in entries[:-1]] == [["provider", "install", name] for name in names]
    assert entries[-1]["argv"] == ["provider", "install", *names]
    for entry, expected_names in zip(entries, [[name] for name in names] + [names], strict=True):
        args = _parser().parse_args(entry["argv"])
        assert (args.verb, args.provider_verb, args.providers) == ("provider", "install", expected_names)
