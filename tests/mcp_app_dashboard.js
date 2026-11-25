'use strict';
const assert = require('assert'), fs = require('fs'), vm = require('vm');
class Node {
 constructor(tag='div') { this.tag=tag; this.children=[]; this.dataset={}; this.style={setProperty:(k,v)=>{this.style[k]=v}}; this.events={}; this.className=''; this.classList={add:(c)=>{this.className+=' '+c},toggle(){}}; this.text=''; this.value=''; this.open=false; this.hidden=false; }
 set textContent(v) { this.text=v; this.children=[]; } get textContent() { return this.text+this.children.map(c=>typeof c==='string'?c:c.textContent).join(''); }
 append(...c) { for(const x of c) { if(typeof x!=='string') x.parent=this; this.children.push(x); } } prepend(...c) { for(const x of c) if(typeof x!=='string') x.parent=this; this.children.unshift(...c); } replaceChildren(...c) { this.text=''; this.children=[]; this.append(...c); }
 addEventListener(t,f) { (this.events[t] ||= []).push(f); } setAttribute(k,v) { this[k]=v; } cloneNode() { return new Node('svg'); }
 contains(node) { return node===this || this.children.some(c=>typeof c!=='string' && c.contains(node)); }
 insertBefore(node,ref) { const old=this.children.indexOf(node); if(old>=0)this.children.splice(old,1); const at=this.children.indexOf(ref); this.children.splice(at<0?this.children.length:at,0,node); node.parent=this; }
 get nextSibling() { const siblings=this.parent?.children || []; return siblings[siblings.indexOf(this)+1]; }
 getBoundingClientRect() { return {height:100}; }
 get selectedOptions() { return this.children.filter(c=>c.selected); }
 dispatch(t,event={}) { for(const f of this.events[t] || []) f({preventDefault(){},target:this,clientX:12,clientY:34,...event}); }
 click(event={}) { this.dispatch('click',event); }
}
const dashboard=new Node(), html=new Node('html'), body=new Node('body'), svg=new Node('svg'), listeners={};
const doc={documentElement:html,body,createElement:t=>new Node(t),createElementNS:(ns,t)=>new Node(t),getElementById:()=>dashboard,querySelector:()=>svg,addEventListener:(k,v)=>{(listeners['doc:'+k] ||= []).push(v)}};
const opened=[]; const win={addEventListener:(k,v)=>{(listeners[k] ||= []).push(v)},removeEventListener:(k,v)=>{listeners[k]=(listeners[k]||[]).filter(f=>f!==v)},open:(...args)=>opened.push(args)};
const context={document:doc,window:win,globalThis:null,__CLUTCH_DASHBOARD_NO_AUTOBOOT__:true,console,URL, setTimeout,clearTimeout}; context.globalThis=context;
vm.createContext(context); const source=fs.readFileSync(process.argv[2],'utf8').match(/<script>([\s\S]*)<\/script>/)[1]; vm.runInContext(source,context);
const help={engine:{text:'engine'},commit:{text:'commit'},section:{text:'section'},status:{text:'status',what:'status',link:{label:'path docs',path:'clutch/docs/host-running.md',line:12}},box:{text:'box'},topic:{text:'help',link:{label:'docs',url:'https://example.com'}}};
for (const entry of Object.values(help)) entry.link ||= {label:'docs',url:'https://example.com'};
const row={stem:'alpha',section:'queued',path:'tickets/alpha/ticket.md',graph:{segments:[],circle:0,width:1},status:'ready',tooltip:'tip',priority:'P1',priorityChoices:[{label:'P1'},{label:'P2'}],runsBeforeChoices:[{label:'beta',picked:true}],menu:{clutchConfirm:'on',clutchReject:'on',clutchPriority:'on',clutchRunsBefore:'on',clutchAskDiagnose:'on',clutchAskReview:'on',clutchAskDrafts:'on',clutchLint:'on'},help:{section:'section',status:'status'},detail:[{heading:null,text:'detail'}],next:['topic']};
const box=id=>({id,summary:id,state:'pending',status:'new',path:`box/${id}.md`,help:{class:'box',outcome:'box'},fields:[],menu:{clutchTriage:'on',clutchDismiss:'on'}});
const snap={root:'/repo #space',configPath:'/repo #space/config.yaml',counts:{},help,headerHelp:{engine:'engine',commit:'commit'},rows:[row],verdictDecisions:[],runningStem:null,box:[box('one'),box('two')],boxCounts:{},boxHeaderHelp:{},steps:JSON.parse(process.argv[3]).map(kind=>({kind,stem:'alpha',timeDisplay:'now',text:'step',path:'step.md',tooltip:'step'})).concat([{kind:'unknown',text:'bad',timeDisplay:'later',tooltip:'bad'}]),engine:true};
let calls=[], messages=[], contexts=[], requests=[], capabilities={message:{},updateModelContext:{}}, fileResult={}, engineRunning=true;
const app={connect:async()=>{},getHostContext:()=>({theme:'dark',styles:{variables:{'--color-text-primary':'red'}}}),getHostCapabilities:()=>capabilities,callServerTool:async x=>{calls.push(x); return {structuredContent:x.name==='clutch_app_snapshot'?snap:x.name==='clutch_engine_control'?{engine:engineRunning}:x.name==='clutch_prompt'?{text:'prompt text'}:x.name==='clutch_app_stats'?{tree:[{label:'Health',description:'',tooltip:'health tip',children:[{label:'Passed',description:'7',children:[]}]}]}:{value:7}}},request:async x=>{requests.push(x); if(fileResult instanceof Error) throw fileResult; return fileResult},sendMessage:async x=>messages.push(x),updateModelContext:async x=>contexts.push(x)};
function find(n,text) { if(n.text===text)return n; for(const c of n.children) if(typeof c!=='string'){const x=find(c,text);if(x)return x;} }
function findAll(n,text) { return (n.text===text?[n]:[]).concat(n.children.flatMap(c=>typeof c==='string'?[]:findAll(c,text))); }
function rowNode(n,key,value) { if(n.dataset[key]===value)return n; for(const c of n.children) if(typeof c!=='string'){const x=rowNode(c,key,value);if(x)return x;} }
const tick=()=>new Promise(r=>setTimeout(r,0));
(async()=>{
 await context.ClutchDashboardApp.createDashboardApp({app,root:dashboard});
 const path=require('path'), repoRoot=path.resolve(__dirname,'..');
 const viewCss=fs.readFileSync(path.join(repoRoot,'vscode-clutchwork/media/view.css'),'utf8'), css=fs.readFileSync(path.join(repoRoot,'clutch/ui/dashboard.css'),'utf8');
 for(const token of new Set(viewCss.match(/--vscode-[A-Za-z0-9-]+/g))) assert(css.includes(token+':'), `missing ${token}`);
 assert(/\.step-row\s*\{[^}]*display:\s*flex[^}]*width:\s*100%/s.test(css));
 const all=(n,p)=>[...(p(n)?[n]:[]),...n.children.flatMap(c=>typeof c==='string'?[]:all(c,p))];
 const section=k=>all(dashboard,n=>n.tag==='details'&&n.dataset.section===k)[0];
 for(const [k,title] of [['tickets','Tickets'],['details','Details'],['steps','Recent Steps']]) { assert(section(k).open); assert(find(section(k),title)); }
 for(const k of ['stats','help']) assert(!section(k).open);
 assert(!all(dashboard,n=>n.tag==='nav'&&n.className==='tabs').length);
 const steps=all(section('steps'),n=>n.className==='step-row'); assert.equal(steps.length,JSON.parse(process.argv[3]).length+1);
 for(const step of steps.slice(0,-1)) { assert(all(step,n=>n.tag==='svg').length); assert(find(step,'alpha')); assert(find(step,'step')); assert(find(step,'now')); assert(!step.textContent.includes('unknown step kind')); }
 assert(all(steps.at(-1),n=>n.tag==='svg').length); assert(steps.at(-1).textContent.includes('unknown step kind unknown'));
 assert(calls.some(x=>x.name==='clutch_app_stats'&&x.arguments.window==='7d'&&x.arguments.tree===true));
 const health=all(section('stats'),n=>n.className==='stats-row'&&n.tag==='details').find(n=>find(n,'Health'));
 assert(health); // Reject unformatted or non-collapsible parent metrics.
 assert.equal(health.children[0].title,'health tip'); // Reject a dropped parent tooltip.
 const passed=all(health,n=>n.className==='stats-row'&&n.tag==='div').find(n=>find(n,'Passed'));
 assert(passed && find(passed,'7')); // Reject flattened children or an incorrect metric value.
 assert(!all(section('stats'),n=>n.tag==='pre').length);
 for (const value of ['#B180D7','#3794FF','#EA5C00','#73C991','#F14C4C','#CCA700','#388A34','#E51400','#BF8803']) assert(css.includes(value));
 assert(!css.includes('--vscode-clutchwork-merged: var(--color-text-success')); assert(!css.includes('--vscode-clutchwork-blocked: var(--color-text-warning'));
 assert(css.includes('font-size: var(--vscode-font-size, 13px)')); for(const cls of ['view-header','menu-sep','agent-actions','section-body','section-resizer']) assert(css.includes('.'+cls));
 assert.equal(all(dashboard,n=>n.className==='view-header').length,2);
 const original=dashboard.children.filter(n=>n.className==='sidebar-section'); const summary=original[1].children[0]; find(summary,'▲').click({stopPropagation(){}}); assert(dashboard.children.indexOf(original[1])<dashboard.children.indexOf(original[0]));
 original[0].children[0].dispatch('dragstart'); original[1].children[0].dispatch('drop'); assert(dashboard.children.indexOf(original[0])<dashboard.children.indexOf(original[1]));
 // Reject inserting before a lower adjacent target, which leaves the order unchanged.
 original[0].children[0].dispatch('dragstart'); original[1].children[0].dispatch('drop'); assert(dashboard.children.indexOf(original[0])>dashboard.children.indexOf(original[1]));
 // Reject landing one position short when dragging onto the final section.
 original[0].children[0].dispatch('dragstart'); original.at(-1).children[0].dispatch('drop'); assert.equal(dashboard.children.filter(n=>n.className==='sidebar-section').at(-1),original[0]);
 const bodySection=original[0].children[1], handle=original[0].children[2]; handle.dispatch('pointerdown',{clientY:100}); for(const f of listeners.pointermove) f({clientY:-100}); assert.equal(bodySection.style.height,'60px'); for(const f of [...listeners.pointerup]) f();
 const top=all(dashboard,n=>n.className==='top-bar')[0]; for(const name of ['Refresh','Open config.yaml','Switch repository: /repo #space']) assert(all(top,n=>n.title===name && n.tag==='button').length);
 assert(!find(section('details'),'Open config.yaml')); for(const name of ['run.md','checks.json','review.md','diagnosis.json','rework.md']) assert(!find(section('details'),name));
 const switcher=all(dashboard,n=>n.className==='repo-switcher')[0]; assert(switcher.hidden); all(top,n=>n.title==='Switch repository: /repo #space')[0].click(); assert(!switcher.hidden);
 all(top,n=>n.title==='Open config.yaml')[0].click(); await tick(); assert(requests.at(-1).params.uri.endsWith('/config.yaml')); requests.length=0;
 let ticket=rowNode(dashboard,'stem','alpha'); const beforeHover=contexts.length; ticket.dispatch('mouseenter'); assert.equal(contexts.length,beforeHover); assert(section('details').textContent.includes('alpha')); ticket.parent.dispatch('mouseleave'); assert(section('details').textContent.includes('Nothing running')); ticket.dispatch('contextmenu'); let menu=all(dashboard,n=>n.className==='context-menu')[0]; assert(!menu.hidden); for(const name of ['Confirm (keep)','Reject (kill)','Run before...','Set priority...','Lint','Open ticket.md','Ask Agent: diagnose','Ask Agent: review','Ask Agent: drafts']) assert(find(menu,name),name); for (const name of ['Open run.md','Open review.md','Open diagnosis.json']) assert(!find(menu,name)); assert.equal(all(menu,n=>n.className==='menu-sep').length,3); find(menu,'Set priority...').click();
 assert.equal(menu.style.left,'12px'); assert.equal(menu.style.top,'34px'); find(menu,'P2').click(); await tick(); assert(calls.some(x=>x.name==='clutch_ticket_order'&&x.arguments.priority==='P2'));
 for(const [label,tool] of [['Confirm (keep)','clutch_app_ticket_confirm'],['Reject (kill)','clutch_app_ticket_reject']]) { ticket=rowNode(dashboard,'stem','alpha'); ticket.dispatch('contextmenu'); find(menu,label).click(); await tick(); assert(calls.some(x=>x.name===tool&&x.arguments.stem==='alpha')); }
 ticket=rowNode(dashboard,'stem','alpha'); ticket.dispatch('contextmenu'); find(menu,'Run before...').click(); find(menu,'Set runs before').click(); await tick(); assert(calls.some(x=>x.name==='clutch_ticket_order'&&x.arguments.runs_before?.join(',')==='beta'));
 ticket=rowNode(dashboard,'stem','alpha'); ticket.dispatch('contextmenu'); for(const f of listeners.keydown) f({key:'Escape'}); assert(menu.hidden);
 ticket.dispatch('contextmenu'); for(const f of listeners['doc:click']) f({target:dashboard}); assert(menu.hidden);
 assert.equal(html['data-theme'],'dark'); assert.equal(html.style['--color-text-primary'],'red');
 app.onhostcontextchanged({theme:'light',styles:{variables:{'--color-text-primary':'blue'}}}); assert.equal(html['data-theme'],'light'); assert.equal(html.style['--color-text-primary'],'blue');
 app.ontoolresult({structuredContent:{repo:'/another'}}); await tick(); assert(calls.filter(x=>x.name==='clutch_app_snapshot').every(x=>!('repo' in x.arguments))); assert(calls.some(x=>x.name==='clutch_app_snapshot')); assert(calls.some(x=>x.name==='clutch_app_stats'&&x.arguments.window==='7d'));
 for(const name of ['Tickets','Details','Recent Steps','Suggestion Box','Stats','Help & Lifecycle']) assert(find(dashboard,name));
 ticket=rowNode(dashboard,'stem','alpha'); ticket.click(); await tick(); assert(contexts.some(x=>x.content[0].name==='alpha'));
 for(const name of ['Confirm','Reject','Set priority','Set runs before']) { find(dashboard,name).click(); await tick(); }
 for(const name of ['clutch_app_ticket_confirm','clutch_app_ticket_reject','clutch_ticket_order']) assert(calls.some(x=>x.name===name));
 assert(!find(dashboard,'Drain')); assert(!find(dashboard,'Serve')); assert(find(dashboard,'Stop'));
 find(dashboard,'Stop').click(); await tick(); assert(calls.some(x=>x.name==='clutch_engine_control'&&x.arguments.action==='stop'));
 engineRunning=false; snap.engine=false; for(const f of listeners.focus) await f(); await tick(); assert(!find(dashboard,'Stop')); assert(find(dashboard,'Drain')); assert(find(dashboard,'Serve'));
 find(dashboard,'Drain').click(); await tick(); assert(calls.some(x=>x.name==='clutch_engine_start'&&x.arguments.mode==='drain'));
 find(dashboard,'Open ticket.md').click(); await tick(); assert.equal(requests[0].method,'com.google.antigravity/toggle-aux-pane'); assert.equal(requests[0].params.uri,'file:///repo%20%23space/tickets/alpha/ticket.md');
 find(dashboard,'path docs').click(); await tick(); assert.equal(requests.at(-1).params.uri,'file:///repo%20%23space/clutch/docs/host-running.md');
 const links=findAll(dashboard,'Learn more'); const beforeDetailHelp=requests.length; links[0].click(); await tick(); assert.equal(requests.length,beforeDetailHelp+1); assert.equal(requests.at(-1).params.uri,'file:///repo%20%23space/clutch/docs/host-running.md'); links[1].click(); assert.equal(opened.at(-1)[0],'https://example.com');
 const urlLink=find(dashboard,'docs'); assert.equal(urlLink.href,'https://example.com'); assert.equal(urlLink.target,'_blank');
 find(dashboard,'Supervise Drain Loop').click(); await tick(); assert.equal(messages[0].content[0].text,'prompt text');
 const checkbox=find(dashboard,'New conversation ').children[0]; checkbox.checked=true; find(dashboard,'Review Drafts').click(); await tick(); assert.equal(messages[1]._meta['com.google.antigravity/message'].target,'new');
 rowNode(dashboard,'id','one').click({}); rowNode(dashboard,'id','two').click({ctrlKey:true}); await tick(); assert(contexts.some(x=>x.content[0].name==='two'));
 let boxRow=rowNode(dashboard,'id','one'); boxRow.dispatch('contextmenu'); assert(!menu.hidden); for(const name of ['Triage','Dismiss','Open message file']) assert(find(menu,name));
 find(menu,'Triage').click(); await tick(); assert(calls.some(x=>x.name==='clutch_box_triage'&&x.arguments.ids.join(',')==='one,two'));
 boxRow=rowNode(dashboard,'id','one'); boxRow.dispatch('contextmenu'); find(menu,'Dismiss').click(); await tick(); assert(calls.some(x=>x.name==='clutch_box_dismiss'&&x.arguments.ids.join(',')==='one,two'));
 find(dashboard,'Triage').click(); await tick(); find(dashboard,'Dismiss').click(); await tick(); assert(calls.some(x=>x.name==='clutch_box_triage'&&x.arguments.ids.length===2)); assert(calls.some(x=>x.name==='clutch_box_dismiss'&&x.arguments.ids.length===2));
 row.menu={clutchConfirm:'off',clutchReject:'off',clutchPriority:'off',clutchRunsBefore:'off'}; snap.box.forEach(r=>{r.menu={clutchTriage:'off',clutchDismiss:'off'}}); for(const f of listeners.focus) await f(); await tick(); rowNode(dashboard,'stem','alpha').click({}); rowNode(dashboard,'stem','alpha').click({}); await tick(); for(const name of ['Confirm','Reject','Set priority','Set runs before','Triage','Dismiss']) assert(!find(dashboard,name));
 ticket=rowNode(dashboard,'stem','alpha'); ticket.dispatch('contextmenu'); for(const name of ['Confirm','Reject','P2','Runs before...','Diagnose Stem']) assert(!find(menu,name)); boxRow=rowNode(dashboard,'id','one'); boxRow.dispatch('contextmenu'); assert(!find(menu,'Triage')); assert(!find(menu,'Dismiss'));
 capabilities={}; app.onhostcontextchanged({}); assert(!find(dashboard,'Review Drafts'));
 fileResult=Object.assign(new Error('unsupported'),{code:-32601}); find(dashboard,'step').parent.click(); await tick(); assert(dashboard.textContent.includes('File opening is unavailable'));
 app.ontoolinput({arguments:{repo:'/chosen'}}); await tick(); assert(calls.some(x=>x.name==='clutch_app_snapshot' && x.arguments.repo==='/chosen')); app.ontoolinput({arguments:{repo:''}}); await tick(); assert(!('repo' in calls.filter(x=>x.name==='clutch_app_snapshot').at(-1).arguments));
 const bootRoot=new Node(); let failBoot=true; const bootApp={...app, callServerTool:async x=>{ if (failBoot && x.name==='clutch_app_snapshot') return {isError:true,structuredContent:{code:'invalid_repo',message:'repo is not a checkout containing tickets/'}}; return app.callServerTool(x); }};
 await context.ClutchDashboardApp.createDashboardApp({app:bootApp,root:bootRoot}); assert.equal(all(bootRoot,n=>n.className==='notice')[0].textContent,''); failBoot=false; bootApp.ontoolresult({structuredContent:{repo:'/repo'}}); await tick(); assert(all(bootRoot,n=>n.className==='repo-switcher')[0].hidden); assert.equal(all(bootRoot,n=>n.className==='notice')[0].textContent,'');
 const d2=new Node(); fileResult={isError:true}; await context.ClutchDashboardApp.createDashboardApp({app,root:d2}); find(d2,'step').parent.click(); await tick(); assert(d2.textContent.includes('File opening is unavailable'));
})().catch(e=>{console.error(e);process.exitCode=1});
