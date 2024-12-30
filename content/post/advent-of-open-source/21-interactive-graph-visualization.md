---
title: "Interactive Graph Visualization 🕸️"
date: 2024-12-21
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 21/24: Creating interactive graph visualizations in Jupyter with AnyWidget and a modernized JavaScript library."
subtitle: "🎄🎁 Advent of Open Source – Day 21/24: Two packages for visualizing pipefunc's computational graphs, born from a dive into JavaScript."
tags:
  - open-source
  - javascript
  - python
  - datavisualization
  - webdev
  - advent
categories:
  - technology
  - open-source
  - advent
authors:
  - admin
---

(See my [intro post](../))

After creating pipefunc (Day 20), I wanted a way to visualize its (possibly large and complex) computational graphs interactively in Jupyter notebooks. What started as a simple visualization PR evolved into two standalone packages: graphviz-anywidget (Python) and graphvizsvg (JavaScript) - which unexpectedly introduced me to JavaScript development!

## 📖 Origin Story

While working on pipefunc's visualization features, I discovered that existing solutions didn't quite meet my needs. However, I found several components that would solve my issue:

- AnyWidget (interactive GraphViz in Jupyter)
- @hpcc-js/wasm-graphviz (GraphViz in WASM)
- d3-graphviz (interactive GraphViz in D3)
- jquery.graphviz.svg (GraphViz SVG manipulation)

AnyWidget would work with ESM modules, however, I had no clue what that even was. The jquery.graphviz.svg package wasn't one and hadn't been maintained in 8 years.

With AI as my JavaScript mentor, I first rewrote jquery.graphviz.svg into a modern ESM module (graphvizsvg), adding comprehensive tests that uncovered bugs in the original. Then, using AnyWidget, I created graphviz-anywidget to connect everything together - combining the WASM-powered d3-graphviz with the interactive features from graphvizsvg into a seamless Python package.

To my surprise, I found JavaScript's development tooling remarkably sophisticated - especially npm, which handles everything from linting to testing to bundling to publishing. Something we're still missing in Python!

## 🔧 Technical Highlights

graphviz-anywidget:

- Interactive Graphviz visualization in Jupyter
- WASM-powered graph rendering
- Directional graph traversal
- Node and edge highlighting
- Works in JupyterLab, Notebook, and VS Code

graphvizsvg:

- Modern ESM module for interactive SVG visualization
- Automatic color transitions
- Bi-directional graph traversal
- Comprehensive test coverage
- My first npm package!

## 📊 Impact

- Enhances pipefunc's visualization capabilities
- Modernizes legacy jQuery code for modern web development
- Proves that diving into new technologies can yield useful tools

## 🎯 Challenges and Solutions

- Learning JavaScript/TypeScript from scratch
- Making WASM work in Jupyter
- Getting it to work in VS Code

## 💡 Lessons Learned

1. Don't let preconceptions limit your tech choices
2. Modern JavaScript development is actually enjoyable
3. AI can be an excellent programming mentor
4. Good visualization makes complex data accessible
5. Breaking features into separate packages increases reusability
6. Test coverage helps find bugs in even well-used code

Want to visualize graphs interactively? Check out [graphviz-anywidget](https://github.com/pipefunc/graphviz-anywidget) and [graphvizsvg](https://github.com/pipefunc/graphvizsvg)!

#OpenSource #JavaScript #Python #DataVisualization #WebDev
