---
title: "How I develop right now 🧵"
subtitle: "From thirty terminal windows to forty agents in one chat room"
summary: "My coding agents now work for an hour to more than a day on their own, so I run fifteen of them at once, and forty on a good day. This is how I went from thirty terminal windows, through cmux, the Codex desktop app and T3 Code, to a MindRoom room that sorts every thread into Needs you, Working, Later and Done."
date: 2026-11-20
draft: false
featured: false
authors:
  - admin
tags:
  - ai
  - agents
  - mindroom
  - agentic-coding
  - terminal
  - open-source
categories:
  - Software Development
  - AI
  - level:intermediate
---

I'm a huge terminal nerd.
I maintain at least twenty different {{< tooltip text="Command-line interface: a program you run by typing a command in a terminal." >}}CLI{{< /tooltip >}} tools, and I use many of them every day.
For a long time, all my coding with AI happened [strictly in the terminal]({{< ref "/post/terminal-ninja" >}}).
At points I had probably thirty terminal windows open at once, with tabs and panes.

So it was hard for me to accept that my next step was a desktop app.
The step after that was a chat room.

I still use my beloved [iTerm2]({{< ref "/post/dotfiles" >}}).
But my coding agents now live in [MindRoom]({{< ref "/post/mindroom" >}}), in a room where every task is a thread, and that room tells me which thread needs me.
This post walks through how I got there: the tools I used, why each one stopped working for me, and how the room in MindRoom changed along the way.

{{< toc >}}

{{% callout note %}}
**TL;DR:** A task I hand to an agent now runs from an hour to more than a day on its own.
So I run many at once: fifteen sessions comfortably, and forty on a good day.
With that many, the hard part is knowing which session needs me.
MindRoom Chat shows every thread as a card under Needs you, Working, Later or Done, and that view is what lets me keep up.
{{% /callout %}}

{{< figure src="room-sections.png" caption="My MindRoom-Dev room in the Compact view, rebuilt as a demo. The client is the real MindRoom Chat, and the threads are real threads from my room, replayed with their own titles and text. Six sit under Working and four under Needs you, and the bar at the bottom counts the background jobs and sub-agents. Each card shows an AI-generated title, what the agent last did, its git worktree or pull request, and when it last replied. The tool counts, the background jobs and the section each thread sits in are staged." alt="MindRoom Chat in the Compact view with a Working section of six thread cards, a Needs you section of four and the start of a Later section. Each card has a title, a line about the agent's last action, a worktree or pull request badge and tags." >}}

## Thirty terminal windows

In August 2025 I described [working on 6 features at once]({{< ref "/post/agentic-coding" >}}): one terminal tab per feature, and a round through all of them every 10 to 15 minutes.
In January I made that setup one command with [`agent-cli dev`]({{< ref "/post/parallel-agentic-coding" >}}), which creates a [git worktree]({{< ref "/post/git-worktree" >}}) and opens a new tab with an agent already working in it.

That worked because a task took minutes.
I'd start one, move to the next tab, and by the time I came back around there was something to review.

Then the models got better and I handed over more scope per task.
The more I hand off, the longer an agent takes to finish.
So I started doing more things in parallel.
Keeping track of what's running and what's done becomes exceedingly hard in the terminal.
Thirty windows all look the same, and the only way to find out what one of them is doing is to open it and read.

