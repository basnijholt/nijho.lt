---
title: "Roll your own, fork the rest 🍴"
subtitle: "A year of building MindRoom taught me that 'battle-tested' was the right rule with the wrong threshold"
summary: "Stars measure interest, not usage. After a year of MindRoom, with forks of a Matrix client, two Matrix servers and a Matrix web client, plus 126 workarounds for one AI framework, my rule is: depend on what millions of projects use every day, roll your own when a library only gives you the easy part, and fork when the problem is hard and few people use the code."
date: 2026-10-19
draft: false
featured: false
authors:
  - admin
tags:
  - software-design
  - dependencies
  - mindroom
  - matrix
  - ai
  - agents
  - open-source
categories:
  - Software Development
  - AI
  - level:intermediate
---

## Introduction: a follow-up to something I wrote

In April 2025 I published [Confessions of an asymmetric hypocrite]({{< ref "/post/dependencies" >}}), about my split personality on dependencies.
Strict minimalism for the libraries I publish, and then, for applications:

> For _applications_ (especially CLIs in isolated environments), I'm far more liberal with dependencies to build features quickly.

I also wrote that I "strongly prefer dependencies that are already widely adopted and trusted by the community" because "these are less likely to cause unexpected issues".

Then I spent a year building [MindRoom]({{< ref "/post/mindroom" >}}), which is an application, exactly the category where I said I could relax.

I want to report back.
"Prefer {{< tooltip text="Code that so many people already run in production that the common bugs have been found and fixed before you get there." >}}battle-tested{{< /tooltip >}} dependencies" was the right rule.
I just had the wrong idea of what battle-tested means.
I thought a project with tens of thousands of GitHub stars qualified.
Now I think it means **millions of downloads, every day.**

{{< toc >}}

{{% callout note %}}
**TL;DR:** Stars measure interest, not usage. For every dependency, ask how many projects actually run the code you are about to rely on, and how much you rely on it.

- **Millions of downloads a day?** Depend on it.
- **Fewer, and it only gives you the easy part?** Roll your own. The hard part was going to be yours anyway.
- **Fewer, and hard to build?** Fork it, and treat the fork as yours.

If I started MindRoom over, I would write my own HTTP requests to the model providers instead of using an AI framework.
{{% /callout %}}

