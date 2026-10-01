---
title: "Self-hosting AI does not save money, and I do it anyway"
subtitle: "I run open-weight models on two RTX 3090s and love it. The math still says an API is cheaper, even with solar panels and zero-data-retention providers."
summary: "Whenever I say that self-hosting AI is not economical, people hear that I am against self-hosting. I am not: I run Qwen3.8 27B at home and think open-weight models are great. This post compares it with GPT-6 Luna on the same benchmark, and explains why batching makes datacenters win."
date: 2026-09-30
draft: true
featured: false
authors:
  - admin
tags:
  - self-hosting
  - local-llm
  - qwen
  - open-source
  - ai
  - homelab
  - nvidia-rtx-3090
  - economics
categories:
  - AI
  - Self-Hosting
  - level:intermediate
---

I have had this debate many times, so I am finally writing it down.

Whenever I say that self-hosting AI does not save money, people hear that I am against self-hosting.
That is not the point at all.
I am a massive fan of open-weight models.
Qwen3.8 27B runs on two RTX 3090s at home, and my phone dictation goes to [Qwen3-ASR on the same machine]({{< ref "/post/diction-agent-cli-qwen" >}}).
I think open-source AI is the best thing since sliced bread.

I don't pretend it saves money.

All benchmark numbers and prices below come from [Artificial Analysis](https://artificialanalysis.ai/) and [OpenRouter](https://openrouter.ai/) as of September 30, 2026.
I did the math for the hardware I own, and for the counterarguments I hear most.

Benchmarks are not everything, and a high score does not reliably predict how a model does on real work.
They are still the best we have: all models are benchmaxed, tuned to do well on the popular benchmarks, so the scores at least work as a reference frame for comparing them with each other.

{{< toc >}}

## 1. The model I love, and the one that beats it on price

My favorite local model right now is [Qwen3.8 27B](https://artificialanalysis.ai/models/qwen3-8-27b).
It came out in August and it is Apache-2.0.
People often say models like this run on a single gaming GPU, but that is only true after quantizing them.
At full precision, Qwen3.8 27B needs about 54 GB of memory; in Q4_K_M, about 5 bits per weight, it fits on one 24 GB card, at some cost in quality.

I compare it with OpenAI's GPT-6 Luna, the cheap tier released on September 22.
Both models let you choose how long they think, but the settings do not mean the same thing for both.
Luna's token use grows more than 20 times from its lowest setting to its highest, while Qwen's barely changes.
Qwen on low already writes more tokens than Luna on xhigh.

{{< plot name="effortTokens" caption="Average output tokens per Intelligence Index task at each reasoning setting. Qwen3.8 27B has no high or max setting. Hover for scores." >}}

So the name of a setting says little on its own.
I compare both models at xhigh, the highest setting Qwen offers, and count the tokens each one actually uses.
The extra tokens Qwen needs are part of what I am measuring.
There, Qwen scores 33.7 on the Artificial Analysis Intelligence Index and Luna scores 34.6.
For reference, Claude Opus 4.6, a frontier model from February, scores 31.9.
That is an amazing feat in itself.
When Opus 4.6 was the best model we had, I never thought that within the same year I could run essentially that level of intelligence in my own house.

Artificial Analysis also publishes how many tokens each model used to run the index, and what that cost.
So the question is simple: what does it cost to run the whole benchmark once?

{{< plot name="runCost" caption="Cost of one run of the Artificial Analysis Intelligence Index. The middle bar is electricity only, with the assumptions from section 2." >}}

Luna runs the whole benchmark for $67.
Qwen at full precision, through the cheapest provider that does not keep your data (ZDR), costs $619.
Two things cause that gap: providers charge almost four times as much per output token for Qwen, and Qwen generates almost three times as many tokens to get the same work done.

The middle bar is my own machine: running Qwen on my GPUs costs about as much in electricity alone as Luna's entire bill.
What I care about is the cheapest way to get answers of Qwen's quality, from whichever model gives them.

## 2. "But my GPUs are already paid for"

This is the argument I hear most, so assume the hardware is free and only the electricity counts.

I assume the best case for my machine.
Both 3090s run their own copy of Qwen with multi-token prediction (MTP), for about 150 tokens per second together, while the machine draws 700 W.[^setup]
My machine then needs three weeks, running day and night, to get through the benchmark once.
I also give my quantized copy the score Artificial Analysis measured through Alibaba's API.
I have not rerun the benchmark on it, and anything lost to quantization makes my machine look worse.

{{< plot name="electricityCost" caption="Electricity for one benchmark run of Qwen3.8 27B on my two 3090s, by electricity price. The dashed line is what Luna charges for the same work, with OpenAI's hardware and margin included. Hover for values." >}}

Above 19 cents per kWh, my electricity alone costs more than Luna's API bill.
Below it, I save a few dollars per run and wait three weeks instead of a few hours.

## 3. Why datacenters are so much better at this

When my 3090 generates a token, it reads all 17 GB of weights from memory to produce one token for one conversation.
Most of the chip's compute sits idle while it waits for memory.
A datacenter GPU reads the same weights once and produces a token for hundreds of conversations at the same time.
This is called batching, and it is where most of the efficiency comes from.

Artificial Analysis measures this with [AgentPerf](https://artificialanalysis.ai/hardware-inference-stack/datacenter), which replays real coding-agent sessions against datacenter hardware.
It counts how many agents a system can serve while each one still gets at least 60 tokens per second.

{{< plot name="agentsPerKw" caption="Coding agents served per kW of accelerator power, each getting at least 60 tokens per second, from AgentPerf. The datacenter systems all run DeepSeek V4 Pro. The 3090 bar is my estimate for Qwen3.8 27B, a much smaller model, so the comparison favors my machine." >}}

The rack of 36 GB300s serves 20 times more agents per kW than the 8-GPU H200 server.
Part of that is newer chips, and part is software: NVIDIA tuned the B300 and GB300 setups itself, while Artificial Analysis configured the H200 one.
The B300 and the GB300 share both the chip generation and the software.
Most of the gap between those two bars comes from the rack itself: 36 GPUs on one fast interconnect keep more than a thousand agents in flight at once.
My two 3090s serve one conversation each.

## 4. "But I have solar panels"

Solar power is not free.
With net metering, every kWh my GPUs burn is a kWh that does not get credited at the retail price.
Without net metering, it is a kWh I do not sell, unless the surplus would go to waste anyway, which is the free-power case below.
And the GPUs also run at night.

But fine, say the electricity is free and the only cost is the hardware.
I was lucky and bought my two 3090s for about $750 each,[^3090] and I write them off over three years.
The GPUs only save money while they do work I would otherwise pay an API for, and while they sit idle they save nothing.
So the question is how many hours a day they have to be busy before they pay for themselves.

To make this fair to open models, imagine an open model that is exactly as efficient as Luna: the same quality from the same number of tokens, sold at Luna's price.

{{< plot name="breakEven" caption="How many hours a day my two $750 RTX 3090s have to be busy, every day for three years, before they cost less than a ZDR API. The host PC is not counted." >}}

With free power, the GPUs pay for themselves if they are busy 3 hours a day, every day for three years.
At 18 cents per kWh, they need 5.
That uses what I paid for the cards; at today's price of about $1,500 each, the 5 hours become 9.

And API prices keep falling.
GPT-6 Luna costs 58% less per output token than GPT-5.6 Luna did in July.
If the price halves again, the 5 hours become 15.
If it halves twice, the API costs less than my electricity alone.

## 5. The bar keeps moving

Five hours a day sounds like a lot, but I run agents for longer than that, just not on Qwen.
When Claude Opus 4.6 came out in February, I was perfectly happy with it.
I thought it was all I would ever need, and I could not have imagined how much better models would get in half a year.
Qwen3.8 27B now scores about the same as Opus 4.6, and I would no longer accept it for coding.
Until GPT-6 Astra came out at the start of September, my go-to was GPT-5.6 Sol, which scores ten points higher than Qwen.
I then used Astra until Claude Opus 5.5 came out less than three weeks later.
Now I don't even accept what was considered the best model a month ago.

{{< plot name="frontierGap" caption="Intelligence Index of the best model available on each date, of the models I used as my go-to, and of Qwen's 27B models, which fit on a single 3090. Scores use the xhigh reasoning setting where a model has it." >}}

The models that fit on my 3090s keep improving, but they stay about half a year behind the frontier, and my standard moves with the frontier.

## 6. A small company has it worse

For me, this is a hobby, and a hobby is allowed to be inefficient.
It gets worse once you try to use self-hosted models seriously, say for a team of ten developers.

If you stay fully self-hosted and want fast responses at peak, you have to buy hardware for the busiest hour of the year, not for the average one.
The rest of the time, it sits idle.

{{< plot name="peakLoad" caption="An illustrative week of coding agents for a ten-person team. The hardware has to cover the busiest hour of the year, but a typical week uses only a fraction of it." >}}

In this made-up but realistic week, the team uses 17% of what it paid for, so every token costs about six times more than it would at full load.
You also need a spare GPU for when one dies, and someone who gets paged when it does.
You could queue work or send the peaks to an API, but then you are paying for an API anyway.

An API provider has the opposite situation.
It serves thousands of customers across every time zone, so its load curve is much flatter than yours.
It fills the nights with discounted batch jobs (Luna's batch tier is half price) and training runs.
And more concurrent requests mean bigger batches, which is where the efficiency from section 3 comes from.

## 7. "They lose money on inference, so prices will go up"

Another argument I hear is that API prices are subsidized by investors and will go up once those investors want their money back.
I don't think that holds for inference.

AgentPerf also reports how many tokens each GPU serves per hour, and Artificial Analysis lists API prices and GPU rental prices.
Take DeepSeek V4 Pro on the GB300 rack at its list price, and assume the worst case for the provider: every input token is billed at the cheap cache-hit rate.
Each GPU still earns about as much per hour as it costs to rent a B200 from a smaller cloud provider, and that rent already includes the cloud provider's margin.
If even 5% of the input tokens miss the cache, it earns three times that.
A lab that owns its GPUs pays less than rent.
This leaves out costs like staff and idle hardware, so it does not tell you whether a provider is profitable overall, only that today's prices cover the hardware that serves the tokens.

The money goes to training, research, free users, and flat-rate subscriptions for heavy users like me.
When I wrote that I used [$10,000 worth of API tokens for $200]({{< ref "/post/agentic-coding" >}}), that was list price, not what those tokens cost to serve.

And prices go down, not up.
This is what the same level of intelligence has cost this year:

{{< plot name="priceDrop" caption="Output price per million tokens for models scoring between 30 and 35 on the Intelligence Index, by release date, as listed by Artificial Analysis. Log scale." >}}

From Claude Opus 4.6 in February to GPT-6 Luna in September, the output price for this level of intelligence dropped by a factor of 50.
Labs are in a race to the bottom on price.

## 8. "But they sell your data"

Some people say APIs are cheap because the provider trains on your data or sells it.
That is why I only used prices from providers that OpenRouter lists as zero data retention (ZDR).

| Model | Provider | ZDR | Output ($ per million tokens) |
|---|---|---|---|
| GPT-6 Luna | OpenAI | no | 0.50 |
| GPT-6 Luna | Azure | yes | 0.50 |
| Qwen3.8 27B | AkashML (FP8) | yes | 1.78 |
| Qwen3.8 27B | DeepInfra (full precision) | yes | 1.88 |
| Qwen3.8 27B | Alibaba | no | 2.55 |
| Qwen3.8 27B | Cloudflare | no | 3.20 |

Azure serves GPT-6 Luna with zero data retention at the same price as OpenAI.
For Qwen3.8 27B, the cheapest endpoints are all ZDR, and the endpoints without ZDR cost more.
The `:free` tier is where you pay with your data.

## 9. Where self-hosting does win: the same model

If you compare running Qwen3.8 27B yourself with paying for Qwen3.8 27B through an API, self-hosting wins.

DeepInfra, the cheapest full-precision ZDR provider, charges $619 for one benchmark run, while my electricity costs $64.
That compares the full model with my quantized copy, so the gap overstates my advantage by whatever quantization costs in quality.
My machine pays for itself if it is busy 1.6 hours a day, or about an hour with free power (the first group in the chart in section 4).

Providers charge a lot for a dense 27B model, because every token runs through all 27 billion parameters.
Sparse open models, which use only a small part of their weights for each token, can be much cheaper to serve.
If you specifically need Qwen and use it heavily, self-hosting it pays off.
But you don't need Qwen to get answers of Qwen's quality.
Luna gives you those for $67, with zero data retention.

## 10. So why do I do it?

First, it is fun.
I like knowing how the whole stack works, from the drivers in [my NixOS configuration]({{< ref "/post/llama-nixos" >}}) to how the layers are split between my two GPUs.

Second, nobody can take it away.
Artificial Analysis already lists GPT-5.6 Luna as deprecated, less than three months after its release.
My Qwen weights will still be on my disk in ten years, and no company can change their license or [close their build system]({{< ref "/post/truenas-to-nixos" >}}) on me.

Third, some data should not leave my house.
I would never send 200 GB of email, my messages, and my location history to an API, zero data retention or not.
That is what [my local AI projects]({{< ref "/post/local-ai-journey" >}}) are for.

Those are good reasons.
Saving money is not one of them.

[^setup]: Artificial Analysis measured 151 tokens per second for Qwen3.8 27B in Q4_K_M on an RTX 5090, using llama.cpp with MTP. A 3090 has about half the memory bandwidth of a 5090, so I assume about 75 tokens per second per card. With a single 3090 and no MTP, you get about 30 tokens per second; one benchmark run then takes 88 days, and the electricity alone costs more than Luna above 8 cents per kWh.

[^3090]: The 3090 is still the value king for VRAM per dollar, and $750 badly understates what mine are worth. That is what I paid more than a year ago; today a used 3090 sells for about $1,500. Even at that price it costs $62.50 per GB of VRAM, the same as an RTX 5090 at its $2,000 launch price, which is not what a 5090 sells for today. The right number for this calculation is what I could sell my cards for, and at $1,500 each the break-even points roughly double: at 18 cents per kWh, the same-model case moves from 1.6 to 2.9 hours per day, and the Luna-efficient case from 5.2 to 9.2 hours per day.
