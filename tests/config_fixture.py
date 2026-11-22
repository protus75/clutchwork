"""Minimal test config text and top-level edits shared by the serve rigs."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared test helpers that build a minimal clutch config.yaml text with overridable providers, routing and inventory, and that amend top-level sections of an existing config file.
# relates: [clutch/config.py, tests/unit/test_config_fixture.py, tests/integration/test_config_fixture_adoption.py, tests/integration/test_cli.py]
# owner: engine
# verified: 6f94fa01
# hash: 1a5f4a84e3e8451d1754a0ebae57f7174808c0fe81e2477da897285ebfe767e3

import yaml


def build_config(*, state_dir=".clutch/state", providers=None, routing=None, inventory=("config.yaml",)) -> str:
    if providers is None:
        providers = [{"name": "claude", "models": dict.fromkeys(("low", "medium", "high", "max"), "m"), "limits": {"concurrency": 1}}]
    if routing is None:
        routing = [{"tier": "medium", "surface": "implement", "candidates": [{"provider": "claude"}]}]

    def flow(value):
        return yaml.safe_dump(value, default_flow_style=True, sort_keys=False, width=float("inf")).strip()

    lines = ["schema_version: 1", yaml.safe_dump({"state_dir": state_dir}, sort_keys=False).strip(), "providers:"]
    for provider in providers:
        lines.extend([f"  - name: {provider['name']}", "    kind: cli", "    package: test-cli"])
        if "auth" in provider:
            lines.append(f"    auth: {provider['auth']}")
        lines.extend([f"    models_by_tier: {flow(provider['models'])}", f"    limits: {flow(provider['limits'])}"])
    lines.append("routing:")
    lines.extend(f"  - {flow(route)}" for route in routing)
    lines.extend(["review: {}", "merge: {}", f"engine_plane_safety_inventory: {flow(list(inventory))}"])
    return "\n".join(lines) + "\n"


def amend_config(root, **sections):
    path = root / "config.yaml"
    config = yaml.safe_load(path.read_text())
    for key, value in sections.items():
        if value is None:
            config.pop(key, None)
        else:
            config[key] = value
    path.write_text(yaml.safe_dump(config))
