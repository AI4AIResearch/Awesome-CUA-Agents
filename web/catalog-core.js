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
export const TOPIC_ALIASES = {'reinforcement-learning':['RL'],'human-in-the-loop':['HITL']};
const CJK = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
export function searchText(values) {
  const text = values.filter(Boolean).join(' ');
  // Index the parts of compound names too, so word-start search finds "osworld" in macOSWorld and "llm" in SpreadsheetLLM.
  const parts = text.split(/\s+/).filter(word => /\p{Ll}\p{Lu}/u.test(word)).map(word => word.replace(/(\p{Ll})(\p{Lu})/gu,'$1 $2'));
  return normalize([text,...parts].join(' '));
}
export function matches(record, state, ignoreKind = false) {
  if (!ignoreKind && state.kind && record.kind !== state.kind) return false;
  if (state.platform && !record.environments.includes(state.platform)) return false;
  if (state.review && record.review_status !== state.review) return false;
  if (state.topic && !record.topics.includes(state.topic)) return false;
  if (state.year && (record.published_at || '').slice(0,4) !== state.year) return false;
  const terms = normalize(state.q).split(' ').filter(Boolean);
  // Latin and digit terms match at word starts; CJK text is not space-delimited, so it keeps substring matching.
  return terms.every(term => CJK.test(term) ? record.search_text.includes(term) : record.search_text.startsWith(term) || record.search_text.includes(' '+term));
}
export function filtered(records, state) {
  const result = records.filter(r => matches(r,state));
  const alpha = (a,b) => a.name.localeCompare(b.name,'en',{sensitivity:'base'});
  if (state.sort === 'name') result.sort(alpha);
  else if (state.sort === 'newest') result.sort((a,b) => (b.published_at || '').localeCompare(a.published_at || '') || alpha(a,b));
  else result.sort((a,b) => {
    const review = Number(a.review_status !== 'curated') - Number(b.review_status !== 'curated');
    if (review) return review;
    if (['paper','survey'].includes(state.kind)) return (b.published_at || '').localeCompare(a.published_at || '') || alpha(a,b);
    const rank = r => r.kind !== 'company' && FEATURED.includes(r.name) ? FEATURED.indexOf(r.name) : FEATURED.length;
    const exact = r => state.q && normalize(r.name) === normalize(state.q) ? -1 : 0;
    return exact(a)-exact(b) || rank(a)-rank(b) || alpha(a,b);
  });
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
