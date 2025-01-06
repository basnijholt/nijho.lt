---
title: "tuitorial: terminal-based interactive code tutorials 📚"
date: 2025-01-04
draft: false
featured: false
summary: A Python package for creating engaging code walkthroughs in your terminal with rich highlighting options and interactive navigation.
tags:
  - python
  - terminal
  - teaching
  - documentation
  - open-source
categories:
  - technology
  - open-source
authors:
  - admin
---

While trying to demonstrate my [`pipefunc` package](https://github.com/pipefunc/pipefunc) (a tool for automating computational pipelines), I hit a common presentation problem: how do you effectively walk through code without endless repetition?

Traditional presentation tools like PowerPoint force you to copy-paste the same code snippets multiple times just to highlight different parts. Jupyter notebooks are great for self-paced learning but clunky for live presentations (too much text that the viewer will try to read). I needed something that would let me define code once and create multiple views highlighting different aspects.

So, during the holiday season, I did what any reasonable developer would do: procrastinated on my actual work and built a new tool instead!

## What is tuitorial?

[`tuitorial`](https://github.com/basnijholt/tuitorial) is a Python package that lets you create interactive, terminal-based code tutorials where you define the code ONCE, then create steps that highlight different parts based on rules (like regex patterns or line numbers). No more copy-paste presentations!

## Key Features

- **Write code once**: Define your code once, then create multiple views highlighting different aspects
- **Rich highlighting options**: From simple literal matches to complex regex patterns
- **Interactive navigation**: Intuitive keyboard controls for stepping through tutorials
- **Beautiful terminal UI**: Powered by Textual for a polished look
- **Flexible configuration**: Choose between Python API or YAML format
- **Development mode**: Live reloading for quick iterations

## See It in Action

Here's a demo of [`tuitorial`](https://github.com/basnijholt/tuitorial) explaining [`pipefunc`](https://github.com/pipefunc/pipefunc) - a package that lets you create computational pipelines with automatic parallelization, caching, and dependency management:

{{< video autoplay="true" loop="true" controls="yes" src="tuitorial-0.4.0.mp4" >}}

## Who Should Use This?

While [`tuitorial`](https://github.com/basnijholt/tuitorial) isn't for everyone, it's perfect for:

- Developers giving technical presentations
- Teachers explaining code concepts
- Teams creating interactive documentation
- Anyone who loves terminal-based tools

## Getting Started

{{% callout note %}}
Have `uv` installed? Run the following command to see a quick example:
`uvx tuitorial https://raw.githubusercontent.com/basnijholt/tuitorial/refs/heads/main/examples/pipefunc.yaml`
{{% /callout %}}


```bash
pip install tuitorial
```

Check out the [documentation](https://github.com/basnijholt/tuitorial) for examples and detailed usage instructions.

## Final Thoughts

Building [`tuitorial`](https://github.com/basnijholt/tuitorial) was a lot of fun!
While it may not replace PowerPoint for your next business presentation, it offers a unique approach to code demonstrations that I hope others will find useful.

Try it out and let me know what you think!
