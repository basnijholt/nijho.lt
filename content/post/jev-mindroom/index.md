---
title: "Exploring the Jev hype in MindRoom"
subtitle: "A System One model for the small yes-or-no decisions in a multi-agent chat"
summary: "TypeSafe's Jev was everywhere, so I tried it in MindRoom. It now decides whether an agent joins a conversation, whether a follow-up message should interrupt a running reply, and which agent should answer. One eval went from 5 out of 40 to 40 out of 40 by changing the question, not the model."
date: 2026-09-23
draft: false
featured: false
authors:
  - admin
tags:
  - ai
  - mindroom
  - matrix
  - agents
  - evals
  - typesafe
  - jev
categories:
  - AI
  - Software Development
  - level:intermediate
---

Last week, every AI newsletter I get was full of [Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev), a new model from TypeSafe.
So were several subreddits.
I am a permanent lurker on [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/), and even though it is about local models, every other post seemed to be about Jev.
There were local clones like [mini-jev](https://github.com/r-ms/mini-jev) and [von](https://github.com/wfzyx/von), CLI wrappers like [jev-cli](https://github.com/joshLong145/jev-cli), and even [someone on Hacker News](https://news.ycombinator.com/item?id=49765348) claiming [they had built the same thing a year earlier](https://laya.convaiinnovations.com/).

I tried Jev in [MindRoom]({{< ref "/post/mindroom" >}}), my [open-source](https://github.com/mindroom-ai/mindroom) agent platform on [Matrix](https://matrix.org), and less than two days later it was making [three decisions](https://github.com/mindroom-ai/mindroom/issues/2156) there.

## What a System One model is

The [name comes](https://docs.typesafe.ai/concepts/system-one) from Daniel Kahneman's [*Thinking, Fast and Slow*](https://en.wikipedia.org/wiki/Thinking,_Fast_and_Slow), where System 1 is fast, intuitive thinking and System 2 is slow and deliberate.
A System One model does not generate text.
You send it a state, for example a chat log, plus typed questions, and it returns [probabilities](https://docs.typesafe.ai/api):

| Type | Question | Answer |
|---|---|---|
| Noul | Yes or no | Probability of yes |
| Choice | Pick one of up to 255 options | Chosen option plus the full distribution |
| Score | Rate against a rubric of 2 to 10 levels | Probability-weighted value |

[TypeSafe claims](https://typesafe.ai/blog/introducing-system-one-models-and-jev) 70 to 500 ms end to end and $0.042 per million input tokens, with output tokens free.
They also write "we can't prove it isn't subsidized."
Either way, it is incredibly cheap and incredibly fast.

## Adaptive participation

In MindRoom, a conversation can have several humans, several agents, or both.
When I talk to a single agent, it simply replies, and I don't need to tag it.
Once another person joins and writes something, the agent cannot tell whether the message was meant for it or for the other person.
Nothing decided that, so the agent stayed quiet unless explicitly tagged.
That confused several users.

So I recently added [adaptive participation](https://docs.mindroom.chat/configuration/#adaptive-agent-participation): an agent that has already replied in a thread decides on its own whether to answer an untagged message.
I first used an LLM as the judge, GPT-5.6 Luna on low reasoning.
A yes-or-no question like "should this agent respond?" is exactly what Jev is for, so it [became the second backend](https://github.com/mindroom-ai/mindroom/pull/2169).
Compared with Luna, it is about ten times cheaper and ten times faster, and if I believe the benchmarks, it is also smarter.

## "Thanks" should not stop the agent

The next thing I used Jev for was interruptions.
When I send a message while an agent is still replying, MindRoom injects a notice at the next tool call telling the agent to stop and wrap up, because there is a new message.
But often I, and other users, would watch the agent start working and then write "looks good" or "thanks."
The agent would stop early and continue in the next turn, which is both wasteful and counterintuitive.

Now [a judgment](https://github.com/mindroom-ai/mindroom/pull/2193) decides whether the new message needs the interruption, which the docs call [mid-turn coalescing](https://docs.mindroom.chat/configuration/#mid-turn-coalescing).
If it does not, the agent reacts with 👀, finishes its reply, and handles the message afterwards.

This is also where I learned a lesson about evals.
My first implementation worked at the code level but not functionally.
My evals, based on real attempts inside MindRoom that had all failed plus synthetic cases from GPT-6 Astra, passed 5 out of 40 with Jev.
[The fix](https://github.com/mindroom-ai/mindroom/pull/2244) changed the question and gave the judge more context, and it went to 40 out of 40.

| | Before: 5/40 | After: 40/40 |
|---|---|---|
| Question | "May the active task finish before the queued human messages are handled in a later turn?" | "Does any newly queued message require an immediate change to, pause of, or stop of the active task?" |
| When unclear | "Also false when context is incomplete, the relationship is unclear…" | "Mere relevance to the task does not make praise or thanks an interruption." |
| Context | The request and the new messages | The same, plus the preceding conversation |

The old question treated anything unclear as a reason to interrupt, and a bare "thanks" without the conversation around it always looks unclear.

## Picking the responder

The third decision is routing.
When a message in a room with many agents does not mention anyone, MindRoom's router picks who should answer.
That used to be a free-text LLM prompt, "choose the most appropriate agent."
It is [now a Jev Choice](https://github.com/mindroom-ai/mindroom/pull/2238) over the eligible agents, plus a `no_fit` option, as described in the [router docs](https://docs.mindroom.chat/configuration/router/).
A confident `no_fit` asks the user to mention an agent instead of guessing, and anything uncertain falls back to the existing LLM router.

## One config line to switch

I built a very simple abstraction layer so I can swap Jev for an LLM without changing any code.
Every decision is one question with criteria for true and false:

```python
MID_TURN_QUESTION = JudgmentQuestion(
    id="interrupt_current_turn",
    instructions="Does any newly queued message require an immediate change to, pause of, or stop of the active task?",
    when_true="A new message requests stopping or pausing the active task, corrects it, ...",
    when_false="The messages acknowledge progress, express thanks, ask to continue unchanged, ...",
)
```

Jev receives it as a Noul question and returns a probability, which MindRoom compares with a threshold.
An LLM receives the same question and context and must return `{"decision": true}` or `{"decision": false}`.
Switching is a configuration change:

```yaml
agents:
  helper:
    mid_turn:
      defer_reaction: "👀"
      judgment:
        provider: typesafe  # or: provider: llm, model: fast
        threshold: 0.8
```

Both backends log their decisions and latency, so I can compare them on real traffic.
The code is in [`src/mindroom/judgment/`](https://github.com/mindroom-ai/mindroom/tree/main/src/mindroom/judgment), and the backends are documented under [participation judgment backends](https://docs.mindroom.chat/configuration/#participation-judgment-backends).

## Named after Jevons

I only read [why TypeSafe named it Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) after building all this: they named it after William Stanley Jevons, who noticed that as steam engines burned coal more efficiently, demand for coal went up instead of down.
This is known as the [Jevons paradox](https://en.wikipedia.org/wiki/Jevons_paradox).
That was literally my experience.
Once I implemented it for one decision, I came up with use case after use case.

One I already built is a plugin, [Response Audit JEV](https://github.com/mindroom-ai/response-audit-jev-plugin).
Right after an agent replies, Jev checks the answer against the request and the tool calls the agent actually made, for example whether things are properly cited.
If a check flags a problem, the plugin posts one follow-up in the thread that tags the agent and asks for a correction.
Because Jev is so fast and cheap, running this after every reply costs almost nothing.

Right now I am full of ideas.
For example, a model router.
In MindRoom, an agent can switch to a different model mid-conversation with a tool call, and I can do the same with `!model`.
Agents rarely do that without being told, though.
So I default to a very expensive model, and I only save money when I remember to switch to a cheap one for something simple.
Jev could run on every message and decide whether it needs the capable model or not.