> **Update 2026-10-31:** In the two weeks after publishing, I took my own advice twice.
> MindRoom's knowledge search no longer uses ChromaDB, and code MindRoom owns has replaced Agno's runtime.
> Agno is now only MindRoom's tool library.
> The full stories are in [the comments](#comments).

## 1. Stars measure interest, not usage

When I picked [Agno](https://github.com/agno-agi/agno) as MindRoom's {{< tooltip text="A library that wraps the model providers' APIs and adds agents, tools, memory, knowledge bases and session storage on top." >}}AI framework{{< /tooltip >}}, it looked like the safe choice.
Today it has over 42,000 stars and 6,000 forks.[^stars]

It also gets about **78,000 downloads a day** on PyPI.
[httpx](https://github.com/encode/httpx), one of Python's standard HTTP libraries, gets about **25 million**.[^downloads]

A star is something you click once, when a README looks exciting.
A download happens every time some project installs the package.

Most of those downloads are {{< tooltip text="Continuous integration: test and build pipelines that install a fresh environment on every push, often many times a day per project." >}}CI{{< /tooltip >}}, not people, so downloads are not users either.
But a package with millions of downloads a day is installed by a huge number of different projects.
Many of them use the same functions you are about to use, so they hit the bugs before you do.

Battle-tested is also not the same as old.
I use [uv](https://github.com/astral-sh/uv) for everything, and it has only been around for a {{< tooltip text="Astral released the first version of uv in February 2024." >}}couple of years{{< /tooltip >}}.
I run into bugs in uv too, but there is simply no better alternative, and it gets about 3.6 million downloads a day.

## 2. A popular protocol is not a popular library

The other place my old idea failed was [Matrix](https://matrix.org).

Building on Matrix felt obviously correct.
An open protocol, about a decade old, with serious security reviews from {{< tooltip text="Governments run their own Matrix deployments, for example Tchap for the French civil service and BwMessenger for the German armed forces." >}}large organizations and governments{{< /tooltip >}}.
Millions of people use it.

Matrix is still a good protocol and I am still on it.
But even though millions of people use Matrix, there are only a few client libraries.

MindRoom streams agent replies by editing the same message many times a second.
Almost every part of the ecosystem I touched had a problem with that: {{< tooltip text="The most widely used Matrix app, made by the company behind the protocol." >}}Element{{< /tooltip >}}, {{< tooltip text="A Matrix web client focused on a simple, Discord-like interface. MindRoom's chat app is a fork of it." >}}Cinny{{< /tooltip >}}, {{< tooltip text="The Python Matrix client library MindRoom's agents use to log in, read and send messages." >}}matrix-nio{{< /tooltip >}}, and the {{< tooltip text="matrix-js-sdk, the library Element Web and Cinny are built on." >}}Matrix JavaScript SDK{{< /tooltip >}}.
In the JavaScript SDK, edits that arrived while a thread was still loading were silently dropped, so you saw stale text until you reloaded.[^jssdk]

What counts is how many projects use the library you build on.
Element's users do not test matrix-js-sdk for you. Other people building on matrix-js-sdk do.
It gets roughly 100,000 downloads a day. matrix-nio, the Python client, about 23,000.

## 3. I checked the rule against my own code

I pulled the daily download numbers for the packages I use and looked for workarounds, patches and forks in my own source.[^method]

| Package | Downloads per day | What it cost me |
|---|---|---|
| requests | 49M | nothing I had to work around |
| pydantic | 35M | nothing |
| numpy | 33M | nothing |
| httpx | 25M | nothing |
| aiohttp | 18M | nothing |
| FastAPI | 17M | nothing |
| chromadb | 270K | workarounds for a bug that holds the GIL |
| matrix-js-sdk | ~100K | patched |
| mem0ai | 79K | largely reimplemented |
| agno | 78K | **126 documented workarounds** |
| matrix-nio | 23K | forked |

Above a million a day, I had nothing to work around.
Below it, every package on this list cost me a patch, a fork, a rewrite, or a pile of workarounds.

Take [ChromaDB](https://github.com/chroma-core/chroma), the vector database behind MindRoom's knowledge bases.
In some cases it holds Python's {{< tooltip text="The Global Interpreter Lock: only one thread can run Python code at a time. Native code is supposed to release it while it waits, so other threads can keep going." >}}GIL{{< /tooltip >}} during I/O, which blocks every other thread in the process.
I opened [a pull request](https://github.com/chroma-core/chroma/pull/7692) to fix it, and nobody has looked at it yet.
Instead of forking, I run every knowledge read in a short-lived child process, because a process can be killed and a blocked thread cannot.[^chroma]

My fork of matrix-nio has about 8,900 lines added and 2,000 removed in the library code since the last upstream release.[^nio]

This does not mean every small package needs replacing.
MindRoom pulls in a few hundred packages in total, and plenty of them have modest download numbers.
The scrutiny should match how much I depend on a package.
Something I use for one small, specific purpose is fine.
Agno and matrix-nio are the base that MindRoom is built on, which is probably also why they hurt the most.

## 4. Roll your own: the library gives you the easy 10%

Take memory libraries, [Mem0](https://github.com/mem0ai/mem0) and friends.
I have [already written about this]({{< ref "/post/file-based-rag-memory" >}}): I cloned LlamaIndex, LangChain, Letta, Mem0 and PydanticAI, studied how they work, and re-implemented the parts I needed. My memory system ended up "mostly modeled after Mem0".

The core idea is not hard.
With {{< tooltip text="Retrieval-augmented generation: look up relevant text first and paste it into the prompt, so the model answers from your documents instead of from memory." >}}RAG{{< /tooltip >}}, you chunk, embed, retrieve, re-rank and reconcile. Once you have read a couple of implementations you can write it, and afterwards you understand every line.

The same is true of an agent framework.
It builds a JSON payload, posts it to an HTTP endpoint, parses a {{< tooltip text="Providers send the reply as server-sent events: a long-lived HTTP response with one small JSON chunk per token or tool-call fragment." >}}streaming response{{< /tooltip >}}, keeps a list of messages, and loops when the model asks for a tool call.
With AI, that is a day or two of work.

The hard part is making it reliable at scale: never blocking the {{< tooltip text="In async Python, one thread runs all tasks by switching between them. A single call that blocks freezes every conversation at once." >}}event loop{{< /tooltip >}}, and handling the crazy edge cases.
With an agent system you end up building a very complicated state machine, and if you do not watch it, any combination of states is possible. Almost all of them are edge cases.

A library gives you the easy 10% and leaves you the hard 90%.
And you do that 90% inside somebody else's code, where you cannot fix the root cause.

MindRoom is now about 360,000 lines of Python, plus about 750,000 lines of tests.[^loc]
A good part of that is code I wrote instead of depending on a library:

- **Memory and knowledge:** about 15,600 lines across 50 files.
- **Conversation history and {{< tooltip text="Summarizing older turns of a conversation so a long thread still fits in the model's context window." >}}compaction{{< /tooltip >}}:** about 8,400 lines.
- **An OpenAI-compatible API:** about 2,300 lines, so MindRoom agents show up as selectable "models" in any chat frontend that speaks the OpenAI protocol.
- **Claude provider support:** about 3,000 lines.

If I have to write the hard 90% either way, I might as well write the easy 10% too.

## 5. Fork your own: when the problem is hard

I am not going to write my own {{< tooltip text="Matrix encryption means per-device keys, the Olm and Megolm ratchets, cross-signing, device verification and key backup, all of which have to interoperate with every other client." >}}end-to-end encrypted{{< /tooltip >}} Matrix SDK, or my own {{< tooltip text="The server that stores your rooms and syncs them with other Matrix servers, like a mail server for chat." >}}homeserver{{< /tooltip >}}.
Those are hard, and also far below the line.
So there I fork.

**I forked the Python Matrix client.** MindRoom ships its own fork of matrix-nio rather than the upstream package.

**I forked the Matrix server, twice.** First {{< tooltip text="The original Matrix homeserver, written in Python by the Matrix.org team." >}}Synapse{{< /tooltip >}}. When I ran into scaling problems I moved to [Tuwunel](https://github.com/matrix-construct/tuwunel) and forked that.

**I forked the web client.** [Cinny](https://github.com/cinnyapp/cinny) is the Matrix web client MindRoom uses.

None of these are AI projects. AI is just where I felt it most.

Whether a fork stays a fork depends on the maintainers.
Tuwunel is extremely receptive to my patches, so I upstream anything that is general enough, and over the last six months I am its fourth most active contributor by commits.[^tuwunel]
Cinny has not accepted any of my pull requests, so I forked it and stopped trying to upstream.
Same with {{< tooltip text="An open-source, self-hosted ChatGPT-style web interface that can talk to many model providers." >}}LibreChat{{< /tooltip >}}: I had patches open for over a year without a reply, so I forked.

Keeping a fork up to date used to be miserable.
With an LLM doing the rebasing, pulling in the latest upstream is now cheap, though still a bit of a risk every time.
The bigger cost is that once you fork, you are responsible for the whole codebase, including the parts you never changed.

### Agno: patches instead of a fork

I did not fork Agno. I {{< tooltip text="Replacing a library's functions or methods at runtime from your own code, without changing the installed package." >}}monkey-patched{{< /tooltip >}} it.
Agno is very actively developed, I have talked to the maintainer, and they know about these problems, so I hoped to upstream my fixes.
I have filed 33 issues and pull requests there.[^agnoissues]

That got out of hand.
MindRoom now carries **126 documented workarounds** for Agno across 59 files.
Most of them live in 36 dedicated compatibility modules, about 7,200 lines of code, with the rest patched inline in 23 other files.
Every one uses the same comment format, so I can [find all of them with one search](https://github.com/search?q=repo%3Amindroom-ai%2Fmindroom+AGNO_COMPAT&type=code).
Each one says what is wrong upstream, links the issue or PR, and says when I can delete it.[^compat]
A few examples:

- **Search failures become plausible empty results.** A failed knowledge search and an empty index return the same empty list, so my agents confidently told me things did not exist.[^agno-search]
- **Streamed tool calls get malformed or merged.**[^agno-stream]
- **Reasoning is silently lost when tool calls are replayed.**[^agno-reasoning]
- **Provider errors collapse into a generic 502**, which throws away the error code you need to decide whether to retry.[^agno-502]

At this size, the patches amount to a fork.

## 6. I am not dunking on open source, including mine

Everything I named is open source I use every day, for free, built by people doing their best.
I filed issues and PRs, and where maintainers merged fixes I deleted my workarounds.

My own software is in the same category.
Most new AI tooling is not very good, and MindRoom may well be included.
It is large, fast-moving, and nowhere near millions of daily downloads.
By my own rule, you should think twice before depending on it.

I also have to admit that I have not yet built a project the roll-your-own way from the start.
So comparing "what I would do next time" with what I actually did is not entirely fair.
This is what I think right now, and a year from now I may have to write another post correcting this one.

## 7. My rule for the next `uv add`

I weigh three questions.

**How many projects use it?**
Daily downloads of the actual package, not stars, and not how many people use the product built on top.
In the millions: depend on it.

**How much do I rely on it?**
Agno and matrix-nio are the base of MindRoom.
A library I use in a CLI to format a question is not, and if I use it in a narrow way I do not need my own version.

**How hard is it, and how receptive is upstream?**
If the library is something AI can write in a couple of days, roll my own.
If it is hard, fork it.
If the maintainers accept patches, upstream what is general enough.

**If I started MindRoom over today, I would write the HTTP requests to the model providers myself.**
Not even the OpenAI or Anthropic SDKs.
And even httpx is less safe than its download numbers suggest: in early 2026 its maintainer closed the issue tracker and discussions, and the latest stable release is from December 2024.[^httpx]

In 2025 I wrote that the right answer is "it depends on the situation", and I still believe that.
I just had the wrong threshold.
Battle-tested means millions of downloads a day.
Below that: roll your own, and fork the rest.

[^stars]: From the GitHub API (`api.github.com/repos/agno-agi/agno`) on 2026-10-02: 42,385 stars and 6,041 forks.

[^downloads]: PyPI numbers are the `last_day` field of the [pypistats.org](https://pypistats.org) API (`/api/packages/<name>/recent`), fetched on 2026-10-02, except uv, fetched on 2026-10-18 (3,648,827). The matrix-js-sdk number is npm's weekly download count (about 730,000) divided by seven. Daily numbers wobble, so treat them as orders of magnitude.

[^jssdk]: When events arrive for a thread that has not finished initializing, the SDK's replay path never applies them, so an `m.replace` edit (the event type Matrix uses for "this replaces message X") is stored and never shown. I replayed a captured event trace through the SDK: unpatched, zero of seventeen edits reached the listeners; patched, all seventeen. MindRoom carries the fix as a `patch-package` patch on the SDK's `thread.ts`.

[^method]: For each direct dependency I looked at three things in the MindRoom repository: whether `pyproject.toml` pins a fork instead of the upstream package, whether `patch-package` patches it, and whether the source has workaround markers or comments pointing at upstream issues for it. The packages above a million downloads a day had none of those.

[^chroma]: The PR is titled "Release GIL during metadata I/O". On the MindRoom side, `knowledge/read_process.py` starts the child process, and a TODO says to remove it once a Chroma release with the fix is pinned. A blocked thread holding the GIL cannot be interrupted from Python, but the kernel will always terminate a child process.

[^nio]: Compared with upstream matrix-nio 0.25.2 (released 2024-10-04): `git diff --shortstat` on the library code gives 8,872 lines added and 1,966 removed across 52 files, from 89 commits, 76 of them mine. The fork is published on PyPI as `mindroom-nio`.

[^loc]: Counted with `git ls-files` and `wc -l` on the MindRoom repository on 2026-10-18: 360,513 lines in 1,222 Python files under `src/`, 750,657 lines under `tests/`, and another 81,543 lines of TypeScript in the frontend. The per-feature numbers below come from the same count over the relevant directories.

[^tuwunel]: Non-merge commits on Tuwunel's main branch since 2026-04-18: Jason Volk 1,332, June Strawberry 325, dasha_uwu 55, me 42.

[^agnoissues]: Issues and pull requests in [agno-agi/agno](https://github.com/agno-agi/agno/issues?q=author%3Abasnijholt) with me as the author, counted on 2026-10-02.

[^compat]: Every workaround starts with a comment like `# AGNO_COMPAT: Knowledge search hides provider failures as empty results.`, followed by `Reason:`, `Upstream issue:`, `Upstream PR:`, `Remove when:` and the tests that cover it. The counts come from `grep` over `src/`: 126 `AGNO_COMPAT:` markers in 59 files, and 7,160 lines in the 36 `agno_compat_*` modules.

[^agno-search]: `Knowledge.search` catches vector store and provider errors and returns `[]`. [agno#10150](https://github.com/agno-agi/agno/issues/10150), partially fixed by [agno#10152](https://github.com/agno-agi/agno/pull/10152).

[^agno-stream]: When a streamed tool-call index does not start at zero, Agno leaves empty placeholder calls. [agno#8879](https://github.com/agno-agi/agno/issues/8879), fix proposed in [agno#8880](https://github.com/agno-agi/agno/pull/8880).

[^agno-reasoning]: With the OpenAI Responses API, Agno keeps only the last reasoning item, so it cannot be replayed with the tool calls it belonged to. [agno#9960](https://github.com/agno-agi/agno/issues/9960); partial fixes landed in [agno#10075](https://github.com/agno-agi/agno/pull/10075) and [agno#10395](https://github.com/agno-agi/agno/pull/10395).

[^agno-502]: Unclassified `ModelProviderError` failures default to HTTP 502, so a real network blip and a permanent error look the same. [agno#8869](https://github.com/agno-agi/agno/issues/8869), partially addressed by [agno#8870](https://github.com/agno-agi/agno/pull/8870).

[^httpx]: The latest stable release on [PyPI](https://pypi.org/project/httpx/#history) is 0.28.1, uploaded 2024-12-06. There have been 1.0 development pre-releases since, the latest in August 2026. The closing of issues and discussions was widely discussed in the Python community in March 2026.
