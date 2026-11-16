---
id: tombstone-box-000479-38cf6e2d
kind: tombstone
link: declined-box-000047-f327cc48
reopen_after_days: 90
---
The note says secret redaction runs on text that is already JSON-encoded, in `EngineLog.event` and in the harvest.json writer. A configured secret that contains a quote, a backslash, a control character or a non-ASCII character would be written in escaped form, so the plain replace would not match it. The note proposes one shared scrub on `Redactor` that runs on the Python value before encoding, and would replace the private `CliAdapter._scrub_event`.

Registry record 000047 already declined this request. It covered the same `EngineLog` scrub-after-`json.dumps` gap and proposed the same fix: scrub fields before encoding and add a pinning test. This message adds two things. It names harvest.json as a second writer with the same pattern. It also points to the provider adapter's existing recursive scrub. Neither one changes the core case, and neither shows that a real leak can happen. `Redactor.from_config` only redacts provider `auth` env-var values, which are API tokens. The message cites no configured token that contains a quote, a backslash, a control character or a non-ASCII character. It also cites no engine log or harvest file that held an unredacted secret. Without that, this is speculative hardening, as before. Reopen if a configured provider credential with a JSON-escaped character is shown to exist, or if an engine.log or harvest.json line is found to carry a secret the scrub missed.

- clutch/enginelog.py:28 scrubs json.dumps(record, default=str) output, which matches the gap in declined-box-000047-f327cc48
- clutch/redact.py:25-27 Redactor.from_config only redacts provider auth env-var values, which are API tokens
- clutch/redact.py:29-32 scrub is a plain str.replace for each secret value
- clutch/providers.py:420-430 CliAdapter._forward/_scrub_event already scrubs decoded event strings, so the provider event path is covered
- The message cites no incident in which a secret reached engine.log or harvest.json unredacted

Message: box-000479-38cf6e2d
