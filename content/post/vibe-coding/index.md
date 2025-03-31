---
title: I tried "vibe coding" for 3 hours, my application worked, but then I spent 15 hours fixing it
subtitle: A cautionary tale about letting AI generate code without careful review or understanding
summary: While "vibe coding" can quickly produce working prototypes, my experience shows why it shouldn't be used for production code without careful human oversight.
projects: []
date: "2025-03-21T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - AI
  - programming
  - coding
  - AI-assisted
  - vibe-coding
  - development
  - python
  - cursor

categories:
  - development
  - level:beginning
---

## I tried "vibe coding" for 3 hours, my application worked, but then I spent 15 hours fixing it

That's not an exaggeration—it's really what happened.

Recently, I tried "[Vibe coding](https://en.wikipedia.org/wiki/Vibe_coding)," a term coined by Andrej Karpathy, a prominent AI researcher, co-founder of OpenAI, and former AI lead at Tesla.
In [his viral tweet](https://x.com/karpathy/status/1886192184808149383) from February 2025, Karpathy described vibe coding as a programming approach where you "fully give in to the vibes, embrace exponentials, and forget that the code even exists."
It's essentially about letting AI handle the coding based on natural language prompts without closely reviewing the generated code.

Intrigued by the hype, I decided to experiment with vibe coding using [Cursor](https://www.cursor.com/) on a new Python project I called [dotbins](https://github.com/basnijholt/dotbins) ([check out my detailed write-up here](../dotbins))."
[Dotbins](https://github.com/basnijholt/dotbins) manages CLI tool binaries within Git repositories, automatically downloading the correct binary from GitHub for the user's platform and architecture, significantly simplifying my dotfiles and bootstrapping process.
I am super excited about this project but it is not what this post is about.

Initially, it was fun to get something working so quickly.
Within just three hours, I had a functioning prototype—without carefully examining the code.
But I had unknowingly created a monster—a true [spaghetti](https://en.wikipedia.org/wiki/Spaghetti_code) monster! 🍝

Once I started reviewing the AI-generated code, I realized it was totally incomprehensible.
The AI had implemented the most complicated and roundabout ways to achieve simple tasks.
It introduced redundant checks for impossible conditions, irrelevant error handling, and execution paths that would never trigger.
The code worked superficially, but beneath the surface, it was chaotic and nearly impossible to understand or maintain.

This realization turned three hours of fun into fifteen hours of meticulous debugging, refactoring, and cleaning up the mess.
Essentially, I had to rewrite the entire project.

My main takeaway: AI-assisted coding, or "vibe coding," is incredibly powerful for quick prototyping but dangerous when used without oversight.
According to [this recent Y Combinator discussion](https://www.youtube.com/watch?v=IACHfKmZMr8), many startup founders are building products almost entirely with AI-generated code, "vibing" the code, meaning they let the AI write the code and don't review it.
For writing a couple of hundred lines of code it likely works pretty well, but for anything more complex, it's a recipe for disaster.
Personally, I would never invest in, build upon, or use such products—they're essentially constructing technical prisons for themselves.

AI is fantastic for inspiration, quick prototyping, writing code, and refactoring—but letting it run wild without careful human review can quickly lead to severe technical debt and hidden bugs.

Thanks for reading!
