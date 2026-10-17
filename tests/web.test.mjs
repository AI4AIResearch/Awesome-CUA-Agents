import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalize,matches,filtered,parseState,serializeState,escapeHTML,safeURL,PAGE_SIZE} from '../web/catalog-core.js';

const rows=readFileSync(new URL('../data/catalog.jsonl',import.meta.url),'utf8').trim().split('\n').map(JSON.parse);
rows.forEach(r=>r.search_text=normalize([r.name,r.summary,...r.aliases,...r.authors,...r.topics,...r.environments].join(' ')));
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
  assert.ok(result[0].published_at);
  const index=result.findIndex(r=>!r.published_at);
  assert.ok(index>0);
  assert.ok(result.slice(index).every(r=>!r.published_at));
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
  assert.ok(result.length>0);assert.ok(result.every(r=>r.published_at.startsWith('2026')));
  assert.equal(parseState('?year=hello').year,'');
});
test('paper curated-first order puts reviewed recent work before older reviewed work',()=>{
  const result=filtered(rows,parseState('?kind=paper'));
  const reviewed=result.filter(r=>r.review_status==='curated');
  assert.ok(reviewed.length>0);assert.ok(reviewed.slice(1).every((r,i)=>(reviewed[i].published_at||'')>=(r.published_at||'')));
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
