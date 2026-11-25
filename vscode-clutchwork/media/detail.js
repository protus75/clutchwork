'use strict';
/* global acquireVsCodeApi */

function createDetailView({ detail, host }) {
for (const method of ['callTool', 'openFile', 'sendPrompt', 'openHelp']) if (typeof host?.[method] !== 'function') throw new TypeError(`host.${method} must be a function`);

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

function openLink(path, label = 'Open ticket.md') {
	const a = el('a', 'link', label);
	a.href = '#';
	a.addEventListener('click', e => {
		e.preventDefault();
		host.openFile(path);
	});
	return a;
}

function section(title, body) {
	const wrap = el('div', 'detail-section');
	wrap.append(el('div', 'detail-heading', title));
	wrap.append(body);
	return wrap;
}

function helpText(snap, topic, short = false) {
	const entry = snap.help[topic];
	const wrap = el('div', 'help-text', short ? entry.what + ' ' : entry.text + ' ');
	const link = el('a', 'link', 'Learn more');
	link.href = '#';
	link.addEventListener('click', e => { e.preventDefault(); host.openHelp(topic); });
	wrap.append(link);
	return wrap;
}

function content(row, snap) {
	const box = el('div');
	const head = el('div', 'detail-title');
	const badge = el('span', `badge ${row.section}`, row.section);
	badge.title = snap.help[row.help.section].text;
	head.append(badge, el('span', 'detail-stem', ` ${row.stem}`));
	box.append(head);
	for (const [index, { heading, text }] of row.detail.entries()) {
		box.append(heading === null ? el('div', 'detail-meta', text) : section(heading, el('div', 'detail-text', text)));
		if (index === 0) box.append(helpText(snap, row.help.status));
	}
	if (row.next.length) {
		const next = el('div');
		for (const topic of row.next) next.append(helpText(snap, topic, true));
		box.append(section('Next', next));
	}
	const links = el('div', 'detail-links');
	links.append(openLink(row.path));
	box.append(links);
	return box;
}

function boxContent(row, snap) {
	const result = el('div');
	const head = el('div', 'detail-title');
	head.append(el('span', `badge ${row.state}`, row.messageClass), el('span', 'detail-stem', ` ${row.id}`));
	result.append(head, helpText(snap, row.help.class), helpText(snap, row.help.outcome));
	for (const [label, text] of row.fields) result.append(section(label, el('div', 'detail-text', text)));
	const links = el('div', 'detail-links');
	if (row.path) links.append(openLink(row.path, 'Open message file'));
	if (row.link) links.append(openLink(row.link, 'Open ticket/record'));
	result.append(links);
	return result;
}

function render(snap, focus) {
	try {
		const box = focus?.kind === 'box' ? snap.box.find(r => r.id === focus.id) : undefined;
		const stem = focus?.kind === 'ticket' ? focus.id : snap.runningStem;
		const row = snap.rows.find(r => r.stem === stem);
		detail.replaceChildren(box ? boxContent(box, snap) : row ? content(row, snap) : el('div', 'detail-meta', 'Nothing running. Hover a ticket or message to see it here; click to pin.'));
	} catch (error) {
		showError(`cannot draw the clutch snapshot: ${error.message}`);
	}
 }
function showError(message) {
 const link = el('a', 'link', 'Open setup help'); link.href = '#';
 link.addEventListener('click', e => { e.preventDefault(); host.openHelp(); });
 detail.replaceChildren(`${message} `, link);
}
return { render, showError };
}
if (typeof module === 'object' && module.exports) module.exports = { createDetailView };
if (typeof acquireVsCodeApi === 'function') {
 const vscode = acquireVsCodeApi();
 const host = { callTool: () => Promise.reject(new Error('unsupported')), sendPrompt: () => Promise.reject(new Error('unsupported')), openFile: path => vscode.postMessage({ type: 'open', path }), openHelp: topic => vscode.postMessage(topic === undefined ? { type: 'readme' } : { type: 'help', topic }) };
 const view = createDetailView({ detail: document.getElementById('detail'), host });
 window.addEventListener('message', e => view.render(e.data.snap, e.data.focus));
 vscode.postMessage({ type: 'ready' });
}
