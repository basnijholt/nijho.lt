---
title: "Parallel agentic coding made trivial with `agent-cli dev`"
subtitle: "Git worktrees + auto-setup + terminal tabs = one command to rule them all"
summary: "I built a CLI that creates isolated development environments with git worktrees, automatically installs dependencies, and launches your AI coding agent in a new terminal tab—all in one command."
date: 2026-01-13
draft: false
featured: true
authors:
  - admin
tags:
  - python
  - ai
  - agentic-coding
  - claude-code
  - git
  - git-worktrees
  - productivity
  - development
  - cli
  - open-source
  - agent-cli
  - zellij
  - tmux
categories:
  - Software Development
  - AI
  - level:intermediate
image:
  caption: "One command to create a complete parallel development environment"
  focal_point: ""
  placement: 2
  preview_only: false
---

{{< toc >}}

## 1. The "just use worktrees" problem

Last week, I was chatting with a friend about my [agentic coding workflow]({{< ref "/post/agentic-coding" >}}).
I was sharing some of my best practices, and when the topic of parallel development came up, I said:

"Just use git worktrees with quickly installable environments."

He stared at me blankly.

And then it hit me: for most developers who just `git add`, `git commit`, `git push` and don't touch their environment setup once it works, this is *not* trivial.
What seems obvious to me involves:

1. Understanding what git worktrees even are
2. Knowing the `git worktree add` command and its flags
3. Remembering to fetch before creating
4. Creating a sibling directory structure
5. Running your package manager's install command
6. Copying over `.env` files
7. Setting up direnv or manually activating your virtual environment
8. Opening a new terminal tab
9. Navigating to the worktree
10. Finally launching your coding agent

That's a lot of friction for something you want to do *frequently* when using agentic tools.

So I built `agent-cli dev`.

{{% callout note %}}
**TL;DR:** `agent-cli dev new --agent` creates a complete, isolated development environment in one command.
It creates a git worktree, installs dependencies, copies env files, sets up direnv, and opens your AI coding agent in a new terminal tab—all automatically.
No more manual setup, no more excuses to not work in parallel.
{{% /callout %}}

## 2. Why parallel development matters for agentic coding

In my [previous post on agentic coding]({{< ref "/post/agentic-coding" >}}), I described my workflow of running 5-6 Claude Code sessions simultaneously, each working on a different feature.
This is how I can easily work on multiple features in parallel while waiting for an agent to process and generate code.

**The usual way:**
Start feature A → wait for Claude to finish → review → move to feature B → repeat.

**The better way:**
Start feature A in tab 1 → switch to tab 2, start feature B while A is working → switch to tab 3, start feature C → circle back to tab 1, review what Claude did → give feedback, move to next tab → repeat every 10-15 minutes.

This parallel approach allows me to go much faster.
But it only works if each tab has its own **completely isolated and working environment**.

That's where [git worktrees]({{< ref "/post/git-worktree" >}}) come in.
A worktree gives you a separate working directory for a branch, sharing the same git history but with independent file states.

The problem is the *setup*.
Every time you want to start a new feature:

```bash
# The manual way (don't do this)
git fetch origin
git worktree add ../my-project-worktrees/cool-feature -b cool-feature origin/main
cd ../my-project-worktrees/cool-feature
uv sync --all-extras  # or npm install, or poetry install, or...
cp ../.env .env
# Now open a new terminal tab...
# Navigate there...
# Finally start claude
```

After the 100th(?) time doing this manually, I knew I needed to automate it.

## 3. One command to rule them all

Here's what I built:

```bash
agent-cli dev new --agent
```

That's it.
One command.
Here's what it looks like:

