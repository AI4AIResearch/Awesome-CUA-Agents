# History

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

10 source-reviewed resources tagged `history`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Models (1)](#models) · [Products (1)](#products) · [Papers (8)](#papers)

## Models

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Aria-UI context-aware checkpoint](https://huggingface.co/Aria-UI/Aria-UI-context-aware) | android, desktop | [2412.16256](https://arxiv.org/abs/2412.16256) (2024) | — | The context-aware Aria-UI release that uses interaction context to support grounding in dynamic Android and desktop agent tasks. | [✓ 2026-10-17](https://huggingface.co/api/models/Aria-UI/Aria-UI-context-aware) |

## Products

| Resource | Publisher | Environments | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Operator](https://openai.com/index/introducing-operator/) | [OpenAI](https://openai.com/index/computer-using-agent/) | web | Historical OpenAI browser-agent research preview. | [✓ 2026-10-16](https://openai.com/index/introducing-operator/) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2025-07-04 | [Less is More: Empowering GUI Agent with Context-Aware Simplification](https://arxiv.org/abs/2507.03730) | web, cross-platform | SimpAgent prunes distracting interface elements with visual masks and compresses interaction history using consistency-based guidance. The study evaluates these two forms of context reduction during GUI navigation in web and mobile environments. |
| 2025-05-27 | [UI-Genie: A Self-Improving Approach for Iteratively Boosting MLLM-based Mobile GUI Agents](https://arxiv.org/abs/2505.21496) | unspecified | UI-Genie jointly improves a mobile GUI agent and a reward model that processes screenshots with interaction history and supplies action- and task-level feedback. Its data pipeline uses rule-based verification, corrupted trajectories, and hard negatives to support reward-guided exploration and iterative training. |
| 2025-05-01 | [ScaleTrack: Scaling and back-tracking Automated GUI Agents](https://arxiv.org/abs/2505.00416) | unspecified | ScaleTrack combines a unified collection of GUI grounding samples with a planning objective that predicts the next action while reconstructing prior actions. This backward prediction links the current screenshot to interaction history during agent training. |
| 2024-10-23 | [Lightweight Neural App Control](https://arxiv.org/abs/2410.17883) | android | LiMAC combines a compact Action Transformer with a fine-tuned vision-language model for Android app control. It uses textual goals and histories of screenshots and UI trees to predict actions, with evaluation on two mobile-control datasets. |
| 2024-10-01 | [Dynamic Planning for LLM-based Graphical User Interface Automation](https://arxiv.org/abs/2410.00467) | unspecified | Dynamic Planning of Thoughts revises a mobile GUI plan using current environmental feedback and execution history. The study compares this planning strategy with long-dialogue prompting and examines its behavior on unfamiliar tasks and different language-model backbones. |
| 2024-06-20 | [Identifying User Goals from UI Trajectories](https://arxiv.org/abs/2406.14314) | android, web, cross-platform | Defines goal identification from observed UI trajectories and an evaluation method for comparing intent descriptions within the same interface context. Experiments reuse Android and web automation data to compare human and model inference of users’ detailed goals. |
| 2024-04-12 | [Training a Vision Language Model as Smartphone Assistant](https://arxiv.org/abs/2404.08755) | android | Trains a smartphone assistant from sequences of screenshots paired with earlier actions. The model predicts UI-only interactions such as taps and swipes, with evaluation on Android in the Wild. |
| 2023-10-20 | [AllTogether: Investigating the Efficacy of Spliced Prompt for Web Navigation using Large Language Models](https://arxiv.org/abs/2310.18331) | web | AllTogether standardizes prompts for HTML-based web navigation and compares prompting with instruction fine-tuning. Its analysis examines how HTML context, interaction history, and current environmental feedback affect task execution. |
