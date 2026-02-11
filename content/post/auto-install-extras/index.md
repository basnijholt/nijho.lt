---
title: "Auto-installing extras at runtime so users never have to think about dependencies"
subtitle: "How I used uv, uvx, and a tiny decorator to make optional dependencies mostly disappear"
summary: "`agent-cli` grew from a voice helper into a local AI toolbox with 13 optional extras. Asking users to pick the right extras upfront became impossible, so I switched to runtime optional dependency resolution: commands declare what they need, missing extras are installed automatically in the correct environment, and the command re-runs transparently."
date: 2026-02-11
draft: true
featured: true
authors:
  - admin
tags:
  - python
  - uv
  - uvx
  - dependencies
  - packaging
  - cli
  - open-source
  - agent-cli
  - developer-experience
categories:
  - Software Development
  - Python
  - level:intermediate
image:
  caption: ""
  focal_point: ""
  placement: 2
  preview_only: false
---

{{< toc >}}

## 1. From one command to a dependency maze

`agent-cli` started simple: voice in, text out.
It connected to a Whisper server for ASR and a TTS service (Piper/Kokoro), mostly as a local-first interface I could trigger from terminal hotkeys.

Then I kept adding things:

- RAG proxy for document chat
- long-term memory proxy
- local server commands
- VAD-based continuous transcription
- multiple LLM providers
- audio utilities

The tool became much more useful, but dependency UX got worse.

Today there are 13 optional extras with very different dependency trees:
`audio`, `faster-whisper`, `kokoro`, `llm`, `memory`, `mlx-whisper`, `piper`, `rag`, `server`, `speed`, `vad`, `whisper-transformers`, `wyoming`.

{{% callout note %}}
**TL;DR:** I moved from “users choose extras upfront” to **runtime optional dependency resolution**.
Commands declare required extras with `@requires_extras(...)`; if something is missing, `agent-cli` installs it in the right environment and re-runs the command automatically.
{{% /callout %}}

## 2. Why normal extras UX breaks down

Python extras are the right packaging primitive, but the user question becomes:

- "Which extras do I need for this command?"
- "Do I need `server` plus a backend, or just one backend?"
- "Which backend should I pick on this machine?"

If users need to read your dependency matrix before running a CLI command, the UX is already off.

I wanted:

1. A lightweight base install.
2. Commands that "just work" when first used.
3. A clear opt-out for people who do not want automatic installs.

## 3. The pattern I landed on

Every command declares its dependency contract in one line.

Examples from real commands:

- [`transcribe-live` requires `audio`, `vad`, `llm`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/agents/transcribe_live.py#L290-L292)
- [`server whisper` requires `server` + one of three ASR backends + `wyoming`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/server/cli.py#L203-L205)
- [`server tts` requires `server` + one of `piper|kokoro` + `wyoming`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/server/cli.py#L562-L564)

The decorator itself is here:

- [`requires_extras(...)`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L365-L383)

And the main orchestration is here:

- [`_check_and_install_extras(...)`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L321-L359)

## 4. Runtime behavior (high level)

When you run a command:

1. `agent-cli` checks whether required extras are available.
2. If all good, command runs.
3. If missing and auto-install is enabled, it installs only what is needed.
4. It re-execs once so the current process sees the newly installed packages.
5. Command continues normally.

No manual “which extra do I install?” step for the common path.

## 5. Why environment detection matters

`agent-cli` needs different install strategies depending on how it was launched.

### A) `uv tool` install (persistent env)

It reads current extras from `uv-receipt.toml`, unions with missing extras, and reinstalls tool deps so extras persist across upgrades.

- [uv tool detection + extras merge + install path](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L179-L235)

### B) `uvx` run (ephemeral env)

No persistent env to mutate.
So it re-execs as `uvx --python 3.13 agent-cli[extras] ...`.

- [uvx cache detection](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L44-L50)
- [uvx re-exec path](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L287-L301)

### C) venv / pip installs

It installs pinned requirements files for each extra, preferring `uv pip` when available and falling back to `pip`.

- [fallback install command selection](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L215-L248)

## 6. What users see

Typical first run of a missing-extra command:

```text
Auto-installing missing extras: audio, llm
Running: uv tool install agent-cli[audio,llm] --force --python 3.13 -q
Installation complete!
Re-running with installed extras...
```

After that, it is just normal command execution.

## 7. Manual mode and opt-out

If someone prefers explicit control, they can disable auto-install.

```bash
export AGENT_CLI_NO_AUTO_INSTALL=1
```

or:

```toml
[settings]
auto_install_extras = false
```

Code path:

- [auto-install setting + precedence](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L34-L39)

Manual command:

- [`agent-cli install-extras`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/install/extras.py#L24-L104)

## 8. Keeping generated dependency artifacts in sync

The runtime flow depends on two generated artifacts:

- `agent_cli/_extras.json` (extra metadata and import probes)
- `agent_cli/_requirements/*.txt` (pinned per-extra requirements)

Generation and checks:

- [`sync_extras.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/sync_extras.py#L29-L149)
- [`check_extras_sync.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/check_extras_sync.py#L42-L71)
- [`sync_requirements.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/sync_requirements.py#L42-L71)

## 9. Tradeoffs

This approach works well, but it is still a tradeoff:

1. There is metadata to maintain.
2. Auto-install can still fail in restricted environments.
3. Re-exec is great for CLIs, not something I would expose as library behavior.

## 10. Not dependency injection

I originally called this "dependency injection" in my head, but that is the wrong term.

Better description:

- runtime optional dependency resolution
- on-demand extras installation
- lazy runtime extras installation

## 11. Conclusion

For multi-capability CLIs, asking users to choose the perfect extras upfront does not scale.

The pattern that worked for me:

- keep base install small
- declare requirements at command level
- auto-resolve missing extras at runtime
- install in the correct environment model (`uv tool`, `uvx`, or venv/pip)
- re-exec once and continue

Result: better UX without bloating the default install.
