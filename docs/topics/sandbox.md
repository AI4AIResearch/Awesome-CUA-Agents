# Sandbox

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

36 source-reviewed resources tagged `sandbox`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Benchmarks (1)](#benchmarks) · [Frameworks (1)](#frameworks) · [Infrastructure (7)](#infrastructure) · [Products (5)](#products) · [Papers (22)](#papers)

## Benchmarks

All entries in this section: android.

| Resource | Paper | Scale | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [AppSim-Bench](https://github.com/Acrab-Agentic-Labs/AppSim) | [2609.07712](https://arxiv.org/abs/2609.07712) (2026) | [557 tasks](https://arxiv.org/abs/2609.07712) · [17 applications](https://raw.githubusercontent.com/Acrab-Agentic-Labs/AppSim/HEAD/README.md) | — | Simulated mobile applications and evaluation tooling for reproducible GUI-agent tasks with controlled application state. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/Acrab-Agentic-Labs/AppSim/HEAD/README.md) |

## Frameworks

All entries in this section: web, desktop.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [RedTeamCUA](https://github.com/OSU-NLP-Group/RedTeamCUA) | [2505.21936](https://arxiv.org/abs/2505.21936) (2025) | code Apache-2.0 | A controlled testing framework that combines desktop virtual machines and replicated websites to evaluate computer-use agents against indirect prompt injection. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/OSU-NLP-Group/RedTeamCUA/HEAD/README.md) |

## Infrastructure

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Agent Infra Sandbox](https://github.com/agent-infra/sandbox) | desktop, web | — | code Apache-2.0 | Sandbox environments supporting computer and browser interaction. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/agent-infra/sandbox/HEAD/README.md) |
| [AgentDesk](https://github.com/agentsea/agentdesk) | desktop | — | code MIT | Virtual desktop provisioning and control tools for agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/agentsea/agentdesk/HEAD/README.md) |
| [AndroidEnv](https://github.com/google-deepmind/android_env) | android | [2105.13231](https://arxiv.org/abs/2105.13231) (2021) | code Apache-2.0 | Android device-control platform with screenshots, accessibility telemetry, input actions, and an optional reinforcement-learning task interface. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/google-deepmind/android_env/HEAD/README.md) |
| [E2B Desktop](https://github.com/e2b-dev/desktop) | desktop, linux | — | code Apache-2.0 | Desktop sandboxes for computer-use agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/e2b-dev/desktop/HEAD/README.md) |
| [Lume](https://github.com/trycua/lume) | macos, linux | — | code MIT | Virtual machine management for local computer-use environments. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/trycua/lume/HEAD/README.md) |
| [ScienceBoard VMware environment](https://huggingface.co/OS-Copilot/ScienceBoard-Env) | linux, desktop | [2505.19897](https://arxiv.org/abs/2505.19897) (2025) | — | A prebuilt Ubuntu virtual-machine archive containing the software environment used for ScienceBoard scientific computer-use tasks. | [✓ 2026‑10‑17](https://huggingface.co/OS-Copilot/ScienceBoard-Env/raw/main/README.md) |
| [Steel Browser](https://github.com/steel-dev/steel-browser) | web | — | code Apache-2.0 | Browser infrastructure for agent applications. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/steel-dev/steel-browser/HEAD/README.md) |

## Products

| Resource | Publisher | Environments | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Browserbase Cloud](https://www.browserbase.com/) | [Browserbase](https://www.browserbase.com/) | web | Managed browser infrastructure for agent applications. | [✓ 2026‑10‑16](https://www.browserbase.com/) |
| [Browserless](https://www.browserless.io/) | [Browserless](https://www.browserless.io/) | web | Hosted browser infrastructure for automation applications. | [✓ 2026‑10‑16](https://www.browserless.io/) |
| [E2B](https://e2b.dev/) | [E2B](https://e2b.dev/) | desktop | Sandbox infrastructure for executing agent workloads. | [✓ 2026‑10‑16](https://e2b.dev/) |
| [Hyperbrowser](https://www.hyperbrowser.ai/) | [Hyperbrowser](https://www.hyperbrowser.ai/) | web | Browser infrastructure and automation services for AI agents. | [✓ 2026‑10‑16](https://www.hyperbrowser.ai/) |
| [Steel Cloud](https://steel.dev/) | [Steel](https://steel.dev/) | web | Managed browser infrastructure associated with Steel Browser. | [✓ 2026‑10‑16](https://steel.dev/) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑10‑14 | [MAI-Gym: An Open All-in-One Platform for GUI Agent Evaluation and RL Training across Mobile and Computer Environments](https://arxiv.org/abs/2610.20939) | cross-platform, desktop, web | Unifies GUI evaluation, trajectory collection, environment synthesis, and online reinforcement learning across mobile, computer, and web tasks. |
| 2026‑10‑08 | [SoftwareGym: Scaling Computer-Use Agent Training with Diverse Synthesized Software Environments](https://arxiv.org/abs/2610.12611) | unspecified | Introduces SoftwareGym, a pipeline that synthesizes runnable GUI applications and iteratively repairs them using execution checks. It also provides a task benchmark and studies whether training on synthesized application trajectories transfers to other computer-use environments. |
| 2026‑09‑26 | [CUA-Sandbox: Efficient Environments for Computer-Use Agent Reinforcement Learning](https://arxiv.org/abs/2609.32750) | web, desktop | Introduces CUA-Sandbox, which separates each rollout’s mutable state from shared initialized software runtimes. State-scoped execution and transactional resets or branches aim to reduce training-environment costs while retaining original interfaces and evaluators. |
| 2026‑09‑07 | [APPSim-Bench: Bridging Real-world Apps and Reproducible Evaluation for Mobile GUI Agents](https://arxiv.org/abs/2609.07712) | unspecified | Introduces controlled simulated mobile apps with deterministic backend data and outcome checks for reproducible evaluation of realistic interactions. |
| 2026‑09‑04 | [CUA-Universe: A Scalable and Dynamic Environment for Hybrid GUI+CLI Agents](https://arxiv.org/abs/2609.05374) | desktop | Turns desktop applications into reproducible GUI-and-CLI environments and generates verified hybrid trajectories for agent post-training. |
| 2026‑08‑25 | [BrowserForge: Scaling Web Episode via Parallel Browser Sandboxes](https://arxiv.org/abs/2608.24848) | web | Introduces BrowserForge, which combines broad website sourcing, parallel browser sandboxes, and task-proposer/solver interaction to collect verified web trajectories. The pipeline uses page structure during synthesis but trains a policy that acts from screenshots. |
| 2026‑08‑22 | [Training Needs Trustworthy Worlds: Verified Synthetic Web Environments for Agent Learning](https://arxiv.org/abs/2608.21898) | web | Builds synthetic websites with verified navigation, backend state, and feasible tasks to provide reliable supervision for web-agent training. |
| 2026‑07‑30 | [Echoverse: Deep, Evolving Environments for Training Computer-Use Agents at Scale](https://arxiv.org/abs/2607.28074) | web | Introduces Echoverse, which compiles specifications into stateful applications with database-grounded graders and uses rollouts to improve both the environments and agent policies. It examines behavioral depth, targeted interface practice, and environment repair as sources of training value. |
| 2025‑11‑11 | [OSGym: Scalable OS Infra for Computer Use Agents](https://arxiv.org/abs/2511.11672) | unspecified | OSGym supplies full operating-system sandboxes with GUIs for parallel computer-use data collection and training. It combines per-replica state management, hardware-aware orchestration, copy-on-write virtual-machine disks, and layered failure recovery. |
| 2025‑10‑17 | [WEBSERV: A Full-Stack and RL-Ready Web Environment for Training Web Agents at Scale](https://arxiv.org/abs/2510.16252) | web | WebServ combines copy-on-write container environments with a compact DOM-derived browser interface for training web agents. Network-aware waiting supports action execution in single-page applications, with evaluations and reinforcement-learning experiments on WebArena-Lite. |
| 2025‑10‑10 | [WARC-Bench: Web Archive Based Benchmark for GUI Subtask Executions](https://arxiv.org/abs/2510.09872) | web | WARC-Bench packages dynamic web pages as replayable archives and evaluates short navigation subtasks involving components such as date pickers and scrollable containers. It also studies supervised training followed by reinforcement learning with verifiable rewards on these browser interactions. |
| 2025‑09‑30 | [SCUBA: Salesforce Computer Use Benchmark](https://arxiv.org/abs/2509.26506) | unspecified | SCUBA evaluates enterprise UI navigation and CRM workflows with 300 task instances derived from Salesforce user interviews. Salesforce sandbox execution and milestone-based assessment support comparisons between zero-shot agents and agents given demonstrations. |
| 2025‑09‑28 | [Efficient Multi-turn RL for GUI Agents via Decoupled Training and Adaptive Data Curation](https://arxiv.org/abs/2509.23866) | desktop | DART separates GUI reinforcement learning into asynchronous environment, rollout, data-management, and training services. It curates experience by task difficulty, successful trajectories, and step uncertainty while correcting rollout-policy mismatch, with evaluation on OSWorld. |
| 2025‑09‑22 | [Orcust: Stepwise-Feedback Reinforcement Learning for GUI Agent](https://arxiv.org/abs/2509.17917) | unspecified | Orcust combines principle-constrained reward modeling with GUI trajectory collection in instrumented virtual machines. Environment-checkable and model-derived principles guide stepwise feedback for grounding, basic operations, and complete task execution. |
| 2025‑09‑02 | [UI-TARS-2 Technical Report: Advancing GUI Agent with Multi-Turn Reinforcement Learning](https://arxiv.org/abs/2509.02544) | web, desktop, windows, android, cross-platform | UI-TARS-2 combines scalable trajectory generation, stabilized multi-turn reinforcement learning, and a sandbox that supports GUI, filesystem, and terminal actions. The report evaluates the resulting agent across web, desktop, Android, and game tasks and analyzes training stability. |
| 2025‑08‑18 | [WebMall -- A Multi-Shop Benchmark for Evaluating Web Agents](https://arxiv.org/abs/2508.13024) | web | WebMall provides four simulated online shops with heterogeneous product data for comparison shopping, related-product searches, and checkout tasks. It evaluates web agents with different observation formats and memory configurations in a fixed offline environment. |
| 2025‑06‑09 | [MCPWorld: A Unified Benchmarking Testbed for API, GUI, and Hybrid Computer Use Agents](https://arxiv.org/abs/2506.07672) | desktop | MCPWorld evaluates API, GUI, and hybrid computer-use agents with 201 tasks in applications whose source can be instrumented and extended with MCP support. It verifies completion from application behavior and packages the testbed in containers with GPU support. |
| 2025‑05‑28 | [RedTeamCUA: Realistic Adversarial Testing of Computer-Use Agents in Hybrid Web-OS Environments](https://arxiv.org/abs/2505.21936) | web, desktop | RedTeamCUA combines a virtual-machine OS environment with containerized websites for controlled prompt-injection tests spanning both interfaces. Its RTC-Bench contains 864 examples and can initialize agents at injection points to separate attack susceptibility from navigation failures. |
| 2024‑12‑06 | [The BrowserGym Ecosystem for Web Agent Research](https://arxiv.org/abs/2412.05467) | web | Describes BrowserGym's shared web interaction environment and AgentLab tooling for consistent experiments across multiple agent benchmarks. |
| 2024‑03‑26 | [AgentStudio: A Toolkit for Building General Virtual Agents](https://arxiv.org/abs/2403.17918) | unspecified | AgentStudio combines an interactive GUI/API environment with tools for creating tasks, annotating interface elements, and labeling actions in videos. Its online suite and GroundUI, IDMBench, and CriticBench datasets examine interaction, grounding, learning from video, and success detection. |
| 2023‑05‑14 | [Mobile-Env: Building Qualified Evaluation Benchmarks for LLM-GUI Interaction](https://arxiv.org/abs/2305.08144) | android | Provides an Android benchmark toolkit with controlled environments, intermediate feedback, and task sets for reproducible GUI-agent evaluation. |
| 2021‑05‑27 | [AndroidEnv: A Reinforcement Learning Platform for Android](https://arxiv.org/abs/2105.13231) | android | Presents an Android environment for training and evaluating reinforcement-learning agents through touchscreen interaction. |
