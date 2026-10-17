import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalize,matches,filtered,parseState,serializeState,escapeHTML,safeURL,PAGE_SIZE,bibliographicDate} from '../web/catalog-core.js';
import {FEATURED} from '../web/catalog-core.js';
import {TOPIC_ALIASES,searchText} from '../web/catalog-core.js';
import {FACT_LABELS,formatFact} from '../web/catalog-core.js';

const rows=readFileSync(new URL('../data/catalog.jsonl',import.meta.url),'utf8').trim().split('\n').map(JSON.parse);
rows.forEach(r=>r.search_text=searchText([r.name,r.summary,...r.aliases,...r.authors,...r.topics,...r.topics.flatMap(x=>TOPIC_ALIASES[x] || []),...r.environments]));
const initial=()=>parseState('');

test('all published resources are searchable without dropping metadata-only records',()=>{
  assert.equal(filtered(rows,initial()).length,rows.length);
  assert.equal(filtered(rows,{...initial(),review:'metadata_verified'}).length,rows.filter(r=>r.review_status==='metadata_verified').length);
});
test('platform, kind, review, and topic filters intersect',()=>{
  const state={...initial(),kind:'dataset',platform:'android',review:'curated',topic:'data-generation'};
  const actual=filtered(rows,state);
  assert.ok(actual.length>0);
  assert.ok(actual.every(r=>r.kind==='dataset'&&r.environments.includes('android')&&r.review_status==='curated'&&r.topics.includes('data-generation')));
  assert.equal(matches(actual[0],{...state,kind:'model'}),false);
});
test('source-pending papers are not silently labeled as Android',()=>{
  const papers=filtered(rows,{...initial(),kind:'paper',platform:'android',review:'metadata_verified'});
  assert.equal(papers.length,0);
});
test('search uses all terms and normalizes punctuation',()=>{
  assert.ok(filtered(rows,{...initial(),q:'UI-TARS'}).some(r=>r.name==='UI-TARS'));
  assert.equal(filtered(rows,{...initial(),q:'this resource does not exist xyzq987654'}).length,0);
  assert.equal(normalize('GUI－定位'),'gui 定位');
});
test('newest publication sorts known dates first and unknown dates last',()=>{
  const result=filtered(rows,{...initial(),sort:'newest'});
  assert.ok(bibliographicDate(result[0]));
  const index=result.findIndex(r=>!bibliographicDate(r));
  assert.ok(index>0);
  assert.ok(result.slice(index).every(r=>!bibliographicDate(r)));
});
test('publisher years and months filter and sort without invented days or arXiv date substitution',()=>{
  const make=(id,parts)=>({id,name:id,kind:'paper',review_status:'curated',environments:['web'],topics:[],search_text:'',published_at:null,details:{publication:{date_parts:parts}}});
  const year=make('url:year',[2017]),month=make('url:month',[2017,8]),day=make('url:day',[2017,8,10]),unknown=make('url:unknown',null);
  assert.equal(bibliographicDate(year),'2017');assert.equal(bibliographicDate(month),'2017-08');
  assert.deepEqual(filtered([unknown,year,month,day],{...initial(),kind:'paper',year:'2017',sort:'newest'}).map(r=>r.id),['url:day','url:month','url:year']);
  const compact={...year,details:undefined,paper_date:'2017'};
  assert.ok(matches(compact,{...initial(),year:'2017'}));
  const preprint={...month,id:'arxiv:2001.00001',published_at:'2020-01-02'};
  assert.equal(bibliographicDate(preprint),'2020-01-02');
  assert.equal(matches(preprint,{...initial(),year:'2017'}),false);
});
test('deep links round-trip search, filters, layout, language, and a selected record',()=>{
  const state={q:'GUI 定位',kind:'model',platform:'desktop',review:'curated',topic:'grounding',year:'',sort:'name',page:2,view:'list'};
  const encoded=serializeState(state,'zh','github:bytedance/ui-tars');
  assert.deepEqual(parseState(encoded),state);
  assert.equal(new URLSearchParams(encoded).get('record'),'github:bytedance/ui-tars');
  assert.equal(new URLSearchParams(encoded).get('lang'),'zh');
  for(const platform of new Set(rows.flatMap(row=>row.environments))) {
    const roundTrip=serializeState({...state,platform},'en','');
    assert.equal(parseState(roundTrip).platform,platform);
  }
});
test('unrecognized sort/type and invalid pages fall back safely',()=>{
  const state=parseState('?kind=bad&sort=bad&page=-10&review=unverified');
  assert.equal(state.page,1);assert.equal(state.kind,'');assert.equal(state.sort,'featured');assert.equal(state.review,'');
  assert.equal(parseState('?page=Infinity').page,1);
  assert.ok(PAGE_SIZE>0);
});
test('untrusted names and source URLs cannot inject active HTML',()=>{
  assert.equal(escapeHTML('<img src=x onerror="alert(1)">'),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
  assert.equal(safeURL('javascript:alert(1)'),'#');
  assert.equal(safeURL('data:text/html,hello'),'#');
  assert.equal(safeURL('https://example.org/path'),'https://example.org/path');
});
test('featured project names do not accidentally feature identically named publishers',()=>{
  const result=filtered(rows,initial());
  const framework=result.findIndex(r=>r.name==='Browser Use'&&r.kind==='framework');
  const company=result.findIndex(r=>r.name==='Browser Use'&&r.kind==='company');
  assert.ok(framework<company);
});

test('paper browsing defaults to dense rows but explicit layout and year round-trip',()=>{
  assert.equal(parseState('?kind=paper').view,'list');
  assert.equal(parseState('?kind=survey').view,'list');
  assert.equal(parseState('?kind=model').view,'grid');
  const state={...parseState('?kind=paper'),year:'2026',view:'grid'};
  assert.deepEqual(parseState(serializeState(state,'zh')),state);
  const result=filtered(rows,{...state,review:'curated'});
  assert.ok(result.length>0);assert.ok(result.every(r=>bibliographicDate(r).slice(0,4)==='2026'));
  assert.equal(parseState('?year=hello').year,'');
});
test('paper curated-first order puts reviewed recent work before older reviewed work',()=>{
  const result=filtered(rows,parseState('?kind=paper'));
  const reviewed=result.filter(r=>r.review_status==='curated');
  assert.ok(reviewed.length>0);assert.ok(reviewed.slice(1).every((r,i)=>bibliographicDate(reviewed[i])>=bibliographicDate(r)));
  assert.ok(result.slice(reviewed.length).every(r=>r.review_status!=='curated'));
});

test('details request only their own JSON and share concurrent/cached requests',async()=>{
  const {createRecordLoader}=await import('../web/catalog-core.js');
  const calls=[];let release;
  const load=createRecordLoader(url=>{calls.push(url);return new Promise(resolve=>{release=resolve;});});
  const record={id:'arxiv:2404.07972',page_url:'/resources/arxiv-2404-07972/'};
  const first=load(record),second=load(record);
  assert.deepEqual(calls,['/resources/arxiv-2404-07972/record.json']);
  const full={id:record.id,review_status:'curated',details:{example:true}};
  release({ok:true,json:async()=>full});
  assert.deepEqual(await first,full);assert.deepEqual(await second,full);assert.deepEqual(await load(record),full);
  assert.equal(calls.length,1);
});
test('failed, mismatched, or scope-excluded detail payloads are not cached as active records',async()=>{
  const {createRecordLoader}=await import('../web/catalog-core.js');
  const record={id:'arxiv:2404.07972',page_url:'/resources/arxiv-2404-07972/'};
  for(const bad of [{ok:false,status:503},{ok:true,json:async()=>({id:'arxiv:other',review_status:'curated'})},{ok:true,json:async()=>({id:record.id,status:'excluded'})}]){
    let calls=0;const load=createRecordLoader(async()=>++calls===1?bad:{ok:true,json:async()=>({id:record.id,review_status:'curated'})});
    await assert.rejects(load(record));assert.equal((await load(record)).id,record.id);assert.equal(calls,2);
  }
});
test('sorting keeps the previous order without a collator or query normalization per comparison',()=>{
  const alpha=(a,b)=>a.name.localeCompare(b.name,'en',{sensitivity:'base'}),newer=(a,b)=>bibliographicDate(b).localeCompare(bibliographicDate(a));
  const legacy=state=>{
    const result=rows.filter(r=>matches(r,state)),rank=r=>r.kind!=='company'&&FEATURED.includes(r.name)?FEATURED.indexOf(r.name):FEATURED.length,exact=r=>state.q&&normalize(r.name)===normalize(state.q)?-1:0;
    if(state.sort==='name')return result.sort(alpha);
    if(state.sort==='newest')return result.sort((a,b)=>newer(a,b)||alpha(a,b));
    return result.sort((a,b)=>Number(a.review_status!=='curated')-Number(b.review_status!=='curated')||(['paper','survey'].includes(state.kind)?newer(a,b)||alpha(a,b):exact(a)-exact(b)||rank(a)-rank(b)||alpha(a,b)));
  };
  for(const sort of ['featured','name','newest'])for(const q of ['','g','browser use'])for(const kind of ['','paper']){
    const state={...initial(),sort,q,kind};
    assert.deepEqual(filtered(rows,state).map(r=>r.id),legacy(state).map(r=>r.id),JSON.stringify(state));
  }
  const {normalize:nativeNormalize,localeCompare}=String.prototype;let normalized=0,collated=0;
  String.prototype.normalize=function(...args){normalized++;return nativeNormalize.apply(this,args);};
  String.prototype.localeCompare=function(...args){collated++;return localeCompare.apply(this,args);};
  try{for(const sort of ['featured','name','newest'])filtered(rows,{...initial(),sort,q:'g'});}finally{String.prototype.normalize=nativeNormalize;String.prototype.localeCompare=localeCompare;}
  assert.equal(collated,0);
  assert.ok(normalized<=5*rows.length,`${normalized} normalizations for ${rows.length} records`);
});
test('desktop and mobile platforms include their operating systems',()=>{
  const ids=platform=>new Set(filtered(rows,{...initial(),platform}).map(r=>r.id));
  const desktop=ids('desktop'),mobile=ids('mobile');
  for(const r of rows){
    assert.equal(desktop.has(r.id),r.environments.some(x=>['desktop','windows','macos','linux'].includes(x)),r.name);
    assert.equal(mobile.has(r.id),r.environments.some(x=>['android','ios','harmonyos'].includes(x)),r.name);
  }
  assert.ok(rows.some(r=>mobile.has(r.id)&&r.environments.includes('ios')&&!r.environments.includes('android')));
  assert.ok(rows.some(r=>desktop.has(r.id)&&r.environments.includes('windows')&&!r.environments.includes('desktop')));
  assert.ok(filtered(rows,{...initial(),platform:'windows'}).every(r=>r.environments.includes('windows')));
  assert.equal(parseState(serializeState({...initial(),platform:'mobile'},'en')).platform,'mobile');
});
test('hero shortcuts and the platform menu offer grouped platforms in order',()=>{
  const html=readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
  const platforms=[...readFileSync(new URL('../web/app.js',import.meta.url),'utf8').match(/const PLATFORMS = (\{.*?\});/)[1].matchAll(/[{,]'?([\w-]+)'?:\[/g)].map(m=>m[1]);
  assert.deepEqual(platforms,['web','desktop','windows','macos','linux','mobile','android','ios','harmonyos','cross-platform','unspecified']);
  assert.deepEqual([...html.matchAll(/data-environment="([^"]+)"/g)].map(m=>m[1]),['web','desktop','mobile']);
  assert.ok(filtered(rows,{...initial(),platform:'mobile'}).some(r=>r.name==='iOSWorld'));
  assert.ok(filtered(rows,{...initial(),platform:'desktop'}).some(r=>r.name.startsWith('Windows Agent Arena')));
});
test('search matches Latin terms at word starts while keeping CJK substrings and topic abbreviations',()=>{
  const rl=filtered(rows,{...initial(),q:'rl'}),tagged=rows.filter(r=>r.topics.includes('reinforcement-learning'));
  assert.ok(!rl.some(r=>r.name==='OSWorld'));
  assert.ok(tagged.length>0&&tagged.every(r=>rl.includes(r)));
  assert.ok(filtered(rows,{...initial(),q:'osworld'}).some(r=>r.name==='OSWorld'));
  assert.ok(filtered(rows,{...initial(),q:'UI-TARS'}).some(r=>r.name==='UI-TARS'));
  const record={search_text:searchText(['macOSWorld SpreadsheetLLM','面向界面理解的 GUI 定位'])};
  for(const q of ['osworld','macosworld','llm','GUI 定位','理解','界面理解 gui'])assert.ok(matches(record,{...initial(),q}),q);
  for(const q of ['sworld','preadsheet','ui','gent'])assert.equal(matches(record,{...initial(),q}),false,q);
});
test('record facts label every published detail and never print raw objects',()=>{
  for(const r of rows)for(const [key,value] of Object.entries(r.details)){
    if(['arxiv_snapshot','publication','license_review'].includes(key))continue;
    assert.ok(FACT_LABELS[key]?.[0]&&FACT_LABELS[key]?.[1],`${key} needs English and Chinese labels`);
    for(const lang of ['en','zh'])assert.doesNotMatch(formatFact(key,value,lang),/\[object |undefined/,`${r.id} ${key}`);
  }
  assert.equal(formatFact('reported_scale',{comparison:'>',unit:'demonstrations',value:15000},'en'),'> 15,000 demonstrations');
  const profile={counts:[{basis:'reported',qualifier:'more-than',unit:'demonstrations',value:15000,population:'AndroidControl collection'},{basis:'computed',qualifier:'exact',unit:'applications',value:833,population:'app list'}],evidence_urls:['https://example.org'],formats:[],modalities:['screenshots','accessibility trees'],notes:'n',splits:[],supervision:['trajectories']};
  assert.equal(formatFact('dataset_profile',profile,'en'),'Supervision: trajectories\nModalities: screenshots, accessibility trees\nScale: > 15,000 demonstrations (AndroidControl collection); 833 applications (app list, computed)');
  assert.ok(formatFact('dataset_profile',profile,'zh').startsWith('监督信号：trajectories\n'));
  assert.equal(formatFact('gated','auto','en'),'Yes, approved automatically');
  assert.equal(formatFact('gated',false,'zh'),'否');
  assert.equal(formatFact('platform_constraints',{harmonyos:'HarmonyOS 4 or earlier'},'en'),'harmonyos: HarmonyOS 4 or earlier');
  assert.equal(formatFact('dataverse',{publisher:'Harvard Dataverse',version_number:5,version_minor_number:0,file_count:261,license:{name:'CC0 1.0'},publication_date:'2025-05-15'},'en'),'Harvard Dataverse · v5.0 · 261 files · CC0 1.0 · published May 15, 2025');
  for(const empty of [null,'',[]])assert.equal(formatFact('languages',empty,'en'),'');
});
const css=readFileSync(new URL('../web/styles.css',import.meta.url),'utf8');
const declaration=(selector,prop)=>{const block=css.match(new RegExp(`(?:^|[}\\n])${selector.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}\\{([^}]*)`))[1];const value=block.match(new RegExp(`(?:^|;)${prop}:([^;]+)`))[1].replace(/^var\(--([\w-]+)\)$/,(_,name)=>declaration(':root','--'+name));return value.length===4?'#'+[...value.slice(1)].map(c=>c+c).join(''):value;};
const luminance=hex=>{const [r,g,b]=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b;};
const contrast=(a,b)=>{const [x,y]=[luminance(a),luminance(b)].sort((m,n)=>n-m);return (x+.05)/(y+.05);};
test('small secondary text meets WCAG AA contrast on its surface',()=>{
  const bg=declaration(':root','--bg'),map=declaration('.ecosystem-map','background-color'),white='#ffffff';
  const pairs=[['.brand-label',white],['.hero-caption',bg],['.map-label',map],['.map-coordinates',map],['.map-foot',map],['.map-node small',white],['.section-eyebrow',declaration('.about-section','background')],['.sidebar-label',bg],['.category-count',bg],['.select-wrap>span',white],['.search-box input::placeholder',white],['.popular-topics',bg],['.popular-topics>button',declaration('.popular-topics>button','background')],['.card-tags span',white],['.card-bottom',white],['.card-bottom.is-curated',white],['.catalog-footnote',bg],['footer',bg],['.license-item span',white],['.coverage-table th',white],['.fact-list dt',white]];
  for(const kind of ['','.resource-card[data-kind=model] ','.resource-card[data-kind=dataset] ','.resource-card[data-kind=benchmark] ','.resource-card[data-kind=agent] '])pairs.push([kind+'.resource-monogram',declaration(kind+'.resource-monogram','background')]);
  for(const [selector,surface] of pairs)assert.ok(contrast(declaration(selector,'color'),surface)>=4.5,`${selector} is ${contrast(declaration(selector,'color'),surface).toFixed(2)}:1`);
});
test('primary navigation stays reachable on narrow screens',()=>{
  const styles=readFileSync(new URL('../web/styles.css',import.meta.url),'utf8');
  const narrow=[...styles.matchAll(/@media\(max-width:(\d+)px\)\{/g)].filter(m=>Number(m[1])<=760).map(m=>{let depth=1,i=m.index+m[0].length;const start=i;while(depth)depth+=({'{':1,'}':-1}[styles[i++]]||0);return styles.slice(start,i-1);}).join('');
  const nav=[...narrow.matchAll(/(?:^|\})\.site-header nav\{([^}]*)\}/g)].map(m=>m[1]).join(';');
  assert.doesNotMatch(nav,/display:none/);
  assert.match(nav,/overflow-x:auto/);
});
test('data and coverage buttons respond while the catalog loads and after it fails',async()=>{
  const coverage=JSON.parse(readFileSync(new URL('../data/coverage.json',import.meta.url),'utf8'));
  const keys=['document','window','location','history','localStorage','fetch'],saved=keys.map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]),consoleError=console.error;
  const boot=async name=>{
    let respond;const elements=new Map(),element=selector=>{if(!elements.has(selector))elements.set(selector,{dataset:{},listeners:{},classList:{toggle(){}},open:false,addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);},setAttribute(){},showModal(){this.open=true;},close(){this.open=false;}});return elements.get(selector);};
    const globals={document:{documentElement:{},body:{classList:{toggle(){}}},addEventListener(){},querySelector:element,querySelectorAll:()=>[]},window:{addEventListener(){}},location:{search:'',pathname:'/',hash:''},history:{replaceState(){}},localStorage:{getItem:()=>null,setItem(){}},fetch:()=>new Promise(resolve=>respond=resolve)};
    for(const [key,value] of Object.entries(globals))Object.defineProperty(globalThis,key,{value,configurable:true,writable:true});
    await import(`../web/app.js?${name}`);
    const dialog=element('#info-dialog');
    const content=()=>element('#info-content').innerHTML;
    return {dialog,content,respond:async value=>{respond(value);await new Promise(resolve=>setImmediate(resolve));},open:id=>{dialog.close();element('#'+id).listeners.click[0]();return content();}};
  };
  try {
    console.error=()=>{};
    const slow=await boot('loading');
    assert.match(slow.open('hero-download'),/\.\/downloads\/catalog\.jsonl/);assert.equal(slow.dialog.open,true);
    assert.match(slow.open('footer-method'),/Loading the catalog[\s\S]*href="\/coverage\/"/);
    await slow.respond({ok:true,json:async()=>({coverage,records:[]})});
    assert.equal(slow.dialog.open,true);assert.match(slow.content(),/coverage-table/);
    const failed=await boot('failed');
    assert.match(failed.open('coverage-button'),/Loading the catalog/);
    await failed.respond({ok:false,status:503});
    assert.equal(failed.dialog.open,true);assert.match(failed.content(),/could not be loaded[\s\S]*href="\/coverage\/"/);
    assert.match(failed.open('footer-method'),/could not be loaded/);
    assert.match(failed.open('sidebar-download'),/\.\/downloads\/catalog\.sqlite/);
  } finally {
    console.error=consoleError;
    for(const [key,descriptor] of saved)if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];
  }
});
