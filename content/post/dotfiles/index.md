---
title: "Open Sourcing My Dotfiles: A Practical, Cross-Platform Terminal Setup"
subtitle: Sharing years of refinement in shell configuration, automation, and tool management for macOS and Linux environments.
summary: After years running them privately across 10+ machines (macOS, Linux, cloud, homelab), I'm open-sourcing my dotfiles, featuring modular configs, dotbins for CLI tools, Nix-Darwin, and more.
projects: []
date: "2025-04-05T00:00:00Z"
draft: false
featured: true

image:
  filename: featured.png
  caption: "4o generated logo for my dotfiles"
  focal_point: "Smart" # Center, Top, Left, Right, Smart...
  placement: 2 # 1 = Above page content, 2 = Within page content (above Fold), 3 = Below page content
  preview_only: false

authors:
  - admin

tags:
  - dotfiles
  - terminal
  - productivity
  - zsh
  - bash
  - cli-tools
  - automation
  - dotbot
  - dotbins
  - nix-darwin
  - cross-platform
  - keychain
  - git
  - uv
  - iterm2

categories:
  - terminal
  - setup
  - level:intermediate
---

## Introduction

Many of us spend a significant amount of time in the terminal.
Over the years, I've found that investing in a well-organized and consistent command-line environment pays dividends in productivity and, frankly, makes the daily grind more enjoyable.
After refining my personal setup across more than 10 different machines – ranging from my primary MacBooks to Linux servers (x86/ARM), Raspberry Pis in my [homelab]({{< ref "/post/homelab" >}}), cloud VMs, and even my iPhone via iSH – I've decided it's time to share it publicly.
The need for a consistent experience across such diverse hardware and operating systems was a major driving force behind this setup's evolution.

Today, I'm open sourcing my complete [dotfiles repository](https://github.com/basnijholt/dotfiles) 🎉.
This isn't about presenting a "perfect" solution, but rather sharing a practical system that has evolved to handle real-world needs like cross-platform consistency, easy setup on new machines, and integrating modern CLI tools effectively.
If you're looking for ideas to streamline your own terminal workflow, I hope you find something useful here.

{{< toc >}}

## Why Open Source Now?

I have maintained my dotfiles for many years in a private repository.
Sharing this setup feels like a natural step for a few reasons:

1.  **Sharing Solutions:** This setup incorporates solutions to problems I've wrestled with, like managing binaries without `sudo` (leading to my [`dotbins`](https://github.com/basnijholt/dotbins) tool), achieving [consistent SSH agent behavior]({{< ref "/post/ssh-1password-funtoo-keychain" >}}), or getting Python environments to activate seamlessly with [direnv](https://direnv.net/).
2.  **Giving Back:** I've learned a lot from countless other dotfiles repos and articles shared by the community. It feels right to contribute my own approach.
3.  **Transparency & Learning:** Open sourcing allows others to see how different pieces fit together and perhaps adapt ideas for their own configurations.

However, the driving force was the recent creation of my [`dotbins` tool]({{< ref "/post/dotbins" >}}) and honestly, I just want to share "my way" of doing things.

## Core Ideas & Highlights

My setup is built around a few key principles aimed at practicality and efficiency:

### 1. Cross-Platform & Shell Agnostic

