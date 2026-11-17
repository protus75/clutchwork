Audit clutch ticket `${stem}` against the merged code and the other open tickets. Read ${ticket}, the ticket authoring guide that `clutch docs` names, every file the ticket names, and every confirmed, unmerged ticket under tickets/ that fences a file this ticket fences or shares an interface with it; `clutch view status` lists the queue.

The ticket may already pass `clutch ticket lint` and `clutch ticket review`. Find what they missed: anything that would make its run park, fail Check, waste a run, or deliver the wrong thing. Report only problems you verified, each with its evidence (a path::Name, heading, or command output). Do not praise.

Check:
- Premise: every fact about current code is true at HEAD.
- Fence closure: for every name, value, verb, path, state, or set member added or altered, grep tests, docs, source, and extension or client code, including registries and closed sets, CLI choices, help entries, snapshot vocabularies, parity tests, spec version pins, and coverage floors that force a unit-test path. Name every forced file missing from ## Scope fence.
- Criteria: each is runnable or readable and names the wrong result it rules out; all can hold together, none contradicts merged behavior or a test outside the fence, and every ## Verification command exists and exits 0 on a correct implementation.
- Fidelity: deliver everything the request asks or drop it with a true reason, and nothing beyond it.
- Budget and kind: expected and stuck are realistic; a bug has real evidence and a valid ## Regression.
- Collisions: check each other ticket in either merge order for edits to the same section, fake or fixture configs missing a field the other adds, values or spec versions the other changes, and criteria the other's merge breaks.

Mark each problem blocking (the run will park, fail, or deliver the wrong thing) or minor.

Write the report to me in plain English, as to someone who has not read the engine code: say what happened and why, explain any clutch term you must use, and name files, stems, and commands only where I need them. End with a "Recommendation" section that walks me through what to do as numbered steps. For each step, say in one sentence what it does and why, give the exact `clutch` command or edit in its own copy/paste block, and say what I should see when it worked. Where a step is a judgment call, lay out the options and say which you would pick. Do not run the steps yourself; wait for me to say go.
