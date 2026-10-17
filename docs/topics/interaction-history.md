# Interaction history

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

15 source-reviewed resources tagged `interaction-history`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Models (1)](#models) · [Papers (14)](#papers)

## Models

All entries in this section: android, desktop.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Aria-UI context-aware checkpoint](https://huggingface.co/Aria-UI/Aria-UI-context-aware) | [2412.16256](https://arxiv.org/abs/2412.16256) (2024) | — | The context-aware Aria-UI release that uses interaction context to support grounding in dynamic Android and desktop agent tasks. | [✓ 2026‑10‑17](https://huggingface.co/api/models/Aria-UI/Aria-UI-context-aware) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2025‑12‑01 | [HiconAgent: History Context-aware Policy Optimization for GUI Agents](https://arxiv.org/abs/2512.01763) | android | HiconAgent trains GUI policies to use history through variable-length context sampling and paired policy updates with compressed and complete histories. Its compression retains past actions while removing historical observations, and an alignment loss couples the two branches. |
| 2025‑11‑12 | [History-Aware Reasoning for GUI Agents](https://arxiv.org/abs/2511.09127) | unspecified | HAR-GUI combines episodic reasoning and short-term memory to use earlier interactions when selecting GUI actions. Its training constructs reflective scenarios and correction guidance and applies a hybrid reinforcement-learning reward to the 3B policy. |
| 2025‑10‑01 | [GUI-KV: Efficient GUI Agents via KV Cache with Spatio-Temporal Awareness](https://arxiv.org/abs/2510.00536) | unspecified | GUI-KV compresses vision-language agents’ attention caches using visual-token saliency and redundancy between screenshot frames. The method requires no retraining and evaluates how cache budgets affect GUI action accuracy and computational cost. |
| 2025‑10‑01 | [PAL-UI: Planning with Active Look-back for Vision-Based GUI Agents](https://arxiv.org/abs/2510.00413) | web, cross-platform | PAL-UI combines observation/action summaries with selective retrieval of historical screenshots during planning. It trains mobile navigation models from step-level supervision and evaluates transfer to web navigation without additional training. |
| 2025‑07‑04 | [Less is More: Empowering GUI Agent with Context-Aware Simplification](https://arxiv.org/abs/2507.03730) | web, cross-platform | SimpAgent prunes distracting interface elements with visual masks and compresses interaction history using consistency-based guidance. The study evaluates these two forms of context reduction during GUI navigation in web and mobile environments. |
| 2025‑05‑27 | [UI-Genie: A Self-Improving Approach for Iteratively Boosting MLLM-based Mobile GUI Agents](https://arxiv.org/abs/2505.21496) | unspecified | UI-Genie jointly improves a mobile GUI agent and a reward model that processes screenshots with interaction history and supplies action- and task-level feedback. Its data pipeline uses rule-based verification, corrupted trajectories, and hard negatives to support reward-guided exploration and iterative training. |
| 2025‑05‑01 | [ScaleTrack: Scaling and back-tracking Automated GUI Agents](https://arxiv.org/abs/2505.00416) | unspecified | ScaleTrack combines a unified collection of GUI grounding samples with a planning objective that predicts the next action while reconstructing prior actions. This backward prediction links the current screenshot to interaction history during agent training. |
| 2024‑10‑31 | [From Context to Action: Analysis of the Impact of State Representation and Context on the Generalization of Multi-Turn Web Navigation Agents](https://arxiv.org/abs/2410.23555) | web | Analyzes how interaction history and webpage representation affect multiturn web-agent generalization across unfamiliar websites, task categories, and geographic settings. |
| 2024‑10‑23 | [Lightweight Neural App Control](https://arxiv.org/abs/2410.17883) | android | LiMAC combines a compact Action Transformer with a fine-tuned vision-language model for Android app control. It uses textual goals and histories of screenshots and UI trees to predict actions, with evaluation on two mobile-control datasets. |
| 2024‑10‑01 | [Dynamic Planning for LLM-based Graphical User Interface Automation](https://arxiv.org/abs/2410.00467) | unspecified | Dynamic Planning of Thoughts revises a mobile GUI plan using current environmental feedback and execution history. The study compares this planning strategy with long-dialogue prompting and examines its behavior on unfamiliar tasks and different language-model backbones. |
| 2024‑06‑20 | [Identifying User Goals from UI Trajectories](https://arxiv.org/abs/2406.14314) | android, web, cross-platform | Defines goal identification from observed UI trajectories and an evaluation method for comparing intent descriptions within the same interface context. Experiments reuse Android and web automation data to compare human and model inference of users’ detailed goals. |
| 2024‑04‑12 | [Training a Vision Language Model as Smartphone Assistant](https://arxiv.org/abs/2404.08755) | android | Trains a smartphone assistant from sequences of screenshots paired with earlier actions. The model predicts UI-only interactions such as taps and swipes, with evaluation on Android in the Wild. |
| 2023‑10‑20 | [AllTogether: Investigating the Efficacy of Spliced Prompt for Web Navigation using Large Language Models](https://arxiv.org/abs/2310.18331) | web | AllTogether standardizes prompts for HTML-based web navigation and compares prompting with instruction fine-tuning. Its analysis examines how HTML context, interaction history, and current environmental feedback affect task execution. |
| 1991 | [Eager: Programming Repetitive Tasks by Example](https://acypher.com/Publications/CHI91/EagerCHI.html) | desktop | Describes Eager, which detects repeated HyperCard interactions, generalizes them into loops, and previews predicted actions by highlighting interface objects. Users can then ask it to execute the inferred repetitive task. |
