---
title: "MindRoom: AI agents that live in Matrix and work everywhere 🧠"
subtitle: "Cross-platform AI agents with Matrix, Python, persistent memory, and 80+ tool integrations"
summary: "MindRoom is an open-source system I built that creates AI agents living in Matrix. Because Matrix bridges to Slack, Telegram, Discord, and more, your agents follow you everywhere—with persistent memory, multi-agent collaboration, and 80+ tool integrations."
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

Programming is my biggest passion in life.
I've been actively involved in open source for over ten years now, maintaining [40+ installable packages](https://github.com/basnijholt) across Python, JavaScript, and Rust.
Some of these have over 100,000 users; others have exactly one—me.
I mention this because it matters for what comes next: when AI coding tools arrived, I didn't start from zero.
As I wrote about in my [agentic coding post]({{< ref "/post/agentic-coding" >}}), AI has completely transformed how I work—when I'm AFK, I regularly build full features or entire projects by [dictating to my phone]({{< ref "/post/agentic-mobile-workflow" >}}) and routing it through my own [transcription software](https://github.com/basnijholt/agent-cli).

Through all of this, I became deeply convinced that AI agents are the future.
But the more I used them, the more problems I noticed with how they work today.

First, every AI tool is a silo.
ChatGPT knows you in one tab, Claude knows you in another, your Slack bot knows you in a third.
Switch platforms, and your AI starts from scratch.
You repeat yourself constantly, re-explain your preferences, re-describe your projects.

Second, most AI agent frameworks require you to *program* them.
That works for developers like me, but it excludes most of the world.
Non-programmers don't want to write code—they just want a chat.

And third, there's the privacy problem.
I'm fine sharing my email with Gemini—Google already owns my Gmail.
But do I want to send my financial data, my health records, or my personal notes to a cloud provider?
Not really.
I'd rather use a local model for sensitive tasks and pick the best, cheapest Chinese model for general-purpose deep research.

These three problems—silos, accessibility, and privacy—bothered me enough that I spent months building something to fix them.
I called it **MindRoom**—and then I got so obsessed with it that I eventually burned out and had to step away completely.

