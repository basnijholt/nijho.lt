---
title: "Self-hosting AI does not save money, and I do it anyway"
subtitle: "I run open-weight models on two RTX 3090s and love it. The math still says an API is cheaper, even with solar panels and zero-data-retention providers."
summary: "Whenever I say that self-hosting AI is not economical, people hear that I am against self-hosting. I am not: I run Qwen3.8 27B at home and think open-weight models are great. This post compares it with GPT-6 Luna on the same benchmark, and explains why batching makes datacenters win."
date: 2026-10-02
draft: false
featured: false
authors:
  - admin
tags:
  - ai
  - local-ai
  - self-hosting
  - hardware
  - model-reviews
categories:
  - AI
  - Homelab
  - level:intermediate
---

I have had this debate many times, so I am finally writing it down.

Whenever I say that self-hosting AI does not save money, people hear that I am against self-hosting.
That is not the point at all.
I am a massive fan of open-weight models.
[Qwen3.8 27B runs on two RTX 3090s at home](https://github.com/basnijholt/dotfiles/blob/e63a3f341ff36b7b57bf31361c2844e1d8b78e95/configs/nixos/hosts/pc/ai.nix#L43) (and 15 more models), and my phone dictation goes to [Qwen3-ASR on the same machine]({{< ref "/post/diction-agent-cli-qwen" >}}).
I think open-source AI is the best thing since sliced bread.

I don't pretend it saves money.
I do it for fun, for sovereignty, and for privacy, which I come back to at the end.

All benchmark numbers and prices below come from [Artificial Analysis](https://artificialanalysis.ai/) and [OpenRouter](https://openrouter.ai/) as of September 30, 2026.
I did the math for the hardware I own, and for the counterarguments I hear most.
All assumptions are listed [at the end](#appendix-all-assumptions).

Benchmarks are not everything, and a high score does not reliably predict how a model does on real work.
They are still the best we have: all models are benchmaxed, tuned to do well on the popular benchmarks, so the scores at least work as a reference frame for comparing them with each other.

*Update, October 2, 2026: after the discussion on r/LocalLLaMA, I added [section 5](#5-but-my-mac-dgx-spark-or-ai-max-does-save-money) on Macs, DGX Sparks, and AMD AI Max machines.*

{{< toc >}}

## 1. The model I love, and the one that beats it on price

My favorite local model right now is [Qwen3.8 27B](https://artificialanalysis.ai/models/qwen3-8-27b).
It came out in August and it is Apache-2.0.
People often say models like this run on a single gaming GPU, but that is only true after quantizing them.
At full precision, Qwen3.8 27B needs about 54 GB of memory.
Quantized to about 4 bits per weight, it fits on one 24 GB card, at some cost in quality.
I still [split it across both of my 3090s](https://github.com/basnijholt/dotfiles/blob/e63a3f341ff36b7b57bf31361c2844e1d8b78e95/configs/nixos/hosts/pc/ai.nix#L56-L65), because the second card leaves room for a larger context window.

I compare it with OpenAI's [GPT-6 Luna](https://artificialanalysis.ai/models/gpt-6-luna), the cheap tier released on September 22.
Both models let you choose how long they think, but the settings do not mean the same thing for both.
Luna's token use grows more than 20 times from its lowest setting to its highest, while Qwen's barely changes.
Qwen on low already writes more tokens than Luna on xhigh.

{{< plot name="effortTokens" caption="Average output tokens per Intelligence Index task at each reasoning setting. Qwen3.8 27B has no high or max setting. Hover for scores." >}}

So the name of a setting says little on its own.
I compare both models at xhigh, the highest setting Qwen offers, and count the tokens each one actually uses.
The extra tokens Qwen needs are part of what I am measuring.
There, Qwen scores 33.7 on the [Artificial Analysis Intelligence Index](https://artificialanalysis.ai/methodology/intelligence-benchmarking) and Luna scores 34.6.
For reference, Claude Opus 4.6, a frontier model from February, scores 31.9.
That is an amazing feat in itself.
When Opus 4.6 was the best model we had, I never thought that within the same year I could run essentially that level of intelligence in my own house.

Artificial Analysis also [publishes](https://artificialanalysis.ai/leaderboards/models) how many tokens each model used to run the index, and what that cost.
So the question is simple: what does it cost to run the whole benchmark once?[^method]

{{< plot name="runCost" caption="Cost of one run of the Artificial Analysis Intelligence Index. The two bars for hardware at home are electricity only: measured on my 3090s, estimated for the RTX PRO 6000." >}}

Luna runs the whole benchmark for $67.
Qwen at full precision, through the [cheapest provider](https://openrouter.ai/qwen/qwen3.8-27b/providers) that does not keep your data (ZDR), costs $619.
Two things cause that gap: providers charge almost four times as much per output token for Qwen, and Qwen generates almost three times as many tokens to get the same work done.

The second bar is my own machine: the electricity alone for running Qwen on my GPUs costs more than Luna's entire bill.

The third bar is what it takes to match the API's full precision at home: an RTX PRO 6000, a workstation card with 96 GB of memory, enough for the full model.[^pro6000]
Its electricity alone costs twice Luna's bill, and one run takes more than seven weeks.
The card by itself sells for $10,000 to $20,000, so with a computer around it, you are paying for a pretty nice car.
Buy a few of them to run agents in parallel, and you are building a small data center of your own.

The bars for hardware at home are electricity only, so they are the lowest these runs can cost: the cards come on top, and how much depends on how busy you keep them, which is what section 4 is about.

What I care about is the cheapest way to get answers of Qwen's quality, from whichever model gives them.

## 2. "But my GPUs are already paid for"

This is the argument I hear most, so assume the hardware is free and only the electricity counts.

I measured my own machine.
It runs Qwen in vLLM, split across both cards, at about 107 tokens per second.[^setup]
The cards are capped at 270 W each,[^powercap] and the whole machine draws about 700 W.
It then needs four weeks, running day and night, to get through the benchmark once.
I also give my quantized copy the score Artificial Analysis measured through Alibaba's API.
I have not rerun the benchmark on it, and anything lost to quantization makes my machine look worse.

{{< plot name="electricityCost" caption="Electricity for one benchmark run of Qwen3.8 27B on my two 3090s, by electricity price. The dashed line is what Luna charges for the same work, with OpenAI's hardware and margin included. Hover for values." >}}

Above 14.5 cents per kWh, my electricity alone costs more than Luna's API bill.
Below it, I save a few dollars per run and wait four weeks instead of a few hours.

Those four weeks matter more than the few dollars.
An API takes hundreds of requests at once, so even one benchmark run can finish in an hour or two.
My setup works on one conversation at a time: when I sent it eight requests at once, seven of them waited in line.

{{< plot name="wallClock" caption="Wall-clock time for one benchmark run. The API times use Artificial Analysis's measured time per task for Luna; the parallel case assumes 100 requests at once. Log scale." >}}

This is one more reason my coding agents run on APIs.
When I [run several agents in parallel]({{< ref "/post/parallel-agentic-coding" >}}), each of them should be as fast as if it were alone.

## 3. Why datacenters are so much better at this

When my 3090s generate a token, they read all of the model's weights from memory to produce one token for one conversation.
Most of the chip's compute sits idle while it waits for memory.
A datacenter GPU reads the same weights once and produces a token for hundreds of conversations at the same time.
This is called batching, and it is where most of the efficiency comes from.

Artificial Analysis measures this with [AgentPerf](https://artificialanalysis.ai/hardware-inference-stack/datacenter), which replays real coding-agent sessions against datacenter hardware.
It counts how many agents a system can serve while each one still gets at least 60 tokens per second.

{{< plot name="agentsPerKw" caption="Coding agents served per kW of accelerator power, each getting at least 60 tokens per second, from AgentPerf. The datacenter systems all run DeepSeek V4 Pro. The 3090 bar is my machine running Qwen3.8 27B, a much smaller model, with GPU power only, so the comparison favors my machine." >}}

The rack of 36 GB300s serves 20 times more agents per kW than the 8-GPU H200 server.
Part of that is newer chips, and part is software: NVIDIA tuned the B300 and GB300 setups itself, while Artificial Analysis configured the H200 one.
The B300 and the GB300 share both the chip generation and the software.
Most of the gap between those two bars comes from the rack itself: 36 GPUs on one fast interconnect keep more than a thousand agents in flight at once.
My two 3090s serve one conversation at a time.

## 4. "But I have solar panels"

Solar power is not free.
With net metering, every kWh my GPUs burn is a kWh that does not get credited at the retail price.
Without net metering, it is a kWh I do not sell, unless the surplus would go to waste anyway, which is the free-power case below.
And the GPUs also run at night.

But fine, say the electricity is free and the only cost is the hardware.
I was lucky and bought my two 3090s for about $750 each,[^3090] and I write them off over three years.
The GPUs only save money while they do work I would otherwise pay an API for, and while they sit idle they save nothing.
So the question is how many hours a day they have to be busy before they pay for themselves.[^breakeven]

To make this fair to open models, imagine an open model that is exactly as efficient as Luna: the same quality from the same number of tokens, sold at Luna's price.

{{< plot name="breakEven" caption="How many hours a day my two $750 RTX 3090s have to be busy, every day for three years, before they cost less than a ZDR API. The host PC is not counted." >}}

With free power, the GPUs pay for themselves if they are busy 4 hours a day, every day for three years.
At 18 cents per kWh, they need 8.5.
That uses what I paid for the cards; at today's price of about $1,500 each, the 8.5 hours become 14.

And API prices keep falling.
GPT-6 Luna costs 58% less per output token than GPT-5.6 Luna did in July.
If the price halves again, no amount of use pays off at 18 cents per kWh.
If it halves twice, the API costs less than my electricity alone.

## 5. "But my Mac, DGX Spark, or AI Max does save money"

Several readers told me their machines do save them money: a MacBook Pro with an M5 Max, an NVIDIA DGX Spark, and a computer with AMD's Ryzen AI Max+ 395.
If you would have bought the machine anyway, that is true, for the reason in section 2: their electricity costs little compared with the API.
Counting the hardware is a different story.

With 128 GB of memory, all three can hold a better model than my 3090s: Qwen3.8-Flash-Next, a sparse model with 180 billion parameters, of which only 6 billion work on each token.
It scores 39.8, close to GPT-6 Luna on its highest setting (38.1), although at the Q2 a reader uses on their Mac it probably loses a few points.[^macspark]
So how many years would each machine have to run nonstop before it pays for itself?

{{< plot name="paybackYears" caption="Years of nonstop generation before each machine pays for itself, compared with the most efficient API model at a similar score. Each machine runs the best model it can hold." >}}

Even with free power, the 128 GB machines need six to ten years.
The AMD machine draws only about 120 W, but it is slow too: one benchmark run of Qwen3.8 27B takes it four and a half months, and almost as much energy as my 3090s.
The RTX PRO 6000 runs the same model about three times as fast but costs about twice as much, so it needs six to nine years.
My 3090s pay off in under two years with free power, which is why the 3090 is still the value king, but at 18 cents per kWh they never do: the electricity for one run already costs more than Luna charges for it.

Ten years is a long time in AI.
Better and more efficient open models will run on the same machines, but the frontier moves at the same pace, and API prices keep falling.
Hardware gets more efficient too, in datacenters and at home, so a machine bought today also ends up competing with next year's machines.
These numbers only show how far apart the two sides start.

## 6. The bar keeps moving

Section 4's eight and a half hours a day would be easy for me: I run agents for longer than that, just not on Qwen.
When Claude Opus 4.6 came out in February, I was perfectly happy with it.
I thought it was all I would ever need, and I could not have imagined how much better models would get in half a year.
Qwen3.8 27B now scores about the same as Opus 4.6, and I would no longer accept it for coding.
Until GPT-6 Astra came out at the start of September, my go-to was GPT-5.6 Sol, which scores ten points higher than Qwen.
I then used Astra until Claude Opus 5.5 came out less than three weeks later.
Now I don't even accept what was considered the best model a month ago.

{{< plot name="frontierGap" caption="Intelligence Index of the best model available on each date, of the models I used as my go-to, and of Qwen's 27B models, which fit on a single 3090. Scores use the xhigh reasoning setting where a model has it." >}}

The models that fit on my 3090s keep improving, but they stay about half a year behind the frontier, and my standard moves with the frontier.

## 7. A small company has it worse

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

## 8. "They lose money on inference, so prices will go up"

Another argument I hear is that API prices are subsidized by investors and will go up once those investors want their money back.
I don't think that holds for inference.

AgentPerf also reports how many tokens each GPU serves.
On the GB300 rack, one GPU serving DeepSeek V4 Pro handles about 4 million output tokens and 530 million input tokens per hour.
Most of that input is conversation history that coding agents send again with every step.
Providers keep it in a cache and charge less than 1% of the normal input price for it.

At [DeepSeek V4 Pro's list prices](https://artificialanalysis.ai/models/deepseek-v4-pro-0424), that GPU brings in at least $5.70 per hour, even if every input token is billed at the cache price.
If 5% of the input misses the cache, it brings in about $17.
Renting a B200, the closest GPU with a [published rental price](https://artificialanalysis.ai/hardware-inference-stack/datacenter), costs $3.50 to $5.90 per hour from smaller cloud providers, and that price already includes their profit.

So the tokens pay for the hardware that serves them, even in the worst case.
This leaves out costs like staff and training, so it does not tell you whether a lab makes money overall.

The money goes to training, research, free users, and flat-rate subscriptions for heavy users like me.
When I wrote that I used [$10,000 worth of API tokens for $200]({{< ref "/post/agentic-coding" >}}), that was list price, not what those tokens cost to serve.

And prices go down, not up.
This is what the same level of intelligence has cost this year:

{{< plot name="priceDrop" caption="Output price per million tokens for models scoring between 30 and 35 on the Intelligence Index, by release date, as listed by Artificial Analysis. Log scale." >}}

From Claude Opus 4.6 in February to GPT-6 Luna in September, the output price for this level of intelligence dropped by a factor of 50.
Labs are in a race to the bottom on price.

## 9. "But they sell your data"

Some people say APIs are cheap because the provider trains on your data or sells it.
That is why I only used prices from providers that OpenRouter lists as [zero data retention](https://openrouter.ai/docs/features/zdr) (ZDR).

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

## 10. Where self-hosting does win: the same model

If you compare running Qwen3.8 27B yourself with paying for Qwen3.8 27B through an API, self-hosting wins.

DeepInfra, the cheapest full-precision ZDR provider, charges $619 for one benchmark run, while my electricity costs $83.
That compares the full model with my quantized copy, so the gap overstates my advantage by whatever quantization costs in quality.
My machine pays for itself if it is busy 2.4 hours a day, or 1.5 hours with free power (the first group in the chart in section 4).

Providers charge a lot for a dense 27B model, because every token runs through all 27 billion parameters.
Sparse open models, which use only a small part of their weights for each token, can be much cheaper to serve.
If you specifically need Qwen and use it heavily, self-hosting it pays off.
But you don't need Qwen to get answers of Qwen's quality.
Luna gives you those for $67, with zero data retention.

## 11. So why do I do it?

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

## Appendix: all assumptions

{{< detail-tag "Show all assumptions, and which side each one favors" >}}

**Assumptions that favor self-hosting**

- The host PC around the GPUs is not counted, and my 3090s count at the $750 each I paid, not the $1,500 they sell for today.
- Quantized local copies get the score Artificial Analysis measured through an API, with no penalty for quantization.
- The payback chart assumes each machine is busy 24 hours a day, with no idle time.
- API prices stay where they are, although GPT-6 Luna's output price is 58% lower than GPT-5.6 Luna's, two and a half months earlier.
- My time to set up and maintain the machine is not counted.
- Every machine also gets a case with free electricity.

**Assumptions that favor the API**

- The example electricity price is 18 cents per kWh, and some people pay less.
- My machine serves one request at a time; batching several requests could raise its total throughput.
- The hardware has no resale value at the end.
- Waste heat that replaces heating in winter is not counted.
- API outages, rate limits, and deprecated models are not counted.

**Inputs**

- Benchmark: the Artificial Analysis Intelligence Index on September 30, 2026, at the xhigh reasoning setting, or the highest setting where noted. Its token counts per model are the unit of work.
- API prices: the cheapest zero-data-retention endpoints on OpenRouter, with cached input billed at the cache price.
- My machine: two RTX 3090s capped at 270 W, running Qwen3.8 27B in vLLM with AutoRound INT4 and DFlash2. Measured: 107 tokens per second, 1,600 tokens per second of prefill, and 540 W for both GPUs. Estimated: about 700 W for the whole machine under load and 150 W idle.
- Break-even: the cards are written off over three years; busy hours save what the API would charge minus the electricity, and idle hours cost the idle power.
- Other machines: prices, power, and speeds as in the footnotes. The M5 Max and RTX PRO 6000 numbers come from readers, and the DGX Spark and AMD Ryzen AI Max+ 395 speeds are estimated from Artificial Analysis measurements.
- Datacenter: AgentPerf measures accelerator power only, and the B200 rental price stands in for the GB300, which has no published rental price.
- Small company: the peak-load week is made up.

{{< /detail-tag >}}

[^method]: For each model, Artificial Analysis publishes how many input and output tokens the whole index took, and how many of the input tokens were read from a cache. I multiplied those by each provider's prices, with cached input at the cache price. For Qwen that is 198 million output tokens and 820 million input tokens that miss the cache. For the bars at home, the same tokens divided by the machine's speed give the run time, with the uncached input processed at the 1,600 tokens per second I measured on my 3090s and an estimated 2,000 on the RTX PRO 6000, and the run time times the machine's power and the price per kWh gives the electricity.

[^breakeven]: While the cards are busy, they save what the API would have charged for the same work, minus the electricity at 700 W. While they are idle, the machine still draws about 150 W, of which the two GPUs with the model loaded take 85 W. The break-even point is the number of busy hours per day at which those savings cover the price of the cards, written off over three years, plus the idle power.

[^pro6000]: The RTX PRO 6000 has the same memory bandwidth as an RTX 5090, and at full precision every token reads three times as many bytes as in Q4_K_M. Scaling Artificial Analysis's 5090 measurement gives about 48 tokens per second. I assume 600 W for the whole machine.

[^setup]: I measured the model as I normally run it: vLLM with an AutoRound INT4 quant and DFlash2 speculative decoding, split across both cards. Single 1,500-token answers came out at 105 to 109 tokens per second, and reading a 22,000-token prompt ran at 1,600 tokens per second. Sending 2, 4, or 8 requests at once did not raise the total above about 110 tokens per second. The two GPUs drew 540 W together, each at its 270 W power limit; the 700 W adds my estimate for the rest of the machine, since I could not measure the CPU. The setup follows the recipes from [club-3090](https://github.com/noonghunna/club-3090), a community project that tunes LLM serving for RTX 3090s and publishes measured numbers, so I think it is about as fast as these cards get. Its benchmarks for this configuration at a similar power limit match mine: about 110 tokens per second for prose, and up to about 195 for code, where speculative decoding guesses more tokens right. Most of Qwen's output on the benchmark is reasoning, which runs at the prose speed.

[^powercap]: The stock limit is 350 W. My cards sit in a [normal desktop case with normal fans]({{< ref "/post/local-ai-journey" >}}), and I worry that running both at full power for hours would shorten their life. The cap is [a few lines in my NixOS configuration](https://github.com/basnijholt/dotfiles/blob/e63a3f341ff36b7b57bf31361c2844e1d8b78e95/configs/nixos/hosts/pc/nvidia-undervolt.nix#L1-L7), and measurements from Puget Systems and r/LocalLLaMA put a 3090 at about 95% of its speed at 270 W. That is 77% of the power for 95% of the speed, so the cap also lowers my electricity cost per token.

[^macspark]: The M5 Max numbers come from the reader: Qwen3.8-Flash-Next at Q2 (about 2.7 bits per weight), about 45 tokens per second, 1,250 tokens per second of prefill, and about 90 W, on a $7,000 laptop. The RTX PRO 6000 numbers come from another reader, [u/TheAILegend](https://www.reddit.com/r/LocalLLaMA/comments/1ww2jsu/comment/pdhs3ea/), who measured Qwen3.8-Flash-Next at NVFP4 on theirs. For a single request, it stays at about 150 tokens per second from 4,000 to 200,000 tokens of context, with about 10,000 tokens per second of prefill and 266 W for the GPU plus about 160 W for the rest of the PC. With 32 short requests in parallel, the card reaches 590 tokens per second and pays off in about two years, which works for short batch jobs. At the long contexts of this benchmark, parallel requests are slower than one, so the chart uses the single-request speed. I use $15,000, the middle of the card's price range. The DGX Spark and the AMD machine run Qwen3.8-Flash-Next at about 4.5 bits. For their speed, I took Artificial Analysis's measurements of Qwen3.8 27B on each machine and doubled them, because the owner of the AMD machine finds Qwen3.8-Flash-Next about twice as fast as Qwen3.8 27B. That gives about 55 tokens per second on the DGX Spark ($6,950, about 150 W) and 47 on the AMD Ryzen AI Max+ 395 ($4,000, the price Artificial Analysis lists, about 120 W). All of them are compared with GPT-6 Luna on its highest setting, which runs the whole benchmark for $122. The 3090s run Qwen3.8 27B, as in the rest of this post, and are compared with Luna on xhigh. Artificial Analysis measured Qwen3.8 27B on the AMD machine at 23 tokens per second, so one benchmark run takes it 134 days and about 390 kWh, against about 460 kWh on my 3090s. Running Qwen3.8-Flash-Next on the 3090s with CPU expert offload, which club-3090 measured at 37 tokens per second, does not change their result: one run then takes 82 days, and at 18 cents per kWh its electricity costs more than Luna's $122 unless the whole machine draws less than about 350 W.

[^3090]: The 3090 is still the value king for VRAM per dollar, and $750 badly understates what mine are worth. That is what I paid more than a year ago; today a used 3090 sells for about $1,500. Even at that price it costs $62.50 per GB of VRAM, the same as an RTX 5090 at its $2,000 launch price, which is not what a 5090 sells for today. The right number for this calculation is what I could sell my cards for, and at $1,500 each the break-even points rise by about two thirds: at 18 cents per kWh, the same-model case moves from 2.4 to 4.0 hours per day, and the Luna-efficient case from 8.5 to 14.2 hours per day.
