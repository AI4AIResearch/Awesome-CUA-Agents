export const KIND_ORDER = ['paper','survey','model','dataset','benchmark','agent','framework','infrastructure','tool','product','company'];
export const FEATURED = ['OSWorld','UI-TARS','Browser Use','OpenCUA','AgentNet','AndroidWorld','WebArena','UI-Venus','Stagehand','ScreenSpot Pro','Agent S','Holo Model Family'];
export const PAGE_SIZE = 24;
export function normalize(value) { return String(value || '').normalize('NFKC').toLowerCase().replace(/[\p{P}\p{S}]+/gu,' ').replace(/\s+/g,' ').trim(); }
export function matches(record, state, ignoreKind = false) {
  if (!ignoreKind && state.kind && record.kind !== state.kind) return false;
  if (state.platform && !record.environments.includes(state.platform)) return false;
  if (state.review && record.review_status !== state.review) return false;
  if (state.topic && !record.topics.includes(state.topic)) return false;
  const terms = normalize(state.q).split(' ').filter(Boolean);
  return terms.every(term => record.search_text.includes(term));
}
export function filtered(records, state) {
  const result = records.filter(r => matches(r,state));
  const alpha = (a,b) => a.name.localeCompare(b.name,'en',{sensitivity:'base'});
  if (state.sort === 'name') result.sort(alpha);
  else if (state.sort === 'newest') result.sort((a,b) => (b.published_at || '').localeCompare(a.published_at || '') || alpha(a,b));
  else result.sort((a,b) => {
    const review = Number(a.review_status !== 'curated') - Number(b.review_status !== 'curated');
    if (review) return review;
    const rank = r => r.kind !== 'company' && FEATURED.includes(r.name) ? FEATURED.indexOf(r.name) : FEATURED.length;
    const exact = r => state.q && normalize(r.name) === normalize(state.q) ? -1 : 0;
    return exact(a)-exact(b) || rank(a)-rank(b) || alpha(a,b);
  });
  return result;
}
export function parseState(search) {
  const p = new URLSearchParams(search);
  return {q:p.get('q') || '',kind:KIND_ORDER.includes(p.get('kind')) ? p.get('kind') : '',platform:p.get('platform') || '',review:['curated','metadata_verified'].includes(p.get('review')) ? p.get('review') : '',topic:p.get('topic') || '',sort:['name','newest'].includes(p.get('sort')) ? p.get('sort') : 'featured',page:Math.max(1,parseInt(p.get('page'),10)||1),view:p.get('view') === 'list' ? 'list' : 'grid'};
}
export function serializeState(state, lang, record='') {
  const p = new URLSearchParams();
  for (const key of ['q','kind','platform','review','topic']) if (state[key]) p.set(key,state[key]);
  if (state.sort !== 'featured') p.set('sort',state.sort);
  if (state.page > 1) p.set('page',String(state.page));
  if (state.view === 'list') p.set('view','list');
  if (lang === 'zh') p.set('lang','zh');
  if (record) p.set('record',record);
  return p.toString();
}
export function escapeHTML(value) { return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
export function safeURL(value) { try {const u=new URL(value); return ['https:','http:'].includes(u.protocol) ? u.href : '#';} catch {return '#';} }
