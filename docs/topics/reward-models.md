# Reward models

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

22 source-reviewed resources tagged `reward-models`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Benchmarks (3)](#benchmarks) · [Datasets (3)](#datasets) · [Models (4)](#models) · [Frameworks (1)](#frameworks) · [Tools (1)](#tools) · [Papers (10)](#papers)

## Benchmarks

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [AgentRewardBench](https://github.com/McGill-NLP/agent-reward-bench) | web | [2504.08942](https://arxiv.org/abs/2504.08942) (2025) | data Custom AgentRewardBench Terms of Use | A benchmark and evaluation toolkit for comparing automatic web-agent judges against expert judgments of task success, side effects and repetition. | [✓ 2026-10-17](https://raw.githubusercontent.com/McGill-NLP/agent-reward-bench/HEAD/README.md) |
| [CUAVerifierBench](https://huggingface.co/datasets/microsoft/CUAVerifierBench) | web | [2604.06240](https://arxiv.org/abs/2604.06240) (2026) | — | Human-annotated browser-agent trajectories for comparing automated task-success and process-quality verifiers against reviewer judgments. | [✓ 2026-10-17](https://huggingface.co/datasets/microsoft/CUAVerifierBench/raw/main/README.md) |
| [WebRewardBench](https://huggingface.co/datasets/LangAGI-Lab/WebRewardBench) | web | [2505.15277](https://arxiv.org/abs/2505.15277) (2025) | — | An offline preference-evaluation set for web process reward models, pairing page and trajectory context with preferred and rejected candidate decisions. | [✓ 2026-10-17](https://huggingface.co/datasets/LangAGI-Lab/WebRewardBench/raw/main/README.md) |

## Datasets

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [UI-Genie reward data](https://huggingface.co/datasets/HanXiao1999/UI-Genie-RM-517k) | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | data mit | Mobile GUI reward annotations released for training UI-Genie’s trajectory-assessment model. | [✓ 2026-10-17](https://huggingface.co/datasets/HanXiao1999/UI-Genie-RM-517k/raw/main/README.md) |
| [WebPRM checklist-generation data](https://huggingface.co/datasets/LangAGI-Lab/WebPRMCollection_checklist_generation) | web | — | — | Web-task context, starting observations and action history paired with structured checklists and subgoal analyses for checklist generation. | [✓ 2026-10-17](https://huggingface.co/api/datasets/LangAGI-Lab/WebPRMCollection_checklist_generation) |
| [WebPRM Collection preference data](https://huggingface.co/datasets/LangAGI-Lab/WebPRMCollection_preference_pair) | web | [2505.15277](https://arxiv.org/abs/2505.15277) (2025) | — | Checklist-annotated web decision records with page observations, prior actions, one preferred continuation and rejected alternatives for process-reward learning. | [✓ 2026-10-17](https://huggingface.co/datasets/LangAGI-Lab/WebPRMCollection_preference_pair/raw/main/README.md) |

## Models

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [GUI-G2 7B](https://huggingface.co/inclusionAI/GUI-G2-7B) | cross-platform | [2507.15846](https://arxiv.org/abs/2507.15846) (2025) | weights apache-2.0 | A Qwen2.5-VL grounding checkpoint trained with Gaussian point and coverage rewards whose granularity adapts to interface-element scale. | [✓ 2026-10-17](https://huggingface.co/inclusionAI/GUI-G2-7B/raw/main/README.md) |
| [WebJudge 7B](https://huggingface.co/osunlp/WebJudge-7B) | web | [2504.01382](https://arxiv.org/abs/2504.01382) (2025) | weights apache-2.0 | A visual trajectory judge that retains selected intermediate screenshots to evaluate whether a web agent completed its task. | [✓ 2026-10-17](https://huggingface.co/osunlp/WebJudge-7B/raw/main/README.md) |
| [WebRL outcome reward model 8B](https://huggingface.co/zai-org/webrl-orm-llama-3.1-8b) | web | [2411.02337](https://arxiv.org/abs/2411.02337) (2024) | — | The outcome-supervision checkpoint used by WebRL to score browser trajectories during policy training. | [✓ 2026-10-17](https://huggingface.co/api/models/zai-org/webrl-orm-llama-3.1-8b) |
| [WebShepherd 3B](https://huggingface.co/LangAGI-Lab/WebShepherd_3B) | web | — | — | A public text-based process-reward checkpoint from the Web-Shepherd collection for scoring web-agent decisions against task checklists. | [✓ 2026-10-17](https://huggingface.co/api/models/LangAGI-Lab/WebShepherd_3B) |

## Frameworks

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [UI-Genie](https://github.com/Euphoria16/UI-Genie) | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | — | Training and evaluation code for a mobile-agent framework that iteratively generates trajectories using agent and reward-model feedback. | [✓ 2026-10-17](https://raw.githubusercontent.com/Euphoria16/UI-Genie/HEAD/README.md) |

## Tools

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Web-Shepherd inference and evaluation](https://github.com/kyle8581/Web-Shepherd) | web | — | — | Process-reward inference and benchmark-evaluation utilities that use task checklists to assess individual web-agent decisions. | [✓ 2026-10-17](https://raw.githubusercontent.com/kyle8581/Web-Shepherd/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026-09-26 | [From Trajectories to Grounded Preferences: Process Preference Synthesis via Interaction Element Graphs for Web PRMs](https://arxiv.org/abs/2609.32351) | web | Introduces SURFPRM, which turns web demonstrations into an interaction-element graph for synthesizing grounded negative actions. Its contrastive preference data trains process reward models to distinguish plausible on-page alternatives and guide downstream trajectory search. |
| 2026-08-25 | [Task-Adaptive Rubrics for GUI Reward Modeling](https://arxiv.org/abs/2608.24174) | unspecified | Introduces AdaptRubric, which retrieves reusable criteria for a GUI task family and then generates instruction-specific checks for concrete values and constraints. It evaluates these adaptive rubrics in offline reward assessment and online agent optimization. |
| 2026-08-24 | [GSAR: Goal-State-Anchor Rewards for Mobile GUI Agents with Self-Evolving Data Synthesis](https://arxiv.org/abs/2608.22847) | android | Introduces GSAR, which synthesizes GUI tasks and successful goal states, then annotates task-relevant interface elements as reward anchors. These anchors support offline trajectory verification and online policy training. |
| 2026-07-30 | [OSReward: Instituting Standardized Evaluation for Cross-Platform Computer-Use Reward Models](https://arxiv.org/abs/2607.28609) | cross-platform | Introduces OSReward and its harder and multidimensional variants for assessing judgments of computer-use trajectories. It also releases a reasoning-annotated judgment corpus and trains reward models, examining reliability, leniency bias, and evaluation cost. |
| 2026-07-28 | [Interactive Reward Agent: GUI Task Evaluation via Environment-State Verification](https://arxiv.org/abs/2607.25904) | desktop, linux | Introduces an Interactive Reward Agent that proposes completion conditions and verifies them using system, application, and GUI tools after execution. GUI-RewardBench provides annotated desktop trajectories for evaluating these evidence-based judgments and their use in reinforcement learning. |
| 2026-07-25 | [SeekJudge: A Practical Reward Framework for Reinforcement Learning in Computer-Use Agents](https://arxiv.org/abs/2607.23263) | unspecified | Introduces SeekJudge, which iteratively searches and analyzes GUI trajectories to assess instruction fulfillment. The work combines dense judgment-data synthesis, a step-label benchmark, and reward-server scheduling to study accurate and practical reward feedback for agent training. |
| 2025-09-22 | [Orcust: Stepwise-Feedback Reinforcement Learning for GUI Agent](https://arxiv.org/abs/2509.17917) | unspecified | Orcust combines principle-constrained reward modeling with GUI trajectory collection in instrumented virtual machines. Environment-checkable and model-derived principles guide stepwise feedback for grounding, basic operations, and complete task execution. |
| 2025-09-17 | [TGPO: Tree-Guided Preference Optimization for Robust Web Agent Reinforcement Learning](https://arxiv.org/abs/2509.14172) | web | TGPO merges semantically equivalent web states into tree-structured trajectories for offline preference optimization. A process reward model scores subgoal progress, redundant behavior, and action validity, while dynamic weighting emphasizes consequential decisions. |
| 2025-08-15 | [CRAFT-GUI: Curriculum-Reinforced Agent For GUI Tasks](https://arxiv.org/abs/2508.11360) | android | CRAFT-GUI organizes GUI trajectories by difficulty for curriculum-based GRPO training. Its reward combines rule-based signals with model judgments, with evaluation on Android Control and an internal online benchmark. |
| 2025-07-21 | [GUI-G$^2$: Gaussian Reward Modeling for GUI Grounding](https://arxiv.org/abs/2507.15846) | unspecified | GUI-G2 replaces binary grounding rewards with Gaussian point rewards and spatial-coverage rewards. An adaptive variance tied to element dimensions supplies continuous training feedback for targets of different sizes, evaluated on the ScreenSpot benchmark family. |
