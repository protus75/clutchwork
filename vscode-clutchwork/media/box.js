'use strict';
/* global acquireVsCodeApi */
const DEFAULT_COLORS = { pending: 'var(--clutch-queued)', resolved: 'var(--clutch-merged)' };
function createBoxView({ header, list, host, colors = DEFAULT_COLORS, keyboardTarget = typeof window !== 'undefined' ? window : null }) {
for (const method of ['callTool', 'openFile', 'sendPrompt', 'openHelp']) if (typeof host?.[method] !== 'function') throw new TypeError(`host.${method} must be a function`);
let snap, selected = new Set(), anchor, pinned, hovered;
function el(tag, cls, text) {
	const node = document.createElement(tag);
	if (cls) node.className = cls;
	if (text !== undefined) node.textContent = text;
	return node;
}
function update() {
	const ids = [];
	for (const row of snap.box) if (selected.has(row.id)) ids.push(row.id);
	const c = snap.boxCounts;
	const counts = Object.entries(snap.boxHeaderHelp).map(([key, topic], i) => {
		const node = el('span', '', `${i ? ' · ' : ''}${c[key]} ${key}`);
		node.title = snap.help[topic].text;
		return node;
	});
	header.replaceChildren(...counts, ids.length > 1 ? ` · ${ids.length} selected` : '');
	for (const node of list.children) {
		const row = snap.box.find(r => r.id === node.dataset.id);
		node.classList.toggle('pinned', selected.has(row.id));
		host.onRowContext?.(node, row, selected.has(row.id) ? ids : [row.id]);
	}
}
function focus() { update(); host.onFocus?.(pinned ?? hovered); }
function render(data) {
	snap = data;
	const oldFocus = pinned ?? hovered;
	for (const id of selected) if (!snap.box.some(row => row.id === id)) selected.delete(id);
	if (pinned && !selected.has(pinned)) pinned = undefined;
	if (hovered && !snap.box.some(row => row.id === hovered)) hovered = undefined;
	if (anchor && !snap.box.some(row => row.id === anchor)) anchor = undefined;
	const rows = snap.box.map(r => {
		const row = el('div', 'row');
		row.dataset.id = r.id;
		row.title = [snap.help[r.help.class].text, snap.help[r.help.outcome].text].join('\n');
		const summary = el('span', 'stem', r.summary);
		summary.style.color = colors[r.state];
		row.append(summary, el('span', 'status', r.status));
		row.addEventListener('mouseenter', () => { hovered = r.id; focus(); });
		row.addEventListener('click', e => {
			if (e.shiftKey && anchor !== undefined) {
				const a = snap.box.findIndex(x => x.id === anchor), b = snap.box.findIndex(x => x.id === r.id);
				selected = new Set();
				for (let i = Math.min(a, b); i <= Math.max(a, b); i++) selected.add(snap.box[i].id);
			} else if (e.ctrlKey || e.metaKey) {
				if (selected.has(r.id)) selected.delete(r.id); else selected.add(r.id);
			} else if (selected.size === 1 && selected.has(r.id)) selected.clear();
			else selected = new Set([r.id]);
			anchor = r.id;
			pinned = selected.has(r.id) ? r.id : undefined;
			focus();
		});
		row.addEventListener('contextmenu', () => {
			if (!selected.has(r.id)) { selected = new Set([r.id]); pinned = anchor = r.id; focus(); }
		});
		row.addEventListener('dblclick', () => { if (r.path) host.openFile(r.path); });
		return row;
	});
	list.replaceChildren(...rows);
	update();
	if (oldFocus !== (pinned ?? hovered)) host.onFocus?.(pinned ?? hovered);
}
list.addEventListener('mouseleave', () => { hovered = undefined; focus(); });
keyboardTarget?.addEventListener('keydown', e => {
	if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
		e.preventDefault(); selected = new Set(snap.box.map(r => r.id)); focus();
	} else if (e.key === 'Escape') { selected.clear(); pinned = undefined; focus(); }
});
function showError(message) {
	const link = el('a', 'link', 'Open setup help');
	link.href = '#';
	link.addEventListener('click', e => { e.preventDefault(); host.openHelp(); });
	header.replaceChildren(`${message} `, link);
}
return { render(data) { try { render(data); } catch (error) { showError(`cannot draw the clutch snapshot: ${error.message}`); } }, showError, getFocus: () => pinned ?? hovered, getSelected: () => [...selected] };
}
if (typeof module === 'object' && module.exports) module.exports = { createBoxView, DEFAULT_COLORS };
if (typeof acquireVsCodeApi === 'function') {
 const vscode = acquireVsCodeApi();
 const host = { callTool: () => Promise.reject(new Error('unsupported')), sendPrompt: () => Promise.reject(new Error('unsupported')), openFile: path => vscode.postMessage({ type: 'open', path }), openHelp: () => vscode.postMessage({ type: 'readme' }), onFocus: id => vscode.postMessage({ type: 'focus', id }), onRowContext: (node, row, ids) => { node.dataset.vscodeContext = JSON.stringify({ ...row.menu, clutchIds: ids, clutchPath: row.path, clutchLink: row.link, preventDefaultContextMenuItems: true }); } };
 const view = createBoxView({ header: document.getElementById('header'), list: document.getElementById('list'), host });
 window.addEventListener('message', e => { if (e.data.type === 'data') view.render(e.data.snap); else if (e.data.type === 'error') view.showError(`snapshot failed: ${e.data.message}`); });
 vscode.postMessage({ type: 'ready' });
}
