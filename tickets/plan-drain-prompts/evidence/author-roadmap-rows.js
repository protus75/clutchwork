// Evidence copy for ticket plan-drain-prompts (2026-11-16). The session's authoring workflow: `COMMON`, `authorPrompt`, and `auditPrompt` are the author and adversarial-audit prompts. Machine paths, another host, credential names, and shell-specific launch commands are replaced with placeholders or generic wording; nothing else changed.

export const meta = {
  name: 'author-roadmap-rows',
  description: 'Author roadmap rows as clutch tickets (clutch new, lint, clutch review, adversarial audit, repair, cross-ticket ordering)',
  phases: [
    { title: 'Author', detail: 'one agent per roadmap row: clutch new, lint, clutch review until approve' },
    { title: 'Audit', detail: 'independent adversarial audit of each authored ticket against HEAD' },
    { title: 'Repair', detail: 'verify and fix blocking audit findings, re-lint, re-review' },
    { title: 'Consistency', detail: 'cross-ticket ordering, fence overlap, spec-bump collisions' },
  ],
}

const SCRATCH = '<scratch>'

const COMMON = `You are working in the clutch repo at <checkout> (branch main; ${args.where}). Run every clutch command as \`uv run clutch <verb>\` from that directory.
The roadmap is docs/roadmap.md (master ticket table = section 8). Its audit sections 2-4 were written at commit 80b76d5d on 2026-11-13 and are STALE: many commits merged since (see \`git log --oneline 80b76d5d..HEAD\`). Never trust a roadmap line number or claim without reading the current code; in tickets cite code as \`path.py::Name\`, not line numbers.
Other agents are authoring other roadmap tickets concurrently in this same checkout. Write ONLY under tickets/<your own stems>/ (plus scratch files under ${SCRATCH}/<stem>/). Never edit code, docs (including docs/roadmap.md), specs, config, CLAUDE.md, AGENTS.md, or another ticket. Never run git add/commit/reset/checkout/stash/clean, and never run clutch drain, run, serve, confirm, reject, triage, dismiss, stop, kill. \`uv run clutch review <stem>\` commits your ticket through intake by itself; that is the only commit you cause.
Second problems you notice (defects, stale docs, missing gates) are NOT folded into a ticket: file each with \`uv run clutch suggest "<one-paragraph summary naming files and evidence>"\`. A cause fix (the change that stops a class of defect recurring) is ALWAYS filed with clutch suggest, never authored as a ticket.
If \`clutch review\` fails with a provider error, drought, or rate limit (not a review verdict), wait about two minutes (e.g. \`timeout 120 tail -f /dev/null\`) and retry, up to 3 times.`



const AUTHOR_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['approved', 'skipped', 'review_stuck', 'failed'] },
    tickets: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          stem: { type: 'string' }, kind: { type: 'string' }, priority: { type: 'string' },
          review_rounds: { type: 'number' }, final_review: { type: 'string' },
          fence: { type: 'array', items: { type: 'string' } },
          depends_on: { type: 'array', items: { type: 'string' } },
          runs_before: { type: 'array', items: { type: 'string' } },
          expected_minutes: { type: 'number' }, stuck_minutes: { type: 'number' },
        },
        required: ['stem', 'fence'],
      },
    },
    skip_reason: { type: 'string' },
    dropped_from_row: { type: 'array', items: { type: 'string' } },
    suggestions_filed: { type: 'array', items: { type: 'string' } },
    last_findings: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['status', 'tickets'],
}

const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['clean', 'issues'] },
    issues: { type: 'array', items: { type: 'object', properties: { stem: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'minor'] }, category: { type: 'string' }, issue: { type: 'string' }, evidence: { type: 'string' }, fix: { type: 'string' } }, required: ['severity', 'issue', 'evidence'] } },
  },
  required: ['verdict', 'issues'],
}

const REPAIR_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['approved', 'review_stuck', 'failed'] },
    fixed: { type: 'array', items: { type: 'string' } },
    rejected_issues: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, why: { type: 'string' } }, required: ['issue', 'why'] } },
    review_rounds: { type: 'number' },
    last_findings: { type: 'string' },
    fence: { type: 'array', items: { type: 'string' } },
  },
  required: ['status'],
}

const CONSISTENCY_SCHEMA = {
  type: 'object',
  properties: {
    ordering_changes: { type: 'array', items: { type: 'object', properties: { stem: { type: 'string' }, change: { type: 'string' }, command: { type: 'string' } }, required: ['stem', 'change'] } },
    content_conflicts: { type: 'array', items: { type: 'object', properties: { stems: { type: 'string' }, issue: { type: 'string' }, suggested_fix: { type: 'string' } }, required: ['stems', 'issue'] } },
    lint_exit: { type: 'number' },
    notes: { type: 'string' },
  },
  required: ['ordering_changes', 'content_conflicts'],
}

