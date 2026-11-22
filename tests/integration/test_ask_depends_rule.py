# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the drain-loop, plan-ticket-drain and plan-ticket-serve supervising prompts, as rendered, include the exact rule for recording Depends on and committing ticket edits, and never say to release a hold after a merge.
# relates: [clutch/ask.py]
# owner: clutch/ask.py
# verified: 64437681
# hash: ce87099bdce42425b8f54ec1758580f0df4ef06d66ed9a2e9b4a17e12a9352f3
import re
from types import SimpleNamespace

import pytest

from clutch import ask

BULLET = (
    "- When a ticket must wait for another, put that stem in the waiting ticket's `## Depends on` "
    "in the same edit, including a premise or hold release; never plan to release a hold after a merge. "
    "Commit every ticket edit immediately, by explicit path or through `clutch ticket review <stem>`."
)


@pytest.mark.parametrize("name", ("drain-loop", "plan-ticket-drain", "plan-ticket-serve"))
def test_supervising_prompt_orders_and_commits_ticket_edits(name, tmp_path):
    config = SimpleNamespace(state_dir=tmp_path / "state", ask_notes=None)
    text = ask.render(name, "", config, tmp_path)
    assert BULLET in text  # Omitting or changing this prompt's rule differs.
    assert not re.search(r"(?<!never plan to )release a hold after (?:a |the )?merge", text, re.IGNORECASE)  # An instruction to release later differs.