I experimented with [cmux](https://cmux.com) for a month or two to improve oversight and clarity.
It's a terminal built for this, with vertical tabs and notifications for coding agents.

## The apps in between

My next step was the {{< tooltip text="OpenAI's desktop app for Codex, its coding agent. It shows several agent sessions next to each other in one window." >}}Codex desktop app{{< /tooltip >}}.
I started using it around GPT-5.2, when the OpenAI models were, at least in my opinion, undoubtedly better.
I absolutely loved it.
It was a massive bump in my productivity, because it gave a much clearer view of what was running and what was done.

Then {{< tooltip text="Claude Fable, a model family from Anthropic." >}}Fable{{< /tooltip >}} came out, and it felt better than the OpenAI models, so I went back to the {{< tooltip text="Anthropic's coding agent, which runs in a terminal." >}}Claude Code{{< /tooltip >}} CLI.
Switching back and forth between the Codex desktop app and the Claude CLI wasn't optimal, so I looked for something that unified the two.
I found [T3 Code](https://github.com/pingdotgg/t3code), which I really adored as well.
It calls itself "the open-source control plane for coding agents".[^t3]
I think of it as a {{< tooltip text="The program around a model that turns it into an agent. It sends the prompts, gives the model tools such as a shell and a file editor, and runs what the model asks for." >}}harness{{< /tooltip >}} for harnesses: it runs the original Claude Code and Codex, and shows them in one web interface.

T3 Code wasn't perfect for massively parallel work either.
With more than twenty concurrent sessions, my relatively beefy AI machine started to struggle.
The machine wasn't overloaded.
As far as I could tell, too many database writes went through a single thread.
Opening a long thread took several seconds.
And threads with background tasks still running showed up as idle, as if they needed me, which added to the confusion.

The awesome bit is that T3 Code is completely open source.
So I ported my favorite functionality and its best ideas to MindRoom, and fixed the things that annoyed me.

## Why I stayed with the native harnesses

All of these tools have one thing in common: they run the coding harness of the company that made the model.
The Codex app runs Codex, Claude Code is Anthropic's own, and T3 Code drives both.

I stayed with them because I felt a model must just work better in its native harness, since that's what it was trained with.
It's why I wrote seven weeks ago that ["for writing code, dedicated tools like Claude Code and Codex are better"]({{< ref "/post/mindroom-at-ionq" >}}).

Then I [tested that belief]({{< ref "/post/native-harness-tools" >}}).
Over {{< tooltip text="12 short terminal tasks, such as writing a report from a CSV file or fixing failing tests, each run many times per model and per set of tools." >}}more than 4,000 runs{{< /tooltip >}} of short terminal tasks, giving a model the tools of its own harness made only one model clearly more efficient.[^harness]
What did matter was how much the agent sends with every request: a minimal agent with one shell tool and a 12-line prompt used 58 to 76% fewer {{< tooltip text="The pieces of text a model reads and writes, each about three quarters of a word. Providers bill per token." >}}tokens{{< /tooltip >}} than MindRoom's standard agent.

That got me over the mental block.
If the native harness doesn't buy much, my agents can just as well work in the place where I already keep everything else.
Most of my coding now happens in MindRoom threads.

## Tasks that run for a day

Two things changed how long an agent can work without me.

The first is the models.
With Opus 5.5 and Fable 5.2 I had another massive boost in productivity, simply because they can handle such an insanely large scope right now.

The second is my skills, which are public as [baspowers](https://github.com/basnijholt/baspowers).
They dictate a workflow where the agent follows established good engineering practices: it writes a spec and a plan, and it works {{< tooltip text="Test-driven development: first write a test that fails because of the bug or the missing feature, then write the code that makes it pass." >}}test-first{{< /tooltip >}}.
But instead of involving me whenever something is ambiguous, it cross-checks with another {{< tooltip text="One of the most capable models available at that moment." >}}frontier model{{< /tooltip >}}, like {{< tooltip text="GPT-6 Astra, a model from OpenAI." >}}Astra{{< /tooltip >}}.
Only if that doesn't resolve it does it involve me.[^crossmodel]

This is what reaches me, replayed from a real thread.
Fable and Astra disagreed about a design choice, so the agent stopped and asked me.
It lists both options and says which one it recommends.
I answer with one click, and the agent goes on.

{{< video autoplay="true" loop="true" controls="yes" src="agent-question.mp4" >}}

I wrote last month that [you don't need skills to start with AI]({{< ref "/post/how-to-start-with-ai" >}}), and I still think so.
In one test, agents wrote a failing test before fixing a bug in 0 of 32 runs without my test-driven development skill, and in 32 of 32 runs with it.
As I wrote there: "That matters when agents run on their own for hours."

The result is that any task I start might run from just an hour to more than a day autonomously.
That means I can run fifteen parallel sessions extremely comfortably.
After a good night's sleep, with a lot of focus, I'm able to orchestrate forty.
That works simply because things take a while to execute, and because I can see what's going on.

One session is often more than one agent.
In this clip the agent has two reviews running in the background, each by a different model.
The bar under the thread lists every run with its tool calls, tokens, cost and time.
A click on a run opens what that sub-agent is doing.
The thread is a real one, and the two runs and their numbers are made up for the demo.

{{< video autoplay="true" loop="true" controls="yes" src="sub-agents.mp4" >}}

## About those lines of code

Programming is my biggest passion.
Before AI coding got really good, I looked at every line of my code, and every comma mattered to me.
I'd often lie in bed scrolling through my own code in the GitHub app, trying to find a place where I could make it a little cleaner, more {{< tooltip text="Don't repeat yourself: every piece of logic lives in one place." >}}DRY{{< /tooltip >}} or more elegant.

In January I gave a presentation to a group of people who weren't very AI native.
I told them that I had written about a million lines of code in the last year, and I felt slightly embarrassed to say that.
In the first twenty days of this month, the count is {{< tooltip text="3,966,635 lines added plus deleted from November 1 through November 20, 2026." >}}almost four million{{< /tooltip >}}.

{{< figure src="lines-per-month.svg" caption="Lines added and deleted per month in my merged pull requests and direct commits, counted by trueloc on November 20, 2026. November 2026 is a partial month." alt="Bar chart of lines touched per month from November 2024 to November 2026. Most months before July 2025 are under 100,000. September and October 2026 are about 2.5 and 2.8 million, and the first twenty days of November 2026 are almost 4 million." >}}

I strongly feel that lines of code is not a measure of quality at all.
It's like measuring how good you are at building airplanes by how much weight you added to them, a comparison that's usually attributed to Bill Gates.[^gates]

The numbers come from [trueloc](https://github.com/basnijholt/trueloc), a tool of mine that counts every line added and deleted in every commit of my merged {{< tooltip text="A proposed change to a repository on GitHub. It gets reviewed and tested, and merging it puts the change into the main code." >}}pull requests{{< /tooltip >}}, plus my direct commits.[^trueloc]
That includes churn, generated files, and code that an agent wrote and then rewrote.
From November 2024 through October 2025 that was {{< tooltip text="1,380,174 lines added plus deleted." >}}about 1.4 million lines{{< /tooltip >}} in 848 merged pull requests.
In the twelve months after that it was {{< tooltip text="9,957,695 lines added plus deleted." >}}about 10 million lines{{< /tooltip >}} in 5,148 pull requests, and {{< tooltip text="6,707,616 of 9,957,695 lines, which is 67%." >}}about two thirds{{< /tooltip >}} of those lines are in code files.[^codefiles]
November looks even bigger than it is: {{< tooltip text="About 1.69 million of 3.97 million lines, which is 43%. This is an estimate from the per-commit data." >}}more than 40%{{< /tooltip >}} of it is the same commits counted again in a stack of six pull requests, plus files I moved from one repository to another.[^november]

So read the chart as the amount of work in flight, because that's what I had to keep track of.

## A thread is the agent's context window

MindRoom started out as just a basic chat interface.
My idea was that every conversation in a room happens in a thread, and the thread is the {{< tooltip text="The amount of text a model can take in at once. Everything the agent knows about the task has to fit in it." >}}context window{{< /tooltip >}} that the agent sees.
The agent has tools to look into other threads if it wants to.
But its context is just that one thread, which is {{< tooltip text="The older part of the conversation is replaced by a summary, so the rest fits again." >}}compacted{{< /tooltip >}} once the context window fills up.

So one task is one thread, and a room is a list of tasks.
For coding, each thread also gets its own {{< tooltip text="A second working copy of the same repository, on its own branch and in its own folder, so several agents can change code without touching each other's files." >}}git worktree{{< /tooltip >}}, and the pull requests the agent opens are linked to the thread.

## From first messages to four sections

The room view went through six versions.
You can click through them here, in a small mock-up of the same room.

<div class="mr-room-evolution"></div>

**First messages.**
In a typical chat room, like Slack, you see the first message of a thread and then you click into it.
Maybe you see a couple of avatars of who's active in the thread.
But that first message isn't always indicative of what the thread is about.
"Ok next thing, see what we discussed" tells me nothing an hour later.

**Titles.**
So I added AI-generated titles to every thread and showed those in the room.
A title is a few words that say what the thread is actually about.

**Resolve.**
Then I realized it was hard to scroll through a room and know which thread is active, which one is done, and which one I was completely done with.
So I added a sense of status.
I can resolve a thread, which means I'm completely done with it, and it turns green.

**Sort and filter.**
I added filters, so I could hide the resolved threads, and filter on streaming or not, on scheduled or not, and more.
Now I could sort on latest message, filter out the resolved threads, and know from the room which ones I had to address.

**Cards.**
That view still had a lot of cruft that obscured what's important.
I'd much rather see the AI-generated title, who's currently working, and when the last reply was.
So I came up with the Compact view, where every thread is one card.
A card has three lines: the title and the time of the last reply, then what the agent is doing right now or the start of its last answer, and then who's in the thread, its git worktree or pull request, its tags, and the number of replies.

**Sections.**
Then, inspired by the sections in T3 Code, I added that type of grouping too.[^sections]
The cards now sit under four headers:

- **Needs you:** the agent finished or asked me something, and nothing is running in the thread.
- **Working:** the agent is replying, or a {{< tooltip text="A second agent that the main agent starts for one part of the task. It works in its own context and reports back." >}}sub-agent{{< /tooltip >}} or background job in the thread is still running.
- **Later:** the thread is snoozed or has something scheduled, so it comes back on its own.
- **Done:** I resolved it.

A thread with a background job counts as Working.
That's the fix for the thing that confused me in T3 Code: a thread that is still working in the background no longer shows up as needing me.

The mock-up uses demo data.
The clips below are the real MindRoom Chat, in a demo copy of my room that replays real threads of mine.
The text in those threads is real.
The tool calls, the background jobs and the numbers next to them are made up.

Here I fold and open the sections, show only the unresolved threads, and turn the grouping off and on.

{{< video autoplay="true" loop="true" controls="yes" src="room-sections.mp4" >}}

And this is one request from start to finish.
I type it in the room, and its card sits under Working while the agent replies.
Once the agent is done, the card moves to Needs you.

{{< video autoplay="true" loop="true" controls="yes" src="request-to-needs-you.mp4" >}}

{{< figure src="room-later-done.png" caption="Later holds the threads that come back on their own: one with a task scheduled in 24 minutes, and two that are snoozed until the next morning. Done holds the threads I resolved." alt="The Later section with three thread cards, one with a scheduled time and two marked as snoozed until November 21, above a Done section with green resolved cards." >}}

This small change in organization also resulted in a massive productivity boost, and it's the interface I'm using right now.

The older view is still there.
These two screenshots are the real MindRoom Chat with a small scripted room: the Threads view, which shows the first message of every thread with its title and reply count, and the same room in the Compact view with sections.

{{< figure src="threads-view.png" caption="The Threads view of a demo room in MindRoom Chat: every thread shows its first message, with the AI-generated title and the number of replies under it. The room and its people are scripted demo content." alt="MindRoom Chat showing a room timeline with four first messages, each followed by an AI-generated thread summary and a replies badge." >}}

{{< figure src="compact-sections.png" caption="The same demo room in the Compact view with sections: two threads under Working, six under Needs you." alt="MindRoom Chat showing thread cards grouped under a Working section with two cards and a Needs you section with six cards." >}}

## Hiding what you don't need to see

I believe that to be productive with AI, you should be exposed to its raw power.
It should be possible to see the agent's reasoning, to see every tool call it makes, and to read the actual output of the model.

But nobody should be overwhelmed by it.
In many cases you don't care how the agent got there, and some people will never care.

So while an agent works, MindRoom Chat shows its reasoning and its tool calls as they happen.
When it's fully done, all of that folds away behind one row, and what stays is its conclusion.
One click opens it again.

<div class="mr-fold-demo"></div>

And this is the real client, with a question I really asked and the agent's real answer.
The answer streams in while the agent works, and its work folds behind one row when it's done.
One click opens that row again.
The tool calls behind the row are made up for the demo.

{{< video autoplay="true" loop="true" controls="yes" src="reply-streams-and-folds.mp4" >}}

What you read is still the direct output of the model.
The conclusion isn't a summary written by a different model, and the folded work is still there when you want it.
The folding is another idea I took from T3 Code, where a finished turn collapses into a "Worked for" row.[^fold]

## What I took from T3 Code

The sections and the folded replies aren't the only things I ported.

- The model picker has an Effort column for the {{< tooltip text="How much a model thinks before it answers. Higher levels are slower and cost more, and they help on hard problems." >}}reasoning level{{< /tooltip >}}.[^effort]
- Pull requests show up as cards, with a side panel that has the changed files and their diffs.

Here it is on a merged pull request of MindRoom Chat.
The badge on a card has a hover card, and a click opens the panel next to the thread.
The panel has the summary, the file tree and the diffs.
What it shows is what GitHub returned for the real pull request.

{{< video autoplay="true" loop="true" controls="yes" src="pull-request-panel.mp4" >}}

That pull request panel isn't part of the chat app itself.
It's a [plugin](https://github.com/mindroom-ai/pull-request-client-plugin), because MindRoom Chat knows nothing about git.
The chat app only knows about rooms, threads and agents, and the coding parts sit on top of that.

I could change the room view this often because [I own the client]({{< ref "/post/roll-your-own-fork-the-rest" >}}).
[MindRoom Chat](https://github.com/mindroom-ai/mindroom-chat) is open source as well, under {{< tooltip text="A permissive open-source license: you can use, change and redistribute the code, also commercially." >}}Apache-2.0{{< /tooltip >}}.
If my four sections don't fit how you work, you can change them, the same way I took what I liked from T3 Code.

## What the numbers do and don't show

The chart is not a measure of good code, as I said above.
It can't credit MindRoom either.
The big jump is in September 2026, which is when [GPT-6 Astra and Claude Opus 5.5 came out]({{< ref "/post/self-hosting-ai-is-not-cheaper" >}}).
The sections landed on November 17, three days before I wrote this.
So the chart shows the problem I had, which is far more work in flight than I could follow in terminal tabs.

Forty sessions is a peak, and fifteen is a normal day.
And I built the tool I'm praising, so of course it fits me.
I loved the Codex app and I adored T3 Code before it.
I also wrote last month that ["most new AI tooling is not very good, and MindRoom may well be included"]({{< ref "/post/roll-your-own-fork-the-rest" >}}).

[TODO Bas: what you read before a merge now, and who presses merge.]
[TODO Bas: what fifteen sessions cost per month.]
[TODO Bas: one run that went wrong.]

## Conclusion

I still have iTerm2 open all day.
A year ago I cycled through five or six tabs every 10 to 15 minutes to see which agent was done.
Now I open one room and look at Needs you.

You can try the same view on [mindroom.chat](https://mindroom.chat), and the [showcase](https://docs.mindroom.chat/showcase/) has recordings of what else it does.

I also wrote that [with every new model, my workflow changes]({{< ref "/post/how-to-start-with-ai" >}}).
So this is how I develop right now, and I expect it to look different in a few months.

[^t3]: From the README of [pingdotgg/t3code](https://github.com/pingdotgg/t3code), read on November 20, 2026. T3 Code is MIT licensed.

[^harness]: That model was Claude Opus 4.8, which did 17% less work and used 19% fewer tokens with Claude Code's tools. GPT-6 Astra and Sol used 43 to 59% more tokens with the tools of their own harness.

[^crossmodel]: The skill is [`consulting-cross-model`](https://github.com/basnijholt/baspowers/tree/main/skills/consulting-cross-model). Claude asks GPT-6 Astra, and Codex asks Claude Opus 5.5.

[^gates]: The line that's usually quoted is "Measuring programming progress by lines of code is like measuring aircraft building progress by weight." I couldn't find a primary source for it.

[^trueloc]: Counted on November 20, 2026 with `uvx trueloc count basnijholt --since 2024-11-01 --until 2026-11-20 --json`, run with my own GitHub login, so it covers every repository that account can see. Over the whole window that's 7,630 merged pull requests and 12,233 direct commits with 15,304,504 lines: 10,886,530 added and 4,417,974 deleted. September 2026 has 2,459,033 lines, October has 2,829,709, and November up to the 20th has 3,966,635.

[^codefiles]: Code files are the ones with one of 26 source extensions, such as `.py`, `.ts`, `.tsx`, `.rs`, `.nix`, `.sh` and `.css`. In the last twelve months that's 6,707,616 of 9,957,695 lines (67%), and the rest is mostly JSON (11.7%), Markdown (9.2%) and SVG (4.4%). In the twelve months before, it was 832,382 of 1,380,174 lines (60%).

[^november]: Six pull requests that merged on November 11 count for 1,133,900 lines here, while their own diffs on GitHub add up to 3,143 lines. Each branch in that stack carried the commits of the branches below it. Files moved between repositories add another 556,672 lines. Together that's 1,690,572 of 3,966,635 lines.

[^sections]: The counted Needs you, Working, Later and Done filters are [mindroom-chat #436](https://github.com/mindroom-ai/mindroom-chat/pull/436), and the sections in the Compact view are [#448](https://github.com/mindroom-ai/mindroom-chat/pull/448). Both merged on November 17, 2026 (UTC).

[^fold]: [mindroom-chat #419](https://github.com/mindroom-ai/mindroom-chat/pull/419) folds a finished reply behind the "Worked for" row, and [#670](https://github.com/mindroom-ai/mindroom-chat/pull/670) does that for every finished reply with a tool call.

[^effort]: [mindroom-chat #562](https://github.com/mindroom-ai/mindroom-chat/pull/562).

<script src="mindroom-mock.js" defer></script>
