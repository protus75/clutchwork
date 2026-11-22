# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that observe.commits parses git log records into commit entries whose message includes the body without splitting records on body newlines.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: 56216342
# hash: 25db2805a6208fb1ae81166589f30062aba233f40f1684513a799c98a239f1d3
from clutch import observe


def test_commit_messages_include_body_without_splitting_records(monkeypatch):
    log = "sha1\x1fone\x1fAda\x1fdate1\x1fsubject\x1fline one\nline two\n\x1e\nsha2\x1ftwo\x1fBob\x1fdate2\x1fsubject\x1f\x1e\n"
    calls = []
    monkeypatch.setattr(observe, "git_output", lambda *args: calls.append(args) or log)

    result = observe.commits(None)

    assert calls == [(None, "log", "--format=%H%x1f%h%x1f%an%x1f%aI%x1f%s%x1f%b%x1e", "main")]
    assert result == {
        "sha1": {"sha": "sha1", "short": "one", "author": "Ada", "date": "date1", "subject": "subject", "message": "subject\n\nline one\nline two"},
        "sha2": {"sha": "sha2", "short": "two", "author": "Bob", "date": "date2", "subject": "subject", "message": "subject"},
    }
