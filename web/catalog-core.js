export const KIND_ORDER = ['paper','survey','model','dataset','benchmark','agent','framework','infrastructure','tool','product','company'];
export const FEATURED = ['OSWorld','UI-TARS','Browser Use','OpenCUA','AgentNet','AndroidWorld','WebArena','UI-Venus','Stagehand','ScreenSpot Pro','Agent S','Holo Model Family'];
export const PAGE_SIZE = 24;
export function createRecordLoader(fetcher) {
  const cache=new Map();
  return async function loadRecord(record) {
    if(!cache.has(record.id))cache.set(record.id,fetcher(record.page_url+'record.json').then(response=>{if(!response.ok)throw new Error('HTTP '+response.status);return response.json();}).then(row=>{if(row.id!==record.id||!['curated','metadata_verified'].includes(row.review_status))throw new Error('Resource snapshot mismatch');return row;}).catch(error=>{cache.delete(record.id);throw error;}));
    return cache.get(record.id);
  };
}
export function normalize(value) { return String(value || '').normalize('NFKC').toLowerCase().replace(/[\p{P}\p{S}]+/gu,' ').replace(/\s+/g,' ').trim(); }
export function matches(record, state, ignoreKind = false) {
  if (!ignoreKind && state.kind && record.kind !== state.kind) return false;
  if (state.platform && !record.environments.includes(state.platform)) return false;
  if (state.review && record.review_status !== state.review) return false;
  if (state.topic && !record.topics.includes(state.topic)) return false;
  if (state.year && (record.published_at || '').slice(0,4) !== state.year) return false;
  const terms = normalize(state.q).split(' ').filter(Boolean);
  return terms.every(term => record.search_text.includes(term));
}
const collator = new Intl.Collator('en',{sensitivity:'base'});
const FEATURED_RANK = new Map(FEATURED.map((name,i) => [name,i]));
const alpha = (a,b) => collator.compare(a.name,b.name);
// published_at is an ISO date, so code-unit order is chronological and avoids a locale comparison per call.
const newer = (a,b) => {const x=a.published_at || '', y=b.published_at || ''; return x<y ? 1 : x>y ? -1 : 0;};
export function filtered(records, state) {
  const result = records.filter(r => matches(r,state));
  if (state.sort === 'name') result.sort(alpha);
  else if (state.sort === 'newest') result.sort((a,b) => newer(a,b) || alpha(a,b));
  else {
    const papers = ['paper','survey'].includes(state.kind), q = normalize(state.q);
    const exact = new Set(state.q ? result.filter(r => normalize(r.name) === q) : []);
    const rank = r => r.kind !== 'company' && FEATURED_RANK.has(r.name) ? FEATURED_RANK.get(r.name) : FEATURED.length;
    result.sort((a,b) => Number(a.review_status !== 'curated') - Number(b.review_status !== 'curated') || (papers ? newer(a,b) || alpha(a,b) : exact.has(b)-exact.has(a) || rank(a)-rank(b) || alpha(a,b)));
  }
  return result;
}
export function parseState(search) {
  const p = new URLSearchParams(search);
  const kind=KIND_ORDER.includes(p.get('kind')) ? p.get('kind') : '';
  return {q:p.get('q') || '',kind,platform:p.get('platform') || '',review:['curated','metadata_verified'].includes(p.get('review')) ? p.get('review') : '',topic:p.get('topic') || '',year:/^(19|20)\d{2}$/.test(p.get('year') || '') ? p.get('year') : '',sort:['name','newest'].includes(p.get('sort')) ? p.get('sort') : 'featured',page:Math.max(1,parseInt(p.get('page'),10)||1),view:['list','grid'].includes(p.get('view')) ? p.get('view') : ['paper','survey'].includes(kind) ? 'list' : 'grid'};
}
export function serializeState(state, lang, record='') {
  const p = new URLSearchParams();
  for (const key of ['q','kind','platform','review','topic','year']) if (state[key]) p.set(key,state[key]);
  if (state.sort !== 'featured') p.set('sort',state.sort);
  if (state.page > 1) p.set('page',String(state.page));
  if (state.view !== (['paper','survey'].includes(state.kind) ? 'list' : 'grid')) p.set('view',state.view);
  if (lang === 'zh') p.set('lang','zh');
  if (record) p.set('record',record);
  return p.toString();
}
export function escapeHTML(value) { return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
export function safeURL(value) { try {const u=new URL(value); return ['https:','http:'].includes(u.protocol) ? u.href : '#';} catch {return '#';} }
