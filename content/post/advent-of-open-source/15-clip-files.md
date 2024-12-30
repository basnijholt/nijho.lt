---
title: "clip-files 📋"
date: 2024-12-15
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 15/24: Automating the process of sharing code context with AI assistants."
subtitle: "🎄🎁 Advent of Open Source – Day 15/24: A command-line tool to quickly copy and format code for AI interactions."
tags:
  - open-source
  - python
  - devtools
  - ai
  - programming
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

Sometimes the most useful tools are born from daily frustrations. When working with AI assistants like ChatGPT or Claude, I found myself constantly copying files to share context. After doing this manually dozens of times, I created a tool to automate it.

## 📖 Origin Story

While contributing to open source, I frequently like to share entire (or large parts of) codebases with AI assistants for context or code review. Since the code is open source anyway, there's no reason not to share the full context! But manually copying files, adding their paths for context, and ensuring I didn't exceed token limits was tedious. Instead of continuing this manual process, I spent an evening creating `clip-files` - and have used it multiple times daily ever since.

In fact, I'm using it right now! The command (shown below) lets me share this entire advent calendar series with AI assistants for proofreading.

```bash
clip-files --initial-file ai.md --files introduction.md day*.md
```


## 🔧 Technical Highlights

- Uses `tiktoken` for accurate GPT token counting
- Supports both directory traversal and specific file selection
- Automatically generates a file index for reference
- Allows custom initial instructions via file
- Preserves file paths in output for context
- Clean, typed, and documented codebase

## 📊 Impact

While this tool has no GitHub stars (I haven't promoted it), its real impact is personal - I use it multiple times daily for:

- Sharing entire open source codebases with AI assistants
- Getting comprehensive code reviews
- Discussing bug fixes with full context
- Documentation improvements
- Open source contributions

The tool's real value isn't in its complexity (it's just ~250 lines of code) but in how it removes friction from open source development. When working with open code, we might as well share all the context we can - and this tool makes that effortless.

## 🎯 Challenges and Solutions

- Maintaining consistent formatting across different input methods
- Calculating accurate token counts for different components
- Providing meaningful error messages for invalid inputs
- Structuring output to be AI-assistant friendly

## 💡 Lessons Learned

1. When working with open source code, sharing full context is valuable
2. Simple command-line tools can significantly improve daily workflows
3. Consistent formatting matters when working with AI assistants
4. Sometimes a 250-line tool can save hours of manual work

Want to make sharing code with AI assistants easier? Check out [clip-files on GitHub](https://github.com/basnijholt/clip-files)!

#OpenSource #Python #DevTools #AI #Programming
