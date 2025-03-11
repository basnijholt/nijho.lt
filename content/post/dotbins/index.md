---
title: "🧰 dotbins: Managing Binary Tools in Your Dotfiles"
subtitle: Managing modern CLI tools across multiple environments without admin privileges, using pre-compiled binaries in your dotfiles
summary: A solution for managing pre-compiled binaries for CLI tools directly in your dotfiles repository, making tools like `zoxide`, `bat`, `eza`, and more available on any system without installation.
projects: []
date: '2025-03-11T00:00:00Z'
draft: false
featured: false

image:
  caption: 'dotbins in action - downloading and managing CLI tools across platforms'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - terminal
  - productivity
  - dotfiles
  - cli-tools
  - binaries
  - zoxide
  - bat
  - eza
  - ripgrep
  - delta
  - fzf
  - python

categories:
  - terminal
  - level:intermediate
---

In my [previous post about terminal productivity](../terminal-ninja/), I shared a setup combining tools like `zsh`, `oh-my-zsh`, `zsh-z`, and various plugins to create a highly efficient command-line environment. While that setup served me well for years, I've recently encountered a challenge: incorporating modern, compiled CLI tools across all my environments without administrative privileges.

Today, I'm excited to [introduce **`dotbins`**](https://github.com/basnijholt/dotbins/) - a solution I created to solve this exact problem.

## The Modern CLI Tools Problem

Over the past few years, we've seen an explosion of incredible, modern CLI tools written in languages like Rust and Go.
Tools like:

- `zoxide` (a smarter, faster alternative to `zsh-z`)
- `bat` (a `cat` replacement with syntax highlighting)
- `eza` (a modern `ls` alternative)
- `delta` (a better diff viewer for Git)
- `fzf` (a fuzzy finder for your terminal)
- `ripgrep` (a faster, better `grep`)

These tools significantly enhance terminal productivity, but they come with a catch: **they're compiled binaries**, not simple scripts.
While my previous setup worked well because all the tools were basic shell scripts I could include as submodules in my dotfiles repository, these modern alternatives require installation.

This became frustrating when working on:
- Remote systems where I lacked admin/sudo permissions
- Machines that I use only temporarily
- Systems where I didn't want to install package managers

I'd spend time carefully setting up my dotfiles with all my configurations, only to find that the actual tools they relied on weren't available.

## Enter `dotbins` 🧰

[`dotbins`](https://github.com/basnijholt/dotbins/) was born out of this frustration.
It's a utility that manages pre-compiled binaries for CLI tools across multiple platforms and architectures, right in your dotfiles repository.

The key insight: **track pre-compiled binaries in a separate Git repository** (using Git LFS for efficiency), include this repository as a submodule in your dotfiles, and ensure all your essential tools are immediately available on any system.

No package manager, no sudo, no problem.

## How `dotbins` Works

`dotbins` handles several critical tasks:

1. **Downloads** binaries directly from GitHub releases for your selected tools
2. **Organizes** them by platform (macOS, Linux) and architecture (amd64, arm64)
3. **Tracks** installed versions and update timestamps
4. **Extracts** binaries from archives in various formats
5. **Integrates** seamlessly with your shell via a simple PATH addition

The configuration is straightforward - a YAML file where you define which tools you want and how to get them:

```yaml
tools:
  ripgrep:
    repo: BurntSushi/ripgrep
    extract_binary: true
    binary_name: rg
    binary_path: ripgrep-*/rg
    asset_patterns:
      linux: ripgrep-{version}-{arch}-unknown-linux-musl.tar.gz
      macos: ripgrep-{version}-{arch}-apple-darwin.tar.gz
    arch_map:
      amd64: x86_64
      arm64: aarch64
```

## My Workflow: A Two-Repository Approach

My approach uses two repositories:

1. **Private dotfiles repository** containing all my configurations
2. **Public [mydotbins repository](https://github.com/basnijholt/mydotbins)** containing all the binaries

I include `mydotbins` as a submodule in my dotfiles repository.
This separation keeps large binary files out of my main dotfiles repository and allows me to share the binary collection publicly while keeping my personal configurations private.

When I clone my dotfiles on a new system, I get not just my configuration files, but also all the CLI tools I depend on for productivity.

## Modern Alternatives to My Previous Setup

With `dotbins`, I've been able to upgrade several tools from my previous setup:

| Old Tool | Modern Alternative | Advantage |
|----------|-------------------|-----------|
| [`zsh-z`](https://github.com/agkozak/zsh-z) | [`zoxide`](https://github.com/ajeetdsouza/zoxide) | Faster, smarter, works across shells |
| `cat` | [`bat`](https://github.com/sharkdp/bat) | Syntax highlighting, Git integration |
| `ls` | [`eza`](https://github.com/eza-community/eza) | Better formatting, Git integration |
| `grep` | [`ripgrep`](https://github.com/BurntSushi/ripgrep) | Much faster, respects `.gitignore` |
| Default Git diff | [`delta`](https://github.com/dandavison/delta) | Syntax highlighting, better visual diffs |
| N/A | [`fzf`](https://github.com/junegunn/fzf) | Fuzzy finding makes everything better |
| N/A | [`atuin`](https://github.com/atuinsh/atuin) | Shell history with search and sync |

The best part? All of these are now automatically available on every machine where I clone my dotfiles, without any additional installation steps.

## Getting Started with `dotbins`

If you'd like to adopt this approach, here's how to get started:

1. Install `dotbins`:
   ```bash
   pip install dotbins
   # Or better yet, use uv:
   uvx dotbins
   ```

2. Create a configuration file at `~/.config/dotbins/config.yaml`:
   ```yaml
   tools_dir: ~/.mydotbins/tools
   
   platforms:
     linux:
       - amd64
       - arm64
     macos:
       - arm64
   
   tools:
     # Add your favorite tools here
     fzf:
       repo: junegunn/fzf
       extract_binary: true
       binary_name: fzf
       binary_path: fzf
       asset_patterns: fzf-{version}-{platform}_{arch}.tar.gz
       platform_map:
         macos: darwin
   ```

3. Initialize and download your tools:
   ```bash
   dotbins init
   dotbins update
   ```

4. Add the shell integration to your `.zshrc` or `.bashrc`:
   ```bash
   # dotbins - Add platform-specific binaries to PATH
   _os=$(uname -s | tr '[:upper:]' '[:lower:]')
   [[ "$_os" == "darwin" ]] && _os="macos"
   
   _arch=$(uname -m)
   [[ "$_arch" == "x86_64" ]] && _arch="amd64"
   [[ "$_arch" == "aarch64" || "$_arch" == "arm64" ]] && _arch="arm64"
   
   export PATH="$HOME/.mydotbins/tools/$_os/$_arch/bin:$PATH"
   ```

5. (Optional) Track your binaries in a separate Git repository with Git LFS for efficiency

## Finding New Tools to Add

Not sure which pattern to use for a new tool? The `analyze` command is here to help:

```bash
dotbins analyze sharkdp/bat
```

This will suggest a configuration for the tool based on its GitHub release assets.

## Conclusion: The Evolution of My Terminal Setup

With [`dotbins`](https://github.com/basnijholt/dotbins/), my terminal productivity setup has evolved beyond what I described in my [previous post](../terminal-ninja/).
I can now seamlessly incorporate the best modern CLI tools without worrying about installation or administrative privileges.

The beauty of this approach is its portability—I get a consistent, powerful environment on any machine where I clone my dotfiles.

If you're a terminal power user who works across multiple environments, give [`dotbins`](https://github.com/basnijholt/dotbins) a try.
It might just be the missing piece in your dotfiles setup!
