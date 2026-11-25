import { App, applyDocumentTheme, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";
import { z } from "zod";
import { renderGraph } from "../../vscode-clutchwork/media/graph.js";
import { createTicketsView } from "../../vscode-clutchwork/media/view.js";
import { createDetailView } from "../../vscode-clutchwork/media/detail.js";
import { createBoxView } from "../../vscode-clutchwork/media/box.js";

export async function createDashboardApp(options = {}) {
  const app = options.app || new App({ name: "ClutchWork", version: "1.0.0" });
  const root = options.root || document.getElementById("dashboard");
  let snap, focus, repo = "", fileOpen = true, inFlight = 0, connected = false;
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
  const svgIcon = (path, color = "muted") => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 16 16"); svg.setAttribute("width", "14"); svg.setAttribute("height", "14");
    svg.classList.add("step-icon"); svg.style.color = `var(--clutch-icon-${color})`;
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "path");
    shape.setAttribute("d", path); shape.setAttribute("fill", "currentColor"); svg.append(shape); return svg;
  };
  const iconPaths = { play: "M4 2v12l9-6z", stop: "M3 3h10v10H3z", refresh: "M8 1a7 7 0 1 0 7 7h-2a5 5 0 1 1-1-3L9 5v2h6V1l-2 2A7 7 0 0 0 8 1z", gear: "M7 1h2l1 2 2-1 2 2-1 2 2 1v2l-2 1 1 2-2 2-2-1-1 2H7l-1-2-2 1-2-2 1-2-2-1V7l2-1-1-2 2-2 2 1zm1 4a3 3 0 1 0 0 6 3 3 0 0 0 0-6z", folder: "M1 3h5l2 2h7v8H1z", warning: "M8 1 0 15h16zm-1 5h2v4H7zm0 5h2v2H7z" };
  const iconButton = (label, icon, action) => { const n = button(label, action); n.prepend(svgIcon(iconPaths[icon])); return n; };
  const repoInput = el("input"); repoInput.placeholder = "Repository path";
  const repoButton = button("Load repository", () => { repo = repoInput.value.trim(); return refresh(); });
  const repoSwitcher = el("div", undefined, "repo-switcher"); repoSwitcher.append(repoInput, repoButton);
  let repoOpen = false, boxInitialized = false;
  const toolbar = el("header", undefined, "top-bar"), promptBar = el("details", undefined, "agent-actions");
  const ticketsHeader = el("div"), ticketsList = el("div"), actions = el("div", undefined, "toolbar"), detail = el("div");
  const boxHeader = el("div"), boxList = el("div"), boxActions = el("div", undefined, "toolbar"), steps = el("div"), stats = el("div", undefined, "stats-list"), help = el("div");
  const windowSelect = el("select"); for (const w of ["24h", "7d", "30d", "20t"]) { const o = el("option", w); o.value = w; windowSelect.append(o); } windowSelect.value = "7d";
  windowSelect.addEventListener("change", () => loadStats().catch(showError));
  const sections = {};
  for (const [key, name, opened] of [["tickets", "Tickets", true], ["details", "Details", true], ["steps", "Recent Steps", true], ["box", "Suggestion Box", false], ["stats", "Stats", false], ["help", "Help & Lifecycle", false]]) {
    const section = el("details", undefined, "sidebar-section"), summary = el("summary"); section.dataset.section = key; section.open = opened;
    summary.append(el("span", name, "section-title"), el("span", "", "section-count")); section.append(summary); sections[key] = section;
  }
  sections.tickets.append(ticketsHeader, ticketsList); sections.details.append(detail, actions); sections.steps.append(steps);
  sections.box.append(boxHeader, boxList, boxActions); sections.stats.append(windowSelect, stats); sections.help.append(help);
  root.replaceChildren(toolbar, repoSwitcher, notice, promptBar, ...Object.values(sections));
  const menu = el("div", undefined, "context-menu"); menu.hidden = true; root.append(menu);
  function closeMenu() { menu.hidden = true; menu.replaceChildren(); }
  document.addEventListener("click", e => { if (!menu.contains(e.target)) closeMenu(); });
  window.addEventListener("keydown", e => { if (e.key === "Escape") closeMenu(); });
  function showMenu(e) { e.preventDefault(); menu.replaceChildren(); menu.hidden = false; menu.style.left = `${e.clientX}px`; menu.style.top = `${e.clientY}px`; }
  function menuItem(parent, label, action) { parent.append(button(label, async () => { closeMenu(); await action(); })); }
  const mutate = async (name, args) => { await callTool(name, args); await refresh(); };
  const ticketEntries = new WeakMap(), boxEntries = new WeakMap();
  function ticketContext(node, row) {
    const first = !ticketEntries.has(node); ticketEntries.set(node, { row }); if (!first) return;
    node.addEventListener("contextmenu", e => {
      const { row } = ticketEntries.get(node); ticketsView.setPinned(row.stem); showMenu(e);
      for (const [label, key, tool] of [["Confirm", "clutchConfirm", "clutch_app_ticket_confirm"], ["Reject", "clutchReject", "clutch_app_ticket_reject"]]) if (row.menu[key] === "on") menuItem(menu, label, () => mutate(tool, { stem: row.stem }));
      if (row.menu.clutchPriority === "on") { const sub = el("div", undefined, "submenu"); sub.append(el("span", "Priority")); for (const choice of row.priorityChoices) menuItem(sub, choice.label, () => mutate("clutch_ticket_order", { stem: row.stem, priority: choice.label })); menu.append(sub); }
      if (row.menu.clutchRunsBefore === "on") { const sub = el("div", undefined, "submenu"); sub.append(el("span", "Runs before...")); const selected = new Set(row.runsBeforeChoices.filter(c => c.picked).map(c => c.label)); for (const choice of row.runsBeforeChoices) { const label = el("label"); const input = el("input"); input.type = "checkbox"; input.checked = choice.picked; input.addEventListener("change", () => { if (input.checked) selected.add(choice.label); else selected.delete(choice.label); }); label.append(input, el("span", choice.label)); sub.append(label); } menuItem(sub, "Set runs before", () => mutate("clutch_ticket_order", { stem: row.stem, runs_before: [...selected] })); menu.append(sub); }
      menuItem(menu, "Open ticket.md", () => openFile(row.path)); for (const name of ["run.md", "review.md", "diagnosis.json"]) menuItem(menu, `Open ${name}`, () => openFile(`tickets/${row.stem}/${name}`));
      if (app.getHostCapabilities()?.message && row.menu.clutchAskDiagnose === "on") menuItem(menu, "Diagnose Stem", () => sendPrompt("diagnose", [row.stem]));
    });
  }
  function boxContext(node, row, ids) {
    const first = !boxEntries.has(node); boxEntries.set(node, { row, ids }); if (!first) return;
    node.addEventListener("contextmenu", e => {
      const { row, ids } = boxEntries.get(node); showMenu(e);
      const selected = ids.map(id => snap.box.find(r => r.id === id));
      for (const [label, key, tool] of [["Triage", "clutchTriage", "clutch_box_triage"], ["Dismiss", "clutchDismiss", "clutch_box_dismiss"]]) if (selected.length && selected.every(r => r && r.menu[key] === "on")) menuItem(menu, label, () => mutate(tool, { ids }));
      if (row.path) menuItem(menu, "Open message file", () => openFile(row.path)); if (row.link) menuItem(menu, "Open ticket/record", () => openFile(row.link));
    });
  }
  const ticketsView = createTicketsView({ header: ticketsHeader, list: ticketsList, renderGraph, host: { ...host, onFocus: id => select("ticket", id), onRowContext: ticketContext } });
  const detailView = createDetailView({ detail, host });
  const boxView = createBoxView({ header: boxHeader, list: boxList, host: { ...host, onFocus: id => select("box", id), onRowContext: boxContext } });
  function renderActions() {
    if (!snap) return;
    const row = focus?.kind === "ticket" ? snap.rows.find(r => r.stem === focus.id) : undefined;
    actions.replaceChildren(); boxActions.replaceChildren();
    if (row) {
      const mutate = async (name, args) => { await callTool(name, args); await refresh(); };
      for (const [label, key, name] of [["Confirm", "clutchConfirm", "clutch_app_ticket_confirm"], ["Reject", "clutchReject", "clutch_app_ticket_reject"]]) if (row.menu[key] === "on") actions.append(button(label, () => mutate(name, { stem: row.stem })));
      if (row.menu.clutchPriority === "on") { const choice = el("select"); for (const item of row.priorityChoices) { const o = el("option", item.label); o.value = item.label; choice.append(o); } choice.value = row.priority; actions.append(choice, button("Set priority", () => mutate("clutch_ticket_order", { stem: row.stem, priority: choice.value }))); }
      if (row.menu.clutchRunsBefore === "on") { const choice = el("select"); choice.multiple = true; for (const item of row.runsBeforeChoices) { const o = el("option", item.label); o.value = item.label; o.selected = item.picked; choice.append(o); } actions.append(choice, button("Set runs before", () => mutate("clutch_ticket_order", { stem: row.stem, runs_before: Array.from(choice.selectedOptions, o => o.value) }))); }
    }
    const ids = boxView.getSelected(); const selected = ids.map(id => snap.box.find(r => r.id === id)).filter(Boolean);
    for (const [label, key, tool] of [["Triage", "clutchTriage", "clutch_box_triage"], ["Dismiss", "clutchDismiss", "clutch_box_dismiss"]]) if (selected.length && selected.every(r => r.menu[key] === "on")) boxActions.append(button(label, async () => { await callTool(tool, { ids }); await refresh(); }));
  }
  function statsRow(row) {
    const node = el(row.children.length ? "details" : "div", undefined, "stats-row");
    const line = row.children.length ? el("summary") : node; line.title = row.tooltip || "";
    line.append(el("span", row.label, "stats-label"), el("span", row.description, "stats-desc"));
    if (row.children.length) { node.append(line); for (const child of row.children) node.append(statsRow(child)); }
    return node;
  }
  async function loadStats() { const result = await callTool("clutch_app_stats", { window: windowSelect.value, tree: true }); stats.replaceChildren(...result.tree.map(statsRow)); }
  const shapes = { meta: "M3 1h7l3 3v11H3z", review_visual: "M1 4h3l1-2h6l1 2h3v9H1zm7 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z", resolve: "M2 3h9L9 1l1-1 4 4-4 4-1-1 2-2H2zm12 10H5l2 2-1 1-4-4 4-4 1 1-2 2h9z", acceptance: "M8 1 15 4v4c0 4-3 6-7 7C4 14 1 12 1 8V4zm-1 9 5-5-1-1-4 4-2-2-1 1z", preflight: "M8 1c4 2 5 6 4 9l-4 4-4-4C3 7 4 3 8 1z", retro_check: "M2 2h12v12H2zm2 4v6h8V6z", requisition_review: "M8 1 1 4v2h14V4zM3 7h2v5H3zm4 0h2v5H7zm4 0h2v5h-2zM1 13h14v2H1z", stage: "M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm-1 10h2v2H7zm1-8c3 0 4 3 1 5v2H7V7c2-1 2-2 1-2S7 6 7 6H5c0-2 1-3 3-3z", author: "M2 11 11 2l3 3-9 9-3 1z", implement: "M5 3 0 8l5 5 1-2-3-3 3-3zm6 0-1 2 3 3-3 3 1 2 5-5z", review: "M0 8c4-7 12-7 16 0-4 7-12 7-16 0zm8-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6z", diagnose: "M6 1a5 5 0 1 0 3 9l4 4 2-2-4-4A5 5 0 0 0 6 1z", rework: "M2 1l4 4-1 2 7 7 2-2-7-7 1-2-3-2 1 3-2 1z", retro: "M8 1a7 7 0 1 1-6 10h2a5 5 0 1 0 0-6l2 2H1V2l2 2a7 7 0 0 1 5-3zm-1 3h2v4l3 2-1 1-4-2z", check: "M1 2h3v3H1zm5 0h9v2H6zM1 7h3v3H1zm5 0h9v2H6zM1 12h3v3H1zm5 0h9v2H6z", merge: "M3 1a2 2 0 1 0 1 4v5a2 2 0 1 0 2 0V9c0-2 5-2 5-5a2 2 0 1 0-2 0c0 2-2 2-3 3V5a2 2 0 0 0-3-4z", triage: "M1 2h14v12H1zm2 2v5h3l1 2h2l1-2h3V4z", engine_start: iconPaths.play, engine_stop: iconPaths.stop, engine_lost: iconPaths.warning };
  const stepIcons = {}; for (const [name, path] of Object.entries(shapes)) { if (name.startsWith("engine_")) stepIcons[name] = [path, name === "engine_lost" ? "warning" : "muted"]; else for (const [suffix, color] of [["start", "muted"], ["ok", "passed"], ["failed", "failed"]]) stepIcons[`${name}_${suffix}`] = [path, color]; }
  function stepRow(step) {
    const known = stepIcons[step.kind], row = button("", () => openFile(step.path)); row.className = "step-row"; row.title = step.tooltip; row.disabled = !step.path;
    row.append(svgIcon(...(known || [iconPaths.warning, "warning"]))); if (step.stem) row.append(el("span", step.stem, "step-stem"));
    row.append(el("span", known ? step.text : `cannot draw the clutch snapshot: unknown step kind ${step.kind}`, "step-text"), el("span", step.timeDisplay, "step-time")); return row;
  }
  async function refresh() {
    try {
      const [data, ping] = await Promise.all([callTool("clutch_app_snapshot"), callTool("clutch_engine_control", { action: "ping" })]); snap = data;
      const running = ping.engine && snap.engine;
      toolbar.replaceChildren(el("span", `Engine: ${running ? "running" : "stopped"}`));
      if (!running) for (const mode of ["drain", "serve"]) toolbar.append(iconButton(`Start ${mode}`, "play", async () => { await callTool("clutch_engine_start", { mode }); await refresh(); }));
      if (running) toolbar.append(iconButton("Stop", "stop", async () => { await callTool("clutch_engine_control", { action: "stop" }); await refresh(); }));
      toolbar.append(iconButton("Refresh", "refresh", refresh), iconButton("Open config.yaml", "gear", () => openFile(snap?.configPath)), iconButton(snap.root || "Repository", "folder", () => { repoOpen = !repoOpen; repoSwitcher.hidden = !!snap?.root && !repoOpen; }));
      repoSwitcher.hidden = !!snap.root && !repoOpen;
      if (!boxInitialized) { sections.box.open = snap.boxCounts.pending > 0; boxInitialized = true; }
      ticketsView.render(snap); boxView.render(snap); detailView.render(snap, focus); renderActions();
      steps.replaceChildren(...snap.steps.map(stepRow));
      help.replaceChildren(...Object.entries(snap.help).map(([key, entry]) => { const section = el("div", `${key}: ${entry.text} `); const link = entry.link.path ? button(entry.link.label, () => openFile(entry.link.path)) : el("a", entry.link.label); if (entry.link.url) { link.href = entry.link.url; link.target = "_blank"; } section.append(link); return section; }));
      const svg = document.querySelector("body > div[hidden] svg"); if (svg) help.append(svg.cloneNode(true));
      await loadStats();
    } catch (error) { showError(error); }
  }
  function renderPrompts() {
    promptBar.replaceChildren(); promptBar.hidden = !app.getHostCapabilities()?.message; if (promptBar.hidden) return;
    promptBar.append(el("summary", "Agent Actions"));
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
