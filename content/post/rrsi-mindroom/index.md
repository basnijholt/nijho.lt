---
title: "Trying RRSI's self-improving agent harnesses on MindRoom"
subtitle: "I let an optimizer rewrite my agents' instructions. It worked, but watching the agents struggle taught me more."
summary: "Google's RRSI lets LLMs rewrite an agent's prompts, tools, and config, and keeps only the changes that hold up on a benchmark. I tried it on MindRoom agents. It found good working habits, but the bigger wins came from building an honest benchmark and watching where the agents got stuck."
date: 2026-10-02
draft: true
featured: false
authors:
  - admin
tags:
  - ai
  - agents
  - mindroom
  - rrsi
  - evaluation
  - agentic-coding
  - open-source
categories:
  - AI
  - open-source
  - level:intermediate
---

Google Research recently published [RRSI](https://github.com/google-research/rrsi), short for Regularized Recursive Self-Improvement of Agent Harnesses.
The harness is everything around the model: the prompts, the tools, the config.
RRSI lets LLMs propose changes to that harness, tests each change on a benchmark, and keeps only the changes that survive some strict statistical checks.

In [MindRoom]({{< ref "/post/mindroom" >}}), every agent is a few lines of YAML: a role, instructions, and a list of tools.
That is exactly a harness, so I wanted to know what RRSI would do with it.
I gave my coding agent the link and asked how to use it with MindRoom.
Two days later I had an answer, and it was not the one I expected.

## The optimizer works

The first useful benchmark was a set of small terminal jobs: clean up a messy CSV, find a commit in git history, fix a package until its tests pass, change one value in a config file without touching anything else.
Each job has a hidden check that runs after the agent finishes, so the agent can't talk its way to a pass.

RRSI took the agent from mostly right to almost always right, including on new instances of the jobs it had never seen.
It did that without adding a single tool.
It only rewrote the instructions, and what it wrote reads like advice a senior engineer gives a junior:

- filter on the field you care about, not on the whole line;
- look at a sample of a big output, but compute over all of it;
- don't glue files together blindly, because one might not end with a newline;
- when only one value should change, change only that value;
- afterwards, check your work: search for the old name after a rename and run the tests.

Almost all of the gain came in the first round.
After that, RRSI mostly rejected its own proposals, which is what it is supposed to do.

It also refused ideas that sounded good.
Giving the agent a Python tool cost more tokens and helped nothing, since the shell can already run Python.
Compressing tool output cost more than it saved.
I liked that a lot: the optimizer has to pay for every token it adds.

## Start with work that matters

My first attempt was a mistake.
I started with arithmetic puzzles and MindRoom's calculator tool, because that was quick to set up.
The scores were so noisy that the same agent scored a few points apart on two identical runs, and nothing RRSI proposed beat that noise.

When I saw the results, my reaction was: why are we optimizing a calculator?
Nobody needs an agent that multiplies.
MindRoom agents spend their days in a shell, so that is what the benchmark had to be.

Measure the noise first, though.
If two runs of the same agent disagree by four points, a three-point improvement means nothing.

## The benchmark was the useful part

Building an honest benchmark meant running MindRoom the way it runs in production, with each agent's shell in an isolated container.
Watching the agents work exposed things no unit test had caught.
Inside the container, the home directory pointed at the host's home, so `cd ~` failed.
MindRoom's OpenAI-compatible API reported every request as using zero tokens.
The calculator quietly turned large integers into floats.

None of those are things an optimizer can fix.
I only found them because I had to look at hundreds of trajectories to understand what was going on.

## Put the lesson in the tool

The improved instructions lived in one agent's config.
That helps nobody else, so I moved a short version of them into the description of MindRoom's shell tool itself.
Now every agent with a shell sees them, without changing anything in its config.

I also tested it on kinds of jobs the optimizer had never seen.
It helped a little there, and not at all on new instances of the original jobs.
That is an honest, modest result, and I'm fine with it: the habits are generally sensible, but they are not magic.

## The comparison that didn't test anything

MindRoom also has a minimal mode.
Instead of dozens of tool definitions, the model sees a single `bash` tool, and it finds and calls every other tool through a small command-line program.
The point is to keep prompts small when an agent has many tools.

I compared both modes on the same terminal jobs, and minimal mode looked great: the same accuracy for about a quarter of the tokens.
I was ready to make it the default for shell-heavy agents.

Then I asked: but did it ever use anything other than the shell?
It had not.
Not once.
The comparison showed that a small prompt beats a big prompt when the job only needs a shell, and nothing about the part that makes minimal mode different.

So we built a benchmark where the shell is useless on its own: react to a specific message, reply in the right thread, schedule a reminder, send a file as an attachment.
Minimal mode found the right tools almost every time, and its accuracy matched standard mode.
But it was three times slower, and about a third of its shell commands were wasted.

## When the agent works around your interface, fix the interface

Most of the waste came from the command-line program itself.
Calling a tool returned "queued" straight away, so the model always needed a second command to wait for the result.
A wrong function name came back as "Tool is unavailable or arguments are invalid", which tells you nothing, and in one trial the agent tried three times and then gave up.
And the model kept writing calls in a natural form the program didn't accept.

The obvious next step was to let RRSI optimize minimal mode's instructions.
It would probably have learned to work around all of this.
But that teaches one agent to cope with a clumsy tool, and every other agent keeps paying for it.

So I fixed the tool instead: calls now wait for their result, a wrong name lists the right ones, and the natural forms just work.
Minimal mode then needed a third fewer tokens, with the extra wait commands gone entirely.

The rerun also caught a confusing error that my own fix had introduced.
Measure again after you fix something.

## Who did the work

My coding agent did almost all of it: the benchmarks, the hidden checks, the runs, and the pull requests.
Every pull request was reviewed by two other models before I merged it, and they kept catching mistakes the other one missed, including a regression in one of my fixes.
My own contribution was mostly a few questions at the right moments: why a calculator, did it ever use anything but the shell, and please don't overcorrect.
Each of those changed the direction more than any round of the optimizer did.

## What I would tell someone trying this

- **Benchmark the work your agents actually do,** and grade it with checks the agent can't see.
- **Measure the noise before you believe any improvement.**
- **Expect the first round to do most of the work.** The gains are general habits, and they show up early.
- **Read the trajectories.** The bugs and the bad interfaces are in there, and no optimizer will fix those for you.
- **Ask what your comparison does not test.**

RRSI is a nice piece of work, and I will keep the setup around to score agent configs.
But the most valuable thing it gave me was a reason to watch my agents closely, and that turned out to be worth more than the instructions it wrote.
