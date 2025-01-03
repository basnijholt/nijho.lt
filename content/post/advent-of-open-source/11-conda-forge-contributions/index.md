---
title: "conda-forge Contributions 🐍"
date: 2024-12-11
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 11/24: Contributing to the backbone of scientific Python through the conda-forge community."
subtitle: "🎄🎁 Advent of Open Source – Day 11/24: Maintaining over 40 conda-forge recipes, enabling easy installation of scientific software."
tags:
  - open-source
  - python
  - scientific
  - programming
  - community
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

Unlike other projects in this advent calendar, I want to celebrate being part of something much bigger: the [conda-forge](https://conda-forge.org/) community, where thousands of volunteers maintain the packages that power scientific Python.

## 📖 Origin Story

I started with conda-forge in 2016 during my PhD work with Kwant, a quantum transport simulator. Installing it was a nightmare - it required system-level numerical libraries like MUMPS and Scotch which required a special config file to link. When I discovered conda-forge and its mission to make scientific software installation painless, I knew this was the solution!

{{< figure src="meme.png" caption="The humble work of conda-forge maintainers" alt="Meme showing a farmer standing in a field, with the text 'MAINTAINING CONDA-FORGE PACKAGES FOR THE SCIENTIFIC COMMUNITY' above and 'It ain't much, but it's honest work' below." >}}

## 🔧 Technical Highlights

Over the past 8 years, I've maintained over 40 build recipes, including:

- Major scientific packages like [VTK](https://vtk.org/), [MUMPS](https://mumps-solver.org/), and [Scotch](https://www.labri.fr/perso/pelegrin/scotch/)
- Quantum physics tools like [Qsim](https://quantumai.google/qsim), [Qcodes](https://github.com/microsoft/Qcodes), and [Kwant](https://kwant-project.org/)
- Visualization libraries like [HoloViews](https://holoviews.org/)
- Plus all the packages I've authored myself

The real magic of conda-forge is its infrastructure:

- Automated builds across Linux, macOS, and Windows
- Strict dependency version management
- Comprehensive CI/CD pipelines
- Community-driven quality control

## 📊 Impact

What makes conda-forge truly special is how initial contributions blossom into collaborative efforts. I've experienced this firsthand: after creating the initial MUMPS feedstock, 25 other contributors joined in, each bringing their unique expertise.

A recent experience also illustrates this: I added CUDA support to both [Google's Qsim](https://github.com/conda-forge/qsimcirq-feedstock/pull/3) and [IBM's Cirq](https://github.com/conda-forge/qiskit-aer-feedstock/pull/19) packages. Shortly after, [Leo Fang](https://github.com/leofang), an engineer from NVIDIA who knows CUDA far better than I do, stepped up and made significant improvements. This is the beauty of open source - experts naturally gravitate to where they can make the biggest impact.

This collaborative approach solves a problem I've encountered at several companies: the tendency to maintain complicated build systems internally with custom hacks. Instead of each organization reinventing the wheel, conda-forge provides a shared platform where:

- Maintenance burden is distributed
- Expert knowledge flows freely
- Build practices are standardized
- Infrastructure is public and reusable

## 🎯 Challenges and Solutions

- Keeping up with upstream changes
- Managing complex dependency trees
- Cross-platform compatibility
- Coordinating with upstream maintainers

## 💡 Lessons Learned

1. Community effort beats solo work for infrastructure
2. Automation is crucial for reliability
3. Small contributions compound over time
4. Being part of something bigger is rewarding

Want to contribute to scientific Python? Check out [conda-forge](https://conda-forge.org/) and the [staged-recipes repository](https://github.com/conda-forge/staged-recipes)!

#OpenSource #Python #Scientific #Programming #Community