```bash
→ Generated branch name: cool-crane
→ Creating worktree for branch 'cool-crane'...
→ Running: git fetch origin
→ Running: git worktree add -b cool-crane ~/Work/project-worktrees/cool-crane origin/main
✓ Created worktree at ~/Work/project-worktrees/cool-crane
✓ Copied env file(s): .env.example, .envrc
→ Detected Python project with uv
→ Running: uv sync --all-extras
→ Running: direnv allow
✓ direnv: allowed existing .envrc
✓ Started claude in new iterm2 tab

╭─────────────────────────────────────────────── Success ───────────────────────────────────────────────╮
│ Dev environment created: ~/Work/project-worktrees/cool-crane                                          │
│ Branch: cool-crane                                                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

4 seconds later, I have a new terminal tab with Claude Code already running in a fresh, isolated environment.
Ready to work on my next feature.

What happens under the hood:

1. **Generates a random branch name** like `clever-fox` (you can just set the name yourself of course)
2. **Creates the git worktree** in a sibling directory
3. **Detects the project type** and runs the appropriate setup (`uv sync`, `npm install`, etc.)
4. **Copies `.env` files** from the main repo
5. **Sets up direnv** so the environment activates automatically
6. **Opens a new terminal tab** (works with tmux, zellij, iTerm2, and more)
7. **Launches your coding agent** in that tab

The Docker-style random names (`clever-fox`, `happy-bear`, `swift-owl`) there just for those too lazy to pick a name.
Just `agent-cli dev new --agent` and start coding.

## 4. It knows your stack

The command auto-detects your project type:

| If it sees... | It runs... |
|---------------|------------|
| `uv.lock` | `uv sync --all-extras` |
| `pixi.lock` | `pixi install` |
| `poetry.lock` | `poetry install` |
| `requirements.yaml` | `unidep install -e .` |
| `package-lock.json` | `npm install` |
| `Cargo.toml` | `cargo build` |
| `go.mod` | `go mod download` |

For my projects using [unidep](https://github.com/basnijholt/unidep), it even detects monorepos and adjusts the command accordingly.

It also generates the right `.envrc` for [direnv](https://direnv.net/).
For a Python project with uv, that's `source .venv/bin/activate`.
For a conda/unidep project, it's the full micromamba activation.
For Nix projects, it's `use flake`.

This means when you `cd` into the worktree later, your environment is automatically activated.
No more `source .venv/bin/activate`.

## 5. Terminal magic

The real magic is opening a new terminal tab with the agent already running.

The command detects which terminal you're in and uses the appropriate API—whether that's iTerm2, Kitty, Warp, or GNOME Terminal.
It even works with terminal multiplexers like **tmux** and **zellij** (my current favorite), opening a new window/tab in your existing session.

## 6. My actual workflow

Here's how I will use this in practice.
I'm working on [agent-cli](https://github.com/basnijholt/agent-cli) itself, and I want to add three features:

```bash
# Tab 1: New RAG feature
agent-cli dev new rag-improvements --agent

# Tab 2: Fix a bug in the transcribe command
agent-cli dev new fix-transcribe-vad --agent

# Tab 3: Refactor the config system
agent-cli dev new config-refactor --agent
```

Three commands, three isolated environments, three Claude Code sessions running in parallel.

I cycle through the tabs every 10-15 minutes:
- Review what Claude did
- Give voice feedback using my [transcription workflow]({{< ref "/post/local-ai-journey" >}})
- Move to the next tab

When a feature is done, I have Claude open a PR from that branch.
When the PR is merged:

```bash
agent-cli dev clean --merged
```

This uses the GitHub CLI to check which branches have merged PRs, then removes those worktrees and deletes the branches.
No more zombie worktrees cluttering my disk.

## 7. Managing environments

A few other commands I use regularly:

```bash
# List all worktrees
agent-cli dev list

# Navigate to a worktree
cd "$(agent-cli dev path clever-fox)"

# Remove a worktree
agent-cli dev rm clever-fox

# Force removal + delete branch
agent-cli dev rm clever-fox --force --delete-branch

# Check what's available on your system
agent-cli dev doctor
```

The `doctor` command is handy for seeing which terminals, editors, and coding agents are installed and detected.

## 8. Getting started

`agent-cli dev` is part of the [agent-cli](https://github.com/basnijholt/agent-cli) package:

```bash
# With uv (recommended)
uv tool install agent-cli
```

Then in any git repository:

```bash
# Check what's available
agent-cli dev doctor

# Create your first parallel environment
agent-cli dev new --agent
```

**Supported coding agents:** Claude Code, Codex, Gemini, Aider, GitHub Copilot, Continue, OpenCode, and Cursor Agent.
Use `--with-agent gemini` to pick a specific one, or set a default in your config.

**Supported terminals:** tmux, zellij, iTerm2, Terminal.app, Kitty, Warp, and GNOME Terminal.

**Supported editors:** Cursor, VS Code, Zed, PyCharm (and other JetBrains IDEs), Neovim, Vim, Emacs, Sublime Text, and nano.

## Conclusion

The barrier between "I want to work on this feature" and "I'm actually working on it in an isolated environment" should be zero.

Before:
- 2-5 minutes of manual setup per feature
- Often skipped because "it's not worth it for a small change"
- Mental overhead remembering all the steps

After:
- One command, few seconds
- No excuse not to work in isolation
- More parallel features, faster iteration

If you're using agentic coding tools and not yet working in parallel, you're leaving productivity on the table.
And if the setup friction was stopping you—well, now it's gone.

Try it out and let me know what you think!
The code is open-source at [github.com/basnijholt/agent-cli](https://github.com/basnijholt/agent-cli).

## Links

- [agent-cli on GitHub](https://github.com/basnijholt/agent-cli)
- [`agent-cli dev` documentation](https://agent-cli.nijho.lt/commands/dev/)
- [My post on git worktrees]({{< ref "/post/git-worktree" >}})
- [My post on agentic coding]({{< ref "/post/agentic-coding" >}})
- [Zellij](https://zellij.dev/) / [tmux](https://github.com/tmux/tmux)
- [direnv](https://direnv.net/)
