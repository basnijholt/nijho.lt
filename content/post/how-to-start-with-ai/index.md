---
title: "How to start with AI"
subtitle: "Yes, I am actually still getting this question. You don't need skills or an AGENTS.md, you just need to ask questions."
summary: "There is a lot of noise about elaborate AI workflows that 99% of people don't need. Install it, use the best model, and ask it everything. The rest can come later, or never."
projects: []
date: "2026-10-08T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - ai
  - agentic-coding
  - claude-code
  - productivity

categories:
  - development
  - level:beginner
---

I am honestly surprised that this is still a question.
But I am literally still getting it: "how do I start with AI?" or "how do I start with coding agents?"

There is a lot of noise, and a lot of pretense, about very specific workflows.
Multi-agent loops, agent and sub-agent graphs, carefully tuned rule files.
None of that is useful for 99% of people.

You don't need skills.
You don't need an `AGENTS.md`.
You don't need anything except the app itself.
You just need to ask questions, and be critical of the answers.

Most of my examples come from code, because that is where I use AI the most.
But the advice is the same whether you write software or not.

{{% callout note %}}
**TL;DR**
1. Install Claude or ChatGPT. The app if you want to chat, Claude Code or Codex in your terminal if you write code. It takes 30 seconds. No setup.
2. Ask it everything, and be critical of what comes back. If it could do something itself, let it.
3. Use the best model. Cheap models are often not cheaper on real work.
4. Trust it in proportion to how measurable the outcome is.
5. Have its work reviewed in a fresh context, by the same model and by another one. Watch for scope creep.
6. Skills, multi-agent loops and the rest come later, if ever.
{{% /callout %}}

{{< toc >}}

## 1. Install it, and that's it

Getting started is downloading the ChatGPT or Claude app, or literally a one-liner to install Claude Code or Codex if you write code.
Maybe you log in, or click a button to get access.
That's the whole setup.
"I need to take time to learn how to use it" was never a real barrier.
The interface is trivial: text in, text out.
Everything else is optional.

I open agents in projects of mine that have never seen any AI, and seconds later they know the entire thing.
The frontier models have much better taste than they used to.
In an established codebase they just follow the existing style.
If you point one at a codebase that is a bunch of crap, it might still produce a bunch of crap.
But even there it does better than it used to.

