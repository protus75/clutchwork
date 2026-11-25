import { App, applyDocumentTheme, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";
import { z } from "zod";
import { renderGraph } from "../../vscode-clutchwork/media/graph.js";
import { createTicketsView } from "../../vscode-clutchwork/media/view.js";
import { createDetailView } from "../../vscode-clutchwork/media/detail.js";
import { createBoxView } from "../../vscode-clutchwork/media/box.js";

export async function createDashboardApp(options = {}) {
  const app = options.app || new App({ name: "ClutchWork", version: "1.0.0" });
  const root = options.root || document.getElementById("dashboard");
  let snap, focus, repo = "", fileOpen = true, active = 0, inFlight = 0, connected = false;
  const waiting = [];
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  const button = (label, action) => { const n = el("button", label); n.addEventListener("click", () => Promise.resolve(action()).catch(showError)); return n; };
  const notice = el("div", "", "notice");
  function showError(error) { notice.textContent = error?.message || String(error); }
  async function callTool(name, args = {}) {
    if (inFlight >= 4) await new Promise(resolve => waiting.push(resolve));
    else inFlight++;
    try {
      const result = await app.callServerTool({ name, arguments: { ...args, ...(repo ? { repo } : {}) } });
      if (result.isError) throw new Error(result.structuredContent?.message || result.content?.[0]?.text || "Tool failed");
      return result.structuredContent;
    } finally { if (waiting.length) waiting.shift()(); else inFlight--; }
  }
  async function openFile(path) {
    if (!fileOpen || !path) return;
    const absolute = path.startsWith("/") ? path : `${snap.root.replace(/\/$/, "")}/${path}`;
    const uri = `file://${absolute.split("/").map(encodeURIComponent).join("/")}`;
    try {
      const result = await app.request({ method: "com.google.antigravity/toggle-aux-pane", params: { tabType: "fileView", uri } }, z.object({}).passthrough());
      if (result?.isError) { fileOpen = false; notice.textContent = "File opening is unavailable in this host."; }
    } catch (error) {
      if (error.code !== -32601) throw error;
      fileOpen = false; notice.textContent = "File opening is unavailable in this host.";
    }
  }
  async function sendPrompt(kind, stems = [], background = false) {
    if (!app.getHostCapabilities()?.message) return;
    const result = await callTool("clutch_prompt", { kind, stems });
    await app.sendMessage({ role: "user", content: [{ type: "text", text: result.text }], ...(background ? { _meta: { "com.google.antigravity/message": { target: "new" } } } : {}) });
  }
  function select(kind, id) {
    focus = id ? { kind, id } : undefined;
    if (snap) { detailView.render(snap, focus); renderActions(); }
    const row = kind === "ticket" ? snap?.rows.find(r => r.stem === id) : snap?.box.find(r => r.id === id);
    if (row?.path && app.getHostCapabilities()?.updateModelContext) {
      const absolute = row.path.startsWith("/") ? row.path : `${snap.root}/${row.path}`;
      app.updateModelContext({ content: [{ type: "resource_link", uri: `file://${absolute.split("/").map(encodeURIComponent).join("/")}`, name: id }] }).catch(showError);
    }
  }
  const host = { callTool, openFile, sendPrompt, openHelp: topic => { const link = snap?.help[topic]?.link; if (link?.path) return openFile(link.path); if (link?.url) window.open(link.url, "_blank"); } };
  const tabs = el("nav", undefined, "tabs"), panels = [], names = ["Tickets", "Details", "Recent Steps", "Suggestion Box", "Stats", "Help & Lifecycle"];
  const repoInput = el("input"); repoInput.placeholder = "Repository path";
  const repoButton = button("Load repository", () => { repo = repoInput.value.trim(); return refresh(); });
  const toolbar = el("div", undefined, "toolbar"), promptBar = el("div", undefined, "toolbar");
  const ticketsHeader = el("div"), ticketsList = el("div"), actions = el("div", undefined, "toolbar"), detail = el("div"), artifacts = el("div", undefined, "toolbar");
  const boxHeader = el("div"), boxList = el("div"), boxActions = el("div", undefined, "toolbar"), steps = el("div"), stats = el("pre"), help = el("div");
  const windowSelect = el("select"); for (const w of ["24h", "7d", "30d", "20t"]) { const o = el("option", w); o.value = w; windowSelect.append(o); } windowSelect.value = "7d";
  windowSelect.addEventListener("change", () => loadStats().catch(showError));
  for (const [i, name] of names.entries()) { const panel = el("section"); const tab = button(name, () => showTab(i)); tabs.append(tab); panels.push(panel); }
  panels[0].append(toolbar, ticketsHeader, ticketsList, actions); panels[1].append(detail, artifacts); panels[2].append(steps); panels[3].append(boxHeader, boxList, boxActions); panels[4].append(windowSelect, stats); panels[5].append(help);
  root.replaceChildren(repoInput, repoButton, notice, promptBar, tabs, ...panels);
  function showTab(i) { active = i; panels.forEach((panel, index) => { panel.hidden = index !== active; }); }
  showTab(0);
  const ticketsView = createTicketsView({ header: ticketsHeader, list: ticketsList, renderGraph, host: { ...host, onFocus: id => select("ticket", id) } });
  const detailView = createDetailView({ detail, host });
  const boxView = createBoxView({ header: boxHeader, list: boxList, host: { ...host, onFocus: id => select("box", id) } });
  function renderActions() {
    if (!snap) return;
    const row = focus?.kind === "ticket" ? snap.rows.find(r => r.stem === focus.id) : undefined;
    actions.replaceChildren(); artifacts.replaceChildren(); boxActions.replaceChildren();
    if (row) {
      const mutate = async (name, args) => { await callTool(name, args); await refresh(); };
      for (const [label, key, name] of [["Confirm", "clutchConfirm", "clutch_app_ticket_confirm"], ["Reject", "clutchReject", "clutch_app_ticket_reject"]]) if (row.menu[key] === "on") actions.append(button(label, () => mutate(name, { stem: row.stem })));
      if (row.menu.clutchPriority === "on") { const choice = el("select"); for (const item of row.priorityChoices) { const o = el("option", item.label); o.value = item.label; choice.append(o); } choice.value = row.priority; actions.append(choice, button("Set priority", () => mutate("clutch_ticket_order", { stem: row.stem, priority: choice.value }))); }
      if (row.menu.clutchRunsBefore === "on") { const choice = el("select"); choice.multiple = true; for (const item of row.runsBeforeChoices) { const o = el("option", item.label); o.value = item.label; o.selected = item.picked; choice.append(o); } actions.append(choice, button("Set runs before", () => mutate("clutch_ticket_order", { stem: row.stem, runs_before: Array.from(choice.selectedOptions, o => o.value) }))); }
      for (const name of ["ticket.md", "run.md", "checks.json", "review.md", "diagnosis.json", "rework.md"]) artifacts.append(button(name, () => openFile(`tickets/${row.stem}/${name}`)));
    }
    artifacts.append(button("config.yaml", () => openFile(snap.configPath)));
    const ids = boxView.getSelected(); const selected = ids.map(id => snap.box.find(r => r.id === id)).filter(Boolean);
    for (const [label, key, tool] of [["Triage", "clutchTriage", "clutch_box_triage"], ["Dismiss", "clutchDismiss", "clutch_box_dismiss"]]) if (selected.length && selected.every(r => r.menu[key] === "on")) boxActions.append(button(label, async () => { await callTool(tool, { ids }); await refresh(); }));
  }
  async function loadStats() { const result = await callTool("clutch_app_stats", { window: windowSelect.value }); stats.textContent = JSON.stringify(result, null, 2); }
  async function refresh() {
    try {
      const [data, ping] = await Promise.all([callTool("clutch_app_snapshot"), callTool("clutch_engine_control", { action: "ping" })]); snap = data;
      const running = ping.engine && snap.engine;
      toolbar.replaceChildren(el("span", `Engine: ${running ? "running" : "stopped"}`));
      if (!running) for (const mode of ["drain", "serve"]) toolbar.append(button(`Start ${mode}`, async () => { await callTool("clutch_engine_start", { mode }); await refresh(); }));
      if (running) toolbar.append(button("Stop", async () => { await callTool("clutch_engine_control", { action: "stop" }); await refresh(); }));
      ticketsView.render(snap); boxView.render(snap); detailView.render(snap, focus); renderActions();
      steps.replaceChildren(...snap.steps.map(step => { const b = button(`${step.timeDisplay} ${step.text}`, () => openFile(step.path)); b.disabled = !step.path; b.title = step.tooltip; return b; }));
      help.replaceChildren(...Object.entries(snap.help).map(([key, entry]) => { const section = el("div", `${key}: ${entry.text} `); const link = entry.link.path ? button(entry.link.label, () => openFile(entry.link.path)) : el("a", entry.link.label); if (entry.link.url) { link.href = entry.link.url; link.target = "_blank"; } section.append(link); return section; }));
      const svg = document.querySelector("body > div[hidden] svg"); if (svg) help.append(svg.cloneNode(true));
      await loadStats();
    } catch (error) { showError(error); }
  }
  function renderPrompts() {
    promptBar.replaceChildren(); if (!app.getHostCapabilities()?.message) return;
    const background = el("input"); background.type = "checkbox"; const label = el("label", "New conversation "); label.append(background); promptBar.append(label);
    for (const [name, kind] of [["Supervise Drain Loop", "drain-loop"], ["Run Roadmap (Drain)", "plan-ticket-drain"], ["Run Roadmap (Serve)", "plan-ticket-serve"], ["Diagnose Stem", "diagnose"], ["Review Drafts", "drafts"]]) promptBar.append(button(name, () => { const stem = focus?.kind === "ticket" ? focus.id : ""; if (kind === "diagnose" && !stem) { showError("Select a ticket to diagnose."); return; } return sendPrompt(kind, stem && kind === "diagnose" ? [stem] : [], background.checked); }));
  }
  const applyContext = context => { if (context?.theme) applyDocumentTheme(context.theme); if (context?.styles?.variables) applyHostStyleVariables(context.styles.variables); };
  app.ontoolinput = params => { if (params?.arguments?.repo) { repo = params.arguments.repo; repoInput.value = repo; if (connected) refresh(); } options.ontoolinput?.(params); };
  app.ontoolresult = options.ontoolresult ?? (() => {});
  app.onhostcontextchanged = context => { applyContext(context); renderPrompts(); options.onhostcontextchanged?.(context); };
  await app.connect(); connected = true; applyContext(app.getHostContext()); renderPrompts(); await refresh();
  window.addEventListener("focus", () => refresh());
  return app;
}
if (typeof document !== "undefined" && !globalThis.__CLUTCH_DASHBOARD_NO_AUTOBOOT__) createDashboardApp();
