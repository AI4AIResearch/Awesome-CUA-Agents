# Training-free methods

[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)

7 source-reviewed resources tagged `training-free`. Curated metadata, not a performance ranking; unknown facts are shown as —.

**Contents:** [Tools (1)](#tools) · [Papers (6)](#papers)

## Tools

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [TAG attention-driven GUI grounding](https://github.com/HeimingX/TAG) | web | [2412.10840](https://arxiv.org/abs/2412.10840) (2024) | — | Grounding and evaluation code that aggregates a pretrained vision-language model’s attention maps to localize requested interface elements without fine-tuning. | [✓ 2026-10-17](https://raw.githubusercontent.com/HeimingX/TAG/HEAD/README.md) |

## Papers

| Date | Resource | Environments | Description |
| --- | --- | --- | --- |
| 2026-09-27 | [Relevance Does Not Imply Applicability: Experience Activation for Personal GUI Agents](https://arxiv.org/abs/2609.33304) | unspecified | Introduces ExpActivator, which matches the current GUI state to relevant historical states before supplying past actions as guidance. A separate activation rule decides whether a recurring user intent is warranted by the current time and situation or should be withheld. |
| 2026-09-04 | [From Interaction Traces to Persistent Skills: Online Evolution for Computer-Use Agents](https://arxiv.org/abs/2609.04869) | desktop | An online skill-evolution framework turns GUI interaction traces and evaluator feedback into a versioned library of reusable procedures without updating model parameters. Controlled OSWorld comparisons examine both the benefits of shared procedural memory and its domain-dependent instability under repeated revision. |
| 2026-08-26 | [LocalLSTC: A Long Short-Term Control Architecture for Locally Deployed GUI Agents](https://arxiv.org/abs/2608.25777) | desktop, windows | Introduces LocalLSTC, a training-free control architecture that maintains persistent task state and uses it to form short execution commitments. Outcomes feed back into that state for progress checks, recovery, and termination in locally deployed desktop agents. |
| 2026-06-28 | [Agent-Computer Observation Interfaces Enable Dynamic Computer Use](https://arxiv.org/abs/2606.29472) | web | The Agent-Computer Observation Interface separates continuous perception from discrete computer actions using captured frames, audio transcription and persistent visual narration. DynaCU-Bench tests these components on dynamic browser tasks and static controls, with model-specific ablations showing that additional observations can also hurt. |
| 2025-09-15 | [How Auxiliary Reasoning Unleashes GUI Grounding in VLMs](https://arxiv.org/abs/2509.11548) | unspecified | Studies the gap between latent visual grounding and explicit coordinate output in general vision-language models. Three zero-shot methods add axes, grids, or labeled intersections to GUI screenshots so models can express spatial locations without fine-tuning. |
| 2025-08-07 | [Test-Time Reinforcement Learning for GUI Grounding via Region Consistency](https://arxiv.org/abs/2508.05615) | unspecified | GUI-RC aggregates multiple grounding predictions into spatial voting grids to choose a consensus region. GUI-RCPO then turns agreement with that region into a reward for test-time policy updates on unlabeled GUI screenshots. |
