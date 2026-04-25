# Vitest Bun Headed Browser Repro

Minimal reproduction for a Vitest Browser Mode issue where headed Chromium fails when the Vitest CLI is forced to run on Bun's runtime.

## Environment Used Locally

- macOS Darwin 24.6.0 arm64
- Bun `1.3.13+bf2e2cecf`
- Node `v24.14.1`
- Vitest `4.1.5`
- `@vitest/browser-playwright` `4.1.5`
- `@vitest/browser-preview` `4.1.5`
- Playwright `1.59.1`

## Setup

```sh
bun install
bun --bun playwright install chromium firefox webkit
```

## Local Reproduction

Key failing command:

```sh
bun --bun vitest run --config vitest.playwright.chromium.config.ts
```

Expected: the single browser test passes in headed Chromium.

Actual locally: Chromium launches and opens the Vitest browser page, but no test executes. After about 35 seconds Vitest reports:

```text
Error: Failed to run the test .../example.test.ts
Caused by: Error: [vitest] Browser connection was closed while running tests. Was the page closed unexpectedly?
Caused by: Error: [birpc] rpc is closed, cannot call "createTesters"

Test Files (1)
Tests no tests
Errors 1 error
```

Useful comparison commands:

```sh
# Bun runtime + Chromium headless: passes locally
bun --bun vitest run --config vitest.playwright.chromium.config.ts --browser.headless

# Node runtime via Bun + Chromium headed: passes locally
bun vitest run --config vitest.playwright.chromium.config.ts

# Bun runtime + Chromium headed with Browser UI disabled: passes locally
bun --bun vitest run --config vitest.playwright.chromium-ui-false.config.ts

# Direct Node + Chromium headed: passes locally
node node_modules/vitest/vitest.mjs run --config vitest.playwright.chromium.config.ts

# Bun runtime + Firefox headed: passes locally, but slower
bun --bun vitest run --config vitest.playwright.firefox.config.ts

# Bun runtime + WebKit headed: passes locally
bun --bun vitest run --config vitest.playwright.webkit.config.ts

# Bun runtime + preview provider: fails locally with "Orchestrator not found"
bun --bun vitest run --config vitest.preview.config.ts
```

## Local Matrix Summary

| Runtime | Provider | Browser | Mode | Local result |
| --- | --- | --- | --- | --- |
| Bun (`--bun`) | Playwright | Chromium | headless | Pass |
| Bun (`--bun`) | Playwright | Chromium | headed + Browser UI | Fail / no tests start |
| Bun (`--bun`) | Playwright | Chromium | headed + `browser.ui: false` | Pass |
| Bun (`--bun`) | Playwright | Firefox | headed | Pass |
| Bun (`--bun`) | Playwright | WebKit | headed | Pass |
| Node via `bun vitest` | Playwright | Chromium | headed | Pass |
| Direct Node | Playwright | Chromium | headed | Pass |
| Bun (`--bun`) | Preview | Chromium | headed | Fail |
| Node via `bun vitest` | Preview | Chromium | headed | Pass |

## CI

The GitHub Actions workflow runs the core comparison on Ubuntu:

- Bun runtime + Chromium headless.
- Bun runtime + Chromium headed under `xvfb-run`.
- Bun runtime + Chromium headed under `xvfb-run` with `browser.ui: false`.
- Node runtime via `bun vitest` + Chromium headed under `xvfb-run`.
- Bun runtime + Firefox/WebKit headed under `xvfb-run` for extra signal.
- Bun runtime + preview provider under `xvfb-run`.

The Bun-headed Chromium and Bun-preview jobs are marked `continue-on-error` so the workflow records the failure without hiding the passing controls.

On Ubuntu CI, `bun-runtime-chromium-headed-xvfb` currently passes. The known failure is local macOS headed Chromium.

## Current Narrowing

Local debugging narrowed the macOS failure to Vitest's Browser UI JavaScript bundle:

- `browser.ui: false` passes under `bun --bun` headed Chromium.
- A static UI page containing `#tester-ui` passes.
- The Browser UI CSS alone passes.
- Adding `__vitest__/assets/index-BPQdrqGZ.js` back makes `bun --bun` headed Chromium fail.
- Stubbing the UI app's own `__vitest_api__` WebSocket client makes the static UI + UI JS experiment pass again.

The failing full run creates and loads the tester iframe, but the tester RPC WebSocket never reaches the server as an upgrade request. With `browser.ui: false`, the server logs `Browser API connected to tester` and the test passes.

## Upstream Links

Likely related:

- https://github.com/oven-sh/bun/issues/11268
- https://github.com/oven-sh/bun/issues/10180
- https://github.com/oven-sh/bun/issues/8222

This repro is intended to support filing a Bun issue. The same Vitest config passes when the CLI runs on Node, and raw headed Playwright Chromium launch works under Bun, so the suspected boundary is Bun runtime plus Vitest Browser Mode's headed Browser UI JavaScript.