Recently, [OpenClaw](https://openclaw.ai) gained a lot of traction (171K GitHub stars and counting), solving a similar problem from a different angle.
Seeing its success reminded me that the idea I'd been working on wasn't just a niche obsession.
People genuinely want AI assistants that aren't locked into a single app.

So here I am, dusting off MindRoom and writing about what it is, how it works, and why I think the approach still matters.

{{% callout note %}}
**TL;DR:** MindRoom is an open-source system that creates AI agents living inside the [Matrix protocol](https://matrix.org/).
Because Matrix has bridges to Slack, Telegram, Discord, WhatsApp, and everything else, your agents can follow you across every platform—with persistent memory, 80+ tool integrations, and multi-agent collaboration.
Think of it as "your AI assistant, but it lives in Matrix and works everywhere."
{{% /callout %}}

> **TODO:** Screenshot of MindRoom in action — a Matrix room (e.g., Element client) showing multiple agents listed as users in the sidebar, with a conversation thread open where an agent is responding with streaming output and tool call indicators.

## 2. What is MindRoom?

MindRoom is an open-source system that creates AI agents living inside the [Matrix protocol](https://matrix.org/).
If you're not familiar with Matrix—it's a federated, end-to-end encrypted communication standard.
The same protocol used by the French government for 5.5 million civil servants, by German healthcare for 150K+ organizations, and by the Element app that millions of people use daily.

The key insight: Matrix has [bridges](https://matrix.org/ecosystem/bridges/) to *everything*.
Slack, Telegram, Discord, WhatsApp, IRC, email—you name it, there's a Matrix bridge for it.

So if your AI agent lives in Matrix, it can reach you on any platform.
One agent, every platform, continuous memory.

{{% callout warning %}}
**Fair warning:** Matrix bridges vary in maturity. Some (like the [Telegram bridge](https://github.com/mautrix/telegram)) work very well, while others can be finicky. Your mileage may vary depending on which platforms you need.
{{% /callout %}}

Here's what a typical setup looks like in `config.yaml`:

```yaml
agents:
  code:
    display_name: CodeAgent
    role: Generate code, manage files, execute shell commands
    model: opus-4-6
    tools: [file, shell, github]
    instructions:
      - Always read files before modifying them.
    rooms: [lobby, dev]

  research:
    display_name: ResearchAgent
    role: Search the web, summarize papers, find information
    model: gpt-5.2
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

> **TODO:** Screenshot of the Element client's member list showing MindRoom agents as Matrix users — each with their own avatar, display name (e.g., CodeAgent, ResearchAgent), and "Online" presence status.

## 3. How it actually works

The architecture is something I iterated on quite a bit, and I think it turned out well.
At the core sits what I call the **MultiAgentOrchestrator**—a class in `bot.py` that boots every configured entity (router, agents, teams), provisions Matrix user accounts for each one via [matrix-nio](https://github.com/matrix-nio/matrix-nio), and keeps sync loops alive.
The agents themselves are powered by the [Agno](https://github.com/agno-agi/agno) framework, which provides a unified interface across AI model providers.

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

> **TODO:** Screen recording (short video/GIF) of an agent responding in real-time — showing the streaming text appearing incrementally, the `⋯` marker while thinking, and tool call/result blocks appearing mid-response.

## 4. Building on Matrix: the good and the tricky

One of the best things about building on Matrix is what you get for free.
End-to-end encryption (Olm/Megolm), a fully bridged chat platform that just works, a choice of clients, federation between organizations—all of that comes with the protocol.
You don't have to build any of it yourself.

But because Matrix has such a tight specification, it also brings challenges.

The protocol doesn't support streaming.
AI agents that think for 30 seconds before dumping a wall of text make for a terrible chat experience, so I hacked streaming in by rapidly editing the same message as new tokens arrive.
An `⋯` marker shows while the agent is still thinking—a small touch, but it makes the experience feel responsive and alive.

There's also a size limit on message content.
That's fine for human chat, but AI responses can get long—especially when tool calls and their results are included.
I worked around this by using Matrix's attachment feature: when a response exceeds the limit, the content continues in an attachment that gets updated as the message keeps streaming in.
This required forking the [Element](https://element.io/) chat client so that attachments display inline rather than as downloadable files, making the whole thing seamless.

{{% callout note %}}
These workarounds are the kind of thing you don't anticipate when you pick a protocol.
Matrix gives you an incredible foundation, but making it work well for AI required bending it in ways it wasn't designed for.
{{% /callout %}}

## 5. Memory that follows you

This is where things get really interesting—and it's the feature that made me most excited when I first got it working.
MindRoom implements a dual memory system inspired by [Mem0](https://mem0.ai/):

- **Agent memory** (`agent_code`): What a specific agent knows about you—your coding style, your preferences, your tech stack.
  This persists across all rooms and platforms.
- **Room memory** (`room_dev`): Project-specific knowledge tied to a room—architectural decisions, constraints, team conventions.
- **Team memory**: Shared context when agents collaborate—joint decisions, consensus, shared insights.

Memories are stored in [ChromaDB](https://www.trychroma.com/) and searched semantically.
When you talk to your code agent on Tuesday in Matrix and then on Wednesday via the Slack bridge, it remembers everything.
You don't have to re-explain yourself.

The implementation uses [Mem0](https://mem0.ai/)'s `AsyncMemory` with configurable embedding providers ([OpenAI](https://platform.openai.com/docs/guides/embeddings), [Ollama](https://ollama.com/), or HuggingFace), so you can keep it fully local if privacy matters to you.

> **TODO:** Screenshot showing a conversation where the agent references something the user told it in a previous session or different room — demonstrating persistent memory in action. Alternatively, a side-by-side of two platforms (Matrix native + Slack/Telegram bridge) showing the same agent maintaining context.

## 6. 80+ tool integrations

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

## 7. Teams: agents that collaborate

Single agents are useful, but sometimes you need a team.
MindRoom supports two collaboration modes:

**Coordinate mode**: A lead agent orchestrates others.
You ask a question, the lead delegates subtasks, collects results, and synthesizes a unified response.

**Collaborate mode**: All agents work on the same task in parallel, each providing their independent analysis.
The system then merges their responses with a consensus summary.

In practice, you might have a research team where one agent searches academic papers, another checks industry news, and a third validates claims—all triggered by a single message.

> **TODO:** Screenshot of a team collaboration in action — a thread where multiple agents respond to a single question, each contributing their specialty (e.g., one does research, another analyzes, a third summarizes).

## 8. Hot-reload: change config without downtime

One detail I'm particularly happy with (and spent way too long perfecting): `config.yaml` is watched at runtime.
When you edit it—add an agent, change a model, update instructions—MindRoom diffs the old and new config, gracefully restarts only the affected agents, and has them rejoin their rooms.
No downtime, no restart required.

This sounds minor, but when you're iterating on agent behavior, being able to tweak a system prompt and see results in seconds significantly improves the development loop.

> **TODO:** Screen recording (short video/GIF) of the hot-reload flow — edit config.yaml in an editor, save, and show the terminal logs detecting the change and the agent appearing in the Matrix room within seconds.

## 9. Voice, scheduling, and other features

Some features I built purely because I wanted them for myself (a recurring theme in my projects, as anyone who's read my [local AI journey]({{< ref "/post/local-ai-journey" >}}) can attest).
I even built [Matty](https://github.com/basnijholt/matty), a Matrix CLI client, from bed at midnight because I needed a way to interact with my agents from the terminal:

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

## 10. The obsession, the SaaS dream, and the burnout

I need to be honest about what actually happened with MindRoom, because "life got in the way" is a sanitized version of the story.

What really happened is that I got completely, utterly obsessed.
Every single second I wasn't working at my day job or sleeping, I was working on MindRoom.
Many hundreds of hours went into it.
I seriously considered quitting my job and starting an AI startup around it.

If you've read Armin Ronacher's post [Agent Psychosis: Are We Going Insane?](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/), you'll know exactly what I'm talking about.
The dopamine hit from building with AI agents is incredibly real.
As Armin writes: "You feel productive, you feel like everything is amazing, and if you hang out just with people that are into that stuff too, without any checks, you go deeper and deeper into the belief that this all makes perfect sense."

That was me.
I was building and building, shipping feature after feature, and it felt incredible.
The codebase grew to over 1,000 commits.
I built the core system, then a React dashboard, then I started on a full SaaS platform—Kubernetes deployments on Hetzner Cloud, a FastAPI backend, a Next.js 15 frontend, Stripe integration, Supabase auth, Helm charts for multi-tenant isolation.

And that's where the enthusiasm started to erode.
Not because the core idea was bad, but because the work shifted from building interesting things (agent orchestration, memory systems, routing intelligence) to grinding through SaaS boilerplate: GDPR compliance, payment processing, automated Kubernetes deployments, terms of service, cookie banners.
The dopamine loop that kept me going at 2 AM broke when the work stopped being creative and started being compliance paperwork.

{{% callout note %}}
Looking back, I think this is a pattern worth recognizing.
Agentic coding makes it so easy to *start* things that you can build yourself into a scope that would normally require a team.
The gap between "I can build this" and "I can maintain and ship this as a product" is larger than the tools make it feel.
{{% /callout %}}

> **TODO:** Screenshot of the SaaS platform dashboard (Next.js frontend) — showing the instance management UI.

## 11. OpenClaw and why it matters

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
The federation angle is something OpenClaw doesn't have: the ability for agents from different organizations to collaborate natively, with end-to-end encryption (Olm/Megolm), on a protocol that governments already trust and deploy at scale.

> **TODO:** Architecture diagram comparing MindRoom vs OpenClaw side-by-side. MindRoom: User → Matrix (federated) → Bridges → platforms. OpenClaw: User → Local Gateway → Direct connectors → platforms.

## 12. What's next

After stepping away for a while, I'm picking MindRoom back up—but with a healthier relationship this time.
The codebase supports 8+ AI model providers ([OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Ollama](https://ollama.com/), [Groq](https://groq.com/), [Google](https://ai.google.dev/), [OpenRouter](https://openrouter.ai/), [DeepSeek](https://www.deepseek.com/), [Cerebras](https://cerebras.ai/)), and the core architecture is solid.
That said, few people besides me have actually tried it so far—and I'd like to change that.
There's already a Docker Compose file and a [starter repository](https://github.com/basnijholt/mindroom-stack) to get started, but I want to make it even simpler.

What I want to focus on:
- **Skills system**: Building an ecosystem of reusable agent behaviors (already partially implemented with OpenClaw-compatible format)
- **Even easier onboarding**: A `docker compose up` gets you running today, but I want a wizard that gets you from zero to working agents without touching a YAML file
- **Community**: The codebase is open-source but I haven't promoted it at all
- **Not burning out again**: Working on this at a sustainable pace, not the obsessive 2 AM marathon from before

I'm deliberately leaving the SaaS ambitions aside for now.
The core system is what matters, and that's where I want to spend my energy.

If you're interested in AI agents that live in Matrix and work everywhere, check out [MindRoom on GitHub](https://github.com/basnijholt/mindroom).

Sometimes all it takes is seeing someone else succeed with a similar idea to remember why you started building in the first place.
And sometimes the most important lesson from a project isn't technical—it's learning when to step away and when to come back.

_Are you running AI agents on any messaging platforms? Have you tried Matrix for anything beyond regular chat? I'd love to hear about your setups!_

## Links and resources

- [MindRoom on GitHub](https://github.com/basnijholt/mindroom)
- [MindRoom Stack (starter repository)](https://github.com/basnijholt/mindroom-stack)
- [Matrix protocol](https://matrix.org/)
- [OpenClaw](https://openclaw.ai)
- [Mem0 (memory system inspiration)](https://mem0.ai/)
- [Agno framework](https://github.com/agno-agi/agno)
- [Matty (Matrix CLI client)](https://github.com/basnijholt/matty)
- [Agent Psychosis: Are We Going Insane?](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/) by Armin Ronacher
- [My agentic coding post]({{< ref "/post/agentic-coding" >}})
- [My local AI journey]({{< ref "/post/local-ai-journey" >}})
- [Coding from my phone]({{< ref "/post/agentic-mobile-workflow" >}})
