"""Keep the step vocabulary aligned with engine LLM surfaces."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Keep the step vocabulary aligned with engine LLM surfaces.
# relates: [clutch/observe.py, clutch/specs/__init__.py]
# owner: engine
# verified: 9a610809
# hash: dc8a447105aad7b721ce4e5eb9072e550c2b58557118bf65d7164274a10fdc06

from clutch.observe import STEP_KINDS, STEP_NAMES
from clutch.specs import ENGINE_LLM_SURFACES


def test_all_engine_llm_surfaces_have_step_names():
    assert ENGINE_LLM_SURFACES <= STEP_NAMES.keys()


def test_acceptance_has_its_own_name_and_event_kinds():
    assert STEP_NAMES["acceptance"] == "Acceptance"
    assert {"acceptance_start", "acceptance_ok", "acceptance_failed"} <= STEP_KINDS.keys()
