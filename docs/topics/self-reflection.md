# Self-reflection

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

10 source-reviewed resources tagged `self-reflection`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Models (2)](#models) · [Frameworks (1)](#frameworks) · [Papers (7)](#papers)

## Models

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [InfiGUI-R1 3B](https://huggingface.co/InfiX-ai/InfiGUI-R1-3B) | web, desktop, android | [2504.14239](https://arxiv.org/abs/2504.14239) (2025) | weights apache-2.0 | A Qwen2.5-VL checkpoint trained with the Actor2Reasoner procedure to combine interface grounding with planning and recovery reasoning. | [✓ 2026-10-17](https://huggingface.co/InfiX-ai/InfiGUI-R1-3B/raw/main/README.md) |
| [OpenCUA 32B](https://huggingface.co/xlangai/OpenCUA-32B) | desktop, linux, windows, macos | [2508.09123](https://arxiv.org/abs/2508.09123) (2025) | weights mit | A Qwen2.5-VL-based computer-use checkpoint that combines screenshot history with planning and grounded executable actions. | [✓ 2026-10-17](https://huggingface.co/xlangai/OpenCUA-32B/raw/main/README.md) |

## Frameworks

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Agent-R](https://github.com/ByteDance-Seed/Agent-R) | web | [2501.11425](https://arxiv.org/abs/2501.11425) (2025) | code Apache-2.0 | Trajectory collection and revision utilities that use tree search and model-guided critique to train agents to recover from mistakes, including WebShop tasks. | [✓ 2026-10-17](https://raw.githubusercontent.com/ByteDance-Seed/Agent-R/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026-08-25 | [Reflection with Action-Induced Visual Differences for Desktop GUI Agents](https://arxiv.org/abs/2608.24015) | desktop, windows | Introduces Evidence-First Reflection, which separates extraction of action-induced screen changes from judgment of whether an operation achieved its objective. It filters visual differences into relevant evidence before a desktop agent’s reflector decides how execution should continue. |
| 2026-07-27 | [Falsifiable Commitment Planning for Self-Correcting Web Agents](https://arxiv.org/abs/2607.24167) | web | Introduces FCPAgent, which attaches confirming and falsifying evidence to each skill-grounded plan step. A plan–test–repair loop checks actions and observations, then localizes contradictions so execution, skills, or plans can be revised at the appropriate level. |
| 2026-03-16 | [GUI-CEval: A Hierarchical and Comprehensive Chinese Benchmark for Mobile GUI Agents](https://arxiv.org/abs/2603.15039) | unspecified | GUI-CEval evaluates Chinese mobile GUI agents through a hierarchy of atomic abilities and application-level tasks collected on physical devices. Its diagnostics cover perception, planning, reflection, execution and post-action evaluation across a broad set of apps. |
| 2026-01-08 | [GUITester: Enabling GUI Agents for Exploratory Defect Discovery](https://arxiv.org/abs/2601.04500) | unspecified | Introduces GUITestBench for interactive defect discovery and GUITester, which separates task navigation from anomaly verification. Testing-oriented plans and history-based reflection help distinguish software defects from agent execution mistakes. |
| 2025-07-21 | [MobileUse: A GUI Agent with Hierarchical Reflection for Autonomous Mobile Operation](https://arxiv.org/abs/2507.16853) | android | MobileUse reflects on errors at action and task timescales, invoking reflection when needed and using proactive exploration to learn unfamiliar apps. It evaluates this mobile execution framework on AndroidWorld and AndroidLab and describes a toolkit for physical-device operation. |
| 2024-02-23 | [On the Multi-turn Instruction Following for Conversational Web Agents](https://arxiv.org/abs/2402.15057) | web | MT-Mind2Web evaluates web navigation through sequences of conversational user instructions. Self-MAP combines memory-augmented planning with reflection to preserve context and dependencies across those interaction turns. |
| 2023-10-12 | [A Zero-Shot Language Agent for Computer Control with Structured Reflection](https://arxiv.org/abs/2310.08740) | web | Studies a zero-shot computer-control agent that plans executable actions and organizes its own reflections after mistakes. MiniWoB++ experiments examine learning to complete tasks without supplied expert trajectories. |
