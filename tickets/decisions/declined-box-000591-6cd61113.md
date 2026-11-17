---
id: declined-box-000591-6cd61113
kind: declined
link: box-000591-6cd61113
reopen_after_days: 14
---
On 2026-11-16 the Diagnose reply for roadmap-accept attempt 0 had two lessons longer than 300 characters. The engine cut both mid-sentence, as `trimmed_lessons: [1, 2]` in tickets/roadmap-accept/diagnosis.json records. Lesson 2 lost its conclusion, and lesson 3 lost its closing instruction. Lesson 3 also tells Implement to rerun the full suite once and commit if it passes. clutch/specs/implement.md says one isolated rerun is the only evidence and never to rerun the full suite and count that as proof. The message asks for two changes: the Diagnose spec puts each lesson's instruction before its evidence, and validation refuses a lesson that contradicts the target stage spec.

Both defects are real. diagnosis.json shows lessons 2 and 3 cut off mid-sentence, and lesson 3 contradicts implement.md lines 46-49. But nothing shows either one has caused a wrong result yet. roadmap-accept is still open, and no later attempt is shown to have failed by following a cut-off or contradicting lesson. Implement still gets its own spec, which states the correct intermittent-failure rule, so that rule outranks the lesson. The open ticket implement-spec-intermittent-by-reproduction also restates it. The proposed fix cannot be built as one ticket with a measurable result. Putting the instruction first is wording about how a model writes lessons, and no test can check that the model follows it. Refusing a lesson that contradicts a stage spec needs a judgment about meaning that no closed check can make. Reopen condition: an Implement attempt fails or bounces because it followed a cut-off or spec-contradicting Diagnose lesson. Or a concrete mechanical repair is proposed, such as cutting at a sentence boundary and re-prompting Diagnose to split the lesson, with a test that checks the result.

- tickets/roadmap-accept/diagnosis.json: trimmed_lessons [1, 2]; lesson 2 ends 'clutch/__main__.py are' and lesson 3 ends 'Do not'
- clutch/specs/diagnose.md:25 and :70 already cap each lesson at 300 characters and say to split a longer one into separate lessons
- clutch/specs/implement.md:46-49 allow only one isolated rerun as evidence of an intermittent failure and say never to rerun the full suite until it passes
- Open ticket implement-spec-intermittent-by-reproduction covers how Implement handles a single intermittent failure
- Merged tickets diagnose-spec-lesson-length and diagnose-lesson-trim-in-engine already set the current length cap and engine trim

Message: box-000591-6cd61113
