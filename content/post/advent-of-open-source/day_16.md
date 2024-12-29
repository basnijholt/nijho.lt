---
title: "🎄🎁 Advent of Open Source – Day 16/24: Adaptive 📈"
date: 2024-12-16
draft: false
featured: false
summary: "Revolutionizing parameter space exploration with adaptive sampling algorithms."
subtitle: "A Python package for efficient, intelligent sampling in scientific computing."
tags:
    - open-source
    - python
    - scientificcomputing
    - parallelcomputing
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

During my PhD, I was running quantum transport simulations on our 800-core computational cluster. Traditional parameter sweeps using dense grids were hitting the cluster's limits - wasting precious compute time on uninteresting regions while potentially missing important features. Most parameter spaces we explored were "boring" with occasional interesting regions that required higher sampling density.

## 📖 Origin Story

Initially, in 2016, I had a collection of one-off adaptive sampling scripts. Together with Joseph Weston and the support of my PhD advisor Anton Akhmerov, we turned it into a full-fledged Python package. What began as an internal tool to make our cluster usage more efficient slowly gained traction in the wider scientific computing community.

## 🔧 Technical Highlights
* Multiple adaptive sampling strategies (1D, 2D, ND, averaging stochastic functions)
* Parallel execution support (local, MPI clusters, distributed systems)
* Live plotting in Jupyter notebooks with real-time feedback
* Customizable loss functions for different sampling priorities
* Minimal dependencies

## 📊 Impact & Applications
* 1164 GitHub stars and thousands of daily downloads
* Cited in 20+ scientific publications
* Dependency of many packages, most notably: Orange Quantum System's Quantify software for controlling real quantum computers!

Used in cutting-edge research across fields:
* **Quantum Computing**: Simulating and controlling superconducting qubits and trapped ion systems
* **Quantum Physics**: Exploring topological quantum systems and novel materials
* **Materials Science**: Studying graphene and other 2D materials
* **Engineering**:
  * Optimizing radar system performance
  * Fluid dynamics simulations
* **Chemistry**: Molecular modeling and vibrational spectroscopy
* **Most Unexpected Use**: Found in a paper on predicting energy usage of wartime bungalows!

This range of applications shows how a tool built for quantum transport simulations can find surprising uses across disciplines, from fundamental physics to everyday buildings.

## 🎯 Challenges and Solutions
* Making parallel execution truly scalable while maintaining sampling intelligence
* Creating intuitive visualization tools for complex parameter spaces
* Handling stochastic functions and noisy data

## 💡 Lessons Learned
1. Building a user base takes active effort - giving talks and engaging online made all the difference
2. Good documentation converts interested users into regular contributors
3. This was my first open source package and learned all about packaging, testing, and CI/CD

Want smarter parameter space exploration? Check out [Adaptive on GitHub](https://github.com/python-adaptive/adaptive) or try our [interactive tutorial](https://adaptive.readthedocs.io/en/latest/tutorial/tutorial.html)!

#OpenSource #Python #ScientificComputing #ParallelComputing #Programming