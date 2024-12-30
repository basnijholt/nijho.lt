---
title: "fileup 📤"
date: 2024-12-19
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 19/24: Sharing files directly from the terminal with a simple, zero-dependency utility."
subtitle: "🎄🎁 Advent of Open Source – Day 19/24: A tiny command-line tool for effortless file sharing, used for over 7 years."
tags:
  - open-source
  - python
  - devtools
  - commandline
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

Sometimes the best tools are the ones you build for yourself and keep using for years. Today's project is [`fileup`](https://github.com/basnijholt/fileup), a tiny command-line utility that's been making my life easier for 7 years - because sharing files shouldn't require leaving the terminal!

## 📖 Origin Story

Back in 2017, I found myself repeatedly going through the same tedious process: needing to share a file, opening a browser, navigating to a file sharing service, waiting for uploads, and copying URLs. As someone who lives in the terminal, this felt inefficient. I wanted something as simple as `fu filename` that would handle everything and put the URL in my clipboard. Seven years and countless file shares later, it's still one of my most-used tools.

## 🔧 Technical Highlights

- Supports both FTP and SCP uploads
- Smart URL generation:
  - Jupyter notebooks → nbviewer links
  - Images → markdown-formatted links
  - Regular files → direct URLs
- Automatic file expiration and cleanup
- Zero dependencies - uses only Python standard library
- Clipboard integration (macOS)
- Simple INI configuration
- Works as both a standalone script or installed package

## 📊 Impact

This is one of those tools where GitHub stars (currently 0!) don't tell the whole story:

- Used almost daily for 7 years
- Shared thousands of files
- Saved countless minutes of browser interactions
- Proves that utility trumps popularity in open source

## 💡 Lessons Learned

1. Longevity comes from solving a real, persistent need
2. A tool doesn't need to be revolutionary to be useful
3. Zero dependencies mean zero maintenance headaches
4. Sometimes the impact of a tool isn't measured in stars
5. Simple tools that remove friction are worth maintaining

Want to share files from your terminal? Check out [fileup on GitHub](https://github.com/basnijholt/fileup)!

#OpenSource #Python #DevTools #CommandLine #Programming
