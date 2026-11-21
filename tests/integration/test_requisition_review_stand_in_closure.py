# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test requisition review stand in closure
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 512e4a26
# hash: 61e9f8e3fa4f2ea8b8e14d7dd641c5311f3d56c8145d6a464918fb5e55990959
from pathlib import Path

from clutch.specs import load_spec, render


def test_stand_in_closure_and_existing_task_bullets():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/requisition_review.md").read_text()
    spec = load_spec(text)
    rendered = render(spec, {name: f"fixture {name}" for name in spec.inputs})
    task = rendered.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    bullets = [line for line in task.splitlines() if line.startswith("- ")]
    # A missing bullet, or a replacement instead of an addition, must fail.
    assert len(bullets) == 19
    # Each prior first sentence rules out replacing or rewording that existing rule.
    prior_sentences = [
        (
            "- When a listed sibling's Scope in changes an interface, fixture shape, attribute, or behavior that a "
            "criterion, `## Verification` line, or test this ticket adds depends on, raise a `snag` naming the sibling "
            "stem, the changed interface, and the criterion or test it would break, whichever ticket merges first."
        ),
        "- Check every stated repo-state precondition against HEAD.",
        ("- Judge any boundary contract for meaning, reuse of the canonical owner, and whether each `none` or `create` reason is true; snag unsupported claims."),
        "- A scope fence misses a file forced by a criterion.",
        (
            "- A path in `## Scope fence` or a `## Verification` command does not exist at the review commit and Scope in "
            "does not say the ticket creates it: report a `snag` finding naming the path; a path the ticket creates is not "
            "a hit, and a path that is only an output of a command is not a hit."
        ),
        (
            "- When Scope in adds, removes, renames, or moves a member of a set (CLI subcommand, file or directory path, "
            "spec name, or an entry of an in-code registry, table, mapping, or closed vocabulary such as a menu, verb, "
            "kind, or adapter table), grep `tests/` and `docs/` for files that list that set or hardcode the old path, and "
            "fence every hit that asserts against the changed set or hardcodes the moved path."
        ),
        (
            "- When Scope in adds, removes, or renames a field of a model, dataclass, or config type, or changes text a "
            "render function emits, grep `tests/` for whole-value comparisons of that type's serialized form or that render "
            "(`model_dump()`, `asdict`, `dict(...) ==`, golden bytes, base64 or digest constants), and fence every hit or "
            "raise a snag; only whole-value equality is a hit: a test that only builds or loads the model, or asserts "
            "fields the change leaves alone, is not a hit."
        ),
        ("- Snag a draft criterion, `## Verification` line, or Scope in that adds a standing test pinning current text of the roadmap (rows or exact gate-block commands) or a plan document."),
        ("- A criterion or a Definition-of-rejected clause contradicts merged behavior, or two criteria cannot both be satisfied."),
        ("- Two statements anywhere in the ticket cannot both hold, for example a declared signature and a call to it, or a named fixture and the result a criterion expects from it."),
        "- A stated or cited invariant has no named test obligation.",
        (
            "- When the ticket's own evidence or Goal says the failure is intermittent, flaky, load-dependent, or did not "
            "reproduce, and it names neither a deterministic trigger (a command, fixture, or seed that reproduces it) nor "
            "an exit for when the failure does not reproduce (for example, file an instrumentation ticket and stop), raise "
            "a `snag` finding with code `no-reproduction-exit` naming the missing trigger or exit."
        ),
        (
            "- If the ticket has `## Regression`, the reproducer must print only one JSON object with exactly the "
            "`regression_result` key: `pass` with exit 0 at head, and `defect` with nonzero exit on the base overlaid with "
            "the carried files, using only code that exists at base."
        ),
        "- Account for every listed dependent exactly once in `dependents`, using its test path.",
        (
            "- When Scope in adds statements or branches to a file listed with a floor above 0 under `[coverage.files]` in "
            "the repo's `test-gate.toml`, the fenced `tests/unit` file's named tests must run the new lines in each floored "
            "file."
        ),
        (
            "- When a criterion or `## Verification` line names a `tests/unit/` file whose test the ticket adds or newly "
            "requires to read a named repo file (a spec, doc, `package.json`, or `importlib.metadata` data), raise a `snag` "
            "finding: place that test under `tests/integration/` and fence that file."
        ),
        (
            "- When a criterion, a test Scope in adds, or a `## Verification` line makes a `tests/unit/` test write disk "
            "outside `tmp_path`, start a process, or open a network connection, raise a `snag` finding: place that test "
            "under `tests/integration/` and fence that file."
        ),
    ]
    normalized_task = " ".join(task.split())
    for sentence in prior_sentences:
        assert sentence in normalized_task
    # Checking one bullet prevents unrelated rules from satisfying its required clauses.
    bullet = next(line for line in bullets if "hand-built stand-ins" in line)
    for phrase in (
        "newly read an attribute or field of a type",
        "grep `tests/`",
        "`SimpleNamespace(...)`, ad-hoc fake classes, partial dicts",
        "both reaches the changed read and lacks the attribute",
        "finding names the reaching call",
        "never reach the changed read or already carry the attribute are not hits",
        "Fence the hit and add a Scope-in line adding only that attribute, or raise a snag",
        "never use a `getattr` fallback in production code",
    ):
        assert phrase in bullet
