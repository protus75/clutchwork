# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test rework review prior
# relates: [clutch/rework.py]
# owner: clutch/rework.py
# verified: 9a610809
# hash: f9213acb040e91ad0df1d9f32093d146263c27bceece3f1276fe8b82f381c8c2
import json

from clutch.rework import TicketProposal, review_prior


def test_review_prior_includes_other_proposals_and_preserves_inputs():
    a = TicketProposal(stem="A", ticket="A ticket text")
    b = TicketProposal(stem="B", ticket="B ticket text")
    inputs = ("split", "original", "original text", [{"message": "snag"}], [{"message": "retry"}])
    split = json.loads(review_prior(*inputs, [a, b], "B"))
    assert split["sibling_proposals"] == [{"stem": "A", "ticket": "A ticket text"}]
    assert isinstance(split["sibling_note"], str) and split["sibling_note"]

    single_inputs = ("update", "original", "revised original", [{"message": "another snag"}], [{"message": "another retry"}])
    single = json.loads(review_prior(*single_inputs, [a], "A"))
    assert single["sibling_proposals"] == []
    assert isinstance(single["sibling_note"], str) and single["sibling_note"]
    for key, value in zip(("action", "original_stem", "original_ticket", "snag_list", "retry_findings"), single_inputs, strict=True):
        assert single[key] == value
