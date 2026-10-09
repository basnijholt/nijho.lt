---
title: "numthreads 🧵"
date: 2024-12-07
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 07/24: Solving a common performance pitfall in scientific computing with a tiny yet powerful tool."
subtitle: "🎄🎁 Advent of Open Source – Day 07/24: A simple utility to control thread counts for numerical libraries, preventing performance degradation."
tags:
  - python
  - open-source
  - scientific-computing
categories:
  - Open Source
authors:
  - admin
excludeFromList: true
---

(See my [intro post](../))

Sometimes the smallest tools solve the most persistent problems.
Today's project is about taming automatic parallelization in scientific computing - a deceptively simple challenge that has cost countless CPU hours.

## 📖 Origin Story

While working on high-performance computing clusters, I frequently encountered a counterintuitive problem: code running slower on multiple CPU cores than on a single one.
Many scientific libraries (NumPy, SciPy) automatically parallelize operations, which sounds great but can actually harm performance when you're already parallelizing at a higher level.
After repeatedly explaining to colleagues why they needed to set various environment variables to disable this behavior, I created [`numthreads`](https://github.com/basnijholt/numthreads) to solve it once and for all.

{{< figure src="meme.png" caption="Overenthusiastic threading" alt="Meme showing a person labeled 'YOUR CODE' about to be hugged by a pink creature labeled 'NUMTHREADS.SET(1)', representing setting the number of threads to 1. In the background, a yellow circle labeled 'CPU PERFORMANCE' is visible." >}}

## 🔧 Technical Highlights

- Controls thread count for major numerical libraries:
  - OpenBLAS
  - Intel's Math Kernel Library (MKL)
  - OpenMP
  - NumExpr
  - Accelerate
- Zero dependencies
- Tiny (≤7KB) yet solves a real problem
- Both CLI and Python API

## 📊 Impact

Over my scientific computing career, I've encountered this threading issue dozens of times. Since creating this package a year ago, I've helped at least 5 different researchers speed up their workflows, sometimes by orders of magnitude. The beauty lies in its simplicity - the fix is often as simple as:

```bash
eval $(numthreads 1)
```

## 💡 Lessons Learned

1. The simplest solutions are often the best
2. More cores doesn't always mean faster code
3. If you find yourself repeating the same instructions, write a tool
4. Even a 7KB package can save hours of computing time

Want better control over your numerical computations? Check out [numthreads on GitHub](https://github.com/basnijholt/numthreads)!

#OpenSource #Python #HPC #ScientificComputing #Programming
