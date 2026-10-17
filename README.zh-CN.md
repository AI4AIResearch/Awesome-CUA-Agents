# Awesome Computer-Use Agents

<!-- BADGES:START -->
[![Resources](https://img.shields.io/badge/resources-2%2C556-4f46e5)](data/catalog.jsonl) [![Curated](https://img.shields.io/badge/source--reviewed-1%2C093-0e8a16)](docs/coverage.md) [![Evidence](https://img.shields.io/badge/evidence%20through-2026--10--17-1d76db)](docs/coverage.md) [![Catalog quality](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml/badge.svg)](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Website](https://img.shields.io/badge/website-awesomecua.github.io-6366f1)](https://awesomecua.github.io/)
<!-- BADGES:END -->

**面向 computer-use、GUI、浏览器和移动端智能体的可溯源数据目录。**

[浏览](#浏览) · [使用数据](#使用数据) · [网站](https://awesomecua.github.io/) · [中文主页](https://awesomecua.github.io/zh/) · [GitHub 组织](https://github.com/AwesomeCUA) · [English](README.md) · [覆盖台账](docs/coverage.md) · [参与贡献](CONTRIBUTING.md)

**供人、RAG 系统和智能体使用——克隆完整目录：**

```sh
git clone https://github.com/reacher-z/Awesome-CUA.git
```

[Agent 操作指南](AGENTS.md) · [RAG 与智能体指南](https://awesomecua.github.io/agents/) · [完整 JSONL](https://awesomecua.github.io/downloads/catalog.jsonl) · [检索文档](https://awesomecua.github.io/downloads/rag-documents.jsonl)

目标是全面覆盖公开的研究和产业资源，并提供可检查的来源证据。论文、模型、训练数据、评测环境、框架、基础设施、产品和发布方都收录在同一个可检索目录中。

**“全球最全”是建设目标，而不是已经核实的结论。** 我们公开来源范围、审阅状态和剩余缺口。核实书目元数据不等于审阅了资源的相关性或质量。

使用 `python3 scripts/catalog.py get arxiv:2404.07972 --related --json` 可按稳定 ID 取得完整记录与已核实关联。[BibTeX](https://awesomecua.github.io/downloads/citations.bib) 和 [CSL JSON](https://awesomecua.github.io/downloads/citations.csl.json) 提供已审阅论文引用；每条资源页面也有可直接读取的 `record.json`。

<!-- STATS:START -->

**2,556 resource records** · **1,093 curated** · **2,164 arXiv records** · **44 discovery documents**

Evidence through `2026-10-17T09:27:51+00:00`. 1,463 records have bibliographic verification only; 1,394 discovered identifiers remain unresolved. 100 scope exclusions retain their original metadata in the archive. Counts overlap as explained below.

<!-- STATS:END -->

## 浏览

- **研究与综述：** [按主题浏览研究](docs/topics.md)、[完整论文目录](docs/papers.md)、[综述](docs/surveys.md)。
- **训练与评测：** [数据集](docs/datasets.md)、[基准](docs/benchmarks.md)、[模型与权重版本](docs/models.md)。
- **工程与产业：** [智能体](docs/agents.md)、[框架](docs/frameworks.md)、[基础设施](docs/infrastructures.md)、[工具](docs/tools.md)、[产品](docs/products.md)、[发布方与品牌](docs/companies.md)。

覆盖 Web、桌面、Android、iOS、Windows、macOS、Linux 和跨平台工作。主题包括 grounding、屏幕理解、规划、记忆、长流程任务、强化学习、数据生成、安全、鲁棒性和评测。环境分面可以重叠；不会根据模型的基准成绩推定框架支持。

英文 README 的 [Highlights](README.md#highlights) 按类别列出被其他已收录资源提及最多的已审阅资源。该计数反映目录内部的关联程度，不代表质量、流行度或基准表现；每个类别页面都列出全部已审阅条目。

英文 README 的 [Recently reviewed](README.md#recently-reviewed) 按时间倒序列出最新通过编辑审阅的模型、数据集、基准、系统和工具；新论文按日期列在[主题页面](docs/topics.md)中。

## 使用数据

打开[交互式网站](https://awesomecua.github.io/)，可以搜索和筛选全部资源、查看来源证据、切换中英文界面，或下载完整目录。网站开发与发布见 [website.md](docs/website.md)。

[已审阅研究](https://awesomecua.github.io/papers/) · [Computer-use agent 指南](https://awesomecua.github.io/guides/) · [静态资源目录](https://awesomecua.github.io/catalog/) · [搜索与 AI 发现](docs/search-discovery.md)

- **[目录 JSONL](data/catalog.jsonl)：** 每行一个资源，包含稳定 ID、类型化字段、来源证据、按范围区分的许可和审阅状态。
- **[引用图](data/references.jsonl)：** 一手来源中的对外引用。`mentions` 不等于 `trained_on` 或 `evaluated_on`。
- **[发现来源登记](data/sources.json)** 和 **[候选条目](data/candidates.jsonl)：** 来源快照，以及每个标识符的发现位置。
- **[待审队列](data/review-queue.jsonl)：** 未解决的证据、尚未收录的发现，以及需要编辑处理的提议。
- **[JSON Schema](schemas/resource.schema.json)** 和 **[覆盖度 JSON](data/coverage.json)：** 可机器检查的数据契约和覆盖度统计。

```bash
# Python 3.11+。搜索和导出只需要标准库。
cd Awesome-CUA
python3 scripts/catalog.py search "grounding" --kind model
python3 scripts/catalog.py search --kind dataset --environment android
python3 scripts/catalog.py search --kind product --status curated --json
python3 scripts/catalog.py get arxiv:2404.07972 --related --json
python3 scripts/catalog.py build
# 生成 dist/catalog.sqlite 和 dist/catalog.json，不发起网络请求。
python3 scripts/export_rag.py --output dist/rag-documents.jsonl
python3 scripts/export_citations.py --format bibtex --output dist/citations.bib
# 加 --include-metadata 可包含全部当前记录，并保留各自的审阅状态。
```

用 SQLite 联查资源、环境/主题分面和已审阅关系，示例见[查询指南](docs/query-guide.md)。`data/catalog.jsonl` 已提交到仓库；SQLite 和 JSON 数组导出是可复现的本地构建产物。

## “已核实”的含义

| 状态 | 已检查的内容 | 尚未确认的内容 |
| --- | --- | --- |
| `curated` | 基于一手来源快照的 AI 辅助编辑审阅，涵盖名称、范围、摘要和分类 | 独立复现、普遍可用性或背书 |
| `metadata_verified` | arXiv 返回的书目身份、标题、作者和日期 | 主题相关性、方法、结论，或是否属于核心领域 |
| `candidate` | 发现了规范化的 URL 或标识符 | 是否收录、是否正确或是否可用；不计入公开目录 |

计数指的是**资源**，而不是独立项目。论文、仓库、数据集发布、模型权重版本、产品和发布方可以是彼此关联的不同资源。模型系列与具体权重版本在审阅后会显式关联。

代码、数据、权重和文档的许可分别记录。缺失值为 `null`。数据集归档文件数不会被换算成训练样本数。来自不同基准版本、数据划分、动作预算或评测器的分数不会合并成排行榜。

## 维护与验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/catalog.py validate
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/catalog.py build --check
```

网络发现和核实需要显式运行相应命令；常规构建不联网。一手来源快照发生变化后，必须重新进行编辑审阅才能发布。[维护指南](docs/maintenance.md) · [方法说明](docs/methodology.md) · [数据字典](docs/data-dictionary.md)

## 致谢与复用

[来源登记](data/sources.json)列出了用于发现资源的社区合集和综述。目录从 arXiv 获取权威书目元数据，并对照发布方的仓库、文档以及模型/数据集卡片核查部分资源。上游 README、论文、模型权重和数据集不在本仓库中再分发。

本仓库的原创代码和标注采用 [MIT 许可](LICENSE)。被链接的资源保留各自的条款；本仓库不对其重新授权。
