---
title: "rsync-time-machine 🕒"
date: 2024-12-03
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 03/24: Rebuilding a popular backup tool in Python for better reliability and cross-platform compatibility."
subtitle: "🎄🎁 Advent of Open Source – Day 03/24: A Python port of rsync-time-backup, enhancing Time Machine-style backups."
tags:
  - open-source
  - python
  - backups
  - devtools
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

Sometimes the best open source projects start with "I can do better than this." That's exactly what happened when I looked at [laurent22/rsync-time-backup](https://github.com/laurent22/rsync-time-backup), a popular 600-line Bash script for Time Machine-style backups. While it worked, it had known bugs and was tricky to maintain due to Bash's limitations. It also lacked tests, type hints (bash duh...), and proper error handling. So, I did what any reasonable developer would do: rewrote it in Python! 🐍

## 📖 Origin Story

I needed reliable backups that worked across platforms and filesystems, unlike Apple's Time Machine. While many excellent backup tools exist, I was drawn to the simplicity of this approach: it just creates folders named `YYYY-MM-DD-HH-MM-SS` containing your files. No special tools needed for restoring or browsing - just your regular file explorer! I created a fully tested, typed, and documented Python port that maintains compatibility with the original while adding modern development practices.

## 🔧 Technical Highlights

- Creates incremental backups using hard links (saving space while keeping full snapshots)
- Works on Linux, macOS, and Windows (via WSL or Cygwin)
- Supports local and remote (SSH) backups
- Smart backup expiration strategy
- Built-in safety checks and locking mechanism
- Pretty terminal output
- Absolutely zero dependencies beyond Python itself - it just works!
- Usable as a standalone `.py` script or pip installable package
- 100% test coverage

## 📊 Impact

The project reached the front page of Y Combinator's Hacker News, causing its popularity to explode:

- 381 GitHub stars
- 16 forks
- 6 contributors
- Featured on Real Python podcast
- Active discussion on Reddit's r/Python

## 🎯 Challenges and Solutions

- Maintaining compatibility with the original Bash script while improving the codebase
- Making it work on Windows through WSL/Cygwin (surprisingly tricky!)
- Handling various edge cases in filesystem operations
- Implementing a robust backup expiration strategy
- Adding comprehensive test coverage for file operations
- Keeping the codebase dependency-free while maintaining functionality

## 💡 Lessons Learned

1. Sometimes a rewrite is worth it, especially when adding modern development practices
2. Good documentation and test coverage are crucial for backup tools
3. The Python community appreciates well-structured ports of useful tools
4. Zero dependencies means zero headaches for users
5. Cross-platform compatibility (especially Windows) requires careful consideration
6. Simple, transparent solutions (like regular folders) can be better than complex ones

Want reliable, cross-platform Time Machine-style backups? Check out [the project on GitHub](https://github.com/basnijholt/rsync-time-machine.py)!

#OpenSource #Python #Backups #DevTools #Programming
