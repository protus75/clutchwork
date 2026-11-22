## Outcome

premise_failed

## Surprises / judgment calls

PythonProviderExec's existing tests require spawn callbacks, streamed output callbacks, process-group termination and capture after callback errors; tests.fakes.FakeExec only returns a fixed result and records argv.

## Dead ends

A subclass cannot preserve the existing arbitrary Python child scripts and real process-group behavior without implementing a process simulator or running a process, neither of which the ticket permits.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

30 minutes expected; stopped during contract inspection.

