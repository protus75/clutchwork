from tests.fakes import turn


async def dispatch_settled(scheduler):
    ticket = await scheduler.dispatch_next()
    while ticket is not None and ticket.stem in scheduler.flying:
        await turn()
    return ticket
