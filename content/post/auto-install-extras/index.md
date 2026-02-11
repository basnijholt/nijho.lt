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

[`agent-cli`](https://github.com/basnijholt/agent-cli) started as a simple thing.
Voice in, text out.
It connected to a [Wyoming](https://github.com/rhasspy/wyoming) Whisper server for speech-to-text and a Piper server for text-to-speech, basically a local, open-source Siri triggered from terminal hotkeys.
I wrote about the early version in my [local AI journey]({{< ref "/post/local-ai-journey" >}}) post.

And then, as tends to happen with side projects I use every day, I kept adding things.

First a RAG proxy with ChromaDB, so I could chat with my documents.
Then a long-term memory system, so conversations could remember context across sessions.
Server commands that run Kokoro TTS or Whisper locally, optimized for whatever hardware you have—Apple Silicon gets MLX, NVIDIA gets CTranslate2.
Voice activity detection with Silero VAD.
Audio speed adjustment.
An [agent orchestration system]({{< ref "/post/parallel-agentic-coding" >}}).
`systemd`/`launchd` service management for running background daemons.

Each of these features pulled in wildly different dependency trees.
`torch` and `transformers` for GPU-accelerated Whisper.
`sounddevice` and `numpy` for microphone access.
`chromadb` and `onnxruntime` for vector storage.
`kokoro` with its entire spacy pipeline for neural TTS.

Today the project has **13 optional extras**.
The tool became much more useful, but dependency UX got progressively worse with every feature.

{{% callout note %}}
**TL;DR:** I moved from "users choose extras upfront" to **runtime optional dependency resolution**.
Commands declare required extras with `@requires_extras(...)`; if something is missing, `agent-cli` installs it in the right environment and re-runs the command automatically.
The user just types `agent-cli transcribe` and everything works.
{{% /callout %}}

## 2. Why "just use extras" breaks down

Python's `optional-dependencies` in `pyproject.toml` is the standard mechanism for this, and it's the right packaging primitive.
You define groups, users install with `pip install agent-cli[rag]`.
On paper, this is perfectly reasonable.

In practice, it falls apart when you have 13 of them:

```toml
[project.optional-dependencies]
audio = ["numpy", "sounddevice>=0.4.6", "agent-cli[wyoming]"]
llm = ["pydantic-ai-slim[openai,google,duckduckgo,vertexai]>=0.1.1"]
rag = ["pydantic-ai-slim[openai,google]>=0.1.1", "chromadb>=0.4.22", ...]
memory = ["pydantic-ai-slim[openai,google]>=0.1.1", "chromadb>=0.4.22", ...]
vad = ["onnxruntime>=1.16.0"]
faster-whisper = ["faster-whisper>=1.0.0"]
mlx-whisper = ["mlx-whisper>=0.4.0; sys_platform == 'darwin' and platform_machine == 'arm64'"]
kokoro = ["kokoro>=0.9.0", "soundfile>=0.12.0", ...]
piper = ["piper-tts>=1.2.0"]
# ... and more
```

The UX problem is obvious.
If I want to transcribe voice to text, do I need `audio`? `llm`? `vad`? All three?
What if I want the Whisper server to run locally—is that `faster-whisper` or `mlx-whisper`?
Do I also need `server` for that?

Expecting users to study a dependency matrix before running a CLI command is a terrible experience.
I wanted three things:

1. A lightweight base install that's fast and doesn't pull in heavy ML dependencies.
2. Commands that "just work" when first used.
3. A clear opt-out for people who don't want automatic installs.

## 3. The decorator

The core idea is simple.
Each CLI command declares what it needs, and the decorator handles the rest:

```python
@app.command("transcribe", rich_help_panel="Voice Commands")
@requires_extras("audio", "llm")
def transcribe(...):
    ...
```

That's it from the command author's perspective.
One line, and you never think about dependency management in that command again.

Here are a few more examples from the codebase to show how this scales:

```python
# Continuous transcription needs audio, voice activity detection, and an LLM
@requires_extras("audio", "vad", "llm")
def transcribe_live(...):
    ...

# TTS server needs the server framework + one of two TTS backends + Wyoming protocol
@requires_extras("server", "piper|kokoro", "wyoming")
def start_tts_server(...):
    ...

# Whisper server: any of three ASR backends will do
@requires_extras("server", "faster-whisper|mlx-whisper|whisper-transformers", "wyoming")
def start_whisper_server(...):
    ...
```

Notice the pipe syntax: `"piper|kokoro"` means "you need *either* Piper *or* Kokoro—any one of these satisfies the requirement."
On Apple Silicon, if you already have `mlx-whisper` installed, it won't try to install `faster-whisper` instead.

The [decorator itself](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L365-L383) is straightforward:

```python
def requires_extras(*extras: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if _check_and_install_extras(extras):
                raise typer.Exit(1)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

The real complexity lives in [`_check_and_install_extras`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L321-L359), which handles several installation scenarios.
But the interface for command authors is always a single line.

## 4. Checking without importing

You don't want to *import* `torch` just to check if it's available—that takes seconds and loads hundreds of megabytes into memory.
Instead, I use `importlib.util.find_spec`, which checks whether a module exists on the import path without executing any of its code.
No heavy imports, no GPU initialization, no side effects.
The check is essentially free.

## 5. The metadata bridge

There's a gap between what `pyproject.toml` knows and what the runtime check needs.
`pyproject.toml` says the `rag` extra requires `chromadb>=0.4.22`—that's the *pip package name*.
But at runtime, I need to check *Python import names*.
Sometimes these are the same (`chromadb` → `import chromadb`), but often they're not: `pydantic-ai-slim` is imported as `pydantic_ai`, `piper-tts` as `piper`.

To bridge this, I generate an [`_extras.json`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/_extras.json) file that maps each extra to its description and the Python import names needed for the runtime check:

```json
{
  "audio": ["Audio recording/playback", ["sounddevice"]],
  "rag": ["RAG proxy (ChromaDB, embeddings)", ["chromadb", "pydantic_ai"]],
  "memory": ["Long-term memory proxy", ["chromadb", "yaml", "pydantic_ai"]],
  "vad": ["Voice Activity Detection (Silero VAD via ONNX)", ["onnxruntime"]],
  "faster-whisper": ["Whisper ASR via CTranslate2", ["faster_whisper"]]
}
```

This file is [generated by a script](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/sync_extras.py) that parses `pyproject.toml` and applies a mapping table for the package-name-to-import-name conversions.
A pre-commit hook ensures it stays in sync—if you add an extra to `pyproject.toml` and forget to update the metadata, the commit fails.

I wish Python packaging had a standard way to discover a package's top-level import name from its distribution name.
It doesn't, so the mapping table is the least-bad option I found.

## 6. Three environments, three strategies

The hard part is that people run `agent-cli` in at least three different ways, and each needs a different installation strategy.

### A) `uv tool install` — the persistent environment

When installed via `uv tool install agent-cli`, the tool lives in a persistent environment under `~/.local/share/uv/tools/agent-cli/`.
This environment has a `uv-receipt.toml` file that tracks which extras are installed.

When auto-install triggers, the system reads the current extras from that receipt, merges in the new ones, and reinstalls:

```python
def install_extras_impl(extras, *, quiet=False):
    if is_uv_tool_install():
        current_extras = _get_current_uv_tool_extras()
        new_extras = sorted(set(current_extras) | set(extras))
        return _install_via_uv_tool(new_extras, quiet=quiet)
```

So if you already had `audio` installed and now run a command that needs `llm`, it becomes `uv tool install agent-cli[audio,llm] --force`.

The key insight: `uv tool upgrade` reads `uv-receipt.toml` and preserves the extras list.
Once auto-install adds an extra, it persists across future upgrades.
You never have to install it again.

([Full implementation](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L179-L235))

### B) `uvx` — the ephemeral environment

`uvx` is uv's tool for running packages in temporary, disposable environments.
Running `uvx agent-cli transcribe` creates a fresh environment, installs `agent-cli`, runs the command, and throws the environment away.

The problem: there's nowhere to persist extras.
No `uv-receipt.toml` to update, no virtualenv that survives the invocation.

The solution is one of my favorite tricks in this system: re-execute the entire command with the extras baked into the `uvx` invocation itself:

```python
def _maybe_reexec_with_uvx(extras):
    if os.environ.get(_REEXEC_MARKER) or not _is_uvx_cache():
        return
    uvx_path = shutil.which("uvx")
    if not uvx_path:
        return
    extras_str = ",".join(extras)
    cmd = [uvx_path, "--python", "3.13", f"agent-cli[{extras_str}]", *sys.argv[1:]]
    _maybe_exec_with_marker(cmd, f"Re-running with extras: {extras_str}")
```

So `uvx agent-cli transcribe` transparently becomes `uvx agent-cli[audio,llm] transcribe`.
The user sees a brief "Re-running with extras: audio, llm" message, and then the command works.

Environment detection is straightforward—`uvx` environments live under the uv cache directory:

```python
def _is_uvx_cache():
    prefix_str = Path(sys.prefix).resolve().as_posix()
    return "/cache/uv/" in prefix_str or "/archive-v" in prefix_str
```

([Full implementation](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L287-L301))

### C) Regular virtualenv or system install

For plain `pip install agent-cli` or virtualenv installs, the system falls back to direct installation from pinned requirements files.
Each extra has a pre-generated requirements file with pinned versions (e.g., `_requirements/audio.txt`), and the install command adapts to whatever's available:

```python
def _install_cmd():
    in_venv = sys.prefix != sys.base_prefix
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", sys.executable]
        if not in_venv:
            cmd.append("--system")
        return cmd
    cmd = [sys.executable, "-m", "pip", "install"]
    if not in_venv:
        cmd.append("--user")
    return cmd
```

Prefers `uv pip` when available (fast), falls back to regular pip.
Uses `--system` or `--user` as appropriate when not in a virtualenv.

([Full implementation](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py#L215-L248))

## 7. Preventing infinite re-execution loops

There's an obvious footgun here: what if the install succeeds but the package still isn't importable for some reason?
You'd get an infinite loop of install → re-exec → check → install → re-exec → ...

The fix is a simple environment variable marker:

```python
_REEXEC_MARKER = "_AGENT_CLI_REEXEC"

def _maybe_exec_with_marker(cmd, message):
    if os.environ.get(_REEXEC_MARKER):
        return  # Already re-executed once, don't loop
    new_env = os.environ.copy()
    new_env[_REEXEC_MARKER] = "1"
    os.execvpe(cmd[0], cmd, new_env)
```

`os.execvpe` replaces the current process entirely—it never returns.
The marker ensures we only do this once.
If the second run still can't find the packages, it falls back to a helpful error message instead of looping forever.

## 8. What users actually see

With auto-install **enabled** (the default), a first run looks like this:

```text
Auto-installing missing extras: audio, llm
Running: uv tool install agent-cli[audio,llm] --force --python 3.13 -q
Installation complete!
Re-running with installed extras...
```

And then the command runs normally.
Next time, it runs instantly—no install needed.

With auto-install **disabled**, the user gets a clear message telling them exactly what to do:

```text
This command requires the 'audio' extra (Audio recording/playback).

Install with:
  uv tool install -p 3.13 "agent-cli\[audio]"
  # or
  agent-cli install-extras audio
```

If you prefer explicit control, there's also a manual [`install-extras`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/install/extras.py#L24-L104) command:

```bash
agent-cli install-extras rag memory    # Install specific extras
agent-cli install-extras --all         # Install everything
agent-cli install-extras --list        # Show available extras with descriptions
```

You can opt out via environment variable or config file:

```bash
export AGENT_CLI_NO_AUTO_INSTALL=1
```

```toml
# ~/.config/agent-cli/config.toml
[settings]
auto_install_extras = false
```

## 9. Keeping everything in sync

The runtime system depends on two generated artifacts:

- **`_extras.json`**: maps extras to descriptions and import names (for the `find_spec` check)
- **`_requirements/*.txt`**: pinned dependency files for each extra (for the pip/uv install)

`_extras.json` is generated by [`sync_extras.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/sync_extras.py) (run manually or in CI).
The requirements files are generated by [`sync_requirements.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/sync_requirements.py), which runs as a pre-commit hook whenever `pyproject.toml` or `uv.lock` changes.
A [check script](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/.github/scripts/check_extras_sync.py) enforces that `_extras.json` stays consistent with `pyproject.toml`—if you add an extra but forget to update the metadata, the commit fails with a clear error.

This means the runtime system never drifts from the source of truth.
`pyproject.toml` is the canonical definition, everything else is derived.

## 10. Why uv made this practical

I want to be clear: this system would be *much* harder without [uv](https://docs.astral.sh/uv/).

- **`uv tool install`** with persistent extras in `uv-receipt.toml`—extras survive upgrades automatically
- **`uvx`** for ephemeral execution with extras specified inline
- **`uv pip install`** that's fast enough for runtime auto-install to feel acceptable
- **`uv export`** for generating pinned requirements files from `uv.lock`

With traditional pip, auto-installing at runtime would take 30-60 seconds and feel terrible.
With uv, it typically takes a few seconds.
That's the difference between "annoying" and "barely noticeable."

## 11. Tradeoffs

This approach works well, but it's still a tradeoff:

1. **There's metadata to maintain.** The package-name-to-import-name mapping requires a lookup table with special cases like `piper-tts` → `piper` and `pydantic-ai-slim` → `pydantic_ai`. I wish `pyproject.toml` had a field for this.

2. **The check only verifies importability, not version compatibility.** `find_spec` tells you a module exists, not whether it's the right version. In practice this hasn't been a problem because uv's pinned requirements handle versions, but it's a theoretical gap.

3. **Auto-install can fail in restricted environments.** Corporate machines, read-only containers, air-gapped systems—the opt-out exists for a reason.

4. **Re-exec is a CLI pattern, not a library pattern.** `os.execvpe` replaces the process, which means any shell hooks or signal handlers set up before the decorator runs are lost. Fine for CLI tools, would be problematic for libraries.

## 12. Not dependency injection

I originally called this "dependency injection" in my head, but that's the wrong term entirely.
Dependency injection is about providing object dependencies through constructors or function parameters.
This is something different.

The best names I've come up with:

- **runtime optional dependency resolution** — accurate but a mouthful
- **on-demand extras installation** — emphasizes the user experience
- **lazy extras** — short, probably what I'd use in conversation

If there's a standard term for this pattern, I haven't found it.

## 13. Conclusion

The underlying principle is simple: **the tool should know what it needs, and it should get it**.
Users shouldn't have to study a matrix of 13 optional extras to figure out which pip command to run.
They should just type the command they want, and it should work.

uv's speed and tooling model made this practical.
A decorator made it ergonomic for command authors.
Pre-commit hooks made it maintainable.
And three environment-detection strategies made it work regardless of how the user installed the tool.

If you're building a Python CLI with optional features that keep growing, consider this pattern.
Your users will thank you—mostly by never having to ask "which extras do I need?"

---

*The code discussed here is part of [`agent-cli`](https://github.com/basnijholt/agent-cli), an open-source suite of AI-powered command-line tools.
The implementation lives primarily in [`agent_cli/core/deps.py`](https://github.com/basnijholt/agent-cli/blob/c9a67b484331b64733edba8d72d20523699c5a72/agent_cli/core/deps.py).*
