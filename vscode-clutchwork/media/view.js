'use strict';
/* global acquireVsCodeApi, renderGraph */


// Status colors for dots and for each section's own lanes.
const DEFAULT_COLORS = {
	merged: 'var(--clutch-merged)',
	running: 'var(--clutch-queued)',
	queued: 'var(--clutch-queued)',
	blocked: 'var(--clutch-blocked)',
};

function createTicketsView(options) {
const { header, list, host, colors = DEFAULT_COLORS } = options;
for (const method of ['callTool', 'openFile', 'sendPrompt', 'openHelp']) if (typeof host?.[method] !== 'function') throw new TypeError(`host.${method} must be a function`);
const graphRenderer = options.renderGraph || (typeof renderGraph === 'function' ? renderGraph : require('./graph.js').renderGraph);
// The Details view shows the pinned row, else the hovered row, else the running ticket (focus undefined).
// Click pins a row so the mouse can leave the list without losing it.
let pinned;
let hovered;

function focus() {
	for (const node of list.children) {
		node.classList.toggle('pinned', node.dataset.stem === pinned);
	}
	host.onFocus?.(pinned ?? hovered);
}

list.addEventListener('mouseleave', () => {
	hovered = undefined;
	focus();
});

function el(tag, cls, text) {
	const node = document.createElement(tag);
	if (cls) {
		node.className = cls;
	}
	if (text !== undefined) {
		node.textContent = text;
	}
	return node;
}

function render(snap) {
	const counts = snap.counts;
	const lock = el('span', '', snap.lock ? '🔒' : '🔓');
	lock.title = [snap.lock || 'unlocked', snap.help[snap.headerHelp.engine].text].join('\n');
	const commitLock = el('span', '', snap.commitLock ? '🔒' : '🔓');
	commitLock.title = [snap.commitLock || 'unlocked', snap.help[snap.headerHelp.commit].text].join('\n');
	const countNodes = Object.entries(snap.headerHelp).filter(([key]) => key !== 'engine' && key !== 'commit').map(([key, topic]) => {
		const node = el('span', '', ` · ${counts[key] ?? 0} ${key}`);
		node.title = snap.help[topic].text;
		return node;
	});
	header.replaceChildren('engine ', lock, ' · commit ', commitLock, ...countNodes);
	const rows = snap.rows.map(r => {
		const row = el('div', `row ${r.section}`);
		row.dataset.stem = r.stem;
		row.title = r.tooltip;
		// Context keys for the right-click menu's `when` clauses in package.json; the command receives this object.
		host.onRowContext?.(row, r);
		row.append(graphRenderer(r.graph, colors[r.section], colors));
		if (r.priorityTag) {
			const priority = el('span', 'priority', r.priorityTag);
			priority.title = snap.help[r.priorityHelp].text;
			row.append(priority);
		}
		row.append(el('span', 'stem', r.stem));
		row.append(el('span', 'status', r.status));
		row.addEventListener('mouseenter', () => {
			hovered = r.stem;
			focus();
		});
		row.addEventListener('click', () => {
			pinned = pinned === r.stem ? undefined : r.stem;
			focus();
		});
		row.addEventListener('dblclick', () => host.openFile(r.path));
		return row;
	});
	const decisions = snap.verdictDecisions.map(d => {
		const row = el('div', 'status', `${d.request_id}: ${d.verb} ${d.stem}: ${d.decision} -- ${d.reason}`);
		row.title = snap.help[snap.verdictDecisionsHelp].text;
		return row;
	});
	list.replaceChildren(...decisions, ...rows);
	if (pinned && !snap.rows.some(r => r.stem === pinned)) {
		pinned = undefined;
	}
	focus();
}

function showError(message) {
	const link = el('a', 'link', 'Open setup help');
	link.href = '#';
	link.addEventListener('click', e => { e.preventDefault(); host.openHelp(); });
	header.replaceChildren(`${message} `, link);
}
return { render(snap) { try { render(snap); } catch (error) { showError(`cannot draw the clutch snapshot: ${error.message}`); } }, showError, getFocus: () => pinned ?? hovered, setPinned(stem) { pinned = stem; focus(); } };
}
if (typeof module === 'object' && module.exports) module.exports = { createTicketsView, DEFAULT_COLORS };
if (typeof acquireVsCodeApi === 'function') {
 const vscode = acquireVsCodeApi();
 const host = { callTool: () => Promise.reject(new Error('unsupported')), sendPrompt: () => Promise.reject(new Error('unsupported')), openFile: path => vscode.postMessage({ type: 'open', path }), openHelp: () => vscode.postMessage({ type: 'readme' }), onFocus: stem => vscode.postMessage({ type: 'focus', stem }), onRowContext: (row, r) => { row.dataset.vscodeContext = JSON.stringify({ ...r.menu, clutchStem: r.stem, clutchSessionId: r.sessionId, preventDefaultContextMenuItems: true }); } };
 const view = createTicketsView({ header: document.getElementById('header'), list: document.getElementById('list'), host });
 window.addEventListener('message', e => { const msg = e.data; if (msg.type === 'data') view.render(msg.snap); else if (msg.type === 'error') view.showError(`snapshot failed: ${msg.message}`); });
 vscode.postMessage({ type: 'ready' });
}
