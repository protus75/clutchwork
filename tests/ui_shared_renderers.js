'use strict';
const assert = require('assert');
class Node {
 constructor() { this.children = []; this.dataset = {}; this.style = {}; this.events = {}; this.classList = { add: x => { this.className = x; }, toggle() {} }; this.text = ''; }
 set textContent(v) { this.text = v; this.children = []; }
 get textContent() { return this.text + this.children.map(x => typeof x === 'string' ? x : x.textContent).join(''); }
 append(...c) { this.children.push(...c); }
 replaceChildren(...c) { this.text = ''; this.children = c; }
 addEventListener(t, f) { this.events[t] = f; }
 setAttribute(k, v) { this[k] = v; }
}
global.document = { createElement: () => new Node(), createElementNS: () => new Node() };
const {renderGraph} = require('../vscode-clutchwork/media/graph.js');
const {createTicketsView} = require('../vscode-clutchwork/media/view.js');
const {createDetailView} = require('../vscode-clutchwork/media/detail.js');
const {createBoxView} = require('../vscode-clutchwork/media/box.js');
const calls = [];
const host = {callTool(){}, sendPrompt(){}, openFile: x => calls.push(['file', x]), openHelp: x => calls.push(['help', x]), onFocus: x => calls.push(['focus', x]), onRowContext: (node, row, ids) => calls.push(['context', row.stem || row.id, ids])};
for (const factory of [createTicketsView, createDetailView, createBoxView]) for (const method of ['callTool','openFile','sendPrompt','openHelp']) { const bad = {...host}; delete bad[method]; assert.throws(() => factory({header:new Node(), list:new Node(), detail:new Node(), host:bad, renderGraph}), TypeError); }
assert.equal(renderGraph({segments:[], dot:'normal', circle:0, width:1}, 'red', {}).className, 'graph');
const header = new Node(), list = new Node();
const row = {stem:'alpha', section:'queued', path:'alpha.md', graph:{segments:[], circle:0, width:1}, status:'ready', tooltip:'tip'};
const snap = {counts:{}, help:{engine:{text:'engine'}, commit:{text:'commit'}, section:{text:'section'}, status:{text:'status',what:'status'}}, headerHelp:{engine:'engine',commit:'commit'}, rows:[row], verdictDecisions:[]};
const tickets = createTicketsView({header,list,host,renderGraph}); tickets.render(snap);
list.children[0].events.mouseenter(); list.children[0].events.click(); list.children[0].events.dblclick();
assert(calls.some(x => x[0] === 'file' && x[1] === 'alpha.md')); assert.equal(tickets.getFocus(),'alpha'); assert(calls.some(x => x[0] === 'context' && x[1] === 'alpha'));
tickets.render({}); header.children[1].events.click({preventDefault(){}}); assert(calls.some(x => x[0] === 'help' && x[1] === undefined));
const detail = new Node(); const dv = createDetailView({detail,host});
const drow = {...row, help:{section:'section',status:'status'}, detail:[{heading:null,text:'details'}], next:[]}; dv.render({...snap, rows:[drow],runningStem:'alpha'});
function find(n, text) { if (n.text === text) return n; for (const c of n.children) if (typeof c !== 'string') { const hit = find(c,text); if (hit) return hit; } }
find(detail,'Learn more').events.click({preventDefault(){}}); find(detail,'Open ticket.md').events.click({preventDefault(){}}); assert(calls.some(x => x[0] === 'help' && x[1] === 'status'));
const bh = new Node(), bl = new Node(), keyboard = new Node(); const bv = createBoxView({header:bh,list:bl,host,keyboardTarget:keyboard});
const br = id => ({id, summary:id, state:'pending', status:'new', path:id+'.md', help:{class:'section',outcome:'status'}});
bv.render({box:[br('one'),br('two')], boxCounts:{},boxHeaderHelp:{},help:snap.help}); bl.children[0].events.click({}); bl.children[1].events.click({ctrlKey:true}); assert.deepEqual(bv.getSelected(),['one','two']); bl.children[1].events.dblclick(); assert(calls.some(x => x[0] === 'file' && x[1] === 'two.md')); assert(calls.some(x => x[0] === 'focus' && x[1] === 'two'));
// Exercise the auto-mounted adapters with real rows and captured webview messages.
const vm = require('vm'), fs = require('fs'), path = require('path');
for (const name of ['view', 'box', 'detail']) {
 const messages = [], handlers = {}, elements = {header:new Node(), list:new Node(), detail:new Node()};
 const context = {document:{getElementById:id => elements[id], createElement:() => new Node()}, window:{addEventListener:(type, fn) => { handlers[type] = fn; }}, acquireVsCodeApi:() => ({postMessage: msg => messages.push(msg)}), renderGraph:() => new Node()};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../vscode-clutchwork/media',name+'.js'),'utf8'), context);
 assert.equal(messages[0].type, 'ready');
 if (name === 'view') {
  handlers.message({data:{type:'data',snap}}); const node = elements.list.children[0]; node.events.mouseenter(); node.events.dblclick();
  assert.equal(messages.at(-1).path, 'alpha.md'); assert(messages.some(m => m.type === 'focus' && m.stem === 'alpha')); assert.equal(JSON.parse(node.dataset.vscodeContext).clutchStem,'alpha');
 } else if (name === 'box') {
  handlers.message({data:{type:'data',snap:{box:[br('one'),br('two')],boxCounts:{},boxHeaderHelp:{},help:snap.help}}}); const [a,b] = elements.list.children; a.events.click({}); b.events.click({ctrlKey:true}); b.events.dblclick();
  assert.equal(messages.at(-1).path, 'two.md'); assert(messages.some(m => m.type === 'focus' && m.id === 'two')); assert.deepEqual(JSON.parse(b.dataset.vscodeContext).clutchIds,['one','two']);
 } else {
  handlers.message({data:{snap:{...snap,rows:[drow],runningStem:'alpha'}}}); find(elements.detail,'Learn more').events.click({preventDefault(){}}); assert.equal(messages.at(-1).topic,'status'); find(elements.detail,'Open ticket.md').events.click({preventDefault(){}}); assert.equal(messages.at(-1).path,'alpha.md');
 }
}
