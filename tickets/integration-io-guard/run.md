## Outcome

premise_failed

## Surprises / judgment calls

On Python 3.14, tempfile.TemporaryFile() first emits open('/tmp', 'w+', 524866), which has write and creation flags but no O_TMPFILE; only its subsequent open event includes O_TMPFILE. The specified guard must block the first event, so the acceptance test fails before the anonymous file opens.

## Dead ends

Implemented the stated audit policy and ran the targeted unit command; the temporary-file case failed at the preliminary open event.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.25

## Predicted vs actual

none

