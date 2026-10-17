# Training-free methods

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

18 source-reviewed resources tagged `training-free`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Agents (1)](#agents) · [Tools (1)](#tools) · [Papers (16)](#papers)

## Agents

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [RCI Agent](https://github.com/posgnu/rci-agent) | [2303.17491](https://arxiv.org/abs/2303.17491) (2023) | code MIT | A MiniWoB++ agent that uses explicit and implicit recursive criticism-and-improvement prompts to refine action plans and ground actions to browser state. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/posgnu/rci-agent/HEAD/README.md) |

## Tools

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [TAG attention-driven GUI grounding](https://github.com/HeimingX/TAG) | [2412.10840](https://arxiv.org/abs/2412.10840) (2024) | — | Grounding and evaluation code that aggregates a pretrained vision-language model’s attention maps to localize requested interface elements without fine-tuning. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/HeimingX/TAG/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026‑09‑27 | [Relevance Does Not Imply Applicability: Experience Activation for Personal GUI Agents](https://arxiv.org/abs/2609.33304) | unspecified | Introduces ExpActivator, which matches the current GUI state to relevant historical states before supplying past actions as guidance. A separate activation rule decides whether a recurring user intent is warranted by the current time and situation or should be withheld. |
| 2026‑09‑04 | [From Interaction Traces to Persistent Skills: Online Evolution for Computer-Use Agents](https://arxiv.org/abs/2609.04869) | desktop | An online skill-evolution framework turns GUI interaction traces and evaluator feedback into a versioned library of reusable procedures without updating model parameters. Controlled OSWorld comparisons examine both the benefits of shared procedural memory and its domain-dependent instability under repeated revision. |
| 2026‑08‑26 | [LocalLSTC: A Long Short-Term Control Architecture for Locally Deployed GUI Agents](https://arxiv.org/abs/2608.25777) | desktop, windows | Introduces LocalLSTC, a training-free control architecture that maintains persistent task state and uses it to form short execution commitments. Outcomes feed back into that state for progress checks, recovery, and termination in locally deployed desktop agents. |
| 2026‑06‑28 | [Agent-Computer Observation Interfaces Enable Dynamic Computer Use](https://arxiv.org/abs/2606.29472) | web | The Agent-Computer Observation Interface separates continuous perception from discrete computer actions using captured frames, audio transcription and persistent visual narration. DynaCU-Bench tests these components on dynamic browser tasks and static controls, with model-specific ablations showing that additional observations can also hurt. |
| 2026‑02‑06 | [Trifuse: Enhancing Attention-Based GUI Grounding via Multimodal Fusion](https://arxiv.org/abs/2602.06351) | unspecified | Trifuse combines attention-based localization with OCR text cues and icon captions to ground GUI instructions. Its fusion procedure favors cross-modal agreement and sharp location peaks, and is evaluated without task-specific fine-tuning. |
| 2026‑01‑30 | [Darwinian Memory: A Training-Free Self-Regulating Memory System for GUI Agent Evolution](https://arxiv.org/abs/2601.22528) | unspecified | Darwinian Memory splits GUI trajectories into reusable units and updates the memory by retaining useful paths and pruning poor ones. It evaluates this training-free memory mechanism on long multi-application tasks. |
| 2025‑12‑09 | [MVP: Multiple View Prediction Improves GUI Grounding](https://arxiv.org/abs/2512.08529) | unspecified | MVP addresses unstable GUI coordinates by predicting across several attention-guided cropped views. It clusters the resulting coordinates and selects the densest cluster centroid, evaluating this training-free inference method across grounding models. |
| 2025‑12‑05 | [Zoom in, Click out: Unlocking and Evaluating the Potential of Zooming for GUI Grounding](https://arxiv.org/abs/2512.05941) | unspecified | ZoomClick uses repeated zooming and context adjustment to improve GUI grounding without training. The paper studies zoom depth, crop sizes, and related choices and introduces GUIZoom-Bench to evaluate how grounding models respond to zoomed views. |
| 2025‑12‑01 | [Chain-of-Ground: Improving GUI Grounding via Iterative Reasoning and Reference Feedback](https://arxiv.org/abs/2512.01979) | unspecified | Chain-of-Ground uses iterative visual reasoning and reference feedback to refine GUI localization without additional training. It evaluates on ScreenSpot-Pro and introduces TPanel-UI to probe grounding on industrial control panels with visual distortions. |
| 2025‑10‑01 | [GUI-KV: Efficient GUI Agents via KV Cache with Spatio-Temporal Awareness](https://arxiv.org/abs/2510.00536) | unspecified | GUI-KV compresses vision-language agents’ attention caches using visual-token saliency and redundancy between screenshot frames. The method requires no retraining and evaluates how cache budgets affect GUI action accuracy and computational cost. |
| 2025‑09‑15 | [How Auxiliary Reasoning Unleashes GUI Grounding in VLMs](https://arxiv.org/abs/2509.11548) | unspecified | Studies the gap between latent visual grounding and explicit coordinate output in general vision-language models. Three zero-shot methods add axes, grids, or labeled intersections to GUI screenshots so models can express spatial locations without fine-tuning. |
| 2025‑08‑07 | [Test-Time Reinforcement Learning for GUI Grounding via Region Consistency](https://arxiv.org/abs/2508.05615) | unspecified | GUI-RC aggregates multiple grounding predictions into spatial voting grids to choose a consensus region. GUI-RCPO then turns agreement with that region into a reward for test-time policy updates on unlabeled GUI screenshots. |
| 2025‑07‑13 | [LaSM: Layer-wise Scaling Mechanism for Defending Pop-up Attack on GUI Agents](https://arxiv.org/abs/2507.10610) | unspecified | Introduces LaSM, a training-free defense that selectively scales attention and MLP components to improve alignment with task-relevant screen regions. It evaluates the approach against pop-up-based GUI injection attacks. |
| 2025‑06‑18 | [Understanding GUI Agent Localization Biases through Logit Sharpness](https://arxiv.org/abs/2506.15425) | unspecified | Introduces a finer-grained taxonomy of GUI localization errors and a logit-based Peak Sharpness Score for analyzing coordinate-prediction uncertainty. A context-aware cropping method refines the visual input without retraining the grounding model. |
| 2023‑03‑30 | [Language Models can Solve Computer Tasks](https://arxiv.org/abs/2303.17491) | web | Introduces recursive criticism and improvement prompting for language-model agents performing computer tasks, evaluated on MiniWoB++ with a small number of demonstrations per task. |
| 2022‑09‑18 | [Enabling Conversational Interaction with Mobile UI using Large Language Models](https://arxiv.org/abs/2209.08655) | unspecified | Studies few-shot prompting of a single language model for four mobile-UI interaction tasks, aiming to support conversational interface use without a separate trained model for each task. |
