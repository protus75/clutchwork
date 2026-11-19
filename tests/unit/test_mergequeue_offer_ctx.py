from types import SimpleNamespace

from clutch.mergequeue import MergeQueue


def test_offer_retains_each_context_and_default():
    original, first, second = object(), object(), object()
    queue = MergeQueue(original, escalate=lambda event: None)
    queue.offer(SimpleNamespace(stem="t1"), attempt=0, ctx=first)
    queue.offer(SimpleNamespace(stem="t2"), attempt=0, ctx=second)
    queue.offer(SimpleNamespace(stem="t3"), attempt=0)
    assert queue.contexts == {"t1": first, "t2": second, "t3": original}
