# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test mergequeue offer ctx
# relates: [clutch/mergequeue.py]
# owner: clutch/mergequeue.py
# verified: 9a610809
# hash: d0df12ee3adea1485b05232e0c991f43dfca37f5b410485d8968077b3d6e07ff
from types import SimpleNamespace

from clutch.mergequeue import MergeQueue


def test_offer_retains_each_context_and_default():
    original, first, second = object(), object(), object()
    queue = MergeQueue(original, escalate=lambda event: None)
    queue.offer(SimpleNamespace(stem="t1"), attempt=0, ctx=first)
    queue.offer(SimpleNamespace(stem="t2"), attempt=0, ctx=second)
    queue.offer(SimpleNamespace(stem="t3"), attempt=0)
    assert queue.contexts == {"t1": first, "t2": second, "t3": original}
