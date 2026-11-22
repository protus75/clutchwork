## Outcome

premise_failed

## Surprises / judgment calls

Leaving PythonProviderExec in the provider hub resolves the prior finding, but the separate provider-script FakeExec still needs capabilities absent from the shared fake.

## Dead ends

Re-exporting tests.fakes.FakeExec cannot preserve the provider helper’s signature or behavior: it accepts only one fixed result and lacks spawn and stdout callbacks, structured call records, hanging, and kill_group.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

The ticket estimated 30 minutes; inspection found a blocking premise before implementation.

