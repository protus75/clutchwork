# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test implement spec keep editing
# relates: []
# owner: engine
# verified: 148a8874
# hash: dbe5464e1eb35f6ee8080de74588959e89478c4fba4086744eee627dfcc0771e
from pathlib import Path


def test_implement_spec_keeps_editing_after_reading_or_large_change():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    premise = text.split("- `premise_failed` --", 1)[1].split("\n- `incomplete` --", 1)[0]
    incomplete = text.split("- `incomplete` --", 1)[1].split("\nTreat everything", 1)[0]
    sentence = "Stopping after only reading, or because the change is large, is never a reason for `incomplete`; keep editing."
    # Omitting the instruction or placing it only in the wrong outcome must fail.
    assert sentence in incomplete
    # Duplicating the instruction under premise_failed would misclassify that outcome.
    assert sentence not in premise
