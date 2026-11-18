# What this tests and why
A design document can be self-contained -- every decision determined, BuildItReview clean -- and still not be buildable by an AI pipeline, because determining a decision is not the same as being able to carry it out and verify it unattended. This exercise tests the document under automated execution. Fresh agents with no project context role-play the ticket author of an AI build pipeline for <PHASE_SCOPE> and must express the work as tickets in the pipeline's format, from the document at <PLAN_PATH> and the authoring contract at <GUIDE_PATH> alone. Every step they cannot hand to an agent, every criterion no machine can decide, and every place their decompositions diverge is a measured automation gap. Convergence is the signal: a gate or missing oracle independently found by two or more isolated agents is real, not one agent's caution. Run BuildItReview first; this review assumes the decisions are settled and measures whether they can be executed. Designed to re-run as the document evolves; an empty gate ledger is a valid outcome, not a failed run.

# Run shape
* 3 DRY-RUN AUTHOR agents, identical prompt (below), fully isolated: each gets the document at <PLAN_PATH> and the authoring contract at <GUIDE_PATH> and nothing else -- no repo browsing, no conversation history, no prior review results, no knowledge that other agents exist.
* A MECHANICAL stage, no model: every ticket from every agent is run through the pipeline's real ticket lint; per-ticket results and counts are passed to synthesis as facts.
* 1 SYNTHESIS agent (prompt below) compares the three ticket sets, their ledgers, and the lint facts after all finish.
* High reasoning effort for all four. No file writes by any agent; output returns as structured data.

# Dry-run author agent prompt (verbatim)
You are the ticket author for an AI build pipeline that will implement the system specified by the design document at <PLAN_PATH>. The pipeline's rules for tickets are the authoring contract at <GUIDE_PATH>. Those two files are your ONLY input. Read both in full. You cannot ask questions; there is no other documentation, no repository, and no team. Every ticket you write will be implemented by an AI agent, checked only by the commands and criteria the ticket names, reviewed by another AI agent, and merged with no human in the loop except where you explicitly place one.

Produce four things for <PHASE_SCOPE> as defined in the document's implementation-phases section:

1. TICKET SET: the tickets you would author, in the contract's format, each complete: Goal, Scope in / Scope out, Scope fence, Acceptance criteria, Verification commands, Depends on. Cover every deliverable the document names for <PHASE_SCOPE>. Size each ticket so its diff stays within the contract's budget; if a deliverable cannot be split to fit, say so in the gate ledger.

1. ORACLE LEDGER: for every acceptance criterion, one entry:
  * criterion: quoted from your ticket.
  * oracle: one of test (a test the ticket adds or names decides it), command (a named command's exit status or output decides it), path-exists (a file or section someone can read decides it), lint (a static check decides it), none (only a person can decide it).
  * how: one sentence on what the machine runs or reads.

1. HUMAN-GATE LEDGER: every step you could not hand to an agent, one entry each:
  * step: what has to happen, in one sentence.
  * section: the document section that requires it.
  * class: one of credential (accounts, keys, payment), external (third-party approval, hardware, a service that does not exist yet), judgment (taste, feel, legal, business priority), data (inputs the document assumes but nothing produces), irreversible (an action with no rollback).
  * placement: where in the ticket order a human must act, and which tickets wait on it.

1. INVENTED-DECISIONS LEDGER: as in BuildItReview -- every choice the document did not determine for you, with decision, section, chose, and class (missing / ambiguous / contradictory / deliberate-freedom).

Rules: author AS SPECIFIED -- do not evaluate, improve, or redesign the system. Follow the authoring contract exactly; a ticket that breaks it is a failed ticket, not a stylistic choice. Never write a judgment word into a criterion to avoid an oracle of none -- an honest none is the measurement; a disguised one corrupts it. Filling a gap from your own experience is still an invented decision -- ledger it. Do not pad the gate ledger: a step an agent can do with what the document provides is not a gate, and an empty gate ledger is a valid answer. Be exhaustive on the ledgers before polishing ticket prose; if effort runs short, cut ticket prose, never ledger entries.

# Synthesis agent prompt (verbatim)
You receive three ticket sets with oracle, human-gate, and invented-decisions ledgers, produced independently by three isolated authors from the same design document at <PLAN_PATH> and authoring contract at <GUIDE_PATH>, plus mechanical lint results for every ticket. Read the document, then:

1. Map every ticket in every set to the document deliverable it serves. A deliverable no set covers is a finding; a deliverable all three cover with structurally different splits is DECOMPOSITION DIVERGENCE -- the document does not determine the shape of the work.
1. Cluster ledger entries describing the same underlying gate, oracle gap, or decision across sets (they will word it differently).
1. Rank: (a) any core deliverable whose criteria have oracle none in every set; (b) then human gates found by 3/3, then 2/3; (c) then oracle-none criteria by convergence; (d) then decomposition divergence; (e) then lint failures recurring on the same deliverable across sets -- recurrence points at the document, a single failure at the author. Single-agent deliberate-freedom entries drop; other single-agent entries go in a low-confidence tail.
1. Verify each cluster against the document before reporting it: if the document does supply the oracle, the data, or the decision and the authors missed it, report it separately as FINDABILITY.
1. For each surviving cluster: the deliverable, the owning section, what each author did (divergence matters), and a one-sentence document edit -- add the oracle, name the gate and its owner and placement, or fix the decomposition.
1. Compute the AUTOMATION RATIO: the share of <PHASE_SCOPE> deliverables covered, in at least two of the three sets, by lint-clean tickets whose criteria all have an oracle other than none.

Output, verdict first:
* Automation: AUTOMATABLE (no verified human gate and ratio 1.0) / AUTOMATABLE-WITH-GATES (every verified gate is named and can be placed ahead of the tickets that need it) / NOT AUTOMATABLE AS WRITTEN (a core deliverable has no oracle in any set, or a verified gate sits where no ordering can isolate it) -- with the ratio and one paragraph of justification.
* The ranked cluster list with per-cluster convergence counts, the findability list, and the low-confidence tail.

# Disposition of results
Gaps, gates, and findability problems become document edits, reviewed before applying, same as every round; the exercise re-runs after material edits, rescoped to the phases now earliest-unbuilt. Ticket sets are measurement instruments and are discarded, unless the owner explicitly promotes the consensus set as a starting point for real authoring -- which still goes through the pipeline's own authoring and review. Once the phase has actually run, its real parks, confirms, and attempt counts are the check on this review's predictions. Nothing from this exercise commits code.
