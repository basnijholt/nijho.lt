---
title: "Auto-installing dependencies at runtime so users never have to think about extras"
subtitle: "How uv, uvx, and a decorator turned a dependency nightmare into a seamless experience"
summary: "When your CLI tool has 13 optional extras spanning voice recognition, TTS, RAG, memory, and LLM frameworks, expecting users to know which ones to install is a non-starter. I built a system that automatically detects missing dependencies at runtime and installs them transparently—even in ephemeral uvx environments. Here's how."
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
  - cli
  - open-source
  - agent-cli
  - developer-experience
  - packaging
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

## 1. The problem: a CLI that does too many things

[`agent-cli`](https://github.com/basnijholt/agent-cli) started as a simple voice interface.
It connected to a Wyoming Whisper server for speech-to-text and a Piper server for text-to-speech.
Basically a local, open-source Siri that actually worked.

Then I kept adding things.

A RAG proxy with ChromaDB.
A long-term memory system.
LLM integration via pydantic-ai.
Server commands that run Kokoro TTS or Whisper locally, optimized for whatever hardware you have.
Voice activity detection with Silero VAD via ONNX.
An agent orchestration system.
Audio speed adjustment.

Over time, the dependency list exploded.
Today the project has **13 optional extras**, each pulling in vastly different dependency trees—from `torch` and `transformers` for GPU-accelerated Whisper to `sounddevice` for microphone access to `chromadb` for vector storage.

{{% callout note %}}
**TL;DR:** I built a decorator (`@requires_extras`) that automatically detects missing dependencies when you run a command, installs them into the correct environment (whether that's a `uv tool` install, a virtualenv, or an ephemeral `uvx` run), and re-executes the command—all transparently.
The user just runs `agent-cli transcribe` and everything works.
{{% /callout %}}

## 2. Why "just use extras" doesn't work

Python's `optional-dependencies` in `pyproject.toml` is the standard mechanism for this.
You define groups like `[project.optional-dependencies]` and users install with `pip install agent-cli[rag]`.
On paper, this is fine.

In practice, it falls apart when you have 13 of them:

```toml
[project.optional-dependencies]
audio = ["numpy", "sounddevice>=0.4.6", "agent-cli[wyoming]"]
llm = ["pydantic-ai-slim[openai,google,duckduckgo,vertexai]>=0.1.1"]
rag = ["pydantic-ai-slim[openai,google]>=0.1.1", "fastapi[standard]", "chromadb>=0.4.22", ...]
memory = ["pydantic-ai-slim[openai,google]>=0.1.1", "fastapi[standard]", "chromadb>=0.4.22", ...]
vad = ["onnxruntime>=1.16.0"]
faster-whisper = ["fastapi[standard]", "faster-whisper>=1.0.0"]
mlx-whisper = ["mlx-whisper>=0.4.0; sys_platform == 'darwin' and platform_machine == 'arm64'"]
kokoro = ["fastapi[standard]", "kokoro>=0.9.0", "soundfile>=0.12.0", ...]
piper = ["fastapi[standard]", "piper-tts>=1.2.0"]
server = ["fastapi[standard]"]
speed = ["audiostretchy>=1.3.0"]
whisper-transformers = ["fastapi[standard]", "transformers>=4.30.0", "torch>=2.0.0"]
wyoming = ["wyoming>=1.5.2"]
```

The user experience problem is obvious: **which extras do I need?**

If I want to transcribe voice to text, do I need `audio`? `llm`? `vad`? All three?
What if I want the Whisper server to run locally—is that `faster-whisper` or `mlx-whisper`?
And do I also need `server` for that?

Expecting users to study a dependency matrix before running a CLI command is a terrible experience.
The base package should be lightweight and fast to install, but any subcommand should "just work."

## 3. The decorator: `@requires_extras`

The core idea is dead simple.
Each CLI command declares what it needs:

```python
@app.command("transcribe", rich_help_panel="Voice Commands")
@requires_extras("audio", "llm")
def transcribe(...):
    ...
```

That's it from the command author's perspective.
The decorator does the rest:

1. Check if the required packages are installed (without importing them—just using `importlib.util.find_spec`)
2. If something's missing, try to install it automatically
3. If the install succeeds, re-execute the command so the new packages are visible
4. If it fails, show a helpful error message

Here's the decorator itself:

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

The real complexity lives in `_check_and_install_extras`, which handles five different scenarios.
But the interface is a single line.

## 4. Detecting what's installed (without importing it)

This is a subtle but important detail.
You don't want to *import* `torch` just to check if it's available—that takes seconds and loads hundreds of megabytes into memory.
Instead, you ask Python's import machinery if it *could* import it:

```python
from importlib.util import find_spec

def _check_package_installed(pkg: str) -> bool:
    top_module = pkg.split(".", maxsplit=1)[0]
    try:
        return find_spec(top_module) is not None
    except (ValueError, ModuleNotFoundError):
        return False
```

`find_spec` checks if a module exists on the import path without executing any of its code.
This means the check is essentially free—no heavy imports, no GPU initialization, no side effects.

## 5. The metadata bridge: `_extras.json`

There's a gap between what `pyproject.toml` knows and what the runtime check needs.
`pyproject.toml` says the `rag` extra requires `chromadb>=0.4.22`.
But `chromadb` is the *pip package name*.
At runtime, you import it as `chromadb`—same in this case, but consider `pydantic-ai-slim` which you import as `pydantic_ai`, or `piper-tts` which you import as `piper`.

To bridge this, I generate an `_extras.json` file that maps each extra to its description and the Python import names needed for the runtime check:

```json
{
  "audio": ["Audio recording/playback", ["sounddevice"]],
  "rag": ["RAG proxy (ChromaDB, embeddings)", ["chromadb", "pydantic_ai"]],
  "memory": ["Long-term memory proxy", ["chromadb", "yaml", "pydantic_ai"]],
  "vad": ["Voice Activity Detection (Silero VAD via ONNX)", ["onnxruntime"]],
  "faster-whisper": ["Whisper ASR via CTranslate2", ["faster_whisper"]]
}
```

This file is generated by a script that parses `pyproject.toml` and applies a mapping table for package-name-to-import-name conversions.
A pre-commit hook ensures it stays in sync—if you add an extra to `pyproject.toml` and forget to update the metadata, the commit fails.

## 6. Three environments, three strategies

Here's where it gets interesting.
Users run `agent-cli` in at least three different ways, and each requires a different installation strategy.

### Strategy 1: `uv tool install` (persistent environment)

When installed via `uv tool install agent-cli`, the tool lives in a persistent environment under `~/.local/share/uv/tools/agent-cli/`.
This environment has a `uv-receipt.toml` file that tracks which extras are installed:

```toml
[tool]
requirements = [
  { name = "agent-cli", extras = ["audio", "llm"] }
]
```

When auto-install triggers, the system:
1. Reads the current extras from `uv-receipt.toml`
2. Merges in the new ones: `{"audio", "llm"} | {"vad"}` → `{"audio", "llm", "vad"}`
3. Runs `uv tool install agent-cli[audio,llm,vad] --force`
4. Re-executes the original command

The key insight: `uv tool upgrade` reads `uv-receipt.toml` and preserves the extras list.
So once auto-install adds an extra, it persists across future upgrades.
You never have to install it again.

### Strategy 2: `uvx` (ephemeral environment)

`uvx` is uv's tool for running packages in temporary, disposable environments.
Running `uvx agent-cli transcribe` creates a fresh environment, installs `agent-cli`, runs the command, and throws the environment away.

The problem: there's nothing to persist extras *to*.
The solution: re-execute with the extras baked into the `uvx` command itself:

```python
def _maybe_reexec_with_uvx(extras: list[str]) -> None:
    if os.environ.get(_REEXEC_MARKER) or not _is_uvx_cache():
        return
    uvx_path = shutil.which("uvx")
    if not uvx_path:
        return
    extras_str = ",".join(extras)
    cmd = [uvx_path, "--python", "3.13",
           f"agent-cli[{extras_str}]", *sys.argv[1:]]
    _maybe_exec_with_marker(cmd, f"Re-running with extras: {extras_str}")
```

So `uvx agent-cli transcribe` becomes, transparently, `uvx agent-cli[audio,llm] transcribe`.
The user sees a brief "Re-running with extras: audio, llm" message, and then the command works.

The environment detection is straightforward—`uvx` environments live under the uv cache directory:

```python
def _is_uvx_cache() -> bool:
    prefix_str = Path(sys.prefix).resolve().as_posix()
    return "/cache/uv/" in prefix_str or "/archive-v" in prefix_str
```

### Strategy 3: Regular virtualenv / system install

For plain `pip install agent-cli` or virtualenv installs, the system falls back to direct pip/uv installation.
Each extra has a pre-generated requirements file with pinned versions:

```
# agent_cli/_requirements/audio.txt
sounddevice==0.5.3
numpy==2.3.5
...
```

The install command adapts to the environment:

```python
def _install_cmd() -> list[str]:
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

After installation, it re-executes the command so the newly installed packages are visible to the Python import system.

## 7. Preventing infinite re-execution loops

There's an obvious footgun here: what if the install succeeds but the package still isn't importable?
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

## 8. Alternative extras with pipe syntax

Some commands need *one of several possible* backends.
For example, the TTS server works with either Piper or Kokoro, and the Whisper server works with faster-whisper, mlx-whisper, or whisper-transformers.

Rather than requiring all of them, the decorator supports a pipe syntax:

```python
@requires_extras("server", "piper|kokoro", "wyoming")
def start_tts_server(...):
    ...
```

This means: you need `server` AND `wyoming` AND **either** `piper` **or** `kokoro`.
The check logic handles this:

```python
def _check_extra_installed(extra: str) -> bool:
    if "|" in extra:
        return any(_check_extra_installed(e) for e in extra.split("|"))
    ...
```

When auto-installing alternatives, the system picks the already-installed one if any, otherwise defaults to the first option.
This means on Apple Silicon, if you already have `mlx-whisper` installed, it won't try to install `faster-whisper` instead.

## 9. The build pipeline: keeping everything in sync

The runtime system depends on two generated artifacts:
- `_extras.json`: Maps extras to descriptions and import names
- `_requirements/*.txt`: Pinned dependency files for each extra

Both are generated from `pyproject.toml` and `uv.lock` by scripts that run as pre-commit hooks:

```yaml
# .pre-commit-config.yaml
- id: sync-extras
  name: sync _extras.json with pyproject.toml
  entry: python .github/scripts/sync_extras.py
  files: ^(pyproject\.toml|agent_cli/_extras\.json)$

- id: sync-requirements
  name: sync requirements files with uv.lock
  entry: python .github/scripts/sync_requirements.py
  files: ^(pyproject\.toml|uv\.lock)$
```

A separate check script validates that everything is consistent—if you add an extra to `pyproject.toml` but forget to add its metadata, the pre-commit hook fails with a clear error.

This means the runtime system never drifts from the source of truth.
`pyproject.toml` is the canonical definition, everything else is derived.

## 10. Disabling auto-install

Not everyone wants software installing things without asking.
The system respects two opt-outs:

1. Environment variable: `AGENT_CLI_NO_AUTO_INSTALL=1`
2. Config file: `[settings] auto_install_extras = false`

When disabled, the decorator shows a clear error message instead:

```
This command requires the 'audio' extra (Audio recording/playback).

Install with:
  uv tool install -p 3.13 "agent-cli\[audio]"
  # or
  agent-cli install-extras audio
```

There's also a manual `install-extras` command for when you want explicit control:

```bash
agent-cli install-extras rag memory    # Install specific extras
agent-cli install-extras --all         # Install everything
agent-cli install-extras --list        # Show available extras with descriptions
```

## 11. Why uv made this possible

I want to be clear: this system would be *much* harder without [uv](https://docs.astral.sh/uv/).
Several uv features are critical:

- **`uv tool install`** with persistent extras in `uv-receipt.toml`—extras survive upgrades
- **`uvx`** for ephemeral execution with extras specified inline
- **`uv pip install`** that's fast enough for runtime auto-install to not feel painful
- **`uv export`** for generating pinned requirements files from `uv.lock`

With traditional pip, auto-installing at runtime would take 30-60 seconds and feel terrible.
With uv, it typically takes a few seconds.
That's the difference between "annoying" and "barely noticeable."

## 12. The full flow

Here's what happens when a user runs `agent-cli transcribe` for the first time:

1. The `transcribe` command has `@requires_extras("audio", "llm")`
2. The decorator calls `_check_and_install_extras(("audio", "llm"))`
3. `find_spec("sounddevice")` returns `None`—`audio` is missing
4. Auto-install is enabled (default), so we proceed
5. **If uvx**: re-exec as `uvx agent-cli[audio,llm] transcribe` (replaces process)
6. **If uv tool**: merge extras, run `uv tool install agent-cli[audio,llm] --force`, re-exec
7. **If virtualenv**: run `uv pip install -r _requirements/audio.txt`, re-exec
8. The re-executed process runs the check again—this time everything is found
9. The command runs normally

The user sees:

```
Auto-installing missing extras: audio, llm
Running: uv tool install agent-cli[audio,llm] --force -q
Installation complete!
Re-running with installed extras...
```

And then their command works.
Next time, it runs instantly—no install needed.

## 13. What I'd do differently

The system works well, but it's not without warts:

**The `_extras.json` metadata is partially manual.**
The package-name-to-import-name mapping requires a lookup table with special cases like `piper-tts` → `piper` and `pydantic-ai-slim` → `pydantic_ai`.
Python packaging has no standard way to discover a package's top-level import name from its distribution name.
I wish `pyproject.toml` had a field for this.

**The check only verifies importability, not version compatibility.**
`find_spec` tells you a module exists, not whether it's the right version.
In practice this hasn't been a problem because uv's pinned requirements handle versions, but it's a theoretical gap.

**Re-execution is invisible to the user's shell.**
`os.execvpe` replaces the process, which means any shell hooks or signal handlers set up before the decorator runs are lost.
This is fine for CLI tools but would be problematic for libraries.

## 14. Conclusion

The underlying principle is simple: **the tool should know what it needs, and it should get it**.
Users shouldn't have to study a matrix of 13 optional extras to figure out which pip command to run.
They should just type the command they want, and it should work.

uv's speed and tooling model made this practical.
A decorator made it ergonomic.
Pre-commit hooks made it maintainable.

If you're building a Python CLI with optional features, consider this pattern.
Your users will thank you—mostly by never having to ask "which extras do I need?"

---

*The code discussed here is part of [`agent-cli`](https://github.com/basnijholt/agent-cli), an open-source suite of AI-powered command-line tools.*
*Specifically, the implementation lives in [`agent_cli/core/deps.py`](https://github.com/basnijholt/agent-cli/blob/main/agent_cli/core/deps.py).*
