# Self-reflection

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

21 source-reviewed resources tagged `self-reflection`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Models (3)](#models) · [Agents (1)](#agents) · [Frameworks (1)](#frameworks) · [Papers (16)](#papers)

## Models

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [InfiGUI-R1 3B](https://huggingface.co/InfiX-ai/InfiGUI-R1-3B) | web, desktop, android | [2504.14239](https://arxiv.org/abs/2504.14239) (2025) | weights apache-2.0 | A Qwen2.5-VL checkpoint trained with the Actor2Reasoner procedure to combine interface grounding with planning and recovery reasoning. | [✓ 2026‑10‑17](https://huggingface.co/InfiX-ai/InfiGUI-R1-3B/raw/main/README.md) |
| [OpenCUA 32B](https://huggingface.co/xlangai/OpenCUA-32B) | desktop, linux, windows, macos | [2508.09123](https://arxiv.org/abs/2508.09123) (2025) | weights mit | A Qwen2.5-VL-based computer-use checkpoint that combines screenshot history with planning and grounded executable actions. | [✓ 2026‑10‑17](https://huggingface.co/xlangai/OpenCUA-32B/raw/main/README.md) |
| [OpenCUA 72B](https://huggingface.co/xlangai/OpenCUA-72B) | desktop, linux, windows, macos | [2508.09123](https://arxiv.org/abs/2508.09123) (2025) | weights mit | A Qwen2.5-VL-based computer-use checkpoint that combines screenshot history and reflective reasoning to predict executable desktop actions. | [✓ 2026‑10‑17](https://huggingface.co/xlangai/OpenCUA-72B/raw/main/README.md) |

## Agents

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [RCI Agent](https://github.com/posgnu/rci-agent) | [2303.17491](https://arxiv.org/abs/2303.17491) (2023) | code MIT | A MiniWoB++ agent that uses explicit and implicit recursive criticism-and-improvement prompts to refine action plans and ground actions to browser state. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/posgnu/rci-agent/HEAD/README.md) |

## Frameworks

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Agent-R](https://github.com/ByteDance-Seed/Agent-R) | [2501.11425](https://arxiv.org/abs/2501.11425) (2025) | code Apache-2.0 | Trajectory collection and revision utilities that use tree search and model-guided critique to train agents to recover from mistakes, including WebShop tasks. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/ByteDance-Seed/Agent-R/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑08‑25 | [Reflection with Action-Induced Visual Differences for Desktop GUI Agents](https://arxiv.org/abs/2608.24015) | desktop, windows | Introduces Evidence-First Reflection, which separates extraction of action-induced screen changes from judgment of whether an operation achieved its objective. It filters visual differences into relevant evidence before a desktop agent’s reflector decides how execution should continue. |
| 2026‑07‑27 | [Falsifiable Commitment Planning for Self-Correcting Web Agents](https://arxiv.org/abs/2607.24167) | web | Introduces FCPAgent, which attaches confirming and falsifying evidence to each skill-grounded plan step. A plan–test–repair loop checks actions and observations, then localizes contradictions so execution, skills, or plans can be revised at the appropriate level. |
| 2026‑03‑16 | [GUI-CEval: A Hierarchical and Comprehensive Chinese Benchmark for Mobile GUI Agents](https://arxiv.org/abs/2603.15039) | unspecified | GUI-CEval evaluates Chinese mobile GUI agents through a hierarchy of atomic abilities and application-level tasks collected on physical devices. Its diagnostics cover perception, planning, reflection, execution and post-action evaluation across a broad set of apps. |
| 2026‑01‑22 | [EvoCUA: Evolving Computer Use Agents via Learning from Scalable Synthetic Experience](https://arxiv.org/abs/2601.15876) | desktop | EvoCUA combines task synthesis with executable validators, asynchronous sandbox rollouts and iterative policy updates. It turns successful routines and analyzed failures into supervision and evaluates the evolving agent on OSWorld. |
| 2026‑01‑12 | [OS-Symphony: A Holistic Framework for Robust and Generalist Computer-Using Agent](https://arxiv.org/abs/2601.07779) | desktop, web | OS-Symphony coordinates milestone-based reflection and memory with tools that build visually aligned tutorials through browser interaction. The framework evaluates trajectory correction and adaptation on online computer-use benchmarks including OSWorld. |
| 2026‑01‑08 | [GUITester: Enabling GUI Agents for Exploratory Defect Discovery](https://arxiv.org/abs/2601.04500) | unspecified | Introduces GUITestBench for interactive defect discovery and GUITester, which separates task navigation from anomaly verification. Testing-oriented plans and history-based reflection help distinguish software defects from agent execution mistakes. |
| 2025‑11‑25 | ["Are We Done Yet?": A Vision-Based Judge for Autonomous Task Completion of Computer Use Agents](https://arxiv.org/abs/2511.20067) | macos | This study tests vision-language models as task-completion judges using screenshots and instructions from 42 built-in macOS applications. It evaluates judgment accuracy on human-labeled tasks and separately studies how judge feedback affects agent task success. |
| 2025‑11‑12 | [History-Aware Reasoning for GUI Agents](https://arxiv.org/abs/2511.09127) | unspecified | HAR-GUI combines episodic reasoning and short-term memory to use earlier interactions when selecting GUI actions. Its training constructs reflective scenarios and correction guidance and applies a hybrid reinforcement-learning reward to the 3B policy. |
| 2025‑07‑21 | [MobileUse: A GUI Agent with Hierarchical Reflection for Autonomous Mobile Operation](https://arxiv.org/abs/2507.16853) | android | MobileUse reflects on errors at action and task timescales, invoking reflection when needed and using proactive exploration to learn unfamiliar apps. It evaluates this mobile execution framework on AndroidWorld and AndroidLab and describes a toolkit for physical-device operation. |
| 2025‑05‑28 | [UI-Evol: Automatic Knowledge Evolving for Computer Use Agents](https://arxiv.org/abs/2505.21964) | desktop | Introduces UI-Evol, which extracts action sequences from agent interactions and critiques external guidance against those traces. Evaluation on OSWorld examines how revised operational knowledge affects execution and behavioral consistency. |
| 2025‑05‑26 | [WebCoT: Enhancing Web Agent Reasoning by Reconstructing Chain-of-Thought in Reflection, Branching, and Rollback](https://arxiv.org/abs/2505.20013) | web | WebCoT turns reflection, look-ahead, branching and rollback procedures into chain-of-thought training rationales. Fine-tuning on these reconstructed trajectories is evaluated for web-agent self-improvement and transfer across navigation tasks. |
| 2025‑04‑22 | [Guiding VLM Agents with Process Rewards at Inference Time for GUI Navigation](https://arxiv.org/abs/2504.16073) | unspecified | Guides visual GUI agents at inference time with a process-reward model that evaluates intermediate actions. It combines stepwise guidance with trajectory reflection and retry mechanisms in static and interactive navigation tasks. |
| 2024‑11‑06 | [From Novice to Expert: LLM Agent Policy Optimization via Step-wise Reinforcement Learning](https://arxiv.org/abs/2411.03817) | web | Introduces StepAgent, which compares agent and expert actions to supply intermediate rewards for policy learning, with implicit-reward and inverse-RL variants. Evaluation includes WebShop and Mind2Web alongside non-web tasks. |
| 2024‑02‑23 | [On the Multi-turn Instruction Following for Conversational Web Agents](https://arxiv.org/abs/2402.15057) | web | MT-Mind2Web evaluates web navigation through sequences of conversational user instructions. Self-MAP combines memory-augmented planning with reflection to preserve context and dependencies across those interaction turns. |
| 2023‑10‑12 | [A Zero-Shot Language Agent for Computer Control with Structured Reflection](https://arxiv.org/abs/2310.08740) | web | Studies a zero-shot computer-control agent that plans executable actions and organizes its own reflections after mistakes. MiniWoB++ experiments examine learning to complete tasks without supplied expert trajectories. |
| 2023‑03‑30 | [Language Models can Solve Computer Tasks](https://arxiv.org/abs/2303.17491) | web | Introduces recursive criticism and improvement prompting for language-model agents performing computer tasks, evaluated on MiniWoB++ with a small number of demonstrations per task. |
