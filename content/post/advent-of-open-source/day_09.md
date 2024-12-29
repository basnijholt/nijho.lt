---
title: "🎄🎁 Advent of Open Source – Day 9/24: yaml2bib 📚"
date: 2024-12-09
draft: false
featured: false
summary: "Solving the universal academic headache of inconsistent BibTeX entries."
subtitle: "A tool to generate perfect BibTeX files from YAML using DOIs, ensuring citation consistency."
tags:
  - open-source
  - python
  - academia
  - latex
  - research
  - advent
categories:
  - technology
  - open-source
  - advent
authors:
  - admin
---

(See my [intro post](https://www.linkedin.com/posts/basnijholt_advent-of-open-source-celebrating-activity-7269075513002909697-M89J))

Every academic writing in LaTeX knows the pain: managing BibTeX files with hundreds of citations, each potentially formatted slightly differently, with inconsistent journal abbreviations, and duplicated entries across chapters. While procrastinating on writing my PhD thesis, I became obsessed with solving this universal academic headache.

## 📖 Origin Story

When writing a PhD thesis with multiple chapters that share citations, maintaining consistency is crucial but tedious. Different chapters might cite the same paper but with slightly different BibTeX entries - one using the full journal name, another using abbreviations, or worse, having slightly different titles or author lists. Rather than manually standardizing ~350 citations, I created yaml2bib: give it a list of DOIs in YAML format, and it generates a perfect BibTeX file with consistent journal abbreviations and formatting.

## 🔧 Technical Highlights

- Fetches citation data from CrossRef using DOIs
- Ensures consistent journal name abbreviations
- Caches API responses to avoid repeated queries
- Supports custom text replacements
- Combines multiple YAML sources
- Works as both CLI tool and Python library
- Zero manual citation formatting needed

## 📊 Impact

While this tool has only 11 GitHub stars, it saved me countless hours during thesis writing and helped ensure professional consistency in my citations. It's particularly useful for:

- Large academic documents with many citations
- Multi-chapter works sharing references
- Collaborative papers needing citation standardization
- Anyone tired of manually formatting BibTeX entries

## 💡 Lessons Learned

1. Procrastination can be productive if channeled right (story of my life...)
2. A single source of truth prevents inconsistencies
3. Good tools make you care about details you'd otherwise skip
4. Every LaTeX user has fought with BibTeX at some point

Want perfectly consistent citations? Check out [yaml2bib on GitHub](https://github.com/basnijholt/yaml2bib)!

#OpenSource #Python #Academia #LaTeX #Research
