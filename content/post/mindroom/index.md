---
title: "MindRoom: AI agents that live in Matrix and work everywhere 🧠"
subtitle: "How OpenClaw's success reminded me why I built this"
summary: "I spent months building MindRoom—an open-source system that gives AI agents a home in Matrix so they can follow you across Slack, Telegram, Discord, and anywhere else. Then life happened and I got distracted. OpenClaw's explosive success reminded me why this idea matters."
date: 2026-02-06
draft: false
featured: true
authors:
  - admin
tags:
  - AI
  - open-source
  - python
  - matrix
  - agents
  - mindroom
  - openclaw
  - self-hosting
  - side-projects
categories:
  - AI
  - open-source
  - level:intermediate
---

{{< toc >}}

## 1. The problem: your AI is trapped in apps

I've been obsessed with AI agents for a while now.
As I wrote about in my [agentic coding post]({{< ref "/post/agentic-coding" >}}), AI has completely transformed how I work—I even built [Matty](https://github.com/basnijholt/matty) (a Matrix CLI client) from my phone in bed at midnight because I needed a way for my agents to communicate.

But one thing kept bugging me: every AI tool is a silo.
ChatGPT knows you in one tab, Claude knows you in another, your Slack bot knows you in a third.
Switch platforms, and your AI starts from scratch.
You repeat yourself constantly, re-explain your preferences, re-describe your projects.

This bothered me enough that I spent months building something to fix it.
I called it **MindRoom**—and then, as side projects often go, life got in the way and my attention drifted.

Recently, [OpenClaw](https://openclaw.ai) exploded onto the scene (171K GitHub stars and counting), solving a similar problem from a different angle.
Seeing its success was a wake-up call: the idea I'd been working on wasn't just a niche obsession.
People genuinely want AI assistants that aren't locked into a single app.

So here I am, dusting off MindRoom and writing about what it is, how it works, and why I think the approach still matters.

{{% callout note %}}
**TL;DR:** MindRoom is an open-source system that creates AI agents living inside the [Matrix protocol](https://matrix.org/).
Because Matrix has bridges to Slack, Telegram, Discord, WhatsApp, and everything else, your agents can follow you across every platform—with persistent memory, 80+ tool integrations, and multi-agent collaboration.
Think of it as "your AI assistant, but it lives in Matrix and works everywhere."
{{% /callout %}}

<!-- TODO: Screenshot of MindRoom in action — a Matrix room (e.g., Element client) showing
     multiple agents listed as users in the sidebar, with a conversation thread open where
     an agent is responding with streaming output and tool call indicators. This gives
     readers an immediate visual of what MindRoom looks like in practice. -->

## 2. What is MindRoom?

MindRoom is an open-source system that creates AI agents living inside the [Matrix protocol](https://matrix.org/).
If you're not familiar with Matrix—it's a federated, end-to-end encrypted communication standard.
The same protocol used by the French government for 5.5 million civil servants, by German healthcare for 150K+ organizations, and by the Element app that millions of people use daily.

The key insight: Matrix has bridges to *everything*.
Slack, Telegram, Discord, WhatsApp, IRC, email—you name it, there's a Matrix bridge for it.

So if your AI agent lives in Matrix, it can reach you on any platform.
One agent, every platform, continuous memory.

Here's what a typical setup looks like in `config.yaml`:

```yaml
agents:
  code:
    display_name: CodeAgent
    role: Generate code, manage files, execute shell commands
    model: sonnet
    tools: [file, shell, github]
    instructions:
      - Always read files before modifying them.
    rooms: [lobby, dev]

  research:
    display_name: ResearchAgent
    role: Search the web, summarize papers, find information
    model: gpt-4
    tools: [tavily, arxiv, wikipedia]
    rooms: [lobby, research]

teams:
  super_team:
    display_name: Super Team
    agents: [code, research]
    mode: collaborate
```

That's it.
Define your agents, give them tools and rooms, and they show up in Matrix as real users—with avatars, typing indicators, and online status.

<!-- TODO: Screenshot of the Element client's member list showing MindRoom agents as
     Matrix users — each with their own avatar, display name (e.g., CodeAgent,
     ResearchAgent), and "Online" presence status. Shows that agents are first-class
     Matrix citizens, not bot integrations. -->

## 3. How it actually works

I'm not going to lie—the architecture of MindRoom is something I'm pretty proud of.
At the core sits the **MultiAgentOrchestrator** (in `bot.py`), which boots every configured entity—router, agents, teams—provisions Matrix user accounts for each one, and keeps sync loops alive.

When someone sends a message in a Matrix room:

1. **Explicit mentions** go directly to the named agent (`@mindroom_code help me debug this`)
2. **Thread continuations** keep the same agent responding (no weird context switches mid-conversation)
3. **New conversations** hit the **router**—an AI that analyzes the message and picks the best agent based on capabilities

All conversations happen in threads, which keeps rooms organized.
Agents stream their responses in real-time, editing a single message as they think rather than spamming new ones.
You see tool calls happening live:

```
🔧 Tool Call: search_web(query="matrix protocol bridges")
[waiting for result...]
✅ search_web result:
[results here]
```

The streaming uses an `⋯` marker while the agent is still thinking—a small detail, but it makes the experience feel responsive and alive.

<!-- TODO: Screen recording (short video/GIF) of an agent responding in real-time —
     showing the streaming text appearing incrementally, the ⋯ marker while thinking,
     and tool call/result blocks (🔧/✅) appearing mid-response. A 10-15 second clip
     captures the "alive" feeling better than any screenshot. -->

## 4. Memory that follows you

This is where things get really interesting—and it's the feature that made me most excited when I first got it working.
MindRoom implements a dual memory system inspired by [Mem0](https://mem0.ai/):

- **Agent memory** (`agent_code`): What a specific agent knows about you—your coding style, your preferences, your tech stack.
  This persists across all rooms and platforms.
- **Room memory** (`room_dev`): Project-specific knowledge tied to a room—architectural decisions, constraints, team conventions.
- **Team memory**: Shared context when agents collaborate—joint decisions, consensus, shared insights.

Memories are stored in ChromaDB and searched semantically.
When you talk to your code agent on Tuesday in Matrix and then on Wednesday via the Slack bridge, it remembers everything.
You don't have to re-explain yourself.

<!-- TODO: Screenshot showing a conversation where the agent references something the
     user told it in a previous session or different room — demonstrating persistent
     memory in action. Alternatively, a side-by-side of two platforms (Matrix native +
     Slack/Telegram bridge) showing the same agent maintaining context. -->

## 5. 80+ tool integrations

One of the more fun parts of building MindRoom was the tool ecosystem—I may have gotten a bit carried away here.
Agents can use over 80 integrations:

| Category | Examples |
|----------|----------|
| **Communication** | Gmail, Slack, Telegram, Discord |
| **Development** | GitHub, Shell, Python, Docker |
| **Search** | Tavily, Wikipedia, Arxiv, DuckDuckGo |
| **Productivity** | Google Calendar, Jira, Linear, Todoist |
| **Smart Home** | Home Assistant |
| **AI/ML** | DALL-E, ElevenLabs, Replicate |
| **Data** | Pandas, SQL, DuckDB, Yahoo Finance |
| **Web** | Firecrawl, Crawl4ai, Browser automation |

Tools are lazy-loaded and credential-managed, so an agent only loads what it needs.
The registration system is clean:

```python
@register_tool("github")
def get_github_toolkit() -> type[Toolkit]:
    return GithubToolkit
```

## 6. Teams: agents that collaborate

Single agents are useful, but sometimes you need a team.
MindRoom supports two collaboration modes:

**Coordinate mode**: A lead agent orchestrates others.
You ask a question, the lead delegates subtasks, collects results, and synthesizes a unified response.

**Collaborate mode**: All agents work on the same task in parallel, each providing their independent analysis.
The system then merges their responses with a consensus summary.

In practice, you might have a research team where one agent searches academic papers, another checks industry news, and a third validates claims—all triggered by a single message.

<!-- TODO: Screenshot of a team collaboration in action — a thread where multiple agents
     respond to a single question, each contributing their specialty (e.g., one does
     research, another analyzes, a third summarizes). Shows the coordinate or collaborate
     mode producing a unified result. -->

## 7. Hot-reload: change config without downtime

One detail I'm particularly happy with (and spent way too long perfecting): `config.yaml` is watched at runtime.
When you edit it—add an agent, change a model, update instructions—MindRoom diffs the old and new config, gracefully restarts only the affected agents, and has them rejoin their rooms.
No downtime, no restart required.

This sounds minor, but when you're iterating on agent behavior, being able to tweak a system prompt and see results in seconds makes a huge difference.

<!-- TODO: Screen recording (short video/GIF) of the hot-reload flow — edit config.yaml
     in an editor (e.g., add a new agent or change instructions), save, and then show
     the terminal logs detecting the change and the agent appearing in the Matrix room
     within seconds. ~10 seconds is enough to show the feedback loop. -->

## 8. Voice, scheduling, and other features

Some features I built purely because I wanted them for myself (a recurring theme in my projects, as anyone who's read my [local AI journey]({{< ref "/post/local-ai-journey" >}}) can attest):

- **Voice messages**: Audio messages in Matrix are auto-transcribed via Whisper and treated as regular text input.
  You can talk to your agents.
- **Scheduled tasks**: Natural language scheduling (`!schedule "check my email every morning at 9 AM"`) backed by cron jobs.
  Agents can run tasks in the background and escalate to you when needed.
- **DM support**: Agents respond naturally in 1:1 conversations without needing mentions.
- **Cross-organization federation**: Because Matrix is federated, two companies' AI agents can collaborate in a shared room.
  This is something no proprietary platform can do.

{{% callout note %}}
The voice feature pairs nicely with my [`agent-cli`](https://github.com/basnijholt/agent-cli) tool—local Whisper transcription on my RTX 3090 means I can talk to my Matrix agents without any cloud dependency.
{{% /callout %}}

## 9. The SaaS platform (half-built)

Because apparently building the core system wasn't enough scope creep, I also started building a hosted version—a Kubernetes-based SaaS platform where people could spin up MindRoom instances without managing infrastructure.
The platform backend is FastAPI, the frontend is Next.js 15, and each customer gets isolated deployments via Helm charts on Hetzner Cloud.

It's functional but unfinished.
Another artifact of attention drifting elsewhere—sound familiar? (See: every side project ever.)

<!-- TODO: Screenshot of the SaaS platform dashboard (Next.js frontend) — showing the
     instance management UI, even if it's half-built. Gives readers a sense of the
     vision for a hosted product. -->

## 10. OpenClaw and why it matters

[OpenClaw](https://openclaw.ai) takes a different approach to the same core problem.
Where MindRoom builds on Matrix federation as the backbone, OpenClaw runs a local Gateway on your machine and connects to messaging platforms directly (WhatsApp via Baileys, Telegram via grammY, Discord via discord.js, and so on).

The similarities are striking:
- Both give you a single AI assistant across all your messaging platforms
- Both have persistent memory
- Both support multiple tools and integrations
- Both are open-source and privacy-focused
- Both let you choose your own AI model

The differences are interesting too.
OpenClaw is local-first and TypeScript-based with 171K stars and a massive community.
MindRoom is Python-based, federation-first, and... well, let's just say my GitHub star count is a few orders of magnitude lower.

But seeing OpenClaw validate the core idea—that people want AI assistants that aren't trapped in apps—reminded me that what I'd been building matters.
The federation angle is something OpenClaw doesn't have: the ability for agents from different organizations to collaborate natively, with military-grade E2E encryption, on a protocol that governments trust.

<!-- TODO: Architecture diagram comparing MindRoom vs OpenClaw side-by-side.
     MindRoom: User → Matrix (federated) → Bridges → Slack/Telegram/Discord/etc.
     OpenClaw: User → Local Gateway → Direct connectors → Slack/Telegram/Discord/etc.
     A simple SVG or drawn diagram highlighting the federation vs local-first difference. -->

## 11. What's next

I'm picking MindRoom back up.
The codebase has over 1,000 commits, supports 8+ AI model providers (OpenAI, Anthropic, Ollama, Groq, Google, OpenRouter, DeepSeek, Cerebras), and the core architecture is solid.

What I want to focus on:
- **Skills system**: Building an ecosystem of reusable agent behaviors (already partially implemented with OpenClaw-compatible format)
- **Better onboarding**: Right now setup requires some technical knowledge—I want a wizard that gets you from zero to working agents in minutes
- **The SaaS platform**: Finishing what I started so non-technical users can try MindRoom
- **Community**: The codebase is open-source but I haven't promoted it at all

If you're interested in AI agents that live in Matrix and work everywhere, check out [MindRoom on GitHub](https://github.com/basnijholt/mindroom).

Sometimes all it takes is seeing someone else succeed with a similar idea to remember why you started building in the first place.

_Are you running AI agents on any messaging platforms? Have you tried Matrix for anything beyond regular chat? I'd love to hear about your setups!_

## Links and resources

- [MindRoom on GitHub](https://github.com/basnijholt/mindroom)
- [Matrix protocol](https://matrix.org/)
- [OpenClaw](https://openclaw.ai)
- [Mem0 (memory system inspiration)](https://mem0.ai/)
- [Agno framework](https://github.com/agno-agi/agno)
- [Matty (Matrix CLI client)](https://github.com/basnijholt/matty)
- [My agentic coding post]({{< ref "/post/agentic-coding" >}})
- [My local AI journey]({{< ref "/post/local-ai-journey" >}})
