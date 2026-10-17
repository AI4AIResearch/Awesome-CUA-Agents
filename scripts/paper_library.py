"""Compact, fully rendered bilingual research libraries; no client script required."""
from collections import Counter, defaultdict
import html
from urllib.parse import urlencode
from publication_metadata import publication, record_date_text, record_year
from specifications import safe_href


# A fixed page size keeps each library page within the HTML byte budget as the reviewed set grows.
PAGE_SIZE = 60

PLATFORMS = {
    'web': ('Web', '网页'), 'desktop': ('Desktop', '桌面'),
    'android': ('Android', 'Android'), 'ios': ('iOS', 'iOS'),
    'linux': ('Linux', 'Linux'), 'macos': ('macOS', 'macOS'),
    'windows': ('Windows', 'Windows'), 'harmonyos': ('HarmonyOS', '鸿蒙'),
    'cross-platform': ('Cross-platform', '跨平台'),
}
TOPICS = {
    'grounding': ('GUI grounding', 'GUI 定位'),
    'evaluation': ('Evaluation', '评测'),
    'data-generation': ('Data generation', '数据生成'),
    'reinforcement-learning': ('Reinforcement learning', '强化学习'),
    'screen-understanding': ('Screen understanding', '界面理解'),
    'safety-security': ('Safety & security', '安全与防护'),
    'planning': ('Planning', '规划'), 'memory': ('Memory', '记忆'),
    'mobile-navigation': ('Mobile navigation', '手机操作'),
    'web-navigation': ('Web navigation', '网页导航'),
    'efficiency': ('Efficiency', '效率'), 'robustness': ('Robustness', '鲁棒性'),
    'long-horizon': ('Long-horizon tasks', '长任务'),
    'world-models': ('World models', '世界模型'),
    'tool-integration': ('Tool integration', '工具集成'),
    'workflow': ('Workflows', '工作流'), 'sandbox': ('Sandboxes', '沙箱'),
    'human-in-the-loop': ('Human in the loop', '人机协作'),
    'automation': ('Automation', '自动化'), 'recording': ('Recording', '录制'),
    'cross-app': ('Cross-app', '跨应用'), 'observability': ('Observability', '可观测性'),
    'science': ('Scientific workflows', '科学工作流'), 'video': ('Video', '视频'),
    'history': ('Historical', '历史'), 'survey': ('Surveys', '综述'),
    'interaction-history': ('Interaction history', '交互历史'),
    'industry': ('Industry', '产业'), 'self-reflection': ('Self-reflection', '自我反思'),
    'action-prediction': ('Action prediction', '动作预测'),
    'state-tracking': ('State tracking', '状态追踪'),
    'reward-models': ('Reward models', '奖励模型'),
    'imitation-learning': ('Imitation learning', '模仿学习'),
    'training-free': ('Training-free methods', '无需训练的方法'),
    'ui-design': ('Interface design', '界面设计'),
}


def esc(value):
    return html.escape(str(value), quote=True)


def library_path(number=1, language='en'):
    base = '/zh/papers/' if language == 'zh' else '/papers/'
    return base if number == 1 else f'{base}page/{number}/'


def reviewed_papers(rows):
    return sorted((r for r in rows if r['kind'] in {'paper', 'survey'}
                   and r['review_status'] == 'curated' and r['scope'] in {'core', 'adjacent'}),
                  key=lambda r: (record_date_text(r), r['id']), reverse=True)


