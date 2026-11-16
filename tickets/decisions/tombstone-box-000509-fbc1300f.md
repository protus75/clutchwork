---
id: tombstone-box-000509-fbc1300f
kind: tombstone
link: declined-box-000163-207e142e
reopen_after_days: 30
---
When a test's FakeLLM runs out of scripted replies, it raises AssertionError. The driver catches that error with its generic Exception handler and ends the run as infra_error, so a test that makes an unscripted model call can still pass. The message asks for exhaustion to fail the test, either by checking at teardown or by raising a BaseException subclass, and adds that about 15 integration tests made an extra unscripted Rework call in an unmerged supervisor-rework prototype and still passed.

Registry record declined-box-000163-207e142e already covers this. It names the same mechanism (FakeLLM exhaustion raises AssertionError, Driver's generic except Exception turns it into infra_error, and a test with a missing reply passes on that path) and essentially the same fix (an exhaustion error the driver does not swallow). The new evidence is the about 15 tests from the supervisor-rework prototype at 4d4cb7b5, which is unmerged work, not current main. It shows the test harness can hide an extra call. It shows no reachable wrong runtime behavior in the engine, so this is still a test-only improvement. Reopen if a merged change is shown to ship an extra or missing model call that the suite missed because exhaustion was swallowed, or once supervisor-rework merges and its tests depend on calls nothing scripts.

- clutch/llm.py:72: FakeLLM.call raises AssertionError('FakeLLM script exhausted at call N; script one more response') when the script is empty
- clutch/driver.py:370-371 and :393-394: `except Exception as e: return await failed(e, call, name, ...)` turns any call exception, including AssertionError, into a failed stage result instead of letting it propagate
- Registry record declined-box-000163-207e142e describes the same swallowed-exhaustion gap and proposes a dedicated exhaustion exception that the driver re-raises
- The about 15 tests that passed with unscripted calls were seen only while prototyping unmerged supervisor-rework at 4d4cb7b5; the message reports no such masking on current main

Message: box-000509-fbc1300f
