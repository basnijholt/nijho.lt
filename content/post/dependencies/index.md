---
title: "Confessions of an Asymmetric Hypocrite: On Python Dependencies"
subtitle: "Why I'm ultra-cautious adding dependencies to my libraries, yet hope you depend on mine, and relax entirely for applications"
summary: "Exploring my seemingly hypocritical stance on dependencies: strict minimalism for my libraries, expecting adoption of my own work, yet embracing a wide range of dependencies in applications due to context and isolation."
projects: []
date: "2025-04-27T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - python
  - dependencies
  - packaging
  - open-source
  - software-design
  - unidep
  - development
  - workflow
  - libraries
  - applications

categories:
  - development
  - philosophy
  - level:intermediate
---

## Introduction: The Dependency Dilemma 🤔

I just listened to a podcast "[Build software that lasts!](https://www.youtube.com/watch?v=5ZyzeeYZgeM) with Bert Hubert (a fellow Dutch), who prefers to reduce the number of dependencies to an absolute minimum (also see his related blog posts [[1](https://berthub.eu/articles/posts/on-long-term-software-development/)] and [[2](https://berthub.eu/articles/posts/a-2024-plea-for-lean-software/)]).
While I agree one shouldn't use [`is-even`](https://www.npmjs.com/package/is-even) as a dependency ([`is-odd`](https://www.npmjs.com/package/is-odd) is a better choice 😏), I think there is a lot of value in reducing the number of dependencies but *also* in using the right tool for the job and not continuously re-inventing the wheel.
The podcast got me thinking about my own stance on dependencies and how I actively avoid introducing dependencies into my libraries while expecting (hoping 🤞) others to depend on my work.

