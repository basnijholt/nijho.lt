---
title: "How to start with AI 🤖"
subtitle: "Yes, I am actually still getting this question. You don't need skills or an AGENTS.md, you just need to ask questions."
summary: "There is a lot of noise about elaborate AI workflows that 99% of people don't need. Install it, use the best model, and ask it everything. The rest can come later, or never."
projects: []
date: "2026-10-08T00:00:00Z"
draft: true
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

My answer is simpler than people expect.
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
2. Ask it everything, and be critical of what comes back. If it could do something itself and tells you to do it, you are a meat proxy.
3. Use the best model. Cheap models are often not cheaper on real work.
4. Trust it in proportion to how measurable the outcome is.
5. Make it review its own work and get a second opinion from another model. Watch for scope creep.
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

I should admit that I used to give different advice.
In [On agentic coding]({{< ref "/post/agentic-coding" >}}), a year ago, I told you to create a `CLAUDE.md` in every project root with your preferences.
(Today that would be an `AGENTS.md`, which all the major agents read.)
I still use them, but not everywhere, and you don't need one to get started.
There is even [research](https://arxiv.org/abs/2602.11988) showing that repository-level context files tend to *lower* the task success rate of coding agents compared to having none, while making each task more expensive.
Files that an LLM generated for itself did worst.
There is no secret sauce.

## 2. Ask it everything 🥩

The real change is a mindset, not a tool.

When you run into a problem, the old reflex is to Google it.
The new reflex is to ask the AI.
For everything.

When the agent says "now you need to run the tests," no.
Everything it can do, you let it do.
If the AI tells you what to do when it could do it itself, you are just a **meat proxy**, and you are wasting your own time.

It is genuinely absurd how good it has gotten.
My mom sent me a photo of [MindRoom]({{< ref "/post/mindroom" >}}) crashing in her browser, a screen full of minified JavaScript.
I sent the photo to my agent.
The answer: the Google Translate extension was interfering with the page.

Many people who still haven't tried it tried GPT-4 once, it was wrong about something, and that became their mental model.
That mental model is years out of date.

## 3. Use the best model 💸

The most common follow-up question: shouldn't I use a cheaper model to save money?
When you're starting out, my answer is to use the best one.

**Your time costs more than the tokens.**
Continuously deciding "do I need the smartest model for this, or the weakest one?" is itself not efficient.
A useful check when a session costs $50: how long would this have taken you without AI?
Often the honest answer is that you would not have done it at all.

**Cheaper per token is not cheaper per task.**
A cheaper model does not necessarily get to the solution in fewer tokens.
On hard problems it typically uses way more.

My favorite plot for this is [Artificial Analysis](https://artificialanalysis.ai/)'s intelligence index versus **cost per task**, which accounts for both price and how many tokens a model burns.
When I last looked, Sonnet scored about 56 against Opus at max effort's 58, and per task they cost roughly the same, maybe 10% apart.
Even though Sonnet is about five times cheaper per token.
It just used a lot more tokens: around 200,000 output tokens versus about 120,000.

So for simple tasks, the cheaper model is cheaper.
For difficult work, it is often the same price or more expensive.
And a worse answer gets more expensive later, because somebody has to fix it.

The one knob worth turning is **reasoning effort**.
The highest level can cost almost twice as much for a marginal gain.
Calculating some usage statistics does not need the highest level of intelligence.
Designing a brand new feature does.

## 4. Decide how much to trust it 🔍

When I started, I read every single line of code it wrote and had so many comments.
By now I trust the output much more, because I've seen it.

How closely I look depends on how important the result is and how measurable it is.
The core of a project, the part everything relies on: there I want to understand precisely what's going on.
An integration that fetches my email from some external API, something written a million times whose outcome is easy to check: I don't read the code.
When I see that it works, I believe it.
The same goes outside code: an answer you can check in a minute needs less scrutiny than one you can't check at all.

## 5. Talk to it, then make it review itself 🗣️

I start by telling it what I want, usually by voice.
I just ramble.
Because it is so good at language, even when I go off track it pushes back: "I understand what you mean, but that approach is bad because of this, I'd do it this way."
Sometimes it says we could do it either way, and I say: let's try both.

It will do what you ask, and the result will look fine.
The question is whether it's good.
So before you accept anything, ask it to review its own work.

The key part for me: I don't let one model be the only judge of its own work.
I have other models review it, against the same criteria, until they agree it's good.
That sounds like a lot of setup.
It isn't magic either.
In a chat app, that can be as simple as pasting the answer into the other company's app and asking what's wrong with it.

And one instruction that matters more than the rest: **be mindful of scope creep.**
A review will always find something.
Very often it's an edge case that looks real in isolation but can never happen in your actual situation.
Ask whether each finding is realistic before you let it build more.

## 6. What about skills and multi-agent loops? 🔁

Yes, I use those things.
No, you don't need them to start.

I never sit down and think "now I need to develop a skill."
I do something with the agent a couple of times, realize I'm going to keep repeating it, and then say: "let's make a skill out of this, and make it self-evolving."
A skill is just a procedure you want to repeat.
You only know what to put in it after you've repeated it.

My own set is public as [baspowers](https://github.com/basnijholt/baspowers), which started as a fork of [superpowers](https://github.com/obra/superpowers).
Some of its skills came from mining my own agent history for procedures I kept repeating, then A/B testing each one with and without the skill.
Four of the ten candidates were dropped because the agents already did the right thing without them.
The rule I ended up with: **keep only skills that change behavior.**

Sometimes they really do.
In one test, agents wrote a failing test before fixing a bug in 0 of 32 runs without my test-driven development skill, and in 32 of 32 runs with it.
That matters when agents run on their own for hours.
It does not matter for your first week of asking questions.

I also run cross-model reviews in loops, which is useful when I have ten things running at once.
But I keep updating those setups, because each new model makes parts of them unnecessary.
My PR review skill used to make agents fix every nitpick.
Now the models are good enough that it will forever find something, even after a hundred rounds, so I had to change it.

That's the honest problem with copying someone's elaborate workflow.
It encodes the weaknesses of last year's models and the habits of one person.
Start with nothing, and let your own repetition tell you what to add.

## 7. If you write code 💻

A few things only apply to software.

**Tests are cheap now, so ask for them.**
"Set up the entire system, run it with real data, don't touch production, crash it at different points in the middle."
All the random things you would check yourself if you had infinite time.
Have it write a lot of tests.
More tests is better, even when some have limited value.
What I care about is that the source code itself is clean.

**The code is the spec.**
A lot of people will disagree here, but I throw away design docs.
What came out in the end was never what the doc said anyway.
The code and the tests are the specification, because that's also what the agent reads.
Documentation that conflicts with the code is the worst: the agent will start changing your code to match the docs without you noticing.

**Review against your own criteria.**
The questions I make it answer about its own work:

- Is the code clean?
- Does it fit well within the existing architecture?
- Does it repeat itself?
- Is it overengineered? Keep it simple, stupid.

**Cross-model review needs two installs.**
As long as you have both Codex and Claude Code installed, you are essentially ready.
Just tell the agent: "have Codex review this in a separate session and address what it finds."
It can usually figure out how to call the other command-line tool on its own.
I personally built a worktree orchestration tool for this, [`agent-cli dev`]({{< ref "/post/parallel-agentic-coding" >}}), which comes with a skill that teaches the agent to use it.
But honestly, that is not necessary anymore nowadays.

**A good AI engineer is just a good engineer.**
People ask me what makes a good agentic engineer.
I've been saying the same thing for a long time: somebody who is literally a good engineer.
Good engineering practices never went away.
They are more important than ever: test-driven development, building things at the right level of abstraction, a proper architecture.

Before AI, you could spend a year writing a few thousand lines of code, maybe a couple tens of thousands at most.
You were intimately familiar with all of it, so you could get away with a somewhat worse architecture.
Now you can produce a million lines of code in a year.
There is no possible way you can keep up with all of it.
If you want to build something lasting and robust, you need proper foundations.
And that is where your opinions matter.
You don't need any setup to start, but you do need taste to build something that lasts.
(I made a related point a year ago in [On agentic coding]({{< ref "/post/agentic-coding" >}}): AI amplifies the experience you already have.)

**Your role changed, it didn't disappear.**
Some software engineers feel personally attacked by all this.
I think you have to get over yourself.
Your secret sauce was never knowing the syntax really well.
Now you need to know what to build, and how it should be built.

And you need to be strict.
You can produce thousands of lines a day, so be thoughtful about whether you want them in your codebase forever.
Changing the color of a button: one prompt, done.
A difficult system deserves more rigor, not by reading every line, but by understanding the architecture and its implications.

## Conclusion: this post has an expiry date

Right now I'd tell you to use Claude Opus 5.5.
Just two weeks ago I was telling people to use GPT-6 Astra.
Things change continuously, and in most cases you'll be fine with either.

I'm also sure that a few weeks from now, I will no longer accept the model I'm praising today.
Not because it can't do the amazing things it does now.
But because the next one will do even more amazing things that it can't.
With every new model, my workflow changes, and the amount of scope I hand over per task grows dramatically.

That is exactly why I don't recommend building an elaborate setup first.
Every skill, rule file and agent graph is tuned to the limitations of the model you have today.
Those limitations are gone in a few months, and the setup quietly turns into dead weight.
The one habit that survives every model change is the simple one: ask it.

So install it today, use the best model, and ask it everything, including whether its own work is any good.
Everything else is optional, and probably temporary.

What's stopping you from trying it today?
