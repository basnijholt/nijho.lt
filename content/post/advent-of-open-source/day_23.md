---
title: "🎄🎁 Advent of Open Source – Day 23/24: pfapack 🔢"
date: 2024-12-23
draft: false
featured: false
summary: "Making efficient Pfaffian computations accessible to Python users with optimized C and FORTRAN under the hood."
subtitle: "A user-friendly Python package for calculating the square root of the determinant of skew-symmetric matrices."
tags:
  - open-source
  - python
  - scientificcomputing
  - math
  - pfaffian
  - fortran
  - c
  - advent
categories:
  - technology
  - open-source
  - advent
  - advent-post
authors:
  - admin
---

(See my [intro post](../))

Ever needed to calculate the square root of the determinant of a skew-symmetric matrix? Probably not, but if you're in quantum physics, you might have! This is called the Pfaffian. Today's project, `pfapack`, is a Python package that provides efficient routines for computing it. The underlying algorithms and original code implementations were developed by my PhD co-promotor Michael Wimmer. I created the `pfapack` package to make this powerful tool easily accessible.

## 📖 Origin Story

Working in quantum physics, I frequently need to compute the Pfaffian. Michael had not only developed the algorithms but also wrote highly optimized C, FORTRAN, and Python implementations, distributing them as a tar file [on his website](https://michaelwimmer.org/downloads.html). To make it easier for researchers working in Python, I packaged his existing Python code, added wrappers for his C and FORTRAN implementations, and set up automated builds for PyPI and conda-forge to make it easily installable.

## 🔧 Technical Highlights

- **Python Wrapper for Efficient Code:** User-friendly Python interface to Wimmer's optimized C and FORTRAN.
- **Multiple Algorithms:** Supports both the Parlett-Reid and Householder methods.
- **Optimized for Performance:** Leverages low-level optimizations for speed.
- **Conda and Pip Installable:** Easy installation via `conda-forge` and PyPI.
- **Automated Wheel Builds:** Uses `pypa/cibuildwheel` for streamlined, automated builds and releases.
- **Cross-Platform Compatibility:** Works on Linux, macOS, and Windows (with some caveats).

## 📊 Impact

- Makes specialized mathematical algorithms readily available to Python users.
- Simplifies the use of highly optimized code.
- 15 GitHub stars.
- Used in research projects that require efficient Pfaffian computations, particularly in quantum physics.

## 🎯 Challenges and Solutions

- **Bridging Languages:** Wrapping C and FORTRAN for Python integration.
- **Automated Builds:** Setting up automated builds for multiple platforms was complex.
- **Windows Compatibility:** As always Windows support is a PITA; it currently requires MSYS2 and MinGW64.

## 💡 Lessons Learned

- Making specialized tools accessible broadens their impact.
- Wrapping low-level code in Python can improve usability.
- Automated builds are essential for maintainability.
- `pypa/cibuildwheel` is awesome for cross-platform builds.

## 🙏 Credits

All the credits for the underlying algorithms and original code implementations go to Michael Wimmer. I simply made it easier to distribute and use in Python.

Want to compute Pfaffians efficiently in Python? Check out `pfapack` on GitHub ([https://github.com/basnijholt/pfapack](https://github.com/basnijholt/pfapack)) or install it via `pip install pfapack` or `conda install -c conda-forge pfapack`!

#OpenSource #Python #ScientificComputing #Math #Pfaffian #FORTRAN #C
