---
id: declined-box-001085-a61c1d81
kind: declined
link: box-001085-a61c1d81
reopen_after_days: 30
---
The engine filed a depends-stage report saying serve-flaky-tests-deterministic was blocked because its dependency restore-io-tests-14 had been rejected or abandoned. It asked for the dependency to be re-wired, the ticket re-scoped, or the ticket rejected. serve-flaky-tests-deterministic is now in the merged set, so nothing is still blocked.

The dependent ticket serve-flaky-tests-deterministic has already merged, so the dependency block holds nothing back and there is no current failure to repair. Registry records 000321, 000327, 001083 and 001084 settled earlier depends-stage reports the same way when the dependent had merged. Reopen if a still-open ticket is found that depends on restore-io-tests-14 and is blocked by its rejection.

- serve-flaky-tests-deterministic appears in the merged stems list
- restore-io-tests-14 is in neither the open tickets nor the merged stems
- Precedent: declined-box-000321-cda44a53, declined-box-000327-a42c7f27, declined-box-001083-fa5b1ae2, declined-box-001084-830340c7

Message: box-001085-a61c1d81
