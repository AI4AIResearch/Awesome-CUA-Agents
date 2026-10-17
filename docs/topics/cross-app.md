# Cross-app workflows

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

38 source-reviewed resources tagged `cross-app`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Benchmarks (9)](#benchmarks) · [Datasets (2)](#datasets) · [Agents (2)](#agents) · [Frameworks (1)](#frameworks) · [Papers (24)](#papers)

## Benchmarks

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [AppWorld](https://github.com/StonyBrookNLP/appworld) | unspecified | [2407.18901](https://arxiv.org/abs/2407.18901) (2024) | code Apache-2.0 | Simulated applications, user data, and state-based task checks for evaluating agents that interact through APIs and code. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/stonybrooknlp/appworld/HEAD/README.md) |
| [CRAB](https://github.com/camel-ai/crab) | desktop, android | [2407.01511](https://arxiv.org/abs/2407.01511) (2024) | — | Cross-environment benchmark framework for multimodal agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/camel-ai/crab/HEAD/README.md) |
| [iOSWorld](https://github.com/ljang0/iOSWorld) | ios | — | code Apache-2.0 | Native iPhone-simulator benchmark with shared user data, application workflows, agent runners, and rubric-based scoring. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/ljang0/iOSWorld/HEAD/README.md) |
| [MobileGUI-VBench](https://huggingface.co/datasets/vivo-ai/MobileGUI-VBench) | unspecified | [2609.12394](https://arxiv.org/abs/2609.12394) (2026) | — | Mobile-app task definitions covering everyday scenarios, with annotated preconditions and clarification requirements for evaluating agent behavior. | [✓ 2026‑10‑17](https://huggingface.co/datasets/vivo-ai/MobileGUI-VBench/raw/main/README.md) |
| [MobileGym++ / MobileGym++ Bench](https://github.com/OpenMobile2/MobileGym-plusplus) | web | [2610.14157](https://arxiv.org/abs/2610.14157) (2026) | code Apache-2.0 | Browser-rendered mobile simulation with resettable app state and a shared task suite for GUI-only and GUI-plus-tool agents. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/OpenMobile2/MobileGym-plusplus/HEAD/README.md) |
| [OS-Map](https://github.com/OS-Copilot/OS-Map) | desktop, linux | [2507.19132](https://arxiv.org/abs/2507.19132) (2025) | code MIT | An OSWorld-derived desktop benchmark with an Ubuntu virtual-machine environment and expanded task configurations for measuring breadth and depth of computer interaction. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/OS-Copilot/OS-Map/HEAD/README.md) |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | desktop, linux, windows, macos | [2404.07972](https://arxiv.org/abs/2404.07972) (2024) | code Apache-2.0 | Execution-based evaluation of agents performing tasks in real desktop environments. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/xlang-ai/OSWorld/HEAD/README.md) |
| [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | web, desktop | [2412.14161](https://arxiv.org/abs/2412.14161) (2024) | code MIT | Self-contained workplace environment for evaluating agents on professional tasks involving websites, files, code, and simulated coworkers. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/TheAgentCompany/TheAgentCompany/HEAD/README.md) |
| [WindowsWorld](https://github.com/HITsz-TMG/WindowsWorld) | windows | — | code Apache-2.0 | Cross-application Windows benchmark with intermediate task evaluation. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/HITsz-TMG/WindowsWorld/HEAD/README.md) |

## Datasets

All entries in this section: android.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [GUI-Odyssey](https://github.com/OpenGVLab/GUI-Odyssey) | [2406.08451](https://arxiv.org/abs/2406.08451) (2024) | — | Cross-application mobile interaction trajectories. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/OpenGVLab/GUI-Odyssey/HEAD/README.md) |
| [GUIOdyssey — current data release](https://huggingface.co/datasets/hflqf88888/GUIOdyssey) | [2406.08451](https://arxiv.org/abs/2406.08451) (2024) | data cc-by-4.0 | Cross-app Android interaction episodes with fine-grained step instructions, screen descriptions, action context, and target boxes. | [✓ 2026‑10‑16](https://huggingface.co/datasets/hflqf88888/GUIOdyssey/raw/main/README.md) |

## Agents

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [PC-Agent](https://github.com/GAIR-NLP/PC-Agent) | desktop | [2412.17589](https://arxiv.org/abs/2412.17589) (2024) | code MIT | Agent framework for desktop workflows. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/GAIR-NLP/PC-Agent/HEAD/README.md) |
| [UFO](https://github.com/microsoft/UFO) | windows, desktop | — | — | Windows agent framework for application and desktop automation. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/microsoft/UFO/HEAD/README.md) |

## Frameworks

All entries in this section: desktop, linux.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [GUI-ReWalk](https://github.com/bytedance/GUI-ReWalk) | [2509.15738](https://arxiv.org/abs/2509.15738) (2025) | code Apache-2.0 | A desktop trajectory-generation framework that moves from stochastic GUI exploration to inferred goals and multi-stage task completion, with retrospective reasoning annotations. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/bytedance/GUI-ReWalk/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑10‑08 | [AgentHorizon: Evaluating Agentic Judges for Long-Horizon Computer-Use Tasks](https://arxiv.org/abs/2610.11050) | cross-platform | Introduces AgentHorizon, a benchmark for judging long computer-use trajectories using closely related instructions paired with recorded actions and screenshots. It tests whether judges can detect constraint violations and distinguish successful tasks from similar but incompatible requests. |
| 2026‑09‑29 | [EngiWorld: What Can Frontier Agents Deliver in Professional Engineering Environments?](https://arxiv.org/abs/2609.37686) | desktop | Introduces professional engineering tasks across software domains, with GUI and CLI access and artifact checks for geometric, physical, and design validity. |
| 2026‑09‑29 | [MatToolBench: Benchmarking Multimodal Agents in Real-World Materials Science Workflows](https://arxiv.org/abs/2609.37053) | desktop, windows | Introduces MatToolBench, a Windows-based materials-science benchmark combining GUI operation, scientific-software scripting, and database queries. Expert-defined subcriteria support partial-credit scoring, while the evaluation examines domain knowledge gaps and cross-tool handoff failures. |
| 2026‑06‑22 | [Capable but Careless: Do Computer-Use Agents Follow Contextual Integrity?](https://arxiv.org/abs/2606.23189) | unspecified | AgentCIBench evaluates whether computer-use agents disclose information in ways that violate its original context. Deterministically scored scenarios test nearby sensitive UI content, ambiguous requests and recipient mismatches, including end-to-end agent execution. |
| 2026‑06‑21 | [MacAgentBench: Benchmarking AI Agents on Real-World macOS Desktop](https://arxiv.org/abs/2606.22557) | desktop, macos | Introduces macOS tasks spanning GUI and command-line interaction, with deterministic checks and intermediate-progress scoring for application workflows. |
| 2026‑06‑16 | [Beyond the GUI Paradigm: Do Mobile Agents Need the Phone Screen?](https://arxiv.org/abs/2606.19388) | android | This study compares general coding agents using mobile command-line access with reproducible GUI agents on AndroidWorld and MobileWorld. It also supplies oracle CLI analyses and a separate task suite for operations such as bulk changes, filtering and hidden device state. |
| 2026‑06‑15 | [MyPCBench: A Benchmark for Personally Intelligent Computer-Use Agents](https://arxiv.org/abs/2606.16748) | linux, web | MyPCBench tests personal-assistant tasks on a Linux desktop with simulated web applications and data for a single fictional persona. A shared computer-and-shell interface enables evaluation of cross-application workflows that depend on personal context and account-like state. |
| 2026‑06‑08 | [iOSWorld: A Benchmark for Personally Intelligent Phone Agents](https://arxiv.org/abs/2606.09764) | ios | Introduces a native iOS simulator benchmark with persistent user data, multi-app tasks, and personalization-dependent phone workflows. |
| 2026‑01‑18 | [Mind the Gap: Action Rebinding Attacks against Android GUI Agents](https://arxiv.org/abs/2601.12349) | android | Studies action-rebinding attacks in which an Android GUI agent’s planned input is redirected to a different application during the observation–action delay. The evaluation examines cross-application execution and the consequences of treating an earlier screen as the current action target. |
| 2025‑12‑30 | [ProSoftArena: Benchmarking Hierarchical Capabilities of Multimodal Agents in Professional Software Environments](https://arxiv.org/abs/2601.02399) | windows, desktop | ProSoftArena evaluates 436 professional-software tasks across six disciplines and 13 applications in a Windows 11 virtual-machine environment. Its capability hierarchy, execution-based checks, and human-in-the-loop evaluation cover precise GUI operations and multi-software workflows. |
| 2025‑09‑19 | [GUI-ReWalk: Massive Data Generation for GUI Agent via Stochastic Exploration and Intent-Aware Reasoning](https://arxiv.org/abs/2509.15738) | android | GUI-ReWalk begins with stochastic interface exploration and then infers goals to generate coherent action trajectories. It supports long-horizon workflows across applications and studies training on the resulting data using grounding and navigation benchmarks. |
| 2025‑06‑22 | [Chain-of-Memory: Enhancing GUI Agents for Cross-Application Navigation](https://arxiv.org/abs/2506.18158) | unspecified | Chain-of-Memory explicitly records action descriptions and task-relevant screen information in short- and long-term memory for GUI navigation. GUI Odyssey-CoM provides 111,000 screen-action pairs with memory annotations for learning and evaluating information retention across applications. |
| 2025‑04‑03 | [ReuseDroid: A VLM-empowered Android UI Test Migrator Boosted by Active Feedback](https://arxiv.org/abs/2504.02357) | android | ReuseDroid migrates Android GUI tests between functionally similar apps using VLM agents that separate shared test intent from app-specific interaction flows. It introduces LinPro, a dataset of 578 migration tasks across 39 apps, to evaluate test transfer. |
| 2025‑02‑20 | [PC-Agent: A Hierarchical Multi-Agent Collaboration Framework for Complex Task Automation on PC](https://arxiv.org/abs/2502.14282) | desktop | Uses active perception and hierarchical agents for instruction decomposition, progress tracking, action selection, and reflection in PC workflows. |
| 2024‑09‑12 | [Windows Agent Arena: Evaluating Multi-Modal OS Agents at Scale](https://arxiv.org/abs/2409.08264) | windows | Adapts real-desktop evaluation to Windows applications and supports parallel execution of benchmark tasks. |
| 2024‑07‑26 | [AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents](https://arxiv.org/abs/2407.18901) | unspecified | Introduces simulated application APIs and state-based task evaluation for interactive coding agents performing everyday digital workflows. |
| 2024‑07‑26 | [OfficeBench: Benchmarking Language Agents across Multiple Applications for Office Automation](https://arxiv.org/abs/2407.19056) | desktop | Evaluates language agents on office workflows requiring information integration, long-term planning, and switching between applications. |
| 2024‑07‑01 | [CRAB: Cross-environment Agent Benchmark for Multimodal Language Model Agents](https://arxiv.org/abs/2407.01511) | desktop, cross-platform | Introduces CRAB, a framework for cross-environment agent tasks with graph-based evaluation and a benchmark spanning desktop and phone interactions. |
| 2024‑07‑01 | [Mobile-Bench: An Evaluation Benchmark for LLM-based Mobile Agents](https://arxiv.org/abs/2407.00993) | unspecified | Evaluates mobile agents using combined UI and API actions, tasks with varying app scope, and checkpoints for intermediate progress. |
| 2024‑06‑12 | [GUIOdyssey: A Comprehensive Dataset for Cross-App GUI Navigation on Mobile Devices](https://arxiv.org/abs/2406.08451) | android | Introduces annotated cross-application mobile trajectories and studies history-aware navigation over long task sequences. |
| 2024‑06‑12 | [Practical, Automated Scenario-based Mobile App Testing](https://arxiv.org/abs/2406.08340) | unspecified | ScenTest builds scenario-specific event knowledge graphs from crowdsourced test reports containing GUI and action information. It uses the current app state and testing context to generate scenario tests across applications. |
| 2024‑04‑11 | [OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments](https://arxiv.org/abs/2404.07972) | desktop, linux, windows, macos | Introduces a real-computer evaluation environment with execution-based checks for tasks spanning desktop applications and operating-system state. |
| 2024‑02‑09 | [Understanding the Weakness of Large Language Model Agents within a Complex Android Environment](https://arxiv.org/abs/2402.06596) | android | Introduces AndroidArena and analyzes agent limitations in cross-application tasks, user constraints, exploration, and reflection. |
| 2024‑02‑08 | [UFO: A UI-Focused Agent for Windows OS Interaction](https://arxiv.org/abs/2402.07939) | windows, desktop | UFO uses two agents to inspect Windows application interfaces and their control metadata, then grounds and executes user requests within and across applications. The study evaluates this UI-focused architecture on nine Windows applications. |
