---
title: "🎄🎁 Advent of Open Source – Day 5/24: markdown-code-runner 📝"
date: 2024-12-05
draft: false
featured: false
summary: "Keeping documentation in sync with code by automatically executing and updating Markdown code blocks."
subtitle: "A tool to ensure code examples and outputs in Markdown files are always up-to-date."
tags:
  - open-source
  - python
  - documentation
  - devtools
  - programming
  - advent
categories:
  - technology
  - open-source
  - advent
authors:
  - admin
---

(See my [intro post](https://www.linkedin.com/posts/basnijholt_advent-of-open-source-celebrating-activity-7269075513002909697-M89J))

Documentation should be as close to the code as possible - that's the principle of "information locality." But how do you keep code examples and their outputs in sync? Enter markdown-code-runner, a tool that executes code blocks within Markdown files and updates their output in-place!

## 📖 Origin Story

While maintaining various open source and work projects, I found myself constantly updating README or Wiki files with new command outputs, updated tables, and fresh examples. This manual process was error-prone and tedious. Instead of using external templating files or more advanced documentation generators like Sphinx and Quarto (which are often overkill for single-page projects), I wanted something simpler: code and its output living together in the same Markdown file, always in sync.

## 🔧 Technical Highlights

- Executes code blocks (Python and Bash) within Markdown files
- Updates outputs in-place while preserving the original file structure
- Supports hidden code blocks for generating content without showing the code
- Works with any language by using file code blocks and bash execution
- Zero external dependencies
- GitHub Actions integration for automatic README updates
- Preserves Markdown spec compatibility by hiding code in HTML comments (`<!-- CODE HERE -->`)

## 📊 Impact

- 97 GitHub stars
- Used in many of my other projects for auto-generating:
  - Command-line help texts
  - API documentation
  - Example outputs
  - Data tables
- Helps maintain "information locality" - everything needed is in one file
- Enables dynamic documentation that stays up-to-date automatically

## 🎯 Challenges and Solutions

- Parsing Markdown without breaking its structure
- Supporting multiple programming languages
- Making it work seamlessly with GitHub Actions
- Handling complex outputs (tables, images, etc.)
- Maintaining backward compatibility with existing Markdown files

## 💡 Lessons Learned

1. Documentation is best when it's close to what it documents
2. Automation should be invisible - the tool shouldn't change how you write Markdown
3. Sometimes the simplest solution (using HTML comments) is the best
4. Good documentation tools should make maintaining docs easier, not harder
5. Auto-generated content should be clearly marked as such

Want to keep your documentation always in sync? Check out [markdown-code-runner on GitHub](https://github.com/basnijholt/markdown-code-runner)!

#OpenSource #Python #Documentation #DevTools #Programming
