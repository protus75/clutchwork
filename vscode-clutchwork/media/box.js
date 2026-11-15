'use strict';
/* global acquireVsCodeApi */
const vscode = acquireVsCodeApi();
const list = document.getElementById('list');
const header = document.getElementById('header');
const COLOR = { pending: 'var(--clutch-queued)', resolved: 'var(--clutch-merged)' };
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
		node.dataset.vscodeContext = JSON.stringify({ ...row.menu, clutchIds: selected.has(row.id) ? ids : [row.id], clutchPath: row.path, clutchLink: row.link, preventDefaultContextMenuItems: true });
	}
}
function focus() { update(); vscode.postMessage({ type: 'focus', id: pinned ?? hovered }); }
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
		summary.style.color = COLOR[r.state];
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
		row.addEventListener('dblclick', () => { if (r.path) vscode.postMessage({ type: 'open', path: r.path }); });
		return row;
	});
	list.replaceChildren(...rows);
	update();
	if (oldFocus !== (pinned ?? hovered)) vscode.postMessage({ type: 'focus', id: pinned ?? hovered });
}
list.addEventListener('mouseleave', () => { hovered = undefined; focus(); });
window.addEventListener('keydown', e => {
	if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
		e.preventDefault(); selected = new Set(snap.box.map(r => r.id)); focus();
	} else if (e.key === 'Escape') { selected.clear(); pinned = undefined; focus(); }
});
window.addEventListener('message', e => {
	if (e.data.type === 'data') render(e.data.snap);
	else if (e.data.type === 'error') {
		const link = el('a', 'link', 'Open setup help');
		link.href = '#';
		link.addEventListener('click', event => { event.preventDefault(); vscode.postMessage({ type: 'readme' }); });
		header.replaceChildren(`snapshot failed: ${e.data.message} `, link);
	}
});
vscode.postMessage({ type: 'ready' });
