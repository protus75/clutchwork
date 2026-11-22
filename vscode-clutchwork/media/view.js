'use strict';
/* global acquireVsCodeApi, renderGraph */

const vscode = acquireVsCodeApi();
const list = document.getElementById('list');
const header = document.getElementById('header');

// Status colors for dots and for each section's own lanes.
const COLOR = {
	merged: 'var(--clutch-merged)',
	running: 'var(--clutch-queued)',
	queued: 'var(--clutch-queued)',
	blocked: 'var(--clutch-blocked)',
};

// The Details view shows the pinned row, else the hovered row, else the running ticket (focus undefined).
// Click pins a row so the mouse can leave the list without losing it.
let pinned;
let hovered;

function focus() {
	for (const node of list.children) {
		node.classList.toggle('pinned', node.dataset.stem === pinned);
	}
	vscode.postMessage({ type: 'focus', stem: pinned ?? hovered });
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
		row.dataset.vscodeContext = JSON.stringify({ ...r.menu, clutchStem: r.stem, clutchSessionId: r.sessionId, preventDefaultContextMenuItems: true });
		row.append(renderGraph(r.graph, COLOR[r.section], COLOR));
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
		row.addEventListener('dblclick', () => vscode.postMessage({ type: 'open', path: r.path }));
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
	link.addEventListener('click', e => { e.preventDefault(); vscode.postMessage({ type: 'readme' }); });
	header.replaceChildren(`${message} `, link);
}
window.addEventListener('message', e => {
	const msg = e.data;
	if (msg.type === 'data') {
		try { render(msg.snap); } catch (error) { showError(`cannot draw the clutch snapshot: ${error.message}`); }
	} else if (msg.type === 'error') {
		showError(`snapshot failed: ${msg.message}`);
	}
});
vscode.postMessage({ type: 'ready' });
