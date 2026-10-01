---
title: "Slowly, then all at once: AI agents that know how a company works"
subtitle: "How I built a company brain that IonQ actually uses"
summary: "MindRoom grew one small group at a time at IonQ, until a company-wide demo made hundreds of people sign up in a day. What surprised me is that the heaviest users include engineers who already live in their coding agents."
date: 2026-09-30
draft: false
featured: false
image:
  caption: "The MindRoom cube and the IonQ logo, connected by a collapsing wave"
  focal_point: ""
  preview_only: true
authors:
  - admin
tags:
  - ai
  - mindroom
  - matrix
  - agents
  - ionq
  - knowledge-management
categories:
  - AI
  - level:beginner
---

IonQ is the world's leading vertically integrated, full-stack quantum platform company.
We build quantum computers, quantum security solutions, quantum networks, and quantum sensors, and we fabricate our own quantum chips.
That means thousands of people working on some of the hardest physics and engineering problems the world faces.
Much of what we know is not written down in one place.
Where a program actually stands lives in Slack threads, tickets, commits, documents, and meetings.
If you want the real picture, somebody has to read all of it, or you ask a colleague who has probably explained it five times already.
And as IonQ grows, everybody is new to something.
Someone who just joined through an acquisition is new to all of it, and after three years here, I still could not explain what half of our programs do.

{{< bleed-svg src="entangled-cores.svg" alt="The MindRoom cube and the IonQ logo, connected by a wave that collapses and lights up both at once" >}}

## Why I built MindRoom

Programming has always been my biggest passion, and when AI coding agents suddenly became extremely good, the jump in what I could do in a single day was the biggest I had ever seen.
But that power only reaches people who are comfortable in a terminal.
My mom will never open one.
Neither will most of the physicists, hardware engineers, and program managers who make a company like IonQ work.

