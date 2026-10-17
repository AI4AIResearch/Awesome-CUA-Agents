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
export const FACT_LABELS = {sample_count:['Sample count','样本数'],sample_unit:['Sample unit','样本单位'],screen_count:['Screen count','界面数量'],example_count:['Example count','示例数量'],modalities:['Modalities','数据模态'],languages:['Languages','语言'],gated:['Access gated','访问需申请'],disabled:['Disabled on Hub','Hub 已停用'],hub_id:['Hub identifier','Hub 标识'],download_url:['Download location','下载入口'],size_category_reported:['Publisher size category','发布方规模分类'],reported_scale:['Reported scale','发布方描述规模'],artifact_type:['Artifact type','资产类型'],task_count:['Task count','任务数量'],task_unit:['Task unit','任务单位'],metrics:['Metrics','评测指标'],evaluation_type:['Evaluation method','评测方式'],access:['Access','访问方式'],pricing_url:['Pricing','价格页面'],availability:['Availability','可用性'],leaderboard_url:['Leaderboard','排行榜'],dataset_profile:['Dataset profile','数据集概况'],benchmark_protocol:['Evaluation protocol','评测协议'],platform_constraints:['Platform constraints','平台限制'],artifact_inspection:['Artifact inspection','资产检查范围'],base_model:['Base model','基础模型'],hub_revision:['Hub revision','Hub 修订版本'],listed_weight_files:['Listed weight files','列出的权重文件'],license_name:['License name','许可名称'],dataverse:['Dataverse release','Dataverse 发布版本'],release_tag:['Release tag','发布标签']};
const PROFILE_PARTS = {dataset_profile:['supervision','modalities','formats','splits','counts'],benchmark_protocol:['focus','setting','observations','actions','evaluation','counts']};
const PROFILE_LABELS = {supervision:['Supervision','监督信号'],modalities:['Modalities','数据模态'],formats:['Formats','文件格式'],splits:['Splits','数据划分'],focus:['Focus','评测重点'],setting:['Setting','评测设置'],observations:['Observations','观测输入'],actions:['Actions / outputs','动作 / 输出'],evaluation:['Evaluation','评测方法'],counts:['Scale','规模']};
const PREFIXES = {exact:'',approximately:'≈ ','at-least':'≥ ','more-than':'> ','>':'> ','>=':'≥ '};
export function formatDate(value, lang='en') { return new Date(value.length === 10 ? value+'T00:00:00Z' : value).toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US',{year:'numeric',month:'short',day:'numeric',timeZone:'UTC'}); }
export function formatFact(key, value, lang='en') {
  const zh=lang==='zh', num=n=>Number(n).toLocaleString(zh?'zh-CN':'en-US');
  // Nested objects are summarized or dropped; String() would render them as "[object Object]".
  const text=v=>v===null||v===undefined?'':typeof v==='boolean'?(zh?(v?'是':'否'):(v?'Yes':'No')):typeof v==='number'?num(v):Array.isArray(v)?v.map(text).filter(Boolean).join(' · '):typeof v==='object'?(typeof v.name==='string'?v.name:Object.entries(v).map(([k,x])=>[k,text(x)]).filter(([,x])=>x).map(([k,x])=>k.replaceAll('_',' ')+': '+x).join(' · ')):/^\d{4}-\d\d-\d\d(T[\d:.]+Z)?$/.test(v)?formatDate(v,lang):String(v);
  const count=c=>{const q=c.qualifier ?? c.comparison;return (PREFIXES[q] ?? (q?q+' ':''))+num(c.value)+' '+c.unit;};
  if(key==='gated'&&(value==='auto'||value==='manual')) return zh?(value==='auto'?'是（自动批准）':'是（人工审批）'):(value==='auto'?'Yes, approved automatically':'Yes, approved manually');
  if(!value||typeof value!=='object'||Array.isArray(value)) return text(value);
  if(key==='reported_scale') return count(value);
  if(key==='dataverse') return [value.publisher,value.version_number!=null&&`v${value.version_number}.${value.version_minor_number ?? 0}`,value.file_count!=null&&num(value.file_count)+(zh?' 个文件':' files'),value.license?.name,value.publication_date&&(zh?'发布于 ':'published ')+formatDate(value.publication_date,lang)].filter(Boolean).join(' · ');
  if(PROFILE_PARTS[key]) return PROFILE_PARTS[key].map(part=>[part,part==='counts'?(value.counts || []).map(c=>`${count(c)} (${c.population}${c.basis==='computed'?(zh?'，计算值':', computed'):''})`).join('; '):Array.isArray(value[part])?value[part].join(', '):text(value[part])]).filter(([,x])=>x).map(([part,x])=>PROFILE_LABELS[part][zh?1:0]+(zh?'：':': ')+x).join('\n');
  return text(value);
}
