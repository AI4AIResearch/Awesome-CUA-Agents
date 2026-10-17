import { KIND_ORDER, PAGE_SIZE, normalize, matches, filtered, parseState, serializeState, escapeHTML as e, safeURL } from './catalog-core.js';

const TEXT = {
  en: {
    navPapers:'Papers',navGuides:'Guides',navExplore:'Explore',navCoverage:'Coverage',navAbout:'About',eyebrow:'A FIELD GUIDE TO COMPUTER-USE AGENTS',heroLine1:'The next interface',heroLine2:'is an agent.',heroDescription:'Explore the research, models, data, and tools teaching AI to use computers. One connected index. Every resource traced to its source.',exploreButton:'Explore the catalog',getData:'Get the data',heroCaption:'Built for researchers, builders, and the curious.',mapLabel:'ONE FIELD. MANY SURFACES.',webLabel:'Web',webCaption:'Navigate & interact',desktopLabel:'Desktop',desktopCaption:'Work across apps',mobileLabel:'Mobile',mobileCaption:'Understand & act',mapFoot:'OBSERVE',reason:'REASON',act:'ACT',resources:'Resources indexed',curatedResources:'Editorially reviewed',categories:'Resource categories',discoverySources:'Discovery documents',snapshot:'DATA SNAPSHOT',viewCoverage:'View coverage',catalogEyebrow:'THE ECOSYSTEM, ORGANIZED',catalogTitle:'Find your next building block.',suggest:'Suggest a resource',browseByType:'BROWSE BY TYPE',useDataTitle:'Made to build on.',useDataCopy:'Take the catalog with you. Structured records, source evidence, and clear review states.',downloadData:'Download the data',searchLabel:'Search the catalog',searchPlaceholder:'Search papers, agents, models, datasets…',platform:'Platform',allPlatforms:'All platforms',review:'Review',allStates:'All states',curated:'Curated',metadata:'Bibliography',topic:'Topic',allTopics:'All topics',clearFilters:'Reset filters',try:'Try',grounding:'GUI grounding',rl:'Reinforcement learning',safety:'Safety & security',loading:'Loading the catalog…',sortBy:'Sort results',curatedFirst:'Curated first',nameSort:'Name A–Z',newest:'Newest publication',errorTitle:'The catalog could not be loaded.',errorCopy:'Check your connection and try again.',retry:'Try again',emptyTitle:'No resources match these filters.',emptyCopy:'Try a broader term or clear a filter. Many papers have not yet been assigned platform or topic tags.',catalogFootnote:'Curated means reviewed against a primary source. Bibliography means title, authors, and dates were verified; relevance and findings still need review.',coverageEyebrow:'TRACEABLE BY DESIGN',coverageTitle:'A useful index earns your trust.',coverageCopy:'You should know what has been checked, where it came from, and what is still missing. We make those boundaries visible.',coverageButton:'Inspect the coverage ledger',principle1Title:'Follow the evidence',principle1Copy:'Every record points to a first-party source, with a retrieval date and content fingerprint.',principle2Title:'Keep the distinctions',principle2Copy:'Papers are not projects. Code licenses are not data licenses. A model checkpoint is not a model family.',principle3Title:'Make the gaps visible',principle3Copy:'Comprehensive coverage is our goal. The unreviewed queue and source boundaries stay visible along the way.',aboutEyebrow:'AN OPEN FIELD DESERVES AN OPEN MAP',aboutTitle:'Help map what comes next.',aboutCopy:'Found a paper, dataset, tool, or a detail we missed? Add your knowledge to the computer-use community.',contribute:'Contribute a resource',footerCopy:'A source-backed map of the computer-use ecosystem.',methodology:'Methodology',allResources:'All resources',showing:'resources',previous:'← Previous',next:'Next →',page:'Page',of:'of',openSource:'Visit primary source',copyLink:'Copy link',copied:'Link copied',copyFailed:'Copy the URL from your address bar.',verified:'Evidence checked',published:'Published',unassigned:'Unassigned platform',topics:'Topics',authors:'Authors',licenses:'License declarations',code:'Code',data:'Data',weights:'Weights',document:'Document',unknown:'Not recorded',evidence:'Source evidence',notes:'Notes & scope',details:'Resource facts',relations:'Related resources',viewRecord:'View record',sourceLanguage:'Original source metadata',scopeCore:'Core resource',scopeAdjacent:'Adjacent resource',scopePending:'Relevance not reviewed',fullCatalog:'Full catalog · JSONL',fullCatalogCopy:'All records, evidence, licenses, and relationships.',sqlite:'SQL database · SQLite',sqliteCopy:'Resources, facets, reviewed relations, and full-text search.',coverageFile:'Coverage ledger · JSON',coverageFileCopy:'Source populations, review states, and known gaps.',sourcesFile:'Discovery sources · JSON',sourcesFileCopy:'Attribution and URLs for the discovery documents.',downloadTitle:'The index is yours to use.',downloadCopy:'These downloads contain catalog metadata, not model weights, papers, or training datasets. Follow the primary links for the original assets.',licenseNote:'Original catalog code and annotations use the MIT license. Linked assets keep their own terms.',coverageDialogTitle:'What is in the index?',coverageDialogCopy:'Counts describe resources, not independent projects. A paper, a repository, and a model checkpoint can be separate related records. Source populations overlap.',unindexed:'Unresolved identifiers',excluded:'Scope exclusions',exclusionCopy:'Reviewed exclusions are outside the active index. Original bibliographic snapshots remain in the archive.',exclusionFile:'Scope decisions and evidence',archiveFile:'Raw arXiv metadata archive',source:'Discovery document',indexed:'Indexed',discovered:'Found',limitations:'Known boundaries',boundaries:'Most bibliography entries still need relevance review. Closed assets and work missing from the discovery sources are not exhaustively represented. Global completeness has not been established.',reviewExplanation:'Curated entries receive AI-assisted editorial review against a primary source. Metadata-only entries have verified bibliographic facts, not verified methods or findings.',sourceEmpty:'No source evidence recorded.',noTaxonomy:'Platform and topic tagging is still pending for this bibliography entry.',licenseCaution:'Public access does not imply a permissive license. Code, data, weights, and document declarations are recorded separately.',referenceDate:'Retrieved',recordID:'Record ID',curatedBadge:'Source reviewed',metadataBadge:'Metadata checked',errorDetail:'This record could not be loaded. Please try again.',noRecord:'This resource is not in the current snapshot.'
  },
  zh: {
    navPapers:'论文',navGuides:'指南',navExplore:'资源目录',navCoverage:'覆盖范围',navAbout:'关于',eyebrow:'COMPUTER-USE AGENT 全景资源指南',heroLine1:'下一个交互界面，',heroLine2:'是智能体。',heroDescription:'探索让 AI 操作电脑的论文、模型、数据与工具。把分散的知识连接起来，让每一条资源都有据可查。',exploreButton:'探索资源目录',getData:'获取完整数据',heroCaption:'为研究者、开发者和每一位探索者而建。',mapLabel:'一个领域，多种交互环境。',webLabel:'浏览器',webCaption:'浏览、理解与交互',desktopLabel:'桌面',desktopCaption:'跨应用完成工作',mobileLabel:'移动设备',mobileCaption:'感知界面，执行操作',mapFoot:'观察',reason:'推理',act:'行动',resources:'已收录资源',curatedResources:'已编辑审阅',categories:'资源分类',discoverySources:'发现来源文档',snapshot:'数据快照',viewCoverage:'查看覆盖范围',catalogEyebrow:'连接整个 COMPUTER-USE 生态',catalogTitle:'找到你的下一个构建模块。',suggest:'推荐资源',browseByType:'按类型浏览',useDataTitle:'让知识继续生长。',useDataCopy:'把资源目录带入你的工作：结构化记录、来源证据和清晰的审阅状态。',downloadData:'下载数据',searchLabel:'搜索资源目录',searchPlaceholder:'搜索论文、智能体、模型、数据集…',platform:'平台',allPlatforms:'全部平台',review:'审阅',allStates:'全部状态',curated:'已审阅',metadata:'论文元数据',topic:'主题',allTopics:'全部主题',clearFilters:'重置筛选',try:'试试',grounding:'GUI 定位',rl:'强化学习',safety:'安全与防护',loading:'正在加载资源目录…',sortBy:'结果排序',curatedFirst:'已审阅优先',nameSort:'名称 A–Z',newest:'论文发表时间',errorTitle:'暂时无法加载目录。',errorCopy:'请检查网络连接后重试。',retry:'重新加载',emptyTitle:'没有符合条件的资源。',emptyCopy:'试试更宽泛的关键词，或清除部分筛选。很多论文的主题和平台尚未完成标注。',catalogFootnote:'「已审阅」表示已对照一手来源进行编辑审阅。「论文元数据」仅核实了标题、作者和日期，相关性与研究结论仍待审阅。',coverageEyebrow:'每一条记录都有迹可循',coverageTitle:'可靠的目录，经得起追问。',coverageCopy:'哪些信息已经检查？来自哪里？还有什么缺口？这些边界都应清楚可见。',coverageButton:'查看覆盖台账',principle1Title:'追溯一手证据',principle1Copy:'每条记录都指向一手来源，并保留获取日期与内容指纹。',principle2Title:'保留必要的区分',principle2Copy:'论文不等于项目，代码许可不等于数据许可，模型权重版本也不等于模型家族。',principle3Title:'让缺口清晰可见',principle3Copy:'全面覆盖是建设目标。待审队列与来源边界始终公开记录。',aboutEyebrow:'开放的领域，需要开放的知识地图',aboutTitle:'一起补全下一块拼图。',aboutCopy:'发现了遗漏的论文、数据集、工具或信息错误？把你的知识带给 Computer-Use 社区。',contribute:'贡献一条资源',footerCopy:'有来源可查的 Computer-Use 生态地图。',methodology:'收录方法',allResources:'全部资源',showing:'条资源',previous:'← 上一页',next:'下一页 →',page:'第',of:'/',openSource:'访问一手来源',copyLink:'复制链接',copied:'链接已复制',copyFailed:'请复制浏览器地址栏中的链接。',verified:'证据核验日期',published:'发表日期',unassigned:'平台待标注',topics:'研究主题',authors:'作者',licenses:'许可声明',code:'代码',data:'数据',weights:'模型权重',document:'文档',unknown:'尚未记录',evidence:'来源证据',notes:'说明与范围',details:'资源规格',relations:'关联资源',viewRecord:'查看记录',sourceLanguage:'保留原始资料语言',scopeCore:'核心资源',scopeAdjacent:'相关基础资源',scopePending:'相关性待审阅',fullCatalog:'完整目录 · JSONL',fullCatalogCopy:'全部资源、来源证据、许可与关联关系。',sqlite:'可查询数据库 · SQLite',sqliteCopy:'资源、标签、已审阅关系与全文搜索。',coverageFile:'覆盖台账 · JSON',coverageFileCopy:'来源范围、审阅状态与已知缺口。',sourcesFile:'发现来源 · JSON',sourcesFileCopy:'发现资料的归属信息与原始链接。',downloadTitle:'把这份目录带入你的工作。',downloadCopy:'下载内容是资源元数据，不包含模型权重、论文全文或训练数据集。请通过一手来源获取原始资产。',licenseNote:'原创代码与目录注释使用 MIT 许可。所链接的资产保留各自的许可条款。',coverageDialogTitle:'目录里有哪些内容？',coverageDialogCopy:'数量以资源为单位，不代表独立项目数。一篇论文、一个仓库和一个模型权重版本可以分别收录。不同发现来源的条目互有重叠。',unindexed:'待核实标识',excluded:'范围排除',exclusionCopy:'经过范围审阅的排除项不计入当前目录，原始书目快照保留在档案中。',exclusionFile:'排除决定与来源',archiveFile:'原始 arXiv 元数据档案',source:'发现来源文档',indexed:'已收录',discovered:'发现数',limitations:'已知边界',boundaries:'多数论文尚待相关性审阅。闭源资产、未发表成果，以及发现来源之外的资料仍未全面覆盖。目前不能证明已达到全球最全。',reviewExplanation:'已审阅条目经过 AI 辅助的一手来源编辑审阅。论文元数据核实的是书目信息，不表示实验方法或结论经过验证。',sourceEmpty:'尚未记录来源证据。',noTaxonomy:'这篇论文的平台和主题仍待标注。',licenseCaution:'可公开访问不代表可自由使用。代码、数据、权重和文档的许可分别记录。',referenceDate:'获取日期',recordID:'资源 ID',curatedBadge:'已审阅来源',metadataBadge:'元数据已核验',errorDetail:'暂时无法加载此条目，请重试。',noRecord:'当前数据快照中没有此条目。'
  }
};
const KINDS = {paper:['Papers','论文','▤'],survey:['Surveys','综述','≋'],model:['Models','模型','◈'],dataset:['Datasets','数据集','▦'],benchmark:['Benchmarks','评测基准','◎'],agent:['Agents','智能体','↗'],framework:['Frameworks','框架','◇'],infrastructure:['Infrastructure','基础设施','▧'],tool:['Tools','工具','⚒'],product:['Products','产品','□'],company:['Publishers','发布方','⌂']};
const PLATFORMS = {'harmonyos':['HarmonyOS','鸿蒙'],web:['Web','浏览器'],desktop:['Desktop','桌面'],android:['Android','Android'],ios:['iOS','iOS'],windows:['Windows','Windows'],macos:['macOS','macOS'],linux:['Linux','Linux'],'cross-platform':['Cross-platform','跨平台'],unspecified:['Unassigned','待标注']};
const TOPICS = {'world-models':['World models','世界模型'],'grounding':['GUI grounding','GUI 定位'],'reinforcement-learning':['Reinforcement learning','强化学习'],'safety-security':['Safety & security','安全与防护'],'planning':['Planning','规划'],'data-generation':['Data generation','数据生成'],'screen-understanding':['Screen understanding','界面理解'],'evaluation':['Evaluation','评测'],'mobile-navigation':['Mobile navigation','手机操作'],'web-navigation':['Web navigation','网页导航'],'workflow':['Workflows','工作流'],'memory':['Memory','记忆'],'long-horizon':['Long-horizon tasks','长任务'],'robustness':['Robustness','鲁棒性'],'sandbox':['Sandboxes','沙箱'],'tool-integration':['Tool integration','工具集成'],'automation':['Automation','自动化'],'cross-app':['Cross-app','跨应用'],'efficiency':['Efficiency','效率'],'video':['Video','视频'],'recording':['Recording','录制'],'human-in-the-loop':['Human in the loop','人机协作'],'observability':['Observability','可观测性'],'science':['Scientific workflows','科学工作流'],'history':['Historical','历史'],'survey':['Survey','综述'],'industry':['Industry','产业']};
Object.assign(TOPICS, {
  'action-prediction':['Action prediction','动作预测'],
  'imitation-learning':['Imitation learning','模仿学习'],
  'reward-models':['Reward models','奖励模型'],
  'self-reflection':['Self-reflection','自我反思'],
  'state-tracking':['State tracking','状态追踪'],
  'training-free':['Training-free methods','无需训练的方法'],
  'ui-design':['UI design','界面设计']
});
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
let lang = new URLSearchParams(location.search).get('lang') === 'zh' ? 'zh' : 'en';
if (!new URLSearchParams(location.search).has('lang')) {try {if (localStorage.getItem('cua-language') === 'zh') lang='zh';} catch {}}
const t = key => TEXT[lang][key] || TEXT.en[key] || key;
const label = (dict,key) => dict[key]?.[lang === 'zh' ? 1 : 0] || key;
const num = n => Number(n).toLocaleString(lang === 'zh' ? 'zh-CN' : 'en-US');
let state = parseState(location.search), records = [], report, dataPromise, activeRecord='', loading=true, toastTimer;
const dates = value => value ? new Date(value.length === 10 ? value+'T00:00:00Z' : value).toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US',{year:'numeric',month:'short',day:'numeric',timeZone:'UTC'}) : t('unknown');
function updateURL() {const query=serializeState(state,lang,activeRecord); history.replaceState(null,'',location.pathname+(query?'?'+query:'')+location.hash);}
function toast(message) {clearTimeout(toastTimer);$('#toast').textContent=message;$('#toast').hidden=false;toastTimer=setTimeout(()=>$('#toast').hidden=true,2600);}
function translate() {
  document.documentElement.lang=lang==='zh'?'zh-CN':'en';
  $$('[data-i18n]').forEach(el=>el.textContent=t(el.dataset.i18n));
  $$('[data-placeholder]').forEach(el=>el.placeholder=t(el.dataset.placeholder));
  $('#language').textContent=lang==='zh'?'EN':'中文';
  if(report) $('#snapshot-date').textContent=dates(report.as_of_utc);
  fillSelects();
}
function fillSelects() {
  $('#platform').innerHTML=`<option value="">${e(t('allPlatforms'))}</option>`+Object.keys(PLATFORMS).map(key=>`<option value="${e(key)}">${e(label(PLATFORMS,key))}</option>`).join('');
  const topics=[...new Set(records.flatMap(r=>r.topics))].sort((a,b)=>label(TOPICS,a).localeCompare(label(TOPICS,b)));
  $('#topic').innerHTML=`<option value="">${e(t('allTopics'))}</option>`+topics.map(key=>`<option value="${e(key)}">${e(label(TOPICS,key))}</option>`).join('');
  syncControls();
}
function syncControls() {$('#search').value=state.q;$('#platform').value=state.platform;$('#review').value=state.review;$('#topic').value=state.topic;$('#sort').value=state.sort;}
function change(patch,scroll=false) {
  Object.assign(state,{page:1},patch);syncControls();render();updateURL();
  if(scroll) $('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
}
function renderCategories() {
  const eligible=records.filter(r=>matches(r,state,true));
  const counts=Object.fromEntries(KIND_ORDER.map(k=>[k,0]));eligible.forEach(r=>counts[r.kind]++);
  const item=(kind,name,icon,count)=>`<button type="button" class="category-button" data-kind="${kind}" aria-pressed="${state.kind===kind}"><span class="category-icon" aria-hidden="true">${icon}</span><span>${e(name)}</span><span class="category-count">${num(count)}</span></button>`;
  $('#categories').innerHTML=item('',t('allResources'),'⊞',eligible.length)+KIND_ORDER.map(k=>item(k,label(KINDS,k),KINDS[k][2],counts[k])).join('');
}
function card(r) {
  const initials = r.name.split(/[\s-]+/).slice(0,2).map(x=>x[0] || '').join('').toUpperCase();
  const curated=r.review_status==='curated';
  const summary=r.summary || (r.authors.slice(0,3).join(' · ')+(r.authors.length>3?' et al.':'')+(r.published_at?' · '+r.published_at.slice(0,4):''));
  const tags=r.environments.filter(x=>x!=='unspecified').slice(0,2).map(x=>label(PLATFORMS,x));
  if(!tags.length && r.published_at) tags.push(r.published_at.slice(0,4),'arXiv');
  if(curated && r.topics.length && tags.length<3) tags.push(label(TOPICS,r.topics[0]));
  return `<article class="resource-card" data-kind="${e(r.kind)}"><div class="card-top"><div class="resource-monogram" aria-hidden="true">${e(initials)}</div><span class="kind-chip">${e(label(KINDS,r.kind))}</span></div><h3 class="card-title"><a href="${e(r.page_url)}" data-record="${e(r.id)}">${e(r.name)}</a></h3><p class="resource-summary ${curated?'':'is-bibliography'}">${e(summary)}</p><div class="card-tags">${tags.map(x=>`<span>${e(x)}</span>`).join('')}</div><div class="card-bottom ${curated?'is-curated':''}"><span class="review-dot"></span><span>${e(t(curated?'curatedBadge':'metadataBadge'))}</span><a class="card-external" href="${e(safeURL(r.url))}" target="_blank" rel="noopener noreferrer" aria-label="${e(t('openSource'))}: ${e(r.name)}">↗</a></div></article>`;
}
function render() {
  if(loading) return;
  renderCategories();
  const result=filtered(records,state), pages=Math.max(1,Math.ceil(result.length/PAGE_SIZE));
  state.page=Math.min(state.page,pages);
  const begin=(state.page-1)*PAGE_SIZE;
  $('#results').innerHTML=result.slice(begin,begin+PAGE_SIZE).map(card).join('');
  $('#results').classList.toggle('list-view',state.view==='list');
  $('#view-grid').setAttribute('aria-pressed',String(state.view==='grid'));$('#view-list').setAttribute('aria-pressed',String(state.view==='list'));
  $('#results-count').innerHTML=`<strong>${num(result.length)}</strong> ${e(t('showing'))}${state.kind?' <span> / '+e(label(KINDS,state.kind))+'</span>':''}`;
  $('#results').setAttribute('aria-busy','false');$('#empty').hidden=result.length!==0;
  $('#clear-filters').hidden=![state.q,state.kind,state.platform,state.review,state.topic].some(Boolean);
  $('#pagination').hidden=result.length===0;
  $('#pagination').innerHTML=`<button type="button" data-page="${state.page-1}" ${state.page===1?'disabled':''}>${e(t('previous'))}</button><span>${e(t('page'))} ${state.page} ${e(t('of'))} ${pages}</span><button type="button" data-page="${state.page+1}" ${state.page===pages?'disabled':''}>${e(t('next'))}</button>`;
}
async function load() {
  loading=true;$('#load-error').hidden=true;$('#results').setAttribute('aria-busy','true');$('#results-count').textContent=t('loading');$('#results').innerHTML=Array.from({length:6},()=>'<div class="skeleton-card" aria-hidden="true"></div>').join('');
  try {
    const response=await fetch('./data/index.json');if(!response.ok)throw new Error('HTTP '+response.status);
    const data=await response.json();report=data.coverage;records=data.records;
    records.forEach(r=>r.search_text=normalize([r.name,r.summary,...r.aliases,...r.authors,...r.environments.flatMap(x=>PLATFORMS[x] || [x]),...r.topics.flatMap(x=>TOPICS[x] || [x]),...(KINDS[r.kind] || [])].filter(Boolean).join(' ')));
    if(!Object.hasOwn(PLATFORMS,state.platform))state.platform='';
    if(!records.some(r=>r.topics.includes(state.topic)))state.topic='';
    $('#stat-resources').textContent=num(records.length);$('#stat-curated').textContent=num(report.curated_records);$('#stat-kinds').textContent=num(Object.keys(report.by_kind).length);$('#stat-sources').textContent=num(report.sources.length);
    loading=false;translate();render();updateURL();
    const rid=new URLSearchParams(location.search).get('record');if(rid)await showRecord(rid,false);
  } catch(error) {loading=false;$('#results').innerHTML='';$('#results').setAttribute('aria-busy','false');$('#load-error').hidden=false;$('#results-count').textContent='';console.error('Catalog loading failed:',error);}
}
async function getDetails() {if(!dataPromise)dataPromise=fetch('./data/records.json').then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).catch(error=>{dataPromise=null;throw error;});return dataPromise;}
const external=(url,text)=>`<a href="${e(safeURL(url))}" target="_blank" rel="noopener noreferrer">${e(text)} ↗</a>`;
function resourceFacts(details) {
  const labels={sample_count:['Sample count','样本数'],sample_unit:['Sample unit','样本单位'],screen_count:['Screen count','界面数量'],example_count:['Example count','示例数量'],modalities:['Modalities','数据模态'],languages:['Languages','语言'],gated:['Access gated','访问需申请'],disabled:['Disabled on Hub','Hub 已停用'],hub_id:['Hub identifier','Hub 标识'],download_url:['Download location','下载入口'],size_category_reported:['Publisher size category','发布方规模分类'],reported_scale:['Reported scale','发布方描述规模'],artifact_type:['Artifact type','资产类型'],task_count:['Task count','任务数量'],task_unit:['Task unit','任务单位'],metrics:['Metrics','评测指标'],evaluation_type:['Evaluation method','评测方式'],access:['Access','访问方式'],pricing_url:['Pricing','价格页面'],availability:['Availability','可用性'],leaderboard_url:['Leaderboard','排行榜']};
  const value=v=>typeof v==='boolean'?(lang==='zh'?(v?'是':'否'):(v?'Yes':'No')):Array.isArray(v)?v.join(' · '):typeof v==='object'?Object.entries(v).map(([k,x])=>k==='value'?num(x):String(x)).join(' '):typeof v==='number'?num(v):String(v);
  return '<dl class="fact-list">'+Object.entries(details).filter(([,v])=>v!==null&&v!==''&&(!Array.isArray(v)||v.length)).map(([key,v])=>'<div><dt>'+e(label(labels,key))+'</dt><dd>'+(key.endsWith('_url')&&typeof v==='string'?external(v,lang==='zh'?'打开链接':'Open link'):e(value(v)))+'</dd></div>').join('')+'</dl>';
}
async function showRecord(id,setURL=true) {
  const found=records.find(r=>r.id===id);if(!found){toast(t('noRecord'));return;}
  activeRecord=id;if(setURL)updateURL();
  $('#detail-overline').textContent=label(KINDS,found.kind);
  $('#detail-content').innerHTML=`<h2 id="detail-title">${e(found.name)}</h2><p>${e(t('loading'))}</p>`;
  if(!$('#detail-dialog').open)$('#detail-dialog').showModal();
  try {
    const full=await getDetails();if(activeRecord!==id)return;const r=full.find(row=>row.id===id);if(!r)throw new Error('Record absent');
    const scope={core:'scopeCore',adjacent:'scopeAdjacent',relevance_pending:'scopePending'}[r.scope];
    let content=`<h2 id="detail-title">${e(r.name)}</h2><p class="detail-description">${e(r.summary || t('noTaxonomy'))}</p><div class="detail-badges"><span>${e(t(r.review_status==='curated'?'curated':'metadata'))}</span><span>${e(t(scope))}</span>${r.environments.filter(x=>x!=='unspecified').map(x=>`<span>${e(label(PLATFORMS,x))}</span>`).join('')}</div><div class="detail-actions"><a class="button primary" href="${e(safeURL(r.url))}" target="_blank" rel="noopener noreferrer">${e(t('openSource'))} ↗</a><button class="button secondary" type="button" data-copy-link>${e(t('copyLink'))} ⧉</button><a class="resource-page-link" href="${e(found.page_url)}">${lang==='zh'?'打开完整资源页':'Open full resource page'} ↗</a></div><div class="detail-dates"><div>${e(t('verified'))}<strong>${e(dates(r.last_verified_at))}</strong></div>${r.published_at?`<div>${e(t('published'))}<strong>${e(dates(r.published_at))}</strong></div>`:''}</div>`;
    if(r.topics.length)content+=`<section class="detail-section"><h3>${e(t('topics'))}</h3><p>${r.topics.map(x=>e(label(TOPICS,x))).join(' · ')}</p></section>`;
    if(r.authors.length)content+=`<section class="detail-section"><h3>${e(t('authors'))}</h3><p>${r.authors.map(e).join(', ')}</p></section>`;
    if(r.kind!=='paper'&&r.kind!=='survey')content+=`<section class="detail-section"><h3>${e(t('licenses'))}</h3><div class="license-grid">${['code','data','weights','document'].map(slot=>{const l=r.licenses[slot];return `<div class="license-item"><span>${e(t(slot))}</span>${l?external(l.url,Array.isArray(l.declared)?l.declared.join(', '):l.declared):e(t('unknown'))}</div>`;}).join('')}</div><p>${e(t('licenseCaution'))}</p></section>`;
    if(Object.values(r.details).some(v=>v!==null&&v!==''&&(!Array.isArray(v)||v.length)))content+=`<section class="detail-section"><h3>${e(t('details'))}</h3>${resourceFacts(r.details)}</section>`;
    if(r.notes)content+=`<section class="detail-section"><h3>${e(t('notes'))}</h3><p>${e(r.notes)}</p></section>`;
    if(r.relations.length)content+=`<section class="detail-section"><h3>${e(t('relations'))}</h3><ul>${r.relations.map(rel=>{const target=records.find(row=>row.id===rel.target_id);return `<li>${e(rel.type.replaceAll('_',' '))} → <button class="subtle-link" type="button" data-record="${e(rel.target_id)}">${e(target?.name || rel.target_id)}</button></li>`;}).join('')}</ul></section>`;
    const connected=full.flatMap(source=>source.relations.filter(rel=>rel.target_id===r.id).map(rel=>({source,relation:rel})));
    if(connected.length)content+=`<section class="detail-section"><h3>${lang==='zh'?'关联资产':'Connected assets'}</h3><ul>${connected.map(({source,relation})=>`<li><a class="subtle-link" href="${e(records.find(x=>x.id===source.id)?.page_url || '#')}" data-record="${e(source.id)}">${e(source.name)}</a> · ${e(label(KINDS,source.kind))} · ${external(relation.evidence_url,lang==='zh'?'关联证据':'Evidence')}</li>`).join('')}</ul></section>`;
    content+=`<section class="detail-section"><h3>${e(t('evidence'))}</h3>${r.evidence.map(ev=>`<div class="evidence-item">${external(ev.url,new URL(ev.url).hostname)}<p>${e(t('referenceDate'))}: ${e(dates(ev.retrieved_at))} · ${e(ev.method.replaceAll('_',' '))}</p><details><summary>SHA-256</summary><p class="detail-meta">${e(ev.sha256)}</p></details></div>`).join('')}</section><section class="detail-section"><h3>${e(t('recordID'))}</h3><div class="detail-meta">${e(r.id)}</div></section>`;
    $('#detail-content').innerHTML=content;
  }catch(error){$('#detail-content').innerHTML=`<h2 id="detail-title">${e(found.name)}</h2><p>${e(t('errorDetail'))}</p><button type="button" class="button secondary" data-record="${e(id)}">${e(t('retry'))}</button>`;}
}
function info(type) {
  if(!report)return;
  let content='';
  if(type==='download') {
    const options=[['catalog.jsonl','fullCatalog','fullCatalogCopy','JSONL'],['catalog.sqlite','sqlite','sqliteCopy','SQLite'],['coverage.json','coverageFile','coverageFileCopy','JSON'],['sources.json','sourcesFile','sourcesFileCopy','JSON']];
    content=`<h2 id="info-title">${e(t('downloadTitle'))}</h2><p>${e(t('downloadCopy'))}</p><div class="download-options">${options.map(([file,title,copy])=>`<a class="download-option" href="./downloads/${file}" download><span><strong>${e(t(title))}</strong><small>${e(t(copy))}</small></span><span>↓</span></a>`).join('')}</div><p>${e(t('licenseNote'))}</p>`;
  }else {
    content=`<h2 id="info-title">${e(t('coverageDialogTitle'))}</h2><p>${e(t('coverageDialogCopy'))}</p><div class="info-stat-grid"><div><strong>${num(report.curated_records)}</strong><span>${e(t('curatedResources'))}</span></div><div><strong>${num(report.metadata_only_records)}</strong><span>${e(t('metadata'))}</span></div><div><strong>${num(report.unindexed_candidates)}</strong><span>${e(t('unindexed'))}</span></div></div><p>${e(t('reviewExplanation'))}</p><table class="coverage-table"><thead><tr><th>${e(t('source'))}</th><th>${e(t('discovered'))}</th><th>${e(t('indexed'))}</th></tr></thead><tbody>${report.sources.map(s=>`<tr><td>${external(s.url,s.name)}</td><td>${num(s.discovered)}</td><td>${num(s.indexed)}</td></tr>`).join('')}</tbody></table><h3>${e(t('limitations'))}</h3><p>${e(t('boundaries'))}</p><a class="button secondary" href="./downloads/coverage.json" download>${e(t('coverageFile'))} ↓</a>`;
  }
  if(type!=='download' && report.excluded_records)content+=`<h3>${e(t('excluded'))}: ${num(report.excluded_records)}</h3><p>${e(t('exclusionCopy'))}</p><p><a href="./downloads/exclusions.json">${e(t('exclusionFile'))}</a> · <a href="./downloads/arxiv-archive.jsonl">${e(t('archiveFile'))}</a></p>`;
  $('#info-content').innerHTML=content;$('#info-dialog').showModal();
}
$('#search').addEventListener('input',event=>change({q:event.target.value}));
for(const [id,key] of [['platform','platform'],['review','review'],['topic','topic'],['sort','sort']])$('#'+id).addEventListener('change',event=>change({[key]:event.target.value}));
const reset=()=>change({q:'',kind:'',platform:'',review:'',topic:'',sort:'featured'});
$('#clear-filters').addEventListener('click',reset);$('#empty-reset').addEventListener('click',reset);
$('#view-grid').addEventListener('click',()=>change({view:'grid',page:state.page}));$('#view-list').addEventListener('click',()=>change({view:'list',page:state.page}));
$('#categories').addEventListener('click',event=>{const button=event.target.closest('[data-kind]');if(button)change({kind:button.dataset.kind});});
$$('[data-environment]').forEach(button=>button.addEventListener('click',()=>change({platform:button.dataset.environment,kind:'',q:''},true)));
$$('[data-search]').forEach(button=>button.addEventListener('click',()=>change({q:button.dataset.search,topic:''})));
$$('[data-topic]').forEach(button=>button.addEventListener('click',()=>change({topic:button.dataset.topic,q:''})));
document.addEventListener('click',event=>{const button=event.target.closest('[data-record]');if(!button)return;if(button.tagName==='A'&&(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button!==0))return;event.preventDefault();showRecord(button.dataset.record);});
$('#pagination').addEventListener('click',event=>{const button=event.target.closest('[data-page]');if(button&&!button.disabled){change({page:Number(button.dataset.page)});$('.results-toolbar').scrollIntoView({block:'start',behavior:'instant'});}});
$('#language').addEventListener('click',()=>{lang=lang==='en'?'zh':'en';try{localStorage.setItem('cua-language',lang);}catch{}translate();render();updateURL();if(activeRecord)showRecord(activeRecord,false);});
for(const id of ['hero-download','sidebar-download'])$('#'+id).addEventListener('click',()=>info('download'));
for(const id of ['coverage-button','footer-method'])$('#'+id).addEventListener('click',()=>info('coverage'));
$$('.dialog-close').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
$$('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}}));
$('#detail-dialog').addEventListener('close',()=>{activeRecord='';updateURL();});
$('#detail-dialog').addEventListener('click',async event=>{if(event.target.closest('[data-copy-link]')){try{await navigator.clipboard.writeText(new URL(records.find(r=>r.id===activeRecord)?.page_url || location.href,location.origin).href);toast(t('copied'));}catch{toast(t('copyFailed'));}}});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)&&!$$('dialog').some(d=>d.open)){event.preventDefault();$('#search').focus();$('#catalog').scrollIntoView({block:'start'});}});
window.addEventListener('popstate',()=>{state=parseState(location.search);const p=new URLSearchParams(location.search);lang=p.get('lang')==='zh'?'zh':'en';translate();render();const id=p.get('record');if(id)showRecord(id,false);else if($('#detail-dialog').open)$('#detail-dialog').close();});
$('#retry').addEventListener('click',load);
translate();
// Preserve a deep-linked record before normalizing the filter URL during initial loading.
activeRecord=new URLSearchParams(location.search).get('record') || '';
load();
