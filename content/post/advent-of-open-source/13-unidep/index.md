---
title: "UniDep 🧬"
date: 2024-12-13
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 13/24: Simplifying Python dependency management across pip, conda, and complex projects."
subtitle: "🎄🎁 Advent of Open Source – Day 13/24: A tool to unify dependency management, making project setup a breeze."
tags:
  - open-source
  - python
  - devtools
  - programming
  - packagemanagement
  - conda
  - advent
categories:
  - technology
  - open-source
  - advent
authors:
  - admin
excludeFromList: true
---

(See my [intro post](../))

Ever tried to set up a Python project that needs both pip and conda packages? Then you know the pain of maintaining multiple requirement files. [UniDep](https://github.com/basnijholt/unidep) was born from years of frustration with this exact problem.

## 📖 Origin Story

While working on large monorepos with hundreds of dependencies, I kept running into the same issue: maintaining separate files for conda (`environment.yml`), pip (`requirements.txt`), and Python packaging (`pyproject.toml`). Coming from languages like Rust, where package management is a joy, Python's fragmented ecosystem can feel overwhelming, especially to newcomers (obligatory [xkcd.com/1987](https://xkcd.com/1987/)).

What started as a simple tool to avoid duplicate dependency definitions turned into something much more powerful. In enterprise environments, it's common to find monorepos with over 1000 dependencies spread across dozens of packages. Setting up these environments traditionally involves following lengthy setup guides, installing packages in the correct order, and hoping nothing breaks.

Then came the "aha" moment - what if we could install everything with a single command? After implementing UniDep, those complex setup guides became a one-liner: `unidep install-all -e`. It installs all dependencies and sets up every package in the monorepo in editable mode. What used to take hours now takes minutes.

{{< figure src="meme.png" caption="The difficulty of managing pip and conda" alt="Meme with the text 'ONE DOES NOT SIMPLY MANAGE BOTH PIP AND CONDA DEPENDENCIES' featuring Sean Bean as Boromir from The Lord of the Rings." >}}

## 🔧 Technical Highlights

- Single source of truth for all dependencies
- Supports both `requirements.yaml` and `pyproject.toml`
- Handles platform-specific dependencies
- Generates conda-lock files both for entire monorepos and fully consistent lock files for its individual packages
- Works with pip, conda, and mamba
- Monorepo-friendly with local dependency support
- Integrates with setuptools and hatchling
- ≥99% test coverage, fully-typed

## 📊 Impact

- 221 GitHub stars
- Featured on [Python Bytes podcast](https://www.youtube.com/live/PRaTs3PnJvI?si=UrVozo81Pj8WcyXh&t=489)
- Saves countless hours of dependency management
- Makes complex project setups accessible
- Actively maintained with 70 releases

## 🎯 Challenges and Solutions

- Different package naming between pip and conda
- Platform-specific dependencies
- Cross-platform compatibility (Linux, Windows, MacOS)
- Supporting pip-only workflows

## 💡 Lessons Learned

1. Good developer experience is worth the effort
2. Sometimes you need to build a bridge between existing tools
3. The best tools make hard things easy
4. Dependency resolution is hard but can be simple for users

## 🔮 Future Plans

- Adding Pixi support - allowing seamless migration to Pixi without changing config files
- Eventually, Pixi might make UniDep obsolete (and that's okay!)
- For now, UniDep bridges the gap between pip and conda, making life easier for developers

Want simpler dependency management? Check out [UniDep on GitHub](https://github.com/basnijholt/unidep)!

#OpenSource #Python #DevTools #Programming #PackageManagement #Conda
