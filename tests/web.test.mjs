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
