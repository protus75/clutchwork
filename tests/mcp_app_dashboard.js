'use strict';
const assert = require('assert'), fs = require('fs'), vm = require('vm');
class Node {
 constructor(tag='div') { this.tag=tag; this.children=[]; this.dataset={}; this.style={setProperty:(k,v)=>{this.style[k]=v}}; this.events={}; this.classList={add(){},toggle(){}}; this.text=''; this.value=''; }
 set textContent(v) { this.text=v; this.children=[]; } get textContent() { return this.text+this.children.map(c=>typeof c==='string'?c:c.textContent).join(''); }
 append(...c) { this.children.push(...c); } replaceChildren(...c) { this.text=''; this.children=c; }
 addEventListener(t,f) { this.events[t]=f; } setAttribute(k,v) { this[k]=v; } cloneNode() { return new Node('svg'); }
 get selectedOptions() { return this.children.filter(c=>c.selected); }
 click(event={}) { return this.events.click?.({preventDefault(){},...event}); }
}
const dashboard=new Node(), html=new Node('html'), body=new Node('body'), svg=new Node('svg'), listeners={};
const doc={documentElement:html,body,createElement:t=>new Node(t),createElementNS:(ns,t)=>new Node(t),getElementById:()=>dashboard,querySelector:()=>svg};
const opened=[]; const win={addEventListener:(k,v)=>{listeners[k]=v},open:(...args)=>opened.push(args)};
const context={document:doc,window:win,globalThis:null,__CLUTCH_DASHBOARD_NO_AUTOBOOT__:true,console,URL, setTimeout,clearTimeout}; context.globalThis=context;
vm.createContext(context); const source=fs.readFileSync(process.argv[2],'utf8').match(/<script>([\s\S]*)<\/script>/)[1]; vm.runInContext(source,context);
const help={engine:{text:'engine'},commit:{text:'commit'},section:{text:'section'},status:{text:'status',what:'status',link:{label:'path docs',path:'clutch/docs/host-running.md',line:12}},box:{text:'box'},topic:{text:'help',link:{label:'docs',url:'https://example.com'}}};
for (const entry of Object.values(help)) entry.link ||= {label:'docs',url:'https://example.com'};
const row={stem:'alpha',section:'queued',path:'tickets/alpha/ticket.md',graph:{segments:[],circle:0,width:1},status:'ready',tooltip:'tip',priority:'P1',priorityChoices:[{label:'P1'},{label:'P2'}],runsBeforeChoices:[{label:'beta',picked:true}],menu:{clutchConfirm:'on',clutchReject:'on',clutchPriority:'on',clutchRunsBefore:'on'},help:{section:'section',status:'status'},detail:[{heading:null,text:'detail'}],next:['topic']};
const box=id=>({id,summary:id,state:'pending',status:'new',path:`box/${id}.md`,help:{class:'box',outcome:'box'},fields:[],menu:{clutchTriage:'on',clutchDismiss:'on'}});
const snap={root:'/repo #space',configPath:'/repo #space/config.yaml',counts:{},help,headerHelp:{engine:'engine',commit:'commit'},rows:[row],verdictDecisions:[],runningStem:null,box:[box('one'),box('two')],boxCounts:{},boxHeaderHelp:{},steps:[{timeDisplay:'now',text:'step',path:'step.md',tooltip:'step'}],engine:true};
let calls=[], messages=[], contexts=[], requests=[], capabilities={message:{},updateModelContext:{}}, fileResult={}, engineRunning=true;
const app={connect:async()=>{},getHostContext:()=>({theme:'dark',styles:{variables:{'--color-text-primary':'red'}}}),getHostCapabilities:()=>capabilities,callServerTool:async x=>{calls.push(x); return {structuredContent:x.name==='clutch_app_snapshot'?snap:x.name==='clutch_engine_control'?{engine:engineRunning}:x.name==='clutch_prompt'?{text:'prompt text'}:{value:7}}},request:async x=>{requests.push(x); if(fileResult instanceof Error) throw fileResult; return fileResult},sendMessage:async x=>messages.push(x),updateModelContext:async x=>contexts.push(x)};
function find(n,text) { if(n.text===text)return n; for(const c of n.children) if(typeof c!=='string'){const x=find(c,text);if(x)return x;} }
function findAll(n,text) { return (n.text===text?[n]:[]).concat(n.children.flatMap(c=>typeof c==='string'?[]:findAll(c,text))); }
function rowNode(n,key,value) { if(n.dataset[key]===value)return n; for(const c of n.children) if(typeof c!=='string'){const x=rowNode(c,key,value);if(x)return x;} }
const tick=()=>new Promise(r=>setTimeout(r,0));
(async()=>{
 await context.ClutchDashboardApp.createDashboardApp({app,root:dashboard});
 assert.equal(html['data-theme'],'dark'); assert.equal(html.style['--color-text-primary'],'red');
 app.onhostcontextchanged({theme:'light',styles:{variables:{'--color-text-primary':'blue'}}}); assert.equal(html['data-theme'],'light'); assert.equal(html.style['--color-text-primary'],'blue');
 assert(calls.some(x=>x.name==='clutch_app_snapshot')); assert(calls.some(x=>x.name==='clutch_app_stats'&&x.arguments.window==='7d'));
 for(const name of ['Tickets','Details','Recent Steps','Suggestion Box','Stats','Help & Lifecycle']) assert(find(dashboard,name));
 rowNode(dashboard,'stem','alpha').events.click({}); await tick(); assert(contexts.some(x=>x.content[0].name==='alpha'));
 for(const name of ['Confirm','Reject','Set priority','Set runs before']) { find(dashboard,name).click(); await tick(); }
 for(const name of ['clutch_app_ticket_confirm','clutch_app_ticket_reject','clutch_ticket_order']) assert(calls.some(x=>x.name===name));
 assert(!find(dashboard,'Start drain')); assert(!find(dashboard,'Start serve')); assert(find(dashboard,'Stop'));
 find(dashboard,'Stop').click(); await tick(); assert(calls.some(x=>x.name==='clutch_engine_control'&&x.arguments.action==='stop'));
 engineRunning=false; snap.engine=false; await listeners.focus(); await tick(); assert(!find(dashboard,'Stop')); assert(find(dashboard,'Start drain')); assert(find(dashboard,'Start serve'));
 find(dashboard,'Start drain').click(); await tick(); assert(calls.some(x=>x.name==='clutch_engine_start'&&x.arguments.mode==='drain'));
 find(dashboard,'ticket.md').click(); await tick(); assert.equal(requests[0].method,'com.google.antigravity/toggle-aux-pane'); assert.equal(requests[0].params.uri,'file:///repo%20%23space/tickets/alpha/ticket.md');
 find(dashboard,'path docs').click(); await tick(); assert.equal(requests.at(-1).params.uri,'file:///repo%20%23space/clutch/docs/host-running.md');
 const links=findAll(dashboard,'Learn more'); const beforeDetailHelp=requests.length; links[0].click(); await tick(); assert.equal(requests.length,beforeDetailHelp+1); assert.equal(requests.at(-1).params.uri,'file:///repo%20%23space/clutch/docs/host-running.md'); links[1].click(); assert.equal(opened.at(-1)[0],'https://example.com');
 const urlLink=find(dashboard,'docs'); assert.equal(urlLink.href,'https://example.com'); assert.equal(urlLink.target,'_blank');
 find(dashboard,'Supervise Drain Loop').click(); await tick(); assert.equal(messages[0].content[0].text,'prompt text');
 const checkbox=find(dashboard,'New conversation ').children[0]; checkbox.checked=true; find(dashboard,'Review Drafts').click(); await tick(); assert.equal(messages[1]._meta['com.google.antigravity/message'].target,'new');
 rowNode(dashboard,'id','one').events.click({}); rowNode(dashboard,'id','two').events.click({ctrlKey:true}); await tick(); assert(contexts.some(x=>x.content[0].name==='two'));
 find(dashboard,'Triage').click(); await tick(); find(dashboard,'Dismiss').click(); await tick(); assert(calls.some(x=>x.name==='clutch_box_triage'&&x.arguments.ids.length===2)); assert(calls.some(x=>x.name==='clutch_box_dismiss'&&x.arguments.ids.length===2));
 row.menu={clutchConfirm:'off',clutchReject:'off',clutchPriority:'off',clutchRunsBefore:'off'}; snap.box.forEach(r=>{r.menu={clutchTriage:'off',clutchDismiss:'off'}}); await listeners.focus(); await tick(); rowNode(dashboard,'stem','alpha').events.click({}); rowNode(dashboard,'stem','alpha').events.click({}); await tick(); for(const name of ['Confirm','Reject','Set priority','Set runs before','Triage','Dismiss']) assert(!find(dashboard,name));
 capabilities={}; app.onhostcontextchanged({}); assert(!find(dashboard,'Review Drafts'));
 fileResult=Object.assign(new Error('unsupported'),{code:-32601}); find(dashboard,'now step').click(); await tick(); assert(dashboard.textContent.includes('File opening is unavailable'));
 const d2=new Node(); fileResult={isError:true}; await context.ClutchDashboardApp.createDashboardApp({app,root:d2}); find(d2,'now step').click(); await tick(); assert(d2.textContent.includes('File opening is unavailable'));
})().catch(e=>{console.error(e);process.exitCode=1});
