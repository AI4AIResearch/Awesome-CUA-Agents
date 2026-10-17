# Awesome Computer-Use Agents

<!-- BADGES:START -->
[![Resources](https://img.shields.io/badge/resources-3%2C004-4f46e5)](data/catalog.jsonl) [![Curated](https://img.shields.io/badge/source--reviewed-1%2C430-0e8a16)](docs/coverage.md) [![Evidence](https://img.shields.io/badge/evidence%20through-2026--10--17-1d76db)](docs/coverage.md) [![Catalog quality](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml/badge.svg)](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Website](https://img.shields.io/badge/website-awesomecua.github.io-6366f1)](https://awesomecua.github.io/)
<!-- BADGES:END -->

**面向 computer-use、GUI、浏览器和移动端智能体的可溯源数据目录。**

[浏览](#浏览) · [重点资源](#重点资源) · [最新审阅](#最新审阅) · [使用数据](#使用数据) · [网站](https://awesomecua.github.io/) · [中文主页](https://awesomecua.github.io/zh/) · [GitHub 组织](https://github.com/AwesomeCUA) · [English](README.md) · [覆盖台账](docs/coverage.md) · [参与贡献](CONTRIBUTING.md)

**供人、RAG 系统和智能体使用——克隆完整目录：**

```sh
git clone https://github.com/reacher-z/Awesome-CUA.git
```

[Agent 操作指南](AGENTS.md) · [RAG 与智能体指南](https://awesomecua.github.io/zh/agents/)（[English](https://awesomecua.github.io/agents/)） · [完整 JSONL](https://awesomecua.github.io/downloads/catalog.jsonl) · [检索文档](https://awesomecua.github.io/downloads/rag-documents.jsonl)

目标是全面覆盖公开的研究和产业资源，并提供可检查的来源证据。论文、模型、训练数据、评测环境、框架、基础设施、产品和发布方都收录在同一个可检索目录中。

**“全球最全”是建设目标，而不是已经核实的结论。** 我们公开来源范围、审阅状态和剩余缺口。核实书目元数据不等于审阅了资源的相关性或质量。

使用 `python3 scripts/catalog.py get arxiv:2404.07972 --related --json` 可按稳定 ID 取得完整记录与已核实关联。[BibTeX](https://awesomecua.github.io/downloads/citations.bib) 和 [CSL JSON](https://awesomecua.github.io/downloads/citations.csl.json) 提供已审阅论文引用；每条资源页面也有可直接读取的 `record.json`。

[按主题浏览](https://awesomecua.github.io/zh/topics/)（[English](https://awesomecua.github.io/topics/)） · [主题子集与指纹](https://awesomecua.github.io/downloads/topics.json)

<!-- STATS:START -->

**3,004 条资源记录** · **1,430 条已审阅** · **2,578 条论文与综述记录** · **44 个发现来源文档**

证据截至 `2026-10-17T14:35:24Z`。1,574 条记录仅完成书目核实；945 个已发现的标识符尚待处理。118 条范围排除记录在归档中保留原始元数据。各项计数存在重叠，详见下文。

<!-- STATS:END -->

## 浏览

<!-- EXPLORE:START -->
| 研究与训练 | 工程与产业 |
| --- | --- |
| [按主题浏览研究](docs/topics.md) · **991** 篇已审阅论文 · [完整论文目录](docs/papers.md) · 2,578 条论文与综述记录 | [智能体](docs/agents.md) · **38** |
| [综述](docs/surveys.md) · **13** | [框架](docs/frameworks.md) · **66** |
| [数据集](docs/datasets.md) · **80** | [基础设施](docs/infrastructures.md) · **15** |
| [基准](docs/benchmarks.md) · **79** | [工具](docs/tools.md) · **20** |
| [模型与权重版本](docs/models.md) · **93** | [产品](docs/products.md) · **19** · [发布方与品牌](docs/companies.md) · **16** |

**按平台：** [Web](docs/environments/web.md) **533** · [Desktop](docs/environments/desktop.md) **277** · [Windows](docs/environments/windows.md) **51** · [macOS](docs/environments/macos.md) **29** · [Linux](docs/environments/linux.md) **39** · [Android](docs/environments/android.md) **275** · [iOS](docs/environments/ios.md) **19** · [HarmonyOS](docs/environments/harmonyos.md) **2** · [Cross-platform](docs/environments/cross-platform.md) **186**
<!-- EXPLORE:END -->

覆盖 Web、桌面、Android、iOS、Windows、macOS、Linux 和跨平台工作。主题包括 grounding、屏幕理解、规划、记忆、长流程任务、强化学习、数据生成、安全、鲁棒性和评测。环境分面可以重叠；不会根据模型的基准成绩推定框架支持。

## 重点资源

按类别列出被其他已收录资源在其已审阅一手来源（README、模型卡或数据集卡）中提及最多的已审阅资源。该计数反映目录内部的关联程度，不代表质量、流行度或基准表现；每个类别页面都列出全部已审阅条目。综述排在最前，按时间倒序。资源名称和简介保留原文。

<!-- HIGHLIGHTS:START -->
**从最新综述入门** · [全部 13 项 →](docs/surveys.md)

| 日期 | 综述 | 环境 |
| --- | --- | --- |
| 2026‑09‑02 | [Efficient GUI Agents: A Systems Survey of Observation, Memory, Action, and Runtime Optimization](https://arxiv.org/abs/2609.02309) | cross-platform |
| 2026‑02‑12 | [Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward](https://arxiv.org/abs/2602.12430) | unspecified |
| 2025‑08‑06 | [OS Agents: A Survey on MLLM-based Agents for General Computing Devices Use](https://arxiv.org/abs/2508.04482) | cross-platform |
| 2025‑05‑16 | [A Survey on the Safety and Security Threats of Computer-Using Agents: JARVIS or Ultron?](https://arxiv.org/abs/2505.10924) | cross-platform |
| 2025‑04‑29 | [A Survey on GUI Agents with Foundation Models Enhanced by Reinforcement Learning](https://arxiv.org/abs/2504.20464) | cross-platform |

**基准** · [全部 79 项 →](docs/benchmarks.md)

| 资源 | 被提及 | 环境 | 论文 | 许可 | 简介（英文） |
| --- | ---: | --- | --- | --- | --- |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | 20 | desktop, linux, windows, macos | [2404.07972](https://arxiv.org/abs/2404.07972) (2024) | 代码 Apache-2.0 | Execution-based evaluation of agents performing tasks in real desktop environments. |
| [WebArena](https://github.com/web-arena-x/webarena) | 13 | web | [2307.13854](https://arxiv.org/abs/2307.13854) (2023) | 代码 Apache-2.0 | Self-hosted web environments and tasks for evaluating autonomous web agents. |
| [ScreenSpot Pro](https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding) | 8 | desktop, windows, macos, linux | — | 代码 MIT | GUI grounding benchmark focused on professional high-resolution interfaces. |
| [BrowserGym](https://github.com/ServiceNow/BrowserGym) | 7 | web | [2412.05467](https://arxiv.org/abs/2412.05467) (2024) | 代码 Apache-2.0 | Unified interfaces for browser-agent tasks and benchmark environments. |
| [VisualWebArena](https://github.com/web-arena-x/visualwebarena) | 7 | web | [2401.13649](https://arxiv.org/abs/2401.13649) (2024) | — | Visually grounded web tasks extending the WebArena evaluation setting. |
| [AndroidWorld](https://github.com/google-research/android_world) | 6 | android | [2405.14573](https://arxiv.org/abs/2405.14573) (2024) | 代码 Apache-2.0 | Android environment with programmatic task evaluation for mobile agents. |

**模型** · [全部 93 项 →](docs/models.md)

| 资源 | 被提及 | 环境 | 论文 | 许可 | 简介（英文） |
| --- | ---: | --- | --- | --- | --- |
| [SeeClick](https://github.com/njucckevin/SeeClick) | 7 | cross-platform | [2401.10935](https://arxiv.org/abs/2401.10935) (2024) | 代码 Apache-2.0 | GUI grounding model trained to locate visual interface elements. |
| [Aguvis](https://github.com/xlang-ai/aguvis) | 5 | cross-platform | [2412.04454](https://arxiv.org/abs/2412.04454) (2024) | — | Vision-based GUI agent models with unified action representations. |
| [UI-TARS](https://github.com/bytedance/UI-TARS) | 5 | cross-platform | [2501.12326](https://arxiv.org/abs/2501.12326) (2025) | 代码 Apache-2.0 | Native GUI agent model family for perception and action. |
| [OpenCUA](https://github.com/xlang-ai/OpenCUA) | 3 | desktop | [2508.09123](https://arxiv.org/abs/2508.09123) (2025) | 代码 MIT | Open computer-use research stack including models and training resources. |
| [OS-Atlas](https://github.com/OS-Copilot/OS-Atlas) | 3 | cross-platform | [2410.23218](https://arxiv.org/abs/2410.23218) (2024) | 代码 Apache-2.0 | Foundation action models and data for GUI interaction. |
| [ShowUI](https://github.com/showlab/ShowUI) | 3 | cross-platform | [2411.17465](https://arxiv.org/abs/2411.17465) (2024) | 代码 Apache-2.0 | Vision-language-action model for GUI interaction. |

**数据集** · [全部 80 项 →](docs/datasets.md)

| 资源 | 被提及 | 环境 | 论文 | 许可 | 简介（英文） |
| --- | ---: | --- | --- | --- | --- |
| [ScreenSpot-Pro data](https://huggingface.co/datasets/likaixin/ScreenSpot-Pro) | 4 | desktop, windows, macos, linux | — | 数据 mit | High-resolution professional interface screenshots and target annotations for evaluating instruction-based GUI localization. |
| [GUI-Odyssey](https://github.com/OpenGVLab/GUI-Odyssey) | 3 | android | [2406.08451](https://arxiv.org/abs/2406.08451) (2024) | — | Cross-application mobile interaction trajectories. |
| [GUIAct](https://huggingface.co/datasets/yiye2023/GUIAct) | 3 | web, android | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | Web and Android GUI action-instruction data, with single-step, multi-step and smartphone partitions. |
| [GUIChat](https://huggingface.co/datasets/yiye2023/GUIChat) | 3 | unspecified | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | Conversational GUI supervision with text-rich images and bounding boxes, organized as single-turn questions and multi-turn dialogues. |
| [GUIEnv-local](https://huggingface.co/datasets/yiye2023/GUIEnv) | 3 | web | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | The released local-supervision portion of GUIEnv, pairing webpage regions and text for OCR and GUI grounding. |
| [OpenMobile-Data-v2](https://huggingface.co/datasets/OpenMobile-2/OpenMobile-Data-v2) | 3 | android, web | [2610.14157](https://arxiv.org/abs/2610.14157) (2026) | — | Mobile-agent supervision from emulator and simulator trajectories, plus executable tasks with starting states and success checks for reinforcement learning. |

**框架** · [全部 66 项 →](docs/frameworks.md)

| 资源 | 被提及 | 环境 | 论文 | 许可 | 简介（英文） |
| --- | ---: | --- | --- | --- | --- |
| [Browser Use](https://github.com/browser-use/browser-use) | 7 | web | — | 代码 MIT | Framework for browser interaction by AI agents. |
| [AgentLab](https://github.com/ServiceNow/AgentLab) | 5 | web | [2412.05467](https://arxiv.org/abs/2412.05467) (2024) | 代码 Apache-2.0 | Experiment framework for developing and evaluating browser agents. |
| [Seg2Click](https://github.com/jcwang0602/Seg2Click) | 5 | cross-platform | [2610.16234](https://arxiv.org/abs/2610.16234) (2026) | 代码 MIT | Training and inference implementation that predicts an executable-region mask and derives a GUI click from that mask. |
| [OpenMobile-2 code](https://github.com/OpenMobile2/OpenMobile2-Code) | 3 | android, web | [2610.14157](https://arxiv.org/abs/2610.14157) (2026) | 代码 Apache-2.0 | Evaluation adapters and training guidance for OpenMobile-2 across Android emulators and browser-rendered mobile simulation. |
| [UI-Genie](https://github.com/Euphoria16/UI-Genie) | 3 | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | — | Training and evaluation code for a mobile-agent framework that iteratively generates trajectories using agent and reward-model feedback. |
| [Computer Use OOTB](https://github.com/showlab/computer_use_ootb) | 2 | desktop | — | 代码 Apache-2.0 | Computer-use agent execution toolkit. |

**智能体** · [全部 38 项 →](docs/agents.md)

| 资源 | 被提及 | 环境 | 论文 | 许可 | 简介（英文） |
| --- | ---: | --- | --- | --- | --- |
| [Mobile-Agent](https://github.com/X-PLUG/MobileAgent) | 8 | android, cross-platform | [2401.16158](https://arxiv.org/abs/2401.16158) (2024), [2406.01014](https://arxiv.org/abs/2406.01014) (2024), [2508.15144](https://arxiv.org/abs/2508.15144) (2025), [2602.16855](https://arxiv.org/abs/2602.16855) (2026) | 代码 MIT | Mobile device agent family using visual interface interaction. |
| [Agent S](https://github.com/simular-ai/Agent-S) | 2 | desktop | [2410.08164](https://arxiv.org/abs/2410.08164) (2024), [2504.00906](https://arxiv.org/abs/2504.00906) (2025) | 代码 Apache-2.0 | Agent framework for general computer interaction. |
| [AppAgent](https://github.com/TencentQQGYLab/AppAgent) | 1 | android | [2312.13771](https://arxiv.org/abs/2312.13771) (2023) | 代码 MIT | Mobile app agent using exploration and reusable knowledge. |
| [Auto-GUI / Auto-UI](https://github.com/cooelf/Auto-GUI) | 1 | android | [2309.11436](https://arxiv.org/abs/2309.11436) (2023) | 代码 Apache-2.0 | Screenshot-based mobile agent implementation with training and inference code for chain-of-action prediction. |
| [MagenticLite / Magentic UI](https://github.com/microsoft/magentic-ui) | 1 | web | — | 代码 MIT | Microsoft agent application combining orchestration with browser interaction; successor to Magentic UI. |
| [Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM) | 1 | android, ios | — | 代码 Apache-2.0 | Phone agent model and framework with device interaction tooling. |

<!-- HIGHLIGHTS:END -->

## 最新审阅

按时间倒序列出最新通过编辑审阅的模型、数据集、基准、系统和工具；新论文按日期列在[主题页面](docs/topics.md)中。

<!-- RECENT:START -->
| 审阅日期 | 资源 | 类型 | 环境 | 简介（英文） |
| --- | --- | --- | --- | --- |
| 2026‑10‑17 | [WebVLN research implementation](https://github.com/WebVLN/WebVLN) | 框架 | web | Training and evaluation code for question-guided website navigation that combines visual observations with web-specific HTML information. |
| 2026‑10‑17 | [WebMarker](https://github.com/reidbarber/webmarker) | 工具 | web | A browser library that labels interactive elements and their boxes for visual prompting, preserving element mappings that automation code can use to execute selected actions. |
| 2026‑10‑17 | [WebLlama](https://github.com/McGill-NLP/webllama) | 框架 | web | Training, evaluation and integration tooling for dialogue-guided web agents, including Llama fine-tuning workflows and BrowserGym examples built around WebLINX. |
| 2026‑10‑17 | [UIBert AppSim and RefExp annotations](https://github.com/google-research-datasets/uibert) | 数据集 | android | Two Rico-derived UI component retrieval datasets: AppSim pairs semantically similar elements across screens, while RefExp links referring expressions to target elements. |
| 2026‑10‑17 | [TongUI training and inference framework](https://github.com/TongUI-agent/TongUI-agent) | 框架 | cross-platform, desktop, web | Training configurations, preprocessing and inference examples for tutorial-trained GUI models, with a LLaMA-Factory fine-tuning workflow and screenshot-grounding interfaces. |
| 2026‑10‑17 | [Synapse](https://github.com/ltzheng/Synapse) | 框架 | web | A computer-control research implementation that retrieves example trajectories from memory, abstracts task-relevant state and prompts an agent to navigate browser tasks. |
| 2026‑10‑17 | [Self-MAP](https://github.com/magicgh/Self-MAP) | 框架 | web | A conversational web-agent implementation with candidate ranking and memory-assisted action planning, including optional memory simplification, refinement and self-reflection modules. |
| 2026‑10‑17 | [OpenAgents Web Agent](https://github.com/xlang-ai/OpenAgents/tree/main/real_agents/web_agent) | 智能体 | web | The OpenAgents browser-control component, connecting a Chrome extension to a web agent and local chat platform for navigating sites and completing interface tasks. |
| 2026‑10‑17 | [MT-Mind2Web](https://huggingface.co/datasets/magicgh/MT-Mind2Web) | 数据集 | web | Multi-turn web-navigation conversations constructed from Mind2Web interactions, with dialogue turns, HTML snapshots, element candidates and click/type/select action sequences. |
| 2026‑10‑17 | [MONDAY annotations](https://huggingface.co/datasets/runamu/MONDAY) | 数据集 | android, ios | Video-derived mobile navigation annotations that pair scene boundaries and screen or element boxes with action labels for training and evaluating GUI agents. |
| 2026‑10‑17 | [MobileGPT](https://github.com/fclab-skku/MobileGPT) | 智能体 | android | An Android client and Python-server agent that learns reusable app subtasks through exploration, selection, derivation and memory recall. |
| 2026‑10‑17 | [MobBench task definitions](https://huggingface.co/datasets/OpenDFM/MobA-MobBench) | 基准 | android | A public set of real-device mobile task definitions used to evaluate MobA, with Chinese and English task material packaged in a versioned JSON release. |
<!-- RECENT:END -->

## 使用数据

打开[交互式网站](https://awesomecua.github.io/)，可以搜索和筛选全部资源、查看来源证据、切换中英文界面，或下载完整目录。网站开发与发布见 [website.md](docs/website.md)。

[中文数据中心](https://awesomecua.github.io/zh/data/)与[English data hub](https://awesomecua.github.io/data/)按六组组织公开下载：完整目录、RAG 检索文档、论文引用、主题与对比、来源与审阅状态、数据规范（schema）。克隆仓库仍可取得同一套完整源目录；数据中心提供其已发布快照的导出文件。

[下载清单](https://awesomecua.github.io/downloads/manifest.json)为每个列出的导出记录实际数量及单位、范围、精确字节数和 SHA-256 指纹。不同格式和视图可能包含相同资源，单位也可能不同，不能把这些数量相加。混合使用下载文件前，请比较各清单的 `catalog_sha256`，确认它们属于同一目录快照。

[已审阅研究](https://awesomecua.github.io/zh/papers/)（[English](https://awesomecua.github.io/papers/)） · [Computer-use agent 指南](https://awesomecua.github.io/guides/) · [静态资源目录](https://awesomecua.github.io/catalog/) · [搜索与 AI 发现](docs/search-discovery.md)

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
| `metadata_verified` | 对照保留的 arXiv 或出版来源核实书目身份、标题、作者和已记录日期 | 主题相关性、方法、结论，或是否属于核心领域 |
| `candidate` | 发现了规范化的 URL 或标识符 | 是否收录、是否正确或是否可用；不计入公开目录 |

计数指的是**资源**，而不是独立项目。论文、仓库、数据集发布、模型权重版本、产品和发布方可以是彼此关联的不同资源。模型系列与具体权重版本在审阅后会显式关联。

代码、数据、权重和文档的许可分别记录。缺失值为 `null`。数据集归档文件数不会被换算成训练样本数。来自不同基准版本、数据划分、动作预算或评测器的分数不会合并成排行榜。

## 维护与验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/catalog.py validate
.venv/bin/python scripts/catalog.py build --check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/catalog.py build
node --test tests/web.test.mjs
.venv/bin/python scripts/build_site.py
```

这些命令与 [Catalog quality](.github/workflows/catalog.yml) 在每次推送和拉取请求时运行的检查一致，顺序也相同。需要 Python 3.11+ 和 Node.js 24+，即 `package.json` 中 `engines` 声明的版本（CI 使用 Python 3.12 和 Node.js 24）。网页测试只使用 Node.js 内置的测试运行器，无需用 npm 安装任何依赖。`npm run test:web` 和 `npm run build:web` 分别是最后两条命令的快捷方式。

网络发现和核实需要显式运行相应命令；常规构建不联网。一手来源快照发生变化后，必须重新进行编辑审阅才能发布。[维护指南](docs/maintenance.md) · [方法说明](docs/methodology.md) · [数据字典](docs/data-dictionary.md)

## 致谢与复用

[来源登记](data/sources.json)列出了用于发现资源的社区合集和综述。书目记录依据保留的 arXiv、出版方及作者来源；出版记录分别保留各版本的题名、作者和日期精度。部分资源还会对照发布方的仓库、文档以及模型/数据集卡片核查。上游 README、论文、模型权重和数据集不在本仓库中再分发。

本仓库的原创代码和标注采用 [MIT 许可](LICENSE)。被链接的资源保留各自的条款；本仓库不对其重新授权。

引用本目录时，请使用 [CITATION.cff](CITATION.cff) 或 GitHub 的“Cite this repository”按钮。数据随每次扫描更新，请固定所用的确切版本：在克隆中用 `git rev-parse HEAD` 记录提交，或链接该提交下的文件，例如 `https://github.com/reacher-z/Awesome-CUA/blob/<commit>/data/catalog.jsonl`。