It's designed to work reliably on macOS (`aarch64`) and various Linux distros (`x86_64`, `aarch64`).
While Zsh is my preference (leveraging [Oh-My-Zsh](https://ohmyz.sh/)), the core configurations in `configs/shell/` are sourced by both `.zshrc` and `.bash_profile`, ensuring basic compatibility.

### 2. Modularity for Sanity

Instead of one giant config file, the shell setup is broken down logically:

```bash
configs/shell/
├── 00_prefer_zsh.sh       # Switches Bash users to Zsh if available
├── 10_aliases.sh          # Common aliases
├── 20_exports.sh          # Environment variables
├── 30_misc.sh             # Dotbins init, secrets sourcing
├── 40_keychain.sh         # SSH agent setup (Keychain/1Password)
├── 50_python.sh           # Python env helpers (conda, uv, direnv)
# ... and others for Zsh specifics, SLURM, etc.
└── main.sh                # Sources the relevant files above
```

This makes it much easier to understand, maintain, and debug specific parts of the configuration. My actual `.zshrc` and `.bash_profile` just source `main.sh`.

### 3. Automation via Dotbot

A core goal here is a true [`./install`](https://github.com/basnijholt/dotfiles/blob/main/install) and done setup.
[Dotbot](https://github.com/anishathalye/dotbot) is key to this automation.
Setting up a new machine or syncing changes is streamlined using this tool.
The [`install.conf.yaml`](https://github.com/basnijholt/dotfiles/blob/main/install.conf.yaml) file defines which config files get symlinked where, _and_ runs initial setup commands.
This includes updating submodules and, importantly, using `uv tool install` to install a curated list of essential Python CLI tools (`ruff`, `pre-commit`, `dotbins` itself, etc.) globally, ensuring they're immediately available after installation.
For remote machines, [`scripts/sync-dotfiles.sh`](https://github.com/basnijholt/dotfiles/blob/main/scripts/sync-dotfiles.sh) handles pulling updates and optionally re-running the install.

### 4. Hassle-Free CLI Tools with `dotbins`

Modern CLI tools are fantastic, but installing them everywhere, especially without `sudo`, can be a pain.
I built [`dotbins`](https://github.com/basnijholt/dotbins) to solve this.
It downloads pre-compiled binaries for specified tools directly from GitHub releases, organizing them by platform/architecture.

```yaml
# Snippet from ~/.dotbins/dotbins.yaml
tools:
  delta: dandavison/delta # Git diff tool
  eza: eza-community/eza # Modern 'ls'
  zoxide: ajeetdsouza/zoxide # Smarter 'cd'
  starship: starship/starship # Shell prompt
  atuin: atuinsh/atuin # Shell history sync
  # ... plus tools with shell integration code
```

The shell setup automatically adds the correct binary path and runs any needed initialization.
More details in my [`dotbins` post]({{< ref "/post/dotbins" >}}).

### 5. Sensible SSH Key Management

Using [Funtoo Keychain](https://www.funtoo.org/Funtoo:Keychain), often integrated with the 1Password CLI for passphrase retrieval, means I typically only deal with my SSH key passphrase once per login session.
This setup is detailed [here]({{< ref "/post/ssh-1password-funtoo-keychain" >}}).

### 6. (macOS) Declarative Setup with Nix-Darwin

On my Macs, I use [Nix-Darwin](https://github.com/LnL7/nix-darwin) to manage system settings and even Homebrew packages declaratively (`configs/nix-darwin/`).
Running `nixswitch` applies the entire configuration, making macOS setups highly reproducible.

## A Note on Alternatives & Design Choices

You might wonder why I haven't adopted certain popular tools or approaches. Here's some rationale behind the choices made in this setup:

- **Why not `fish` shell?** While `fish` offers many appealing modern features (and [its Rust rewrite is intriguing](https://fishshell.com/blog/rustport/)!), a core requirement for my setup is broad compatibility. I need my core shell environment to function reliably even on minimal Linux systems (servers, containers, HPC nodes) where `bash` is often the only guarantee. For this reason, I use `zsh` as a powerful, yet largely POSIX-compatible, middle ground that works well across my diverse environments without requiring a non-standard shell installation everywhere.

- **Why iTerm2 on macOS?** I've experimented with newer terminals like WezTerm, Ghostty, Kitty, and Alacritty. Many offer benefits like impressive speed and GPU rendering. However, I consistently return to [iTerm2](https://iterm2.com/).

  - **Criticisms & Rebuttals:** iTerm2 is often criticized for being "bloated" or "slow," and historically, its settings weren't easily version controllable. Frankly, on modern hardware, any perceived slowness is negligible for my use cases. More importantly, iTerm2 _does_ allow its profiles to be saved as JSON (see [my `Profiles.json`](https://github.com/basnijholt/dotfiles/blob/main/configs/iterm/Profiles.json) in this repo), making the configuration easily version controlled via dotfiles.
  - **The Killer Feature:** The primary reason I stick with iTerm2 is its robust **Semantic History** feature. The ability to Cmd-Click URLs/filenames in terminal output – even complex ones with line numbers like `src/my_module/file.py:123` – and have them open directly in VS Code at the correct line is indispensable for my debugging and development workflow. I haven't found this replicated with the same reliability and ease of configuration elsewhere.
  - **Other Features:** I also like simple features selecting text and (without `⌘+C`!) pasting it right back into the terminal, and the window and tab management features.
  - **Ghostty Example:** I recently tried Ghostty and liked many aspects, but quickly ran into limitations that highlighted my reliance on iTerm2 features, such as the lack of built-in text search, scrollbars, and crucially, the clickable file paths with line numbers ([as discussed here](https://bsky.app/profile/basnijholt.bsky.social/post/3lehtwv2pxc2j)).

- **No `sudo` Required:** A key design principle is that the installation process via `./install` (Dotbot symlinking, `uv tool install`, `dotbins` fetching binaries) operates _entirely within the user's home directory_. No `sudo` access is needed to get the core environment up and running. This makes the setup viable in restricted environments like HPC clusters, shared servers, or locked-down corporate machines where admin rights aren't available.

## A Look Inside: Structure

The repository is organized to keep things separated logically:

```bash
.
├── configs/              # Configs (atuin, bash, git, nix, shell, zsh...)
├── install               # Main installation script (runs dotbot)
├── install.conf.yaml     # Dotbot: Links configs, runs setup commands
├── scripts/              # Utility scripts (syncing, backups, helpers)
├── submodules/           # External tools managed as submodules (dotbot, dotbins, plugins...)
└── README.md             # Detailed overview
```

## Getting Started

If you want to try this setup or adapt parts of it:

1.  **Prerequisites:** `git` is essential. SSH access to GitHub is needed if you fork and want to manage the private `secrets` submodule or other private submodules.
2.  **Clone:**
    ```bash
    # Clone recursively to get submodules
    git clone --recurse-submodules -j8 git@github.com:basnijholt/dotfiles.git
    cd dotfiles
    ```
3.  **Install:**
    ```bash
    ./install
    ```
    This single command runs Dotbot, which handles creating configuration symlinks, updating Git submodules, _and_ installing numerous Python tools via `uv` (as defined in `install.conf.yaml`).
    Combined with `dotbins` automatically fetching other pre-compiled binaries, your environment should be remarkably complete after this step.
    Restart your shell after it finishes.
4.  **⚠️ Important: Customize!**

    - **Fork the repository first!** Don't use my configuration directly, especially `configs/git/gitconfig`.
    - Update `configs/git/gitconfig` with _your_ name and email.
    - Review `install.conf.yaml` – remove links or shell commands you don't need. You can see the full list of Python tools installed via `uv` [here](https://github.com/basnijholt/dotfiles/blob/main/install.conf.yaml).
    - Modify `configs/shell/` files to suit your workflow.
    - Adjust the `dotbins` configuration (`submodules/dotbins/dotbins.yaml`) to include _your_ favorite tools.

## A Note on Secrets

Sensitive information (API keys, etc.) is _not_ stored directly in the public repository.
I use a private Git repository included as a submodule (`secrets/`).
This requires SSH authentication.
Within that private repo, I use `gpg` and [git-secret](https://github.com/sobolevn/git-secret) to encrypt sensitive files, adding another layer of security.
You'll need your own strategy for managing secrets, whether it's a similar private repo, environment variables, or a dedicated secrets manager.

## Conclusion

This dotfiles setup represents my ongoing effort to build a productive, consistent, and enjoyable terminal environment across a diverse range of machines – from personal laptops to [homelab servers]({{< ref "/post/homelab" >}}) and cloud instances.
It solves real problems I've encountered in maintaining that consistency.
By sharing it, I hope to offer some practical ideas and perhaps save others some time in crafting their own ideal setup.

Feel free to explore the [repository](https://github.com/basnijholt/dotfiles), borrow what you find useful, and adapt it to your needs.
If you find it helpful, consider giving it a star!
If you have suggestions or find issues, contributions are welcome!

Happy terminal tinkering!

---

**Further Reading & Links:**

- [My Dotfiles Repository on GitHub](https://github.com/basnijholt/dotfiles)
- Blog Post: [My Homelab Setup]({{< ref "/post/homelab" >}})
- Blog Post: [Be a Ninja in the Terminal 🥷]({{< ref "/post/terminal-ninja" >}})
- Blog Post: [dotbins: Managing Binary Tools in Your Dotfiles 🧰]({{< ref "/post/dotbins" >}})
- Blog Post: [Combining Keychain and 1Password CLI for SSH Agent Management]({{< ref "/post/ssh-1password-funtoo-keychain" >}})
- [Dotbot](https://github.com/anishathalye/dotbot)
- [Dotbins](https://github.com/basnijholt/dotbins)
- [Git Secret](https://github.com/sobolevn/git-secret)
- [iTerm2](https://iterm2.com/)
