# Infrastructure catalog

[Home](../README.md) · [Methodology](methodology.md) · [Machine-readable catalog](../data/catalog.jsonl)

Curated metadata, not a performance ranking. Each entry links its first-party evidence. Unknown facts are shown as —.

*Paper* lists reviewed `introduced_by`/`documented_by` relations with the record's year. *License* lists publisher declarations by scope (code, data, weights, document). *Evidence* links the reviewed first-party snapshot and its retrieval date.

**14 resources:** [Web (2)](#web) · [Desktop (6)](#desktop) · [Mobile (3)](#mobile) · [Cross-platform (3)](#cross-platform)

Resources tagged with environments from more than one family are listed under *Cross-platform*; their exact environments stay in the table.

## Web

All entries in this section: web.

| Resource | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- |
| [Playwright](https://github.com/microsoft/playwright) | — | code Apache-2.0 | Browser automation library used as an execution layer by agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/microsoft/playwright/HEAD/README.md) |
| [Steel Browser](https://github.com/steel-dev/steel-browser) | — | code Apache-2.0 | Browser infrastructure for agent applications. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/steel-dev/steel-browser/HEAD/README.md) |

[↑ Back to top](#infrastructure-catalog)

## Desktop

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [AgentDesk](https://github.com/agentsea/agentdesk) | desktop | — | code MIT | Virtual desktop provisioning and control tools for agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/agentsea/agentdesk/HEAD/README.md) |
| [E2B Desktop](https://github.com/e2b-dev/desktop) | desktop, linux | — | code Apache-2.0 | Desktop sandboxes for computer-use agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/e2b-dev/desktop/HEAD/README.md) |
| [Lume](https://github.com/trycua/lume) | macos, linux | — | code MIT | Virtual machine management for local computer-use environments. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/trycua/lume/HEAD/README.md) |
| [Nut.js](https://github.com/nut-tree/nut.js) | desktop | — | — | Desktop automation library for keyboard, mouse, and screen interaction. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/nut-tree/nut.js/HEAD/README.md) |
| [PyAutoGUI](https://github.com/asweigart/pyautogui) | desktop | — | — | Mouse, keyboard, and screenshot automation library. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/asweigart/pyautogui/HEAD/README.md) |
| [ScienceBoard VMware environment](https://huggingface.co/OS-Copilot/ScienceBoard-Env) | linux, desktop | [2505.19897](https://arxiv.org/abs/2505.19897) (2025) | — | A prebuilt Ubuntu virtual-machine archive containing the software environment used for ScienceBoard scientific computer-use tasks. | [✓ 2026‑10‑17](https://huggingface.co/OS-Copilot/ScienceBoard-Env/raw/main/README.md) |

[↑ Back to top](#infrastructure-catalog)

## Mobile

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [AndroidEnv](https://github.com/google-deepmind/android_env) | android | [2105.13231](https://arxiv.org/abs/2105.13231) (2021) | code Apache-2.0 | Android device-control platform with screenshots, accessibility telemetry, input actions, and an optional reinforcement-learning task interface. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/google-deepmind/android_env/HEAD/README.md) |
| [Appium](https://github.com/appium/appium) | android, ios | — | code Apache-2.0 | Cross-platform UI automation infrastructure. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/appium/appium/HEAD/README.md) |
| [Mobile Env](https://github.com/X-LANCE/Mobile-Env) | android | — | code Apache-2.0 | Environment toolkit for mobile interaction agents. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/X-LANCE/Mobile-Env/HEAD/README.md) |

[↑ Back to top](#infrastructure-catalog)

## Cross-platform

| Resource | Environments | Paper | License | Description | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Agent Infra Sandbox](https://github.com/agent-infra/sandbox) | desktop, web | — | code Apache-2.0 | Sandbox environments supporting computer and browser interaction. | [✓ 2026‑10‑16](https://raw.githubusercontent.com/agent-infra/sandbox/HEAD/README.md) |
| [BrowserOS / BrowserOS neo](https://github.com/browseros-ai/BrowserOS) | web, windows, macos, linux | — | code AGPL-3.0 | Chromium-based browser implementations for external agent control and built-in assistant workflows, with session visibility and replay facilities. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/browseros-ai/BrowserOS/HEAD/README.md) |
| [Universe legacy GUI interaction client](https://github.com/openai/universe) | web, desktop | — | code MIT | An archived Gym-compatible client that exposes screen observations and keyboard/mouse actions over VNC for remote application and browser environments, including the historical World of Bits integration. | [✓ 2026‑10‑17](https://raw.githubusercontent.com/openai/universe/HEAD/README.rst) |

[↑ Back to top](#infrastructure-catalog)

Detailed notes and separate code/data/weights license declarations are in `data/catalog.jsonl`.
