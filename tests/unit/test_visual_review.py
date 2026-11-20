# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test visual review
# relates: [clutch/config.py, clutch/visual.py]
# owner: engine
# verified: 9a610809
# hash: 509f29332fe29aa778d54be6371b2cdd5ecbc4a11561efd6ec02c5c25ac8fe19
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from clutch.config import Config
from clutch.visual import majority, parse_reply, rubric_ids


def reply(rows, verdict="accept"):
    return json.dumps({"rows": [{"id": key, "verdict": value, "observation": f"observed {key} {value}"} for key, value in rows], "verdict": verdict, "reason": f"Result is {verdict}."})


def test_rubric_ids():
    assert rubric_ids(["a"], "generate") == ["a", "identity", "placement", "lighting", "unchanged", "artifacts"]
    assert rubric_ids(["a"], "command") == ["a"]


def test_parse_reply_refusals():
    good = reply([("a", "pass"), ("b", "fail")])
    assert [row.id for row in parse_reply(good, ["a", "b"]).rows] == ["a", "b"]
    for bad in (reply([("a", "pass")]), reply([("a", "pass"), ("a", "fail"), ("b", "pass")]), reply([("a", "pass"), ("b", "pass"), ("c", "fail")]), reply([("a", "pass"), ("b", "fail")], "maybe")):
        with pytest.raises(ValueError, match="return"):
            parse_reply(bad, ["a", "b"])


def test_majority():
    def sample(a, b, verdict):
        return parse_reply(reply([("a", a), ("b", b)], verdict), ["a", "b"])

    one = sample("pass", "pass", "accept")
    two = sample("pass", "fail", "accept")
    three = sample("fail", "unsure", "reject")
    combined = majority([one, two, three])
    assert [r.verdict for r in combined.rows] == ["pass", "unsure"]
    assert combined.verdict == "accept"
    tied = majority([one, three])
    assert [r.verdict for r in tied.rows] == ["unsure", "unsure"]
    assert tied.verdict == "unsure"
    split = majority([one, sample("fail", "fail", "reject"), sample("unsure", "unsure", "unsure")])
    assert split.rows[0].verdict == "unsure"
    assert split.verdict == "unsure"
    assert majority([one]) is one


def test_judge_samples_config():
    raw = {
        "schema_version": 1,
        "state_dir": "state",
        "providers": [{"name": "p", "kind": "api", "models_by_tier": dict.fromkeys(("low", "medium", "high", "max"), "m"), "limits": {"concurrency": 1}}],
        "routing": [{"tier": "medium", "surface": "review", "candidates": [{"provider": "p"}]}],
        "review": {},
        "merge": {},
        "engine_plane_safety_inventory": [],
    }

    def config(graphics=None):
        return Config.model_validate({**raw, **({"graphics": graphics} if graphics is not None else {})}, context={"base": Path("/")})

    assert config().graphics.judge_samples == 1
    assert config({"judge_samples": 3}).graphics.judge_samples == 3
    for graphics in ({"judge_samples": 0}, {"judge_samples": 4}, {"extra": 1}):
        with pytest.raises(ValidationError):
            config(graphics)


def test_invalid_schema_and_incompatible_samples():
    with pytest.raises(ValueError, match="specified JSON"):
        parse_reply("not json", ["a"])
    with pytest.raises(ValueError, match="at least one"):
        majority([])
    first = parse_reply(reply([("a", "pass")]), ["a"])
    other = parse_reply(reply([("b", "fail")]), ["b"])
    with pytest.raises(ValueError, match="same rubric"):
        majority([first, other])


def test_majority_keeps_winning_observations():
    first = parse_reply(reply([("a", "fail")], "reject"), ["a"])
    second = parse_reply(reply([("a", "pass")], "accept"), ["a"])
    third = parse_reply(reply([("a", "pass")], "accept"), ["a"])
    combined = majority([first, second, third])
    assert combined.rows[0].observation == "observed a pass"
    assert combined.reason == "Result is accept."
    tied = majority([first, second])
    assert tied.rows[0].observation == "No strict majority among observations."
    assert tied.reason == "No strict majority among verdicts."