I used to give different advice.
In [On agentic coding]({{< ref "/post/agentic-coding" >}}), a year ago, I told you to create a `CLAUDE.md` in every project root with your preferences.
(Today that would be an `AGENTS.md`, which all the major agents read.)
I still use them, but not everywhere, and you don't need one to get started.
There is even [research](https://arxiv.org/abs/2602.11988) showing that repository-level context files don't generally improve the task success rate of coding agents, while raising the cost by over 20%.
They help when you have non-standard practices the agent can't guess.
A list of standard rules or an overview of the repository does not.

## 2. Ask it everything 🥩

The real change is a mindset, not a tool.

When you run into a problem, the old reflex is to Google it.
The new reflex is to ask the AI about everything.

When the agent says "now you need to run the tests," no.
Everything it can do, you let it do.
If the AI tells you what to do when it could do it itself, you are just a **meat proxy**, and you are wasting your own time.

It is genuinely absurd how good it has gotten.
My mom sent me a photo of [MindRoom]({{< ref "/post/mindroom" >}}) crashing in her browser, a screen full of minified JavaScript.
I sent the photo to my agent.
The answer: the Google Translate extension was interfering with the page.
It wrote the fix too.

The people who still don't use it are, I think, in one of two groups.
Some had a bad experience once, years ago, and never tried again.
That experience is badly out of date.
Others, and I suspect it's a large group, avoid AI on principle.
This post won't change their minds, but it might make starting easier for everyone else.

## 3. Use the best model

Another very common question: shouldn't I use a cheaper model to save money?
When you're starting out, my answer is to use the best one.

**Your time almost certainly costs more than the tokens.**
For an engineer, it certainly does.
Continuously deciding "do I need the smartest model for this, or the weakest one?" is itself not efficient.
A useful check when a session costs $50: what would this have cost you without AI?
If you would have done it anyway, the answer is almost always way more.
(If you only did it because AI made it possible, the comparison gets harder.)

**Cheaper per token is not cheaper per task.**
A cheaper model does not necessarily get to the solution in fewer tokens.
On hard problems it typically uses way more.

My favorite way to see this is [Artificial Analysis](https://artificialanalysis.ai/)'s intelligence index versus **cost per task**, which accounts for both the price and how many tokens a model burns.
Here are Claude Opus 5.5 and Claude Sonnet 5.5 at each reasoning effort:

{{< plot name="costPerTask" caption="Artificial Analysis Intelligence Index versus the average cost of one of its tasks, for each reasoning effort, as of 2026-10-08. Hover for the output tokens per task." >}}

Sonnet costs half as much per token.
But at max effort it scores 56, the same as Opus at xhigh, and costs $5.46 per task against Opus's $3.46.
It just uses a lot more tokens: about 197,000 output tokens per task versus 66,000.
Above a score of about 47, the Opus line is both higher and further to the left.

So for simple tasks, the cheaper model is cheaper.
For difficult work, it is sometimes the same price, often takes longer, and can cost more, because it burns through so many more tokens.
And a worse answer gets more expensive later, because somebody has to fix it.

**Don't put reasoning effort on max.**
Going from xhigh to max on Opus buys 1.6 points for 73% more money.
On Sonnet it is 2.7 times the cost.
I default to xhigh myself, which is probably overkill for half of what I do.

## 4. Decide how much to trust it

When I started, I read every single line of code it wrote and had so many comments.
By now I trust the output much more, because I've seen it.
The scope I hand over has grown with that trust.
[Canvases in MindRoom Chat](https://chat.mindroom.chat/canvases/), interactive pages an agent can show you next to the conversation, felt like a half-year project.
I built it in a day, on my phone.

How closely I look depends on how important the result is and how measurable it is.
The core of a project, the part everything relies on: there I want to understand precisely what's going on.
An integration that fetches my email from some external API, something written a million times whose outcome is easy to check: I don't read the code.
When I see that it works, I believe it.
The same goes outside code: an answer you can check in a minute needs less scrutiny than one you can't check at all.

{{< figure src="trust-tree.svg" alt="A tree with three large blue core nodes at the top and six small grey leaf nodes at the bottom. The core is labeled: everything depends on it, read it and understand it. The leaves are labeled: nothing depends on them, check that they work." >}}

This is also why expertise still matters.
When I scroll through a large piece of code, I can judge its complexity at a glance.
When it explains something in a field I know, I can tell when it's wrong and call bullshit.
In a field I don't know, I can't, so I spend much more time validating to reach the same level of trust.
Match your scrutiny to your expertise.

## 5. Talk to it, then make it review itself

I start by telling it what I want, usually by voice.
I just ramble.
It is so good at language that even when I go off track and talk incoherently, it almost always understands what I mean.
And sometimes it pushes back: "I understand what you mean, but that approach is bad because of this, I'd do it this way."
Sometimes it says we could do it either way, and I say: let's try both.

In almost all cases, AI can now deliver what you asked for in a single prompt, and it will actually work.
The question is whether it's actually good, and whether it meets your standards.
So before you accept anything, have it reviewed.

For me, the review has to come from a fresh context that never saw the conversation that produced the work.
A new session, or a sub-agent, that only sees the result.
That can be the same model or a different one.
I do both: the same model in a fresh context, and other models, until they agree it's good.
That sounds like a lot of setup, but it isn't.
In a chat app, it can be as simple as pasting the answer into a new chat, or into the other company's app, and asking what's wrong with it.

Whatever you use, also tell it to **be mindful of scope creep.**
A review will always find something.
Very often it's an edge case that looks real in isolation but can never happen in your actual situation.
Ask whether each finding is realistic before you let it build more.

## 6. What about skills and multi-agent loops?

Yes, I use those things.
No, you don't need them to start.

I never sit down and think "now I need to develop a skill."
I do something with the agent a couple of times, realize I'm going to keep repeating it, and then say: "let's make a skill out of this, and make it self-evolving."
A skill is just a procedure you want to repeat.
You only know what to put in it after you've repeated it.
(In [MindRoom](https://docs.mindroom.chat/skills/#automatic-skill-learning), an agent can even do this on its own: with automatic skill learning turned on, it reviews its recent work in the background and turns repeated workflows into skills.)

My own set of skills is public as [baspowers](https://github.com/basnijholt/baspowers), which started as a fork of [superpowers](https://github.com/obra/superpowers).
Some of its skills came from mining my own agent history of more than ten thousand conversations for procedures I kept repeating, then A/B testing each one with and without the skill.
An A/B test sounds like a lot of work, but you can ask the agent to run it for you, and tell it which other models to test with.
Four of the ten candidates were dropped because the agents already did the right thing without them.
The rule I ended up with: **keep only skills that change behavior.**

Sometimes they really do.
In one test, agents wrote a failing test before fixing a bug in 0 of 32 runs without my [test-driven development skill](https://github.com/basnijholt/baspowers/tree/main/skills/test-driven-development), and in 32 of 32 runs with it.
That matters when agents run on their own for hours.
It does not matter for your first week of asking questions.

I also run cross-model reviews in loops, which is useful when I have ten things running at once.
But I keep updating those setups, because each new model makes parts of them unnecessary.
My [PR review skill](https://github.com/mindroom-ai/mindroom/blob/main/.claude/skills/pr-review/SKILL.md) used to make agents fix every nitpick.
Now the models are good enough that it will forever find something, even after a hundred rounds, so I had to change it: it now only blocks on issues with a realistic scenario.

That is the problem with copying someone's elaborate workflow.
It encodes the weaknesses of last year's models and the habits of one person.
Start with nothing, and add things once you notice you keep repeating them.

## 7. If you write code

A few things only apply to software.

### Tests are cheap now, so ask for them

"Set up the actual live system, end to end (don't touch production!), run it with real data, crash it at different points in the middle."
All the random things you would check yourself if you had infinite time.
Have it write a lot of tests.
More tests is better, even when some have limited value.
What I care about is that the source code itself is clean.

### The code is the spec

A lot of people will disagree here, but I throw away design docs.
What came out in the end was never what the doc said anyway.
The code and the tests are the specification, because that's also what the agent reads.
The only thing I keep is what the code can't say: why something was done a certain way.
Documentation that conflicts with the code is the worst: the agent will start changing your code to match the docs without you noticing.

### Review against your own criteria

The questions I make it answer about its own work:

- Is the code clean?
- Does it fit well within the existing architecture?
- Does it repeat itself?
- Is it overengineered? Keep it simple, stupid.

### Cross-model review needs two installs

As long as you have both Codex and Claude Code installed, you are essentially ready.
Just tell the agent: "have Codex review this in a separate session and address what it finds."
It can usually figure out how to call the other command-line tool on its own.
I personally built a worktree orchestration tool for this, [`agent-cli dev`]({{< ref "/post/parallel-agentic-coding" >}}), which comes with a skill that teaches the agent to use it.
But honestly, that is not necessary anymore nowadays.

### A good AI engineer is just a good engineer

People ask me what makes a good agentic engineer.
I've been saying the same thing for a long time: somebody who is literally a good engineer.
Good engineering practices never went away.
They are more important than ever: test-driven development, building things at the right level of abstraction, a proper architecture.

I think of engineering skill as a scale that runs from negative to positive.
A good engineer removes work for others.
A bad engineer creates work for others.
Give the bad engineer AI, and they multiply their bad output, because AI is a multiplier.

Before AI, you could spend a year writing a few thousand lines of code, maybe a couple tens of thousands at most.
You were intimately familiar with all of it, so you could get away with a somewhat worse architecture.
Now you can produce a million lines of code in a year.[^loc]
There is no possible way you can keep up with all of it.
If you want to build something lasting and robust, you need proper foundations.
And that is where your opinions matter.
You don't need any setup to start, but you do need taste to build something that lasts.
(I made a related point a year ago in [On agentic coding]({{< ref "/post/agentic-coding" >}}): AI amplifies the experience you already have.)

### Your role changed, it didn't disappear

Some software engineers feel personally attacked by all this.
I think you have to get over yourself.
Your secret sauce was never knowing the syntax really well.
Now you need to know what to build, and how it should be built.

And you need to be strict.
You can produce thousands of lines a day, so be thoughtful about whether you want them in your codebase forever.
Changing the color of a button takes one prompt.
A difficult system needs more rigor, which means understanding the architecture and what it implies instead of reading every line.

## This post has an expiry date

Right now I'd tell you to use Claude Opus 5.5.
Just two weeks ago I was telling people to use GPT-6 Astra.
Things change continuously, and in most cases you'll be fine with either.

I'm also sure that a few weeks from now, I will no longer accept the model I'm praising today.
Not because it can't do the amazing things it does now.
But because the next one will do even more amazing things that it can't.
With every new model, my workflow changes, and the amount of scope I hand over per task grows dramatically.

That's why I don't recommend building an elaborate setup first.
Every skill, rule file and agent graph is tuned to the limitations of the model you have today.
Those limitations are gone in a few months, and then the setup is dead weight.
Asking it things is the one habit that survives every model change.

Install it today, use the best model, and ask it everything, including whether its own work is any good.
The rest is optional, and probably temporary.

[^loc]: I wrote about 4.5 million lines of code this year, as counted by [trueloc](https://github.com/basnijholt/trueloc), another tool of mine that counts every line added across all commits in my pull requests.
