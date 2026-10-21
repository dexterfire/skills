---
name: opencode
description: Call non-Claude models (GPT, Gemini, GLM, DeepSeek, Grok, free OpenCode Zen models, Bedrock) through the opencode CLI from a cloud session — for a second opinion, a vision check, or work routed to a specific model or provider. Use when the user names a non-Claude model, asks to "ask another model" or "check with GPT/Gemini", or wants model or account rotation.
---

# opencode

opencode (`opencode-ai` on npm) is a coding agent that talks to any provider in `opencode models`. `opencode run` drives it non-interactively, so one CLI reaches every model the environment has credentials for.

## Setup

The cloud environment carries it, so a fresh session needs nothing:

- **Setup script:** `npm i -g opencode-ai`
- **Allowed domains:** `opencode.ai`, `models.opencode.ai`, `models.dev`, plus each provider's API host
- **Secrets:** `OPENCODE_API_KEY` (Zen), `AWS_BEARER_TOKEN_BEDROCK` + `AWS_REGION` (Bedrock), `GEMINI_API_KEY`, …

A blocked host fails with `Forbidden: request blocked ... host "<host>"`; that is the environment's network policy, and only its settings fix it.

## Calling a model

```bash
cd <scratch dir>   # opencode works in, and may edit, the current directory
opencode run -m <provider/model> "<prompt>"
```

- `-m provider/model`: take the id from `opencode models [provider]`, never from memory.
- `-f <file>` attaches a file or image. **The prompt goes before `-f`**: `-f` is variadic and swallows every argument after it.
- `-s <sessionID>` or `-c` continues a conversation; `opencode session list --format json` lists sessions.
- `--format json` emits raw JSON events; the default prints the answer under a `> agent · model` header.
- `--variant low|medium|high` sets reasoning effort where the model has variants.
- `--auto` approves tool use (edits, shell). Use it only in a scratch directory. Without it, tool calls outside the working directory are auto-rejected.
- For many calls in a row, start `opencode serve --port 4096` in the background once and add `--attach http://localhost:4096` to skip cold start.

## Picking a model by capability

Not every model takes images, PDFs or audio. **A model without image input never sees the picture**: opencode hands it the file path instead, and the model either says it cannot see it or tries to open the file with tools. Check before routing:

```bash
scripts/capabilities.py [provider]        # markdown table: image, pdf, audio, tools, reasoning, context, free
scripts/capabilities.py [provider] --json # same, for scripting
```

The table comes from each model's declared `capabilities` in `opencode models --verbose`. `scripts/test_model.sh <model> <outdir> <image>` checks one model live (text, image, tool use) — run it before trusting a new or free model.

Free Zen models, tested live on 2026-10-21. Cells are passes/runs; "declared" image support is from `capabilities.py`.

| model | text | image (declared → live) | tools | use for |
|---|---|---|---|---|
| `opencode/glm-5.3-flash-free` | 1/2 | yes → 2/2 | 2/2 | Default: text, vision and agentic work |
| `opencode/minimax-m3.1-flash-free` | 1/2 | yes → 2/2 | 1/2 | Vision fallback |
| `opencode/deepseek-v4.1-flash-free` | 1/2 | yes → 2/2 | 0/2 | Vision only; never completes tool work |
| `opencode/nemotron-3.5-super-vl-free` | 1/2 | yes → 1/3 | 2/2 | Unreliable on images despite the "VL" |
| `opencode/mimo-v2.6-flash-free` | 1/2 | yes → 0/2 | 2/2 | Text and tools; images come back empty |
| `opencode/big-pickle` | 1/2 | no | 1/2 | Text and tools |
| `opencode/nemotron-3-ultra-free` | 1/1 | no → says it can't see | 1/1 | Text and tools |
| `opencode/nemotron-3.5-lightning-free` | 1/1 | no → tries to open the file | 1/1 | Text and tools |
| `opencode/beam-free` | 1/1 | no → tries to open the file | 1/1 | Text and tools, 1M context |
| `opencode/flint-40b-free` | 1/1, ~47s | no → says it can't see | 1/1 | Slow |
| `opencode/longcat-2.5-preview-free` | 0/2 | yes | 0/2 | Endpoint unavailable |

Every failed text run above was a silent 120-second hang, spread across all models, including the default. On free models, put a `timeout` on every call and treat a hang as a signal to rotate, not as a property of the model. A passing answer takes 5–10 seconds.

Free models are rate-limited and rotate in and out of the catalogue; refresh with `opencode models --refresh`. Paid Zen models (`opencode/gpt-*`, `opencode/gemini-*`, `opencode/claude-*`, …) bill the Zen balance, so use one only when the user asked for it.

## Rotation

Keep an ordered list of equivalent models (same capabilities the task needs) and fall through on failure: a non-zero exit, an `Error:` line, or a timeout means try the next one. Filter the list with `scripts/capabilities.py --json` first, so a vision task never falls through to a text-only model.

## Providers

| Provider | Credential | Notes |
|---|---|---|
| `opencode/*` (Zen) | `OPENCODE_API_KEY`, or `opencode auth login` | Free and paid models behind one key |
| `amazon-bedrock/*` | `AWS_BEARER_TOKEN_BEDROCK`, `AWS_REGION` | Access keys stored as network secrets reach the container as proxy placeholders, and SigV4 signing fails on them ("security token included in the request is invalid"); use a Bedrock API key |
| `github-copilot/*` | — | Listed because `GITHUB_TOKEN` is set, but that is the session's git token, not a Copilot login; don't use it |
| `google/*` | `GEMINI_API_KEY` | |
