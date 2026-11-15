---
id: declined-box-000383-f10c031a
kind: declined
link: box-000383-f10c031a
reopen_after_days: 30
---
The note says control/active.json stays in place after drain or serve exits. A one-shot lock holder such as review or triage would then cause confirm, reject or pause to publish a control request to an engine that is gone and still print 'submitted'. Current code already clears the advertisement on a normal exit, so this cannot happen there.

The main claim is wrong for current code. Both engine loops retire their control identity in a finally block on exit: clutch/drain.py:289 and clutch/serve.py:672 call retire(). retire() (clutch/daemon.py:224-227) writes JSON null to control/active.json. read_active (clutch/control.py:282-295) rejects any value that is not a dict, raising ValueError. The confirm/reject/pause/retro LockHeld paths (clutch/__main__.py:597, :746, :795) turn that into a Refusal ('current control identity unavailable'). So after drain or serve exits normally, a one-shot holder holding the lock causes a refusal, not a 'submitted' message. The only gap left is a hard kill (SIGKILL or power loss) that skips the finally block and leaves a stale lifecycle id behind. The note neither claims nor shows that case, and nobody has observed a request being lost that way.

- clutch/drain.py:285-289 calls consumer.retire() in a finally block when the drain exits
- clutch/serve.py:670-672 calls self.control.retire() in a finally block when serve exits
- clutch/daemon.py:224-225: retire() calls write_active(state_dir, None, ...), which writes JSON null
- clutch/control.py:285-294: read_active raises ValueError unless the value is a dict with a non-empty lifecycle_id
- clutch/__main__.py:597-599, 746-748, 795-797: the LockHeld fallbacks turn that ValueError into runner.Refusal instead of publishing the request

Message: box-000383-f10c031a