def library_pages(rows):
    return max(1, -(-len(reviewed_papers(rows)) // PAGE_SIZE))


def library_years(rows, language='en'):
    """Map each publication year to the library page and anchor where its newest entry appears."""
    links = {}
    for i, row in enumerate(reviewed_papers(rows)):
        year = record_year(row) or 'undated'
        links.setdefault(year, library_path(i // PAGE_SIZE + 1, language) + '#papers-' + year)
    return links


def paper_library(rows, resource_path, *, language='en', site_url='https://awesomecua.github.io', number=1):
    """Return one library page's HTML and an ItemList describing exactly its visible reviewed papers."""
    zh = language == 'zh'
    def tr(en, cn):
        return cn if zh else en
    def label(mapping, key):
        return mapping.get(key, (key.replace('-', ' ').capitalize(),) * 2)[int(zh)]
    papers = reviewed_papers(rows)
    pages = library_pages(rows)
    if not 1 <= number <= pages:
        raise ValueError(f'Library page {number} is outside 1..{pages}')
    start = (number - 1) * PAGE_SIZE
    visible = papers[start:start + PAGE_SIZE]
    totals = Counter(record_year(row) or 'undated' for row in papers)
    year_links = library_years(rows, language)
    groups = defaultdict(list)
    for row in visible:
        groups[record_year(row) or 'undated'].append(row)
    topics = Counter(topic for row in papers if row['kind'] == 'paper' for topic in row['topics'])
    survey_count = sum(row['kind'] == 'survey' for row in papers)
    years = sorted(totals, reverse=True)
    if 'undated' in years:
        years.remove('undated'); years.append('undated')
    def search_link(**filters):
        return '/?' + esc(urlencode({'kind': 'paper', 'review': 'curated', 'lang': 'zh' if zh else 'en', **filters})) + '#catalog'
    title = tr('Computer-use research library', 'Computer-Use 论文库')
    title_markup = 'Computer-Use <span class="library-title-tail">论文库</span>' if zh else esc(title)
    body = ['<section class="paper-library" aria-labelledby="library-title">',
            '<div class="library-heading"><div><div class="eyebrow">RESEARCH LIBRARY</div>',
            '<h1 id="library-title">' + title_markup + '</h1></div>',
            '<a class="library-language" href="' + library_path(number, 'en' if zh else 'zh') + '">' + ('English' if zh else '中文') + '</a></div>',
            '<p class="library-intro">' + tr('Source-backed papers on GUI grounding, agents, training, evaluation, and safety.', '从 GUI 定位到智能体训练、评测与安全，每篇都可追溯到原始论文。') + '</p>',
            '<div class="library-toolbar"><p class="library-count"><strong>' + f'{len(papers):,}' + '</strong> ' + tr('reviewed papers & surveys', '篇已审阅论文与综述') + '</p>',
            '<div class="library-downloads"><a class="button primary" href="' + search_link() + '">' + tr('Search papers', '检索论文') + ' ↗</a>',
            ('<a class="button secondary" href="' + search_link(kind='survey') + '">' + tr('Surveys', '综述') + ' ' + str(survey_count) + '</a>') if survey_count else '',
            '<a class="button secondary" href="/downloads/citations.bib" download>BibTeX ↓</a>',
            '<a class="button secondary" href="/downloads/citations.csl.json" download>CSL JSON ↓</a></div></div>',
            '<nav class="paper-years" aria-label="' + tr('Jump to publication year', '按发表年份跳转') + '"><span>' + tr('YEAR', '年份') + '</span>']
    for year in years:
        link = year_links[year]
        if link.startswith(library_path(number, language) + '#'):
            link = link[link.index('#'):]
        body.append('<a href="' + link + '">' + (tr('Undated', '日期待录') if year == 'undated' else year)
                    + '<span>' + str(totals[year]) + '</span></a>')
    body.append('</nav><div class="library-topics"><span>' + tr('PAPER TOPICS', '论文主题') + '</span>')
    for topic, _count in topics.most_common(8):
        body.append('<a href="' + search_link(topic=topic) + '">' + esc(label(TOPICS, topic)) + '</a>')
    body.append('<a class="library-all-topics" href="' + ('/zh/topics/' if zh else '/topics/') + '">' + tr('All topics', '全部主题') + ' ↗</a>')
    body.append('</div><p class="library-method">' + tr('AI-assisted editorial review of primary sources; experiments are not independently reproduced. Dates keep their recorded precision.', '条目经过 AI 辅助的一手来源编辑审阅，实验未独立复现。发表日期保留来源记录的精度。') + ' <a href="/about/">' + tr('Method', '收录方法') + ' ↗</a></p>')
    for year in (year for year in years if year in groups):
        body.append('<section class="paper-year-group" aria-labelledby="papers-' + year + '"><div class="paper-year-heading"><h2 id="papers-' + year + '">' + (tr('Date not recorded', '日期待录') if year == 'undated' else year) + '</h2><span>' + str(totals[year]) + ' ' + tr('papers & surveys', '篇论文与综述') + '</span><a href="#library-title">' + tr('Back to years', '回到年份') + ' ↑</a></div>')
        for row in groups[year]:
            path = resource_path(row)
            snapshot = row.get('details', {}).get('arxiv_snapshot', {})
            source = snapshot.get('versioned_url') or row['url']
            date = record_date_text(row)
            pub = publication(row)
            body.append('<article class="paper-entry" data-resource-id="' + esc(row['id']) + '"><div class="paper-date">')
            body.append('<time datetime="' + esc(date) + '">' + esc(date) + '</time>' if len(date)==10 else '<span>' + esc(date or tr('Date unknown', '日期待录')) + '</span>')
            if snapshot.get('version'):
                body.append('<span>arXiv v' + str(snapshot['version']) + '</span>')
            elif pub and pub.get('publisher'):
                body.append('<span>' + esc(pub['publisher']) + '</span>')
            if row['kind'] == 'survey':
                body.append('<span class="paper-survey">' + tr('Survey', '综述') + '</span>')
            body.append('</div><div class="paper-entry-main"><h3><a href="' + path + '">' + esc(row['name']) + '</a></h3>')
            authors = row.get('authors', [])
            if authors:
                names = ', '.join(authors[:2])
                if len(authors) > 2:
                    names += tr(' + ' + str(len(authors) - 2) + (' author' if len(authors) == 3 else ' authors'), ' 等 ' + str(len(authors)) + ' 位作者')
                body.append('<p class="paper-authors">' + esc(names) + '</p>')
            if row.get('summary'):
                body.append('<p class="paper-annotation">' + esc(row['summary']) + '</p>')
            if pub and pub.get('venue'):
                body.append('<p class="paper-publication"><a href="' + safe_href(pub['url']) + '">' + esc(pub['venue']) + ' ↗</a></p>')
            body.append('<div class="paper-facets">')
            for platform in row['environments']:
                if platform != 'unspecified':
                    body.append('<span class="paper-platform">' + esc(label(PLATFORMS, platform)) + '</span>')
            for topic in row['topics'][:3]:
                body.append('<a href="' + search_link(kind=row['kind'],topic=topic) + '">' + esc(label(TOPICS, topic)) + '</a>')
            if row['scope'] == 'adjacent':
                body.append('<span class="paper-adjacent">' + tr('Adjacent research', '相关研究') + '</span>')
            body.append('</div></div><div class="paper-entry-links"><a href="' + safe_href(source) + '">' + tr('Paper', '原论文') + ' ↗</a><a href="' + path + 'citation.bib" download aria-label="' + esc(tr('BibTeX for ', 'BibTeX：') + row['name']) + '">BibTeX ↓</a><a href="' + path + '">' + tr('Details', '详情') + ' →</a></div></article>')
        body.append('</section>')
    if pages > 1:
        body.append('<nav class="pagination library-pager" aria-label="' + tr('Library pages', '论文库分页') + '">')
        body.append('<a href="' + library_path(number - 1, language) + '" rel="prev">' + tr('← Previous', '← 上一页') + '</a>' if number > 1 else '<span></span>')
        body.append('<span class="page-numbers">' + ''.join('<a href="' + library_path(n, language) + '" aria-label="' + tr('Page ', '第 ') + str(n) + tr('', ' 页') + '"' + (' aria-current="page"' if n == number else '') + '>' + str(n) + '</a>' for n in range(1, pages + 1)) + '</span>')
        body.append('<a href="' + library_path(number + 1, language) + '" rel="next">' + tr('Next →', '下一页 →') + '</a>' if number < pages else '<span></span>')
        body.append('</nav><p class="library-range">' + tr(f'Showing {start + 1:,}–{start + len(visible):,} of {len(papers):,}, newest first.', f'第 {start + 1:,}–{start + len(visible):,} 篇，共 {len(papers):,} 篇，按发表时间由新到旧排列。') + '</p>')
    body.append('<p class="library-footer">' + tr('Explore the complete catalog, including bibliography entries awaiting relevance review.', '完整目录还包含相关性待审阅的论文元数据，并明确标注审阅状态。') + ' <a href="/?kind=paper&amp;lang=' + ('zh' if zh else 'en') + '#catalog">' + tr('All paper records', '全部论文记录') + ' ↗</a> · <a href="/?kind=survey&amp;lang=' + ('zh' if zh else 'en') + '#catalog">' + tr('All survey records', '全部综述记录') + ' ↗</a></p></section>')
    schema = {'@type': 'ItemList', 'name': title, 'numberOfItems': len(visible),
              'itemListElement': [{'@type': 'ListItem', 'position': start + i + 1,
                                   'url': site_url + resource_path(row), 'name': row['name']}
                                  for i, row in enumerate(visible)]}
    return ''.join(body), schema
