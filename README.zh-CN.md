# Awesome Computer-Use Agents

**面向研究、训练评测和产业应用的 Computer-Use Agent 数据目录。**

[在线主页](https://awesomecua.github.io/) · [GitHub 组织](https://github.com/AwesomeCUA) · [English](README.md) · [覆盖度与缺口](docs/coverage.md)

目标是把全球公开的 GUI、浏览器、桌面和手机智能体资料整理成可检索、可追溯、可持续扩充的数据资产。论文、模型、数据集、基准、框架、基础设施、产品和发布方统一建模，并保留它们之间的关系。

<!-- STATS:START -->

**2,036 resource records** · **842 curated** · **1,694 arXiv records** · **36 discovery documents**

Evidence through `2026-10-17T02:49:45Z`. 1,194 records have bibliographic verification only; 812 discovered identifiers remain unresolved. 70 scope exclusions retain their original metadata in the archive. Counts overlap as explained below.

<!-- STATS:END -->

## 三类用途全部覆盖

- **全景研究：** [论文](docs/papers.md)、[综述](docs/surveys.md)、[模型](docs/models.md)，覆盖 grounding、规划、记忆、强化学习、长任务、安全与鲁棒性等方向。
- **训练与评测：** [数据集](docs/datasets.md)、[基准](docs/benchmarks.md)、[训练框架](docs/frameworks.md)，记录下载入口、平台、许可和能够核实的数据规格。
- **产业与工程：** [智能体](docs/agents.md)、[产品](docs/products.md)、[工具](docs/tools.md)、[基础设施](docs/infrastructures.md)、[发布方与品牌](docs/companies.md)。

## 直接使用

打开 [AwesomeCUA 网站](https://awesomecua.github.io/)，即可搜索和筛选全部资源、查看来源证据、切换中英文界面，并下载完整数据。网站构建和发布说明见 [website.md](docs/website.md)。

```bash
python3 scripts/catalog.py search "grounding" --kind model
python3 scripts/catalog.py search --kind dataset --environment android
python3 scripts/catalog.py search --kind benchmark --topic safety-security
python3 scripts/catalog.py build
```

主数据在 [data/catalog.jsonl](data/catalog.jsonl)。构建命令还会生成 `dist/catalog.sqlite` 和 `dist/catalog.json`，支持本地查询、SQL 分析和下游集成。

## 质量口径

`curated` 表示已经过 AI 辅助的编辑审阅，并绑定到一手来源快照；`metadata_verified` 仅表示官方论文元数据已核实，不代表相关性、实验或结论经过审阅；`candidate` 是待核验线索，不计入正式目录。

论文、仓库、数据集、模型权重版本、产品和发布方是不同资源，不能把它们的总数当成独立项目数。代码、数据、权重的许可分别记录；无法核实的规模、价格和许可留空。目录不把不同版本或不同实验设置的评测成绩拼成排行榜。

**“全球最全”是建设目标，目前没有足够证据宣称已经达到。** [覆盖台账](docs/coverage.md)列明每个来源的抓取范围、收录数量、待处理条目和已知缺口；[待审队列](data/review-queue.jsonl)可以继续执行。

维护方法见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [maintenance.md](docs/maintenance.md)。原始 README、论文全文、数据集和模型权重不在本仓库中再分发。
