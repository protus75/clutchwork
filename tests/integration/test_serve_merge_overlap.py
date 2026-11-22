# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify merge and rebase complete beside a held implementation.
# relates: [clutch/config.py, clutch/mergequeue.py, clutch/stages.py, tests/integration/serve_rig.py, tests/integration/test_cli.py]
# owner: engine
# verified: d32c32ad
# hash: 987472fa30436837c3fd02a569af46cab8f735de7366e4691ceb5f805370bcc4
import asyncio
from dataclasses import replace

import pytest
import yaml

from clutch.config import load_config
from clutch.llm import FakeLLM
from clutch.mergequeue import TREE_MISMATCH
from tests.integration.serve_rig import admission_graph, admission_ticket, finish, start_admission, terminals, until
from tests.integration.test_cli import root

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.asyncio
async def test_merge_while_other_implementation_holds_slot(root, monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()
    call = FakeLLM.call

    async def held(model, req):
        if req.surface == "implement":
            if req.ticket == "two":
                entered.set()
                await release.wait()
            else:
                await entered.wait()
        return await call(model, req)

    monkeypatch.setattr(FakeLLM, "call", held)
    rig = await admission_graph(root, monkeypatch, {"one": {"docs/one": "one\n"}, "two": {"docs/two": "two\n"}})
    path = root / "config.yaml"
    config = yaml.safe_load(path.read_text())
    config["scheduler"] = {"parallel": {"enabled": True, "max_runs": 2}, "max_unmerged": 4}
    path.write_text(yaml.safe_dump(config))
    rig.checkout = replace(rig.checkout, config=load_config(path, cwd=root))
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    admission_ticket(root, "two", paths=("docs/two",), priority="P1")
    rebased = []
    rebase = rig.checkout.git.rebase_stop_at_conflict

    async def tracked_rebase(worktree, onto):
        result = await rebase(worktree, onto)
        if worktree.name == "two":
            rebased.append(await rig.checkout.git._run(worktree, "show", "HEAD:docs/one"))
        return result

    monkeypatch.setattr(rig.checkout.git, "rebase_stop_at_conflict", tracked_rebase)
    run = await start_admission(rig, monkeypatch)
    pending = []
    original_pending = rig.owner.core.admission.exclusive_pending

    def observed_pending():
        value = original_pending()
        pending.append(value)
        return value

    monkeypatch.setattr(rig.owner.core.admission, "exclusive_pending", observed_pending)
    try:
        await until(rig, lambda: terminals(rig, "one"))
        # Serial merge cannot produce this terminal while two remains blocked.
        assert not release.is_set()
        terminal = terminals(rig, "one")[-1]
        assert terminal.body["to"] == "merged"
        assert await rig.checkout.git.rev_parse(root, "main") == terminal.body["commit"]
        assert await rig.checkout.git._run(root, "show", "main:docs/one") == "one\n"
        assert pending and not any(pending)
        release.set()
        await until(rig, lambda: terminals(rig, "two"))
        # Skipping the rebase loses one's content; a mismatched checked tree holds two.
        assert rebased == ["one\n"]
        assert terminals(rig, "two")[-1].body["to"] == "merged"
        assert not any(e.body.get("kind") == TREE_MISMATCH for e in rig.journal.read())
    finally:
        release.set()
        await finish(rig, run)
