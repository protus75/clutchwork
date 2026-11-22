## Outcome

premise_failed

## Surprises / judgment calls

Both test_cli.py and bench.py already call yaml.safe_dump outside their config literals.

## Dead ends

Considered removing the existing yaml.safe_dump call, but the ticket permits only the config literal and its import to change in test_cli.py.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

none

