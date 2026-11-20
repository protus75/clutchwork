'use strict';

const path = require('path');
const vm = require('vm');
const fs = require('fs');
const [view, scenario] = process.argv.slice(2);
const handlers = {};
const messages = [];
class Node {
	constructor() { this.children = []; this.dataset = {}; this.style = {}; this.classList = { toggle() {} }; this.text = ''; this.events = {}; }
	set textContent(value) { this.text = value; this.children = []; }
	get textContent() { return this.text + this.children.map(child => typeof child === 'string' ? child : child.textContent).join(''); }
	append(...children) { this.children.push(...children); }
	replaceChildren(...children) { this.text = ''; this.children = children; }
	addEventListener(type, handler) { this.events[type] = handler; }
}
const elements = { header: new Node(), list: new Node(), detail: new Node() };
const context = {
	document: { getElementById: id => elements[id], createElement: () => new Node() },
	window: { addEventListener: (type, handler) => { handlers[type] = handler; } },
	acquireVsCodeApi: () => ({ postMessage: message => messages.push(message) }),
	renderGraph: () => new Node(),
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '..', 'vscode-clutchwork', 'media', `${view}.js`), 'utf8'), context);
const snapshots = {
	view: { counts: {}, help: { engine: { text: 'engine' }, commit: { text: 'commit' } }, headerHelp: { engine: 'engine', commit: 'commit' }, rows: [], verdictDecisions: [] },
	box: { box: [], boxCounts: {}, boxHeaderHelp: {}, help: {} },
	detail: { rows: [] },
};
const snap = scenario === 'valid' ? snapshots[view] : {};
const data = scenario === 'error' ? { type: 'error', message: 'boom' } : view === 'detail' ? { snap, focus: undefined } : { type: 'data', snap };
handlers.message({ data });
const target = elements[view === 'detail' ? 'detail' : 'header'];
const link = target.children.find(child => typeof child !== 'string' && child.className === 'link');
if (link) link.events.click({ preventDefault() {} });
console.log(JSON.stringify({ text: target.textContent, message: messages.at(-1) }));