Like many software developers, I've spent countless hours wrestling with dependencies.
Dependency hell is easy to fall into, *especially* in dynamic languages like Python.
Those moments where installing or updating one package breaks another, or where a tiny library pulls in hundreds of transitive dependencies, are frustratingly common.
This frustration partly motivated me to create [`unidep`](https://github.com/basnijholt/unidep), a tool aimed at simplifying dependency management across different Python tools like `pip` and `conda`.

But working on `unidep` and my other projects forces me to think about my own relationship with dependencies.
I've realized I operate with what feels like an "asymmetric hypocrisy."
My standards for the libraries I _publish_ are extremely strict regarding which external dependencies I _consume_.
Yet, as an author of over 30 Python packages, I inherently _produce_ dependencies, hoping others will adopt my work.
And then, when building applications or CLIs, my caution often disappears entirely.

This post dives into that asymmetry.
It's about the different hats I wear: the minimalist library author (as a dependency _consumer_), the hopeful library author (as a dependency _producer_), and the pragmatic application developer.
In this post, I'll explain why I take these different approaches and why it's really about the situation, not a contradiction.

{{< toc >}}

{{% callout note %}}
**TL;DR:** I'm extremely strict about adding external dependencies to my _libraries_, preferring widely-used, low-dependency packages.
Simultaneously, I _create_ libraries expecting adoption.
For _applications_ (especially CLIs in isolated environments), I'm far more liberal with dependencies to build features quickly.
It's all about managing risks depending on the situation.
{{% /callout %}}

## 1. The Library Author Hat 🎩 (as Dependency Consumer): Maximum Caution

When I build and publish an open-source Python library – like [`Adaptive`](https://github.com/python-adaptive/adaptive), [`pipefunc`](https://github.com/pipefunc/pipefunc), or [`unidep`](https://github.com/basnijholt/unidep) – my primary focus shifts to the _users_ who will depend on my code.
My choices directly impact their projects.
This responsibility means I have to be very careful about adding external dependencies:

- **Minimize and Scrutinize:** Fewer dependencies mean fewer potential conflicts for users.
  I aggressively minimize the core runtime dependency list.
- **Favor Battle-Tested Dependencies:** I strongly prefer dependencies that are already widely adopted and trusted by the community.
  (I have been called that person that always wants the latest and greatest, the truth is that I am a sucker for shiny new things but typically only adopt them once they are already quite popular.)
  Think `numpy` or `cloudpickle`.
  These are less likely to cause unexpected issues or disappear overnight.
- **Low Transitive Dependency Count:** A key criterion is how many _other_ packages a potential dependency pulls in.
  Ideally, I choose dependencies with zero or very few further dependencies.
  For example, in [`pipefunc`](https://github.com/pipefunc/pipefunc), dependencies like [`numpy`](https://numpy.org/), [`networkx`](https://networkx.org/), and [`cloudpickle`](https://github.com/cloudpipe/cloudpickle) are good examples – they are popular and don't rely on many other things.
- **Optional Dependencies for Heavy Features:** If a feature really needs a large or less common dependency, I try making it a _optional_ extra (`project.optional-dependencies`).
  Users opt-in only if they need that specific capability.
- **Avoid Pinning (Mostly):** As mentioned before, hard version pins (`==1.2.3`) in libraries are usually harmful.
  Minimum versions (`>=1.2`) or safe upper bounds (`<2.0`) are preferred.
- **License Awareness:** The license of a dependency matters immensely, especially regarding compatibility and obligations ([GPL considerations]({{< ref "/post/gpl" >}})).

The guiding principle is: **Do not cause pain for your users.**
A library should integrate smoothly into diverse environments.

## 2. The Library Author Hat 🎩 (as Dependency Producer): The Paradox

Here's where the "hypocrisy" might seem to surface.
While I'm cautious about _consuming_ dependencies for my libraries, I am also the author of over 30 packages.
I invest time and effort into these tools, naturally hoping they prove useful and that others _will adopt them_ – making _my_ libraries dependencies in _their_ projects.

Is it hypocritical to be wary of adding dependencies while simultaneously creating them for others?
Perhaps slightly, but it's also the nature of contributing to an ecosystem.
I try to handle this by strictly following the rules from Section 1 for my own libraries.
If I expect others to rely on my code, I feel responsible to make that dependency as
low-risk and stable as possible.
I want my libraries to be the kind of well-behaved, minimal-friction dependencies
that I myself would be comfortable adding.

## 3. The Application Developer / Contributor Hat 🧢: Practicality is Key

When the context shifts to building an application – like a command-line tool, a web service, or a personal project – my rules become *much* less strict.
The key differences are isolation (keeping things separate) and how far the effects reach.

- **Isolation Reduces Risk:** Applications often run in controlled, isolated environments.
  [`Docker`](https://www.docker.com/), `conda`/[`micromamba`](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html) ([Python Environment Jungle post]({{< ref "/post/python-environments" >}})), or simple `venv`s contain the dependencies.
  A conflict within the application's environment doesn't break the user's entire system or other unrelated projects.
- **CLIs as a Prime Example:** Many tools I've built are CLIs (like [`tuitorial`](https://github.com/basnijholt/tuitorial) or helpers within my [`dotfiles`](https://github.com/basnijholt/dotfiles)).
  These might have tens of dependencies.
  Because they are installed into isolated environments (often via [`uv`](https://docs.astral.sh/uv/), [`pipx`](https://pipx.pypa.io/stable/), or within a dedicated `conda` env), this complexity is okay.
  The risk is contained.
- **Developer Tools Welcome:** Productivity boosters like [`ruff`](https://beta.ruff.rs/docs/rules/), [`mypy`](https://mypy.readthedocs.io/en/stable/), etc., are fair game as development dependencies ([My Python Project Toolkit]({{< ref "/post/best-python-dev-tooling" >}})).
  They don't impact the end-user runtime (if packaged properly), so I am much more lenient with dev tools.
- **Focus on Functionality:** The goal is often to deliver features or solve a problem efficiently.
  Leveraging existing libraries, even those with dependencies, is usually faster and more robust than reimplementing complex logic.
  It usually makes more sense to use existing libraries.

In this context, the focus changes from _minimizing external impact_ (libraries) to _maximizing internal capability and maintainability_ within a controlled scope (applications).

## 4. Conclusion: Not Hypocrisy, but Context-Driven Strategy 🙏

My approach to dependencies _is_ "it depends on the situation".
I'm stricter about dependencies for my libraries than for my applications or personal tools.
I am cautious about adopting dependencies while actively producing them for others.

But I don't see this as hypocrisy.
It's a practical approach based on different situations and goals:

- **Libraries (as Consumer):** Focus on keeping the software community stable and making things easy for users. Be conservative.
- **Libraries (as Producer):** Create software responsibly, following the same high standards you expect from others.
- **Applications:** Focus on adding features and developing quickly within separate environments. Be pragmatic.

Understanding the different risks and goals for each situation helps make good decisions about dependencies.
It's about choosing the right trade-offs for the specific situation, whether you're building a foundational block for the community or a specific tool for a controlled environment.

How do you handle dependencies across different types of projects?
Do you find yourself navigating similar questions?
Share your thoughts!
