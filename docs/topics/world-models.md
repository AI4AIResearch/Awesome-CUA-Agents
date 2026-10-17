# World models

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

24 source-reviewed resources tagged `world-models`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Datasets (1)](#datasets) · [Models (1)](#models) · [Frameworks (1)](#frameworks) · [Papers (21)](#papers)

## Datasets

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Dreamer V1 Data](https://huggingface.co/datasets/osunlp/Dreamer-V1-Data) | [2411.06559](https://arxiv.org/abs/2411.06559) (2024) | data cc-by-nc-sa-4.0 | Web-world-model training data with prompts, images, action descriptions, and responses, released with the WebDreamer project. | [✓ 2026‑10‑16](https://huggingface.co/datasets/osunlp/Dreamer-V1-Data/raw/main/README.md) |

## Models

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Dreamer-7B](https://huggingface.co/osunlp/Dreamer-7B) | [2411.06559](https://arxiv.org/abs/2411.06559) (2024) | weights apache-2.0 | WebDreamer model checkpoint that predicts the consequences of web actions from screenshots and textual descriptions. | [✓ 2026‑10‑16](https://huggingface.co/osunlp/Dreamer-7B/raw/main/README.md) |

## Frameworks

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [WebDreamer](https://github.com/OSU-NLP-Group/WebDreamer) | [2411.06559](https://arxiv.org/abs/2411.06559) (2024) | — | World-model and planning components that simulate web-action outcomes, with linked training data and model checkpoints. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/OSU-NLP-Group/WebDreamer/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑10‑09 | [Latent World Action Model for GUI Agents](https://arxiv.org/abs/2610.14228) | unspecified | Replaces future-screenshot generation with a shared latent representation for GUI action selection and action-conditioned transition prediction. An action-aware contrastive objective encourages the transition representation to retain discriminative action-induced changes. |
| 2026‑10‑08 | [Right Screen, Wrong Transition: World Models as Verifiers for GUI Agents](https://arxiv.org/abs/2610.11942) | unspecified | Presents LGWM, a decoder-free GUI world model that predicts the next screen representation from an action and compares it with the observed state to verify transitions. Its paired diagnostic separates legitimate and hijacked transitions that lead to the same credential screen. |
| 2026‑10‑06 | [AdvSim2Real : Training Web Agents Against Adaptive Prompt Injection in a Web World Model](https://arxiv.org/abs/2610.08773) | web | Presents AdvSim2Real, which jointly adapts web-task curricula, prompt-injection adversaries, and agent policies inside a frozen web world model. It evaluates robustness against an unseen adversary and transfer from simulated interaction to a real browser. |
| 2026‑10‑05 | [Imagine to Act: High-Fidelity Data Synthesis via Image Editing World Model for Scalable GUI Agent Training](https://arxiv.org/abs/2610.05861) | android | Introduces Infinite-Dreamer, which learns action-conditioned screenshot editing from structured descriptions of GUI changes and uses it to synthesize robustness examples and multi-step trajectories. The synthetic data trains a mobile GUI agent evaluated on AndroidWorld, MobileWorld, and AndroidControl-Curated. |
| 2026‑10‑01 | [AutoGUIWorld: Image Generators as Visual World Models for GUI Agent](https://arxiv.org/abs/2610.01215) | desktop, linux, windows, macos, web | Introduces AutoGUIWorld, which combines task planning and image editing to synthesize action-grounded GUI trajectories without running the depicted software. It filters generated transitions and tests whether training on them improves agents operating real desktop and scientific applications. |
| 2026‑09‑29 | [PrecogUI: Proactive GUI Agents via Pre-cognitive Simulation and Experience Retrieval](https://arxiv.org/abs/2609.36923) | unspecified | Presents PrecogUI, which retrieves prior anomaly and success patterns and predicts symbolic UI transitions before choosing actions. It also introduces InterfereBench, generated for evaluating long GUI workflows with disruptive events and recovery requirements. |
| 2026‑09‑26 | [The GUI Is Not the State: Diagnosing State Aliasing in GUI World Models](https://arxiv.org/abs/2609.32679) | android | Introduces StateAliasBench to isolate GUI world-model ambiguities in which matching visible screens and actions can lead to different futures. It augments frozen world models with structured state recovered from interaction history and evaluates the effect on prediction and agent execution. |
| 2026‑08‑30 | [GUI-CC: Benchmarking Contextual Consistency of GUI World Models as Agent Environments](https://arxiv.org/abs/2609.00048) | unspecified | Introduces GUI-CC, a benchmark for assessing GUI world models as multi-step agent environments. Separate reference-action and agent-loop tracks test whether generated screens preserve context, plausible transitions, and task progress throughout interaction. |
| 2026‑08‑27 | [WM-R1: Training GUI Agents to Reason and leverage World Models with Reinforcement Learning](https://arxiv.org/abs/2608.27508) | android | Uses learned world models for mobile-agent training rollouts and for reasoning about the consequences of candidate GUI actions. |
| 2026‑07‑27 | [Scaling GUI Agents with Visual State Transitions](https://arxiv.org/abs/2607.24112) | desktop, android | Introduces State Transition Pretraining, which jointly learns to infer actions from GUI changes and predict future states from current screens and actions. Subsequent instruction-trajectory fine-tuning tests whether these representations transfer to desktop and mobile agent tasks. |
| 2026‑07‑19 | [EvoGUI: An Evolution-Aware Benchmark for GUI State-Transition Understanding](https://arxiv.org/abs/2607.17050) | web | Introduces EvoGUI, which derives temporal ordering, inverse action/value prediction, and successor-discrimination probes from recorded GUI trajectories. Its web-derived benchmark isolates transition understanding from the other abilities involved in end-to-end task success. |
| 2026‑07‑17 | [SeerGuard: A Safety Framework for Mobile GUI Agents via World Model Prediction](https://arxiv.org/abs/2607.15550) | unspecified | Uses instruction screening and a safety-augmented world model to assess likely consequences of mobile GUI actions before execution. |
| 2025‑12‑16 | [MobileWorldBench: Towards Semantic World Modeling For Mobile Agents](https://arxiv.org/abs/2512.14014) | android | Evaluates semantic world models for mobile interfaces and studies natural-language state transitions as a tool for agent planning. |
| 2025‑10‑13 | [R-WoM: Retrieval-augmented World Model For Computer-use Agents](https://arxiv.org/abs/2510.11892) | desktop, web | R-WoM evaluates how well world models predict nearby GUI states, align complete procedures, and recognize milestone transitions. It retrieves external tutorials to guide simulated future interactions, with experiments on subsets of OSWorld and WebArena. |
| 2025‑08‑06 | [SEAgent: Self-Evolving Computer Use Agent with Autonomous Learning from Experience](https://arxiv.org/abs/2508.04700) | desktop | SEAgent explores unfamiliar software using a world-state assessor and an automatically generated task curriculum. It learns from failed and successful interactions through adversarial imitation and GRPO, then combines specialist experience into a generalist agent evaluated on five OSWorld software environments. |
| 2025‑04‑23 | [WebEvolver: Enhancing Web Agent Self-Improvement with Coevolving World Model](https://arxiv.org/abs/2504.21024) | web | WebEvolver trains a co-evolving world model to predict web observations and generate additional agent-training trajectories. The same model supports look-ahead action selection at inference, with evaluation on live web-task benchmarks. |
| 2025‑04‑15 | [ViMo: A Generative Visual GUI World Model for App Agents](https://arxiv.org/abs/2504.13936) | unspecified | ViMo predicts the next mobile-app screenshot after a candidate action by separately modeling graphics and text. A symbolic placeholder representation preserves layout while a second predictor supplies readable text, enabling visual lookahead for GUI-agent planning. |
| 2025‑02‑26 | [VEM: Environment-Free Exploration for Training GUI Agent with Value Environment Model](https://arxiv.org/abs/2502.18906) | android | Trains GUI agents with a frozen value model learned from offline interactions, guiding action exploration without predicting complete next observations. |
| 2024‑11‑10 | [Is Your LLM Secretly a World Model of the Internet? Model-Based Planning for Web Agents](https://arxiv.org/abs/2411.06559) | web | Introduces WebDreamer, which simulates candidate web actions with language-model world models and value estimates before acting. |
| 2024‑10‑17 | [Web Agents with World Models: Learning and Leveraging Environment Dynamics in Web Navigation](https://arxiv.org/abs/2410.13232) | web | Uses a learned web world model to predict important state changes and compare candidate actions before executing them. |
| 2024‑06‑12 | [Tell Me What's Next: Textual Foresight for Generic UI Representations](https://arxiv.org/abs/2406.07822) | unspecified | Textual Foresight learns UI representations by describing the future screen expected after an action on the current interface. The OpenApp dataset supports pretraining and downstream evaluation of representations that connect individual elements with whole-screen changes. |