function authorPrompt(row) {
  return `${COMMON}

TASK: author the clutch ticket for roadmap row #${row.n} \`${row.stem}\` (kind ${row.kind}, priority ${row.priority}).

Row content (docs/roadmap.md section 8): ${row.content}
Owning design to read: ${row.design}
Ordering: Depends on: ${row.depends || 'none'}. Runs before: ${row.runsBefore || 'none'}. Only name stems that exist under tickets/ (lint refuses unknown stems); a named stem that does not exist yet is simply omitted.
Orchestrator scouting hints (verify them, they may be wrong): ${row.hints}

Procedure:
1. Read the owning design and every code and doc location the row and design cite, at HEAD. Grep \`git log --oneline\` and tickets/ for merged tickets that already did part of this row. Decide:
   - fully satisfied or superseded at HEAD: create nothing; return status "skipped" with concrete evidence (commit hashes, path::symbol facts) in skip_reason.
   - partially satisfied: author only what remains; list what you dropped and why in dropped_from_row.
2. Run \`uv run clutch new ${row.stem} --kind ${row.kind}\`${row.kind === 'bug' ? ' (a bug: FIRST save real observed evidence — output of commands you just ran, a journal excerpt, a reproduction — to a file under ' + SCRATCH + '/' + row.stem + '/ and pass --evidence <file>; never a placeholder)' : ''}. It prints the authoring guide path: read clutch/docs/host-authoring.md IN FULL, then the generated tickets/${row.stem}/ticket.md skeleton. Read one recent approved ticket for shape, e.g. tickets/status-retires-settled-rows/ticket.md (and tickets/provider-capture-overwrite/ticket.md for a bug).
3. Fill every section per the guide, plus:
   - The smallest change that satisfies the row (CLAUDE.md "Simplest thing"); nothing the row does not ask for.
   - Contention rules (docs/parallel-tickets-plan.md section 7): new tests in NEW test files, new fixtures in new modules; fence only what the change forces.
   - Verification uses \`./dev.py test [pytest args]\`, never raw pytest.
   - Fence closure: grep tests/, docs/, clutch/ for every name, value, verb, path, state, or set member the ticket adds or changes — including in-code registries and closed sets (argparse choices, help entries in clutch/help.py, snapshot vocabularies, menu/parity tables, verb tables in clutch/docs/host-running.md) — and fence each hit that asserts against it or must change; fence documents describing the changed behavior and say in Scope in which part to update; when a prompt spec under clutch/specs/ is bumped, state the bump as "the next minor above main" and fence its version-pin test.
   - priority ${row.priority}; ordering as given above; Depends on only for merged code this ticket needs.
   - Realistic Time budget; stuck must not exceed 180 minutes (config drain.max_ticket_minutes). If the row cannot fit one ticket, split into at most 3: keep \`${row.stem}\` as one (other rows depend on that name), name the others \`${row.stem}-<part>\`, order them with Runs before (or Depends on when one needs the other's merged code).
4. \`uv run clutch lint <stem>\` until it exits 0.
5. The guide's pre-review checks: no criterion contradicts merged behavior or a test outside the fence; all criteria can hold together; every invariant the ticket states has a criterion whose test fails when it is dropped.
6. \`uv run clutch review <stem>\`; repair EVERY finding in ticket.md, re-lint, re-review, until it prints approve. After 6 rounds without approve, stop and return status "review_stuck" with the last findings verbatim in last_findings.
Return the structured result (one entry in tickets per ticket you authored, with its final fence).`
}

function auditPrompt(row, res) {
  const stems = res.tickets.map(t => t.stem).join(', ')
  return `${COMMON}

TASK: adversarially audit the clutch ticket(s) ${stems}, authored from roadmap row #${row.n} \`${row.stem}\`. They already passed clutch lint and the clutch review model. Find what those missed: defects that will make the run fail (premise park, impossible fence, Check failure), waste a run, or deliver the wrong thing. Do not praise; report only concrete problems you verified.

Row content: ${row.content}
Owning design: ${row.design}
Author's notes: ${res.notes || ''} Dropped from row: ${(res.dropped_from_row || []).join('; ')}

Read each tickets/<stem>/ticket.md, clutch/docs/host-authoring.md in full, and the current code every ticket cites. Check:
a. Premise: every fact the ticket states about current code is true at HEAD (open the file, find the symbol).
b. Fence closure: for every name, value, verb, path, state, or set member the change adds or alters, grep tests/, docs/, clutch/, vscode-clutchwork/ (in-code registries, closed sets, argparse choices, clutch/help.py entries, snapshot vocabularies, parity tests such as tests/**/test_*parity*.py, spec version pins, test-gate.toml coverage floors that force a tests/unit path) and list every forced file missing from the fence.
c. Criteria: each is runnable or readable, names the wrong result it rules out, all can hold together, none contradicts merged behavior or a test outside the fence; the Verification commands exist and would exit 0 on a correct implementation.
d. Row fidelity: everything the row asks is delivered or explicitly dropped with a true reason; nothing beyond the row.
e. Budget and kind: expected/stuck realistic; bug tickets have real evidence and a valid ## Regression protocol per the guide.
Edit nothing. Severity "blocking" = the run will park, fail, or deliver the wrong thing; "minor" = everything else. verdict "clean" when no blocking issue.`
}