So I built [MindRoom]({{< ref "/post/mindroom" >}}), which is [open source](https://github.com/mindroom-ai/mindroom), and I run it at IonQ as a central hub for collaboration and knowledge sharing, what I like to call a company brain.
It looks like a chat app.
Everybody gets a personal agent the moment they log in, running on its own [sandboxed computer](https://docs.mindroom.chat/tools/worker-computer/) in the cloud.
Every program can get a shared agent that is connected to that program's Slack, Confluence, Jira, code, meeting notes, and even the parts database.
Its answers link back to what a human wrote, so you can check them instead of trusting them.

The personal agent is where most people start.
I can send mine a voice message like "every week, just before my one-on-one with my manager, give me a clear summary of what I've been up to."
I never told it who my manager is, when we meet, or where to look.
It works that out on its own, sends me a link to the summary, and from then on [does it every week](https://docs.mindroom.chat/scheduling/) without being asked again.

## Slowly

For months, MindRoom grew one small group at a time.
It started with a single colleague, then a pilot of about ten, and then the team behind [Superion 10K](https://ionq.com/walking-cat), our 10,000-qubit quantum computer.
We rolled it out carefully, and each step at most doubled the group.
Every new group needed a hand-held onboarding, so I recorded short videos to make that scale.
The people who tried it kept using it, but it was hard to explain what it could do without showing it.

{{< demo-clips more="More in the [MindRoom showcase](https://docs.mindroom.chat/showcase/)." >}}
{{< demo-clip caption="A voice message becomes a reminder" light="https://github.com/user-attachments/assets/7bf1bb2f-31c7-4ef4-ac07-4ec1b22b2da1" dark="https://github.com/user-attachments/assets/8abba58e-790f-4c80-a57d-62ab683ea18c" >}}
{{< demo-clip caption="An approval card before anything is sent" light="https://github.com/user-attachments/assets/d62d98e8-c066-4e1f-8a8f-d840da7b0bd1" dark="https://github.com/user-attachments/assets/6a2033ea-3354-4afd-9d58-fc617b18cd24" >}}
{{< demo-clip caption="Watch the agent's browser and take over" light="https://github.com/user-attachments/assets/cc079b2f-6dbf-4509-9fdc-4ec21da85d7a" dark="https://github.com/user-attachments/assets/63868e17-6824-4073-8904-e1b7abc4b173" >}}
{{< /demo-clips >}}

## Then all at once

That changed with a company-wide demo.
Instead of explaining what agents can do, I played someone new to the Superion 10K program and asked its shared agent, by voice, to explain what we are building, how the work is split, and how the pieces fit together.
A few minutes later it had made an interactive slide deck, built entirely from our own documents, Slack threads, and code, with every claim linked to its source.

Hundreds of people signed up that same day, and within weeks about a third of everyone who can create an account had one.
At the time of the demo, five programs and teams used it every day, and now it is about fifteen.
People had already had access to tools like Claude and ChatGPT for months, but those never clicked for them in the same way.
An agent that already knew *our* work did.

## The surprise

I built MindRoom for people who never open a terminal, simple enough that even my mom could use it, so I expected non-technical colleagues to be the main audience.
They did adopt it.
Program managers use it to write weekly updates from what actually happened in Slack and Jira, instead of from whatever people remembered to tell them.
Our configuration management team uses it to check the hardware as it was actually built against the engineering baseline, and to find policy documents that contradict each other across different systems.

What I did not expect was that some of the most capable engineers I know, who already run their own coding agents every day, would become some of the heaviest users.
One of them, who already lived in Claude Code, cleared his entire inbox, Slack, and task list from his phone on a single flight.
I think they like it for the same reason everyone else does: it keeps context.
For writing code, dedicated tools like Claude Code and Codex are better, because they are built for exactly that.[^coding]
But engineers use MindRoom as a layer for gathering knowledge.
A coding agent does not need to know who you are or who you report to in order to fix a bug.
Coordinating a large group of people is mostly that kind of context.

## Institutional knowledge

A colleague wrote about [why AI's biggest opportunity in large programs is institutional knowledge](https://m-malinowski.github.io/2026/08/24/ai-knowledge-management.html), from the perspective of someone using it every day.
From the builder's side, what I like most is that a shared agent gets better the more people use it.

When someone works through a problem with it, it keeps what it learned, so the next person benefits without ever having been in that thread.

In Claude Code or Codex, you handle memory yourself, by asking the agent to write things down in Markdown files.
Agents get lazy: they forget to write things down, and later they forget to read them.
MindRoom agents are also told to write down durable facts, in plain text files under version control, but they do not have to remember to.
A [background process](https://docs.mindroom.chat/memory/#file-auto-flush-worker) picks out what is worth keeping from every conversation and adds it to a semantic search index.
When a new message comes in, the relevant memories are looked up and added to the context automatically.
So remembering and looking things up no longer depend on the agent deciding to do it.
When someone asks a question that was already answered, the agent re-verifies its earlier analysis instead of starting from zero, so the second answer usually comes faster and builds on the first.

One very cool and yet simple idea is agent dreaming, which I picked up from [a talk by Lance Martin from Anthropic](https://www.youtube.com/watch?v=9QebvrrY3KY).
People collect short-term memories during the day and consolidate them while they sleep.
The analogy is loose, but the idea carries over.
Every night, a first pass reads the agent's memories, every conversation it has had, and the original sources, and looks for contradictions, for example when someone corrected something a few minutes later and the two memories were never reconciled.
It writes a patch to fix them.
A second pass, in a completely fresh context, checks every proposed fix and accepts or rejects it.
It rejects about half, which is exactly the kind of skepticism I want.
Dreaming is not even platform code, just a [skill](https://docs.mindroom.chat/skills/), a short set of written instructions: you tell an agent to set up dreaming, and it knows what to do, including scheduling itself to run every night.

It also notices when two documents disagree, which is easy to miss when nobody reads all of them.
Its reports end with "Corrections welcome, tell the agent and the next report improves," and a correction becomes a memory that the next report uses.
And when nobody ever wrote something down, it usually still knows who to ask, because it keeps track of what everybody is working on.

## Why build it ourselves

There are plenty of AI products that promise something similar.
Building our own gives us complete flexibility and no vendor lock-in.
We are not waiting for a third party to support the model, the system, or the feature we need.
When a better model comes out, we can switch the same day.
And the knowledge it builds up is stored in IonQ's own cloud environment.

It also means we can experiment quickly.
Features that could take a large organization months often take me days:

- Agents can open a real browser on their own remote computer, not on your laptop, and you can [watch it live and take over](https://docs.mindroom.chat/tools/worker-computer/#watch-take-control-and-resume), for example to log in somewhere, before handing control back.
- An [MCP](https://modelcontextprotocol.io) [gateway](https://docs.mindroom.chat/deployment/mcp-gateway/) lets people connect their local tools, like Claude Code or Codex, to every agent they have access to and all of those agents' tools, so they benefit from what the agents have collected even outside MindRoom.
- A day after OpenAI released [GPT-Live-1 in its API](https://openai.com/index/introducing-gpt-live-1-in-the-api/), you could [call your MindRoom agent](https://docs.mindroom.chat/voice-calls/#openai-live-with-agent-delegation): the same agent, with the same memory, which hands longer tasks to a background process while you keep talking. On my commute, I talk to my agent to plan my day and get things started.
- Agents can [host small sites](https://docs.mindroom.chat/tools/agent-orchestration/#report_publishing), much like [ChatGPT Sites](https://help.openai.com/en/articles/20001339-creating-and-managing-chatgpt-sites), behind a temporary link with access control. That is how an agent can answer a question with an interactive presentation or a dashboard instead of a wall of text.

## What it takes to run this at a company

A demo on a laptop is easy.
Running a central hub that hundreds of people rely on every day is a different problem, and most of my time went there.

People [sign in with their normal company account](https://docs.mindroom.chat/deployment/trusted-upstream-auth/), and their account and personal agent are created on first login.
There is nothing to install.

Every agent runs in its own [sandboxed container](https://docs.mindroom.chat/deployment/sandbox-proxy/) with no secrets inside it.
Credentials are injected from outside, so the agent never sees a token.
Agents also cannot reach arbitrary websites: [outbound traffic is denied by default](https://docs.mindroom.chat/deployment/approved-egress/), and a new domain needs a person's time-limited approval.

Reading is free, but anything that sends or changes something on your behalf, like an email, shows an [approval card](https://docs.mindroom.chat/authorization/#tool-approval-and-resource-ownership) with exactly what will be sent and to whom.
A shared agent [only answers the people](https://docs.mindroom.chat/authorization/) who work on that program, and it only reaches the systems it was granted.

It runs in IonQ's own cloud environment, and a security review ran alongside the rollout.
At its busiest moment so far, 200 people were writing to their agents at the same time, and it held up fine.
The chat layer has plenty of room to grow: the French government runs [Matrix](https://fr.wikipedia.org/wiki/Tchap) for about 400,000 civil servants.

## What's next

With our recent acquisitions and a lot of new hires, there is a steady flow of people joining IonQ who are new to all of it, and to MindRoom.
Because MindRoom is built on [Matrix](https://matrix.org), which is federated like email, groups with different data rules can each get their own instance and still work together where that is allowed.
And whoever joins next can log in on their first day and ask their program's agent how the work fits together and who to ask.

[^coding]: That does not mean you cannot write code from MindRoom. Because every agent has its own computer, it can run any software, so my MindRoom agent simply runs Claude Code or Codex itself when there is coding to do.
