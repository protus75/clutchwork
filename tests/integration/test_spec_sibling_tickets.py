from clutch.specs import load_spec
from tests.integration.test_requisition import SPECS, TICKET, reply, run, setup


def test_sibling_instruction_and_real_render(tmp_path):
    source = (SPECS / "requisition_review.md").read_text()
    task = load_spec(source).body.split("## Task", 1)[1].split("## Inputs", 1)[0]
    assert "{{sibling_tickets}}" in source
    for phrase in ("sibling stem", "changed interface", "criterion or test it would break", "shared file alone", "is not a hit"):
        assert phrase in task
    repo, driver, llm = setup(tmp_path, [reply("approve")])
    sibling = repo / "tickets" / "other" / "ticket.md"
    sibling.parent.mkdir(parents=True)
    sibling.write_text(TICKET)
    assert run(driver, repo).verdict == "approve"
    block = llm.requests[0].rendered.split("<<clutch-data:begin sibling_tickets>>")[1].split("<<clutch-data:end sibling_tickets>>")[0]
    assert "other" in block