function repairPrompt(row, res, issues) {
  const stems = res.tickets.map(t => t.stem).join(', ')
  return `${COMMON}

TASK: repair the clutch ticket(s) ${stems} (roadmap row #${row.n} \`${row.stem}\`) against these findings:
${JSON.stringify(issues, null, 1)}

Read clutch/docs/host-authoring.md in full and each ticket.md first. For each finding: verify it yourself against the current code; if real, fix tickets/<stem>/ticket.md; if not real, record why in rejected_issues. Keep the row's goal and scope; do not widen it. Then \`uv run clutch lint <stem>\` until exit 0 and \`uv run clutch review <stem>\` until it prints approve (at most 4 rounds; else status review_stuck with last_findings verbatim). Return the final fence.`
}

const ROWS = args.rows

const rowsP = pipeline(
  ROWS,
  row => agent(authorPrompt(row), { label: `author:${row.stem}`, phase: 'Author', schema: AUTHOR_SCHEMA }),
  (res, row) => {
    if (!res) return { row, res: null, audit: null }
    if (res.status !== 'approved' || !res.tickets || !res.tickets.length) return { row, res, audit: null }
    return agent(auditPrompt(row, res), { label: `audit:${row.stem}`, phase: 'Audit', schema: AUDIT_SCHEMA, effort: 'high' }).then(a => ({ row, res, audit: a }))
  },
  (x) => {
    if (!x.res || !x.res.tickets || !x.res.tickets.length) return { ...x, repair: null }
    let issues = (x.audit && x.audit.issues || []).filter(i => i.severity === 'blocking')
    if (x.res.status === 'review_stuck') issues = [{ severity: 'blocking', issue: 'clutch review did not approve after 6 rounds', evidence: x.res.last_findings || '' }, ...issues]
    if (!issues.length) return { ...x, repair: null }
    return agent(repairPrompt(x.row, x.res, issues), { label: `repair:${x.row.stem}`, phase: 'Repair', schema: REPAIR_SCHEMA }).then(r => ({ ...x, repair: r }))
  },
)

const rows = await rowsP

const authored = rows.filter(Boolean).filter(x => x.res && x.res.tickets && x.res.tickets.length)
  .map(x => ({ row: x.row.stem, status: x.repair ? x.repair.status : x.res.status, tickets: x.res.tickets.map(t => ({ stem: t.stem, priority: t.priority, fence: (x.repair && x.repair.fence && x.res.tickets.length === 1) ? x.repair.fence : t.fence, depends_on: t.depends_on, runs_before: t.runs_before })) }))
log(`authored ${authored.length} of ${ROWS.length} rows; running cross-ticket consistency`)

phase('Consistency')
const consistency = authored.length < 2 ? null : await agent(`${COMMON}

TASK: cross-ticket consistency over the roadmap tickets just authored (also read every confirmed, unmerged ticket under tickets/ listed by \`uv run clutch status\` intake, since they share the queue):
${JSON.stringify(authored, null, 1)}

Read each tickets/<stem>/ticket.md. Find: (1) two tickets that bump the same prompt spec, or edit the same section of the same file (CLAUDE.md, AGENTS.md, clutch/hostfiles.py CORE_TEMPLATE, docs/how-clutch-works.md, clutch/docs/*.md, clutch/__main__.py verb tables), with no Runs before between them — pick the order that keeps each ticket's criteria true when the other merges first, preferring docs/roadmap.md row order and its Runs before column (contention-authoring-rules runs before every feature ticket); (2) a ticket whose criteria or line-level premises would be invalidated by another queued ticket merging first; (3) Depends on used for ordering only; (4) duplicate work across tickets. Fix ORDERING only, with \`uv run clutch order\` (read \`uv run clutch order --help\` first), then \`uv run clutch lint <every stem>\` must exit 0. Content conflicts (duplicate work, invalidated criteria): report with a suggested fix; do not edit content.`, { label: 'consistency', phase: 'Consistency', schema: CONSISTENCY_SCHEMA, effort: 'high' })

return { rows: rows.filter(Boolean).map(x => ({ stem: x.row.stem, author: x.res, audit: x.audit, repair: x.repair })), consistency }
