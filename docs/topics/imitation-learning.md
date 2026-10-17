# Imitation learning

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

19 source-reviewed resources tagged `imitation-learning`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Datasets (5)](#datasets) · [Models (3)](#models) · [Frameworks (3)](#frameworks) · [Papers (8)](#papers)

## Datasets

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Go-Browse-WA processed data](https://huggingface.co/datasets/apurvaga/go-browse-wa) | web | [2506.03533](https://arxiv.org/abs/2506.03533) (2025) | — | Flattened web-interaction training records with accessibility-tree observations, assistant completions, trajectory rewards and step-link metadata. | [✓ 2026‑10‑17](https://huggingface.co/api/datasets/apurvaga/go-browse-wa) |
| [OS-Genesis mobile training data](https://huggingface.co/datasets/OS-Copilot/OS-Genesis-mobile-data) | android | [2412.19723](https://arxiv.org/abs/2412.19723) (2024) | data mit | Reverse-task-synthesis mobile trajectories released in separate AndroidControl and AndroidWorld training annotation files. | [✓ 2026‑10‑17](https://huggingface.co/datasets/OS-Copilot/OS-Genesis-mobile-data/raw/main/README.md) |
| [ShowUI-π training data](https://huggingface.co/datasets/showlab/ShowUI-pi-data) | desktop | [2512.24965](https://arxiv.org/abs/2512.24965) (2025) | — | Drag-and-click episode data for the ShowUI-π model, spanning desktop editing, presentation, handwriting and other interface tasks. | [✓ 2026‑10‑17](https://huggingface.co/datasets/showlab/ShowUI-pi-data/raw/main/README.md) |
| [UI-Genie trajectory data](https://huggingface.co/datasets/HanXiao1999/UI-Genie-Agent-16k) | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | data mit | Synthetic mobile GUI trajectory supervision and screenshots released with the UI-Genie agent-training pipeline. | [✓ 2026‑10‑17](https://huggingface.co/datasets/HanXiao1999/UI-Genie-Agent-16k/raw/main/README.md) |
| [VideoCAD data](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/WX8PCK) | unspecified | [2505.24838](https://arxiv.org/abs/2505.24838) (2025) | data CC0 1.0 | CAD screen recordings paired with action logs and target model images for studying precise interface control and long-horizon visual imitation. | [✓ 2026‑10‑17](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/WX8PCK) |

## Models

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Go-Browse WebArena Qwen 7B](https://huggingface.co/apurvaga/go-browse-wa-qwen-7B) | web | [2506.03533](https://arxiv.org/abs/2506.03533) (2025) | — | A Qwen-2.5-7B-Instruct checkpoint fine-tuned on Go-Browse WebArena trajectories for website task execution. | [✓ 2026‑10‑17](https://huggingface.co/apurvaga/go-browse-wa-qwen-7B/raw/main/README.md) |
| [OS-Genesis 7B AC](https://huggingface.co/OS-Copilot/OS-Genesis-7B-AC) | android | [2412.19723](https://arxiv.org/abs/2412.19723) (2024) | weights apache-2.0 | The AndroidControl-oriented Qwen2-VL checkpoint trained with mobile trajectories generated through OS-Genesis reverse task synthesis. | [✓ 2026‑10‑17](https://huggingface.co/OS-Copilot/OS-Genesis-7B-AC/raw/main/README.md) |
| [UI-Genie Agent 7B](https://huggingface.co/HanXiao1999/UI-Genie-Agent-7B) | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | weights mit | A Qwen2.5-VL mobile action model trained using existing and reward-guided synthetic trajectories from the UI-Genie framework. | [✓ 2026‑10‑17](https://huggingface.co/HanXiao1999/UI-Genie-Agent-7B/raw/main/README.md) |

## Frameworks

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Go-Browse](https://github.com/ApGa/Go-Browse) | web | [2506.03533](https://arxiv.org/abs/2506.03533) (2025) | code MIT | Structured website-exploration and data-processing code that revisits discovered pages, proposes tasks and collects trajectories for web-agent fine-tuning. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/ApGa/Go-Browse/HEAD/README.md) |
| [UI-Genie](https://github.com/Euphoria16/UI-Genie) | android | [2505.21496](https://arxiv.org/abs/2505.21496) (2025) | — | Training and evaluation code for a mobile-agent framework that iteratively generates trajectories using agent and reward-model feedback. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/Euphoria16/UI-Genie/HEAD/README.md) |
| [VideoCAD training and evaluation code](https://github.com/UDGOK/videocad) | unspecified | [2505.24838](https://arxiv.org/abs/2505.24838) (2025) | — | VideoCADFormer training, action-log preprocessing and evaluation code for learning long sequences of CAD interface operations from screen recordings. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/UDGOK/videocad/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑07‑05 | [UI-MOPD: Multi-Platform On-Policy Distillation for Unified GUI Agents](https://arxiv.org/abs/2607.04425) | desktop, cross-platform | Introduces Uni-GUI, a collection of executable desktop and mobile trajectories, and UI-MOPD, which trains a shared policy from its own rollouts using platform-specific teachers. The distillation procedure routes each visited state to the appropriate teacher to preserve distinct interaction conventions. |
| 2025‑09‑29 | [Scaling Synthetic Task Generation for Agents via Exploration](https://arxiv.org/abs/2509.25047) | android, linux, desktop, cross-platform | AutoPlay explores application states and functions to generate tasks, then uses a model executor and verifier to construct demonstrations. It produces 20,000 tasks across 20 Android apps and 10,000 tasks across 13 Ubuntu apps for supervised and reinforcement learning of UI agents. |
| 2025‑09‑22 | [UIPro: Unleashing Superior Interaction Capability For GUI Agents](https://arxiv.org/abs/2509.17328) | cross-platform | UIPro pretrains GUI understanding on 20.6 million tasks and then harmonizes interaction datasets through a unified action space. Continued fine-tuning uses the merged multi-platform data to train action prediction for generalist GUI operation. |
| 2025‑08‑27 | [CODA: Coordinating the Cerebrum and Cerebellum for a Dual-Brain Computer Use Agent with Decoupled Reinforcement Learning](https://arxiv.org/abs/2508.20096) | desktop | CODA combines a generalist planner with a specialist GUI executor and trains application-specific planners through decoupled GRPO. Successful specialist trajectories then support supervised training of a consolidated planner, evaluated across four ScienceBoard applications. |
| 2025‑08‑06 | [SEAgent: Self-Evolving Computer Use Agent with Autonomous Learning from Experience](https://arxiv.org/abs/2508.04700) | desktop | SEAgent explores unfamiliar software using a world-state assessor and an automatically generated task curriculum. It learns from failed and successful interactions through adversarial imitation and GRPO, then combines specialist experience into a generalist agent evaluated on five OSWorld software environments. |
| 2025‑07‑05 | [How to Train Your LLM Web Agent: A Statistical Diagnosis](https://arxiv.org/abs/2507.04103) | web | Studies compute allocation for web-agent post-training with teacher-generated supervised fine-tuning followed by on-policy reinforcement learning. It samples 1,370 training configurations and uses bootstrap analysis to examine hyperparameter sensitivity on WorkArena and MiniWoB++. |
| 2025‑02‑10 | [AppVLM: A Lightweight Vision Language Model for Online App Control](https://arxiv.org/abs/2502.06395) | android | AppVLM first learns app actions from AndroidControl and then refines its policy through data collected in AndroidWorld. The study compares offline action prediction and online task completion for a lightweight vision-language smartphone agent. |
| 2024‑09‑24 | [Synatra: Turning Indirect Knowledge into Direct Demonstrations for Digital Agents at Scale](https://arxiv.org/abs/2409.15637) | web | Synatra converts indirect procedural knowledge, including human-oriented tutorials, into direct demonstrations for digital agents. It trains a 7B CodeLlama on 100,000 synthesized demonstrations and evaluates the resulting policy on Mind2Web, MiniWoB++, and WebArena. |
