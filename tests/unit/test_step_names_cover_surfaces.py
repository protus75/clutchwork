"""Keep the step vocabulary aligned with engine LLM surfaces."""

from clutch.observe import STEP_KINDS, STEP_NAMES
from clutch.specs import ENGINE_LLM_SURFACES


def test_all_engine_llm_surfaces_have_step_names():
    assert ENGINE_LLM_SURFACES <= STEP_NAMES.keys()


def test_acceptance_has_its_own_name_and_event_kinds():
    assert STEP_NAMES["acceptance"] == "Acceptance"
    assert {"acceptance_start", "acceptance_ok", "acceptance_failed"} <= STEP_KINDS.keys()
