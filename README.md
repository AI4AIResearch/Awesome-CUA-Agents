# Awesome Computer-Use Agents

<!-- BADGES:START -->
[![Resources](https://img.shields.io/badge/resources-2%2C545-4f46e5)](data/catalog.jsonl) [![Curated](https://img.shields.io/badge/source--reviewed-996-0e8a16)](docs/coverage.md) [![Evidence](https://img.shields.io/badge/evidence%20through-2026--10--17-1d76db)](docs/coverage.md) [![Catalog quality](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml/badge.svg)](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Website](https://img.shields.io/badge/website-awesomecua.github.io-6366f1)](https://awesomecua.github.io/)
<!-- BADGES:END -->

**A source-backed data catalog for computer-use, GUI, browser, and mobile agents.**

[Highlights](#highlights) · [Recently reviewed](#recently-reviewed) · [Explore](#explore) · [Use the data](#use-the-data) · [Website](https://awesomecua.github.io/) · [GitHub organization](https://github.com/AwesomeCUA) · [简体中文](README.zh-CN.md) · [Coverage ledger](docs/coverage.md) · [Contribute](CONTRIBUTING.md)

**For people, RAG systems, and agents — clone the complete catalog:**

```sh
git clone https://github.com/reacher-z/Awesome-CUA.git
```

[Agent instructions](AGENTS.md) · [RAG and agent guide](https://awesomecua.github.io/agents/) · [Complete JSONL](https://awesomecua.github.io/downloads/catalog.jsonl) · [Retrieval documents](https://awesomecua.github.io/downloads/rag-documents.jsonl)

The goal is comprehensive coverage of public research and industry resources, with provenance that can be inspected. Papers, models, training data, evaluation environments, frameworks, infrastructure, products, and publishers belong in the same searchable catalog.

**Global completeness is a goal, not a verified claim.** We publish the source populations, review states, and remaining gaps. Bibliographic metadata verification is different from reviewing a resource's relevance or quality.

<!-- STATS:START -->

**2,545 resource records** · **996 curated** · **2,164 arXiv records** · **44 discovery documents**

Evidence through `2026-10-17T07:57:59Z`. 1,549 records have bibliographic verification only; 1,402 discovered identifiers remain unresolved. 100 scope exclusions retain their original metadata in the archive. Counts overlap as explained below.

<!-- STATS:END -->

## Explore

<!-- EXPLORE:START -->
| Research and training | Engineering and industry |
| --- | --- |
| [Research by topic](docs/topics.md) · **604** reviewed papers · [Full bibliography](docs/papers.md) · 2,164 arXiv records | [Agents](docs/agents.md) · **31** |
| [Surveys](docs/surveys.md) · **11** | [Frameworks](docs/frameworks.md) · **50** |
| [Datasets](docs/datasets.md) · **73** | [Infrastructure](docs/infrastructures.md) · **14** |
| [Benchmarks](docs/benchmarks.md) · **70** | [Tools](docs/tools.md) · **17** |
| [Models and checkpoint releases](docs/models.md) · **91** | [Products](docs/products.md) · **19** · [Publishers and brands](docs/companies.md) · **16** |
<!-- EXPLORE:END -->

Coverage spans web, desktop, Android, iOS, Windows, macOS, Linux, and cross-platform work. Topics include grounding, screen understanding, planning, memory, long-horizon workflows, reinforcement learning, data generation, safety, robustness, and evaluation. Environment facets overlap; framework support is not assumed from a model's benchmark results.

## Highlights

The most-mentioned curated resources per category: the count is how many other cataloged resources mention each one in their reviewed first-party source (README, model or dataset card). It reflects connectedness inside this catalog, not quality, popularity, or benchmark performance. Every category page lists all reviewed entries.

<!-- HIGHLIGHTS:START -->
**Benchmarks** · [all 70 →](docs/benchmarks.md)

| Resource | Mentions | Environments | Paper | License | Description |
| --- | ---: | --- | --- | --- | --- |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | 20 | desktop, linux, windows, macos | [2404.07972](https://arxiv.org/abs/2404.07972) (2024) | code Apache-2.0 | Execution-based evaluation of agents performing tasks in real desktop environments. |
| [WebArena](https://github.com/web-arena-x/webarena) | 13 | web | [2307.13854](https://arxiv.org/abs/2307.13854) (2023) | code Apache-2.0 | Self-hosted web environments and tasks for evaluating autonomous web agents. |
| [ScreenSpot Pro](https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding) | 8 | desktop, windows, macos, linux | — | code MIT | GUI grounding benchmark focused on professional high-resolution interfaces. |
| [BrowserGym](https://github.com/ServiceNow/BrowserGym) | 7 | web | [2412.05467](https://arxiv.org/abs/2412.05467) (2024) | code Apache-2.0 | Unified interfaces for browser-agent tasks and benchmark environments. |
| [VisualWebArena](https://github.com/web-arena-x/visualwebarena) | 7 | web | [2401.13649](https://arxiv.org/abs/2401.13649) (2024) | — | Visually grounded web tasks extending the WebArena evaluation setting. |
| [AndroidWorld](https://github.com/google-research/android_world) | 6 | android | [2405.14573](https://arxiv.org/abs/2405.14573) (2024) | code Apache-2.0 | Android environment with programmatic task evaluation for mobile agents. |

**Models** · [all 91 →](docs/models.md)

| Resource | Mentions | Environments | Paper | License | Description |
| --- | ---: | --- | --- | --- | --- |
| [SeeClick](https://github.com/njucckevin/SeeClick) | 7 | cross-platform | [2401.10935](https://arxiv.org/abs/2401.10935) (2024) | code Apache-2.0 | GUI grounding model trained to locate visual interface elements. |
| [Aguvis](https://github.com/xlang-ai/aguvis) | 5 | cross-platform | [2412.04454](https://arxiv.org/abs/2412.04454) (2024) | — | Vision-based GUI agent models with unified action representations. |
| [UI-TARS](https://github.com/bytedance/UI-TARS) | 5 | cross-platform | [2501.12326](https://arxiv.org/abs/2501.12326) (2025) | code Apache-2.0 | Native GUI agent model family for perception and action. |
| [OpenCUA](https://github.com/xlang-ai/OpenCUA) | 3 | desktop | [2508.09123](https://arxiv.org/abs/2508.09123) (2025) | code MIT | Open computer-use research stack including models and training resources. |
| [OS-Atlas](https://github.com/OS-Copilot/OS-Atlas) | 3 | cross-platform | [2410.23218](https://arxiv.org/abs/2410.23218) (2024) | code Apache-2.0 | Foundation action models and data for GUI interaction. |
| [ShowUI](https://github.com/showlab/ShowUI) | 3 | cross-platform | [2411.17465](https://arxiv.org/abs/2411.17465) (2024) | code Apache-2.0 | Vision-language-action model for GUI interaction. |

**Datasets** · [all 73 →](docs/datasets.md)

| Resource | Mentions | Environments | Paper | License | Description |
| --- | ---: | --- | --- | --- | --- |
| [ScreenSpot-Pro data](https://huggingface.co/datasets/likaixin/ScreenSpot-Pro) | 4 | desktop, windows, macos, linux | — | data mit | High-resolution professional interface screenshots and target annotations for evaluating instruction-based GUI localization. |
| [GUI-Odyssey](https://github.com/OpenGVLab/GUI-Odyssey) | 3 | android | [2406.08451](https://arxiv.org/abs/2406.08451) (2024) | — | Cross-application mobile interaction trajectories. |
| [GUIAct](https://huggingface.co/datasets/yiye2023/GUIAct) | 3 | web, android | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | Web and Android GUI action-instruction data, with single-step, multi-step and smartphone partitions. |
| [GUIChat](https://huggingface.co/datasets/yiye2023/GUIChat) | 3 | unspecified | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | Conversational GUI supervision with text-rich images and bounding boxes, organized as single-turn questions and multi-turn dialogues. |
| [GUIEnv-local](https://huggingface.co/datasets/yiye2023/GUIEnv) | 3 | web | [2406.11317](https://arxiv.org/abs/2406.11317) (2024) | — | The released local-supervision portion of GUIEnv, pairing webpage regions and text for OCR and GUI grounding. |
| [OpenMobile-Data-v2](https://huggingface.co/datasets/OpenMobile-2/OpenMobile-Data-v2) | 3 | android, web | [2610.14157](https://arxiv.org/abs/2610.14157) (2026) | — | Mobile-agent supervision from emulator and simulator trajectories, plus executable tasks with starting states and success checks for reinforcement learning. |

**Frameworks** · [all 50 →](docs/frameworks.md)

| Resource | Mentions | Environments | Paper | License | Description |
| --- | ---: | --- | --- | --- | --- |
| [Browser Use](https://github.com/browser-use/browser-use) | 7 | web | — | code MIT | Framework for browser interaction by AI agents. |
| [AgentLab](https://github.com/ServiceNow/AgentLab) | 5 | web | [2412.05467](https://arxiv.org/abs/2412.05467) (2024) | code Apache-2.0 | Experiment framework for developing and evaluating browser agents. |
| [Seg2Click](https://github.com/jcwang0602/Seg2Click) | 5 | cross-platform | [2610.16234](https://arxiv.org/abs/2610.16234) (2026) | code MIT | Training and inference implementation that predicts an executable-region mask and derives a GUI click from that mask. |
| [OpenMobile-2 code](https://github.com/OpenMobile2/OpenMobile2-Code) | 3 | android, web | [2610.14157](https://arxiv.org/abs/2610.14157) (2026) | code Apache-2.0 | Evaluation adapters and training guidance for OpenMobile-2 across Android emulators and browser-rendered mobile simulation. |
| [UI-Genie](https://github.com/Euphoria16/UI-Genie) | 3 | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | — | Training and evaluation code for a mobile-agent framework that iteratively generates trajectories using agent and reward-model feedback. |
| [Computer Use OOTB](https://github.com/showlab/computer_use_ootb) | 2 | desktop | — | code Apache-2.0 | Computer-use agent execution toolkit. |

**Agents** · [all 31 →](docs/agents.md)

| Resource | Mentions | Environments | Paper | License | Description |
| --- | ---: | --- | --- | --- | --- |
| [Mobile-Agent](https://github.com/X-PLUG/MobileAgent) | 8 | android, cross-platform | [2401.16158](https://arxiv.org/abs/2401.16158) (2024), [2406.01014](https://arxiv.org/abs/2406.01014) (2024), [2508.15144](https://arxiv.org/abs/2508.15144) (2025), [2602.16855](https://arxiv.org/abs/2602.16855) (2026) | code MIT | Mobile device agent family using visual interface interaction. |
| [Agent S](https://github.com/simular-ai/Agent-S) | 2 | desktop | [2410.08164](https://arxiv.org/abs/2410.08164) (2024), [2504.00906](https://arxiv.org/abs/2504.00906) (2025) | code Apache-2.0 | Agent framework for general computer interaction. |
| [AppAgent](https://github.com/TencentQQGYLab/AppAgent) | 1 | android | [2312.13771](https://arxiv.org/abs/2312.13771) (2023) | code MIT | Mobile app agent using exploration and reusable knowledge. |
| [Auto-GUI / Auto-UI](https://github.com/cooelf/Auto-GUI) | 1 | android | [2309.11436](https://arxiv.org/abs/2309.11436) (2023) | code Apache-2.0 | Screenshot-based mobile agent implementation with training and inference code for chain-of-action prediction. |
| [MagenticLite / Magentic UI](https://github.com/microsoft/magentic-ui) | 1 | web | — | code MIT | Microsoft agent application combining orchestration with browser interaction; successor to Magentic UI. |
| [Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM) | 1 | android, ios | — | code Apache-2.0 | Phone agent model and framework with device interaction tooling. |

<!-- HIGHLIGHTS:END -->

## Recently reviewed

Newest editorial approvals of models, datasets, benchmarks, systems, and tools (newest first). New papers appear by date in the [topic hubs](docs/topics.md).

<!-- RECENT:START -->
| Reviewed | Resource | Kind | Environments | Description |
| --- | --- | --- | --- | --- |
| 2026‑10‑17 | [WebRewardBench](https://huggingface.co/datasets/LangAGI-Lab/WebRewardBench) | benchmark | web | An offline preference-evaluation set for web process reward models, pairing page and trajectory context with preferred and rejected candidate decisions. |
| 2026‑10‑17 | [WebPRM Collection preference data](https://huggingface.co/datasets/LangAGI-Lab/WebPRMCollection_preference_pair) | dataset | web | Checklist-annotated web decision records with page observations, prior actions, one preferred continuation and rejected alternatives for process-reward learning. |
| 2026‑10‑17 | [Go-Browse-WA processed data](https://huggingface.co/datasets/apurvaga/go-browse-wa) | dataset | web | Flattened web-interaction training records with accessibility-tree observations, assistant completions, trajectory rewards and step-link metadata. |
| 2026‑10‑17 | [Go-Browse WebArena Qwen 7B](https://huggingface.co/apurvaga/go-browse-wa-qwen-7B) | model | web | A Qwen-2.5-7B-Instruct checkpoint fine-tuned on Go-Browse WebArena trajectories for website task execution. |
| 2026‑10‑17 | [WebShepherd 3B](https://huggingface.co/LangAGI-Lab/WebShepherd_3B) | model | web | A public text-based process-reward checkpoint from the Web-Shepherd collection for scoring web-agent decisions against task checklists. |
| 2026‑10‑17 | [Web-Shepherd inference and evaluation](https://github.com/kyle8581/Web-Shepherd) | tool | web | Process-reward inference and benchmark-evaluation utilities that use task checklists to assess individual web-agent decisions. |
| 2026‑10‑17 | [SkillWeaver](https://github.com/OSU-NLP-Group/SkillWeaver) | framework | web | A web-agent framework that explores sites, synthesizes reusable interaction APIs and builds a skill library for later tasks. |
| 2026‑10‑17 | [ShowUI-π checkpoint](https://huggingface.co/showlab/ShowUI-pi) | model | unspecified | A compact visual-action checkpoint that predicts continuous GUI drag trajectories from a screenshot and a natural-language instruction. |
| 2026‑10‑17 | [ScaleCUA 7B](https://huggingface.co/OpenGVLab/ScaleCUA-7B) | model | web, desktop, android, linux | A Qwen2.5-VL-based computer-use checkpoint with direct grounding and agent action modes across desktop, mobile and web interfaces. |
| 2026‑10‑17 | [RedTeamCUA](https://github.com/OSU-NLP-Group/RedTeamCUA) | framework | web, desktop | A controlled testing framework that combines desktop virtual machines and replicated websites to evaluate computer-use agents against indirect prompt injection. |
| 2026‑10‑17 | [Holo1 7B](https://huggingface.co/Hcompany/Holo1-7B) | model | web | A Qwen2.5-VL-based action model released for the Surfer-H web-agent system, supporting policy, interface-localization and validation roles. |
| 2026‑10‑17 | [Go-Browse](https://github.com/ApGa/Go-Browse) | framework | web | Structured website-exploration and data-processing code that revisits discovered pages, proposes tasks and collects trajectories for web-agent fine-tuning. |
<!-- RECENT:END -->

## Use the data

Browse the [interactive website](https://awesomecua.github.io/) to search and filter all resources, inspect source evidence, switch between English and Chinese, or download the complete catalog. [Website development and publishing](docs/website.md).

[Reviewed research](https://awesomecua.github.io/papers/) · [Computer-use agent guides](https://awesomecua.github.io/guides/) · [Static resource directory](https://awesomecua.github.io/catalog/) · [Search and AI discovery](docs/search-discovery.md)

- **[Catalog JSONL](data/catalog.jsonl):** one resource per line, with stable IDs, typed fields, provenance, scoped licenses, and review status.
- **[Reference graph](data/references.jsonl):** outbound references from primary sources. `mentions` does not mean `trained_on` or `evaluated_on`.
- **[Discovery registry](data/sources.json)** and **[candidates](data/candidates.jsonl):** source snapshots and where each identifier was found.
- **[Review queue](data/review-queue.jsonl):** unresolved evidence, unindexed discoveries, and proposals requiring editorial work.
- **[JSON Schema](schemas/resource.schema.json)** and **[coverage JSON](data/coverage.json):** machine-checkable contracts and coverage accounting.

```bash
# Python 3.11+. Search and export require only the standard library.
cd Awesome-CUA
python3 scripts/catalog.py search "grounding" --kind model
python3 scripts/catalog.py search --kind dataset --environment android
python3 scripts/catalog.py search --kind product --status curated --json
python3 scripts/catalog.py build
# Creates dist/catalog.sqlite and dist/catalog.json, with no network calls.
python3 scripts/export_rag.py --output dist/rag-documents.jsonl
# Add --include-metadata to include every active record, with its review state intact.
```

Use SQLite to join resources, environment/topic facets, and reviewed relations. See [query examples](docs/query-guide.md). `data/catalog.jsonl` is committed; SQLite and JSON array exports are reproducible local build products.

## What “verified” means

| State | What has been checked | What has not been established |
| --- | --- | --- |
| `curated` | AI-assisted editorial review against a first-party source snapshot, with name, scope, summary, and taxonomy | Independent reproduction, universal availability, or endorsement |
| `metadata_verified` | Bibliographic identity, title, authors, and dates returned by arXiv | Topic relevance, methodology, findings, or inclusion in the core field |
| `candidate` | A normalized URL or identifier was discovered | Inclusion, correctness, or availability; excluded from the published catalog |

Counts refer to **resources**, not unique projects. A paper, repository, dataset release, model checkpoint, product, and publisher can be separate related resources. Model families and individual checkpoints are explicitly linked where reviewed.

Code, data, weights, and document licenses are separate. Missing values are `null`. Dataset archive counts are not converted into training-example counts. Scores from different benchmark versions, splits, action budgets, or evaluators are not combined into a ranking.

## Maintain and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/catalog.py validate
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/catalog.py build --check
```

Network discovery and verification are explicit commands; ordinary builds are offline. Changed primary snapshots require another editorial review before publication. [Maintenance guide](docs/maintenance.md) · [Methodology](docs/methodology.md) · [Data dictionary](docs/data-dictionary.md)

## Acknowledgments and reuse

The [source registry](data/sources.json) credits the community collections and surveys used for discovery. The catalog obtains authoritative bibliographic metadata from arXiv and checks selected assets against publisher repositories, documentation, and model/dataset cards. Upstream READMEs, papers, model weights, and datasets are not redistributed here.

Original repository code and annotations use the [MIT license](LICENSE). Linked resources retain their own terms; this repository does not relicense them.
