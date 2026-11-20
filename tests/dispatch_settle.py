# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: dispatch settle
# relates: [tests/fakes.py]
# owner: tests/fakes.py
# verified: d7719818
# hash: edd6c15d8051b8be69897b759b31c94e9f0d6a3b207043fd485b381a7bfcff7e
from tests.fakes import turn


async def dispatch_settled(scheduler):
    ticket = await scheduler.dispatch_next()
    while ticket is not None and ticket.stem in scheduler.flying:
        await turn()
    return ticket
