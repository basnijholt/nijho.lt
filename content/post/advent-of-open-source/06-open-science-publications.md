---
title: "Open Science Publications 🔬"
date: 2024-12-06
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 06/24: Making scientific research truly reproducible with fully open-source code and data."
subtitle: "🎄🎁 Advent of Open Source – Day 06/24: A commitment to open science through publicly available, runnable code for every publication."
tags:
  - open-source
  - openscience
  - physics
  - quantumcomputing
  - python
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

Today's post is about something I have strong opinions on: making scientific research reproducible. While many researchers talk about open science, actually making your work reproducible for anyone requires significant effort.

## 📖 Origin Story

During my Ph.D. and subsequent research, I noticed a frustrating pattern in scientific publications: claims of "code available upon request" that often led nowhere, or code snippets that wouldn't run without substantial modification. I made an effort that my publications would be different – each includes complete, runnable code that reproduces every figure and result.

## 🔧 Technical Highlights

- Multiple repositories covering quantum physics experiments and simulations:
  - [orbitalfield](https://github.com/basnijholt/orbitalfield) - "Orbital effect of magnetic field on the Majorana phase diagram" (94 citations)
  - [supercurrent-majorana-nanowire](https://github.com/basnijholt/supercurrent-majorana-nanowire) - "Supercurrent interference in few-mode nanowire Josephson junctions" (78 citations)
  - [zigzag-majoranas](https://github.com/basnijholt/zigzag-majoranas) - "Enhanced proximity effect in zigzag-shaped Majorana Josephson junctions" (56 citations)
  - [azure-quantum-tgp](https://github.com/microsoft/azure-quantum-tgp) - "Protocol to identify a topological superconducting phase in a three-terminal device" (52 citations)
  - [spin-orbit-nanowires](https://github.com/basnijholt/spin-orbit-nanowires) - "Spin-orbit protection of induced superconductivity in Majorana nanowires" (81 citations)

## 🔄 Evolution of Best Practices

What I consider best practices has evolved over time. Today, I would:

- Use Pixi for universal lock files across operating systems and programming languages
- Provide a minimal Docker container that just installs the pixi lock file
- Create self-documenting Jupyter notebooks that reproduce every result
- Include clear figure-to-code mapping for paper reproducibility

## 🎯 Challenges and Solutions

- Balancing code cleanliness with research deadlines
- Managing large datasets efficiently
- Ensuring long-term reproducibility
- Making complex physics simulations accessible

## 💡 Lessons Learned

1. Clean code takes time but saves more in the long run
2. Documentation is as crucial as the code itself
3. Lock files are essential for true reproducibility
4. Making code public improves its quality

Want to explore quantum physics simulations? Check out the repositories above, each linked to their corresponding papers with full reproduction instructions.

#OpenSource #OpenScience #Physics #QuantumComputing #Python
