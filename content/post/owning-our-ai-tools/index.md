---
title: "Designing functions for AI isn't the same as designing them for humans 🔧"
subtitle: "Wrapping a REST API into an MCP server one endpoint at a time wastes tokens on every turn. Redesigning 155 toolkits in MindRoom cut 729 functions down to 298, halved our schema size, and improved tool-calling performance without dropping features."
summary: "A lot of teams convert existing REST APIs straight into MCP servers, exposing one function per endpoint. Designing functions for an AI isn't the same as designing them for a human programmer. After deleting Agno and redesigning all 155 built-in toolkits in MindRoom, we cut 729 default functions down to 298 without losing features, shrank total tool schemas by 50%, and learned why you should split reads from writes and test schemas on small local models."
date: 2026-11-27
draft: true
featured: false
authors:
  - admin
tags:
  - ai
  - agents
  - mindroom
  - software-design
  - dependencies
  - open-source
categories:
  - Software Development
  - AI
  - level:intermediate
---

A lot of people connect AI agents to their services by converting an existing REST API straight into an {{< tooltip text="Model Context Protocol: an open standard for connecting AI models to external tools and data sources." >}}MCP{{< /tooltip >}} server, one tool per endpoint.
That's probably the least token-efficient way to give an AI tools.
Designing functions for an AI isn't the same as designing them for a human programmer.

I learned how much difference that makes this week while redesigning all 155 built-in toolkits in [MindRoom]({{< ref "/post/mindroom" >}}) ([GitHub <i class="fab fa-github"></i>](https://github.com/mindroom-ai/mindroom)), after deleting the AI framework underneath it.
Across the whole catalog, we cut {{< tooltip text="Measured across all built-in toolkits in tests/fixtures/agno_parity/tools/schemas.json in default configuration, from Nov 24 to Nov 27, 2026." >}}729 default functions down to 298{{< /tooltip >}} and shrank total tool schemas by 50%.
We didn't drop capabilities to get there: we gained richer ways to express calls, fixed a pile of bugs, and cut the fixed per-turn prefix of our representative agent fixture by 57%.

{{< toc >}}

{{% callout note %}}
**TL;DR:** Turning a human REST API straight into an MCP server or one-function-per-endpoint toolkit burns tokens on every turn.
Group related verbs under an `action=` parameter to shrink schemas without losing features, then split reads and writes into separate functions so read-only access and human approvals stay crisp.
To verify your tool schemas are clear, test them with the dumbest local model you'd reasonably use, because frontier models pass almost anything and hide the flaws in the noise.
{{% /callout %}}

## How AI harnesses and tool schemas work

For a lot of people, AI harnesses feel like magic.
Really, all the magic is in the models.

Every request an agent sends to an AI API is mostly freeform natural language text, plus a small block of structured data.
That structured data is a list of {{< tooltip text="JSON descriptions of each tool's name, purpose, argument names, and argument types so the model knows what it can call." >}}tool schemas{{< /tooltip >}} describing every tool the model is allowed to call.
When the model wants to use one, it replies with the tool name and arguments, and the harness executes the code on your own machine and sends the result back.
Any AI harness is just that loop: hand the model a prompt and tool schemas, run the tools it asks for, and repeat.

Because those schemas travel along with the conversation on every turn, the way you shape them matters.
If you define tools the way you'd write normal Python functions or wrap a REST API into MCP, you end up very verbose.
For email alone, you might expose separate functions like `read_email`, `write_email`, `save_draft`, `star_email`, and `archive_email`.
Every one of those functions repeats shared arguments like `to`, `message_id`, or `subject`, burning {{< tooltip text="Chunks of text a model reads and writes, about three quarters of a word each. Providers count them on every turn." >}}tokens{{< /tooltip >}} on every single turn.
Instead, you can describe the same capability as one `email(action, to, message_id, subject, ...)` tool where `action` is `read`, `write`, `draft`, `star`, or `archive`, and pay for the shared arguments once.

## Why deleting Agno forced the redesign

When I started building MindRoom {{< tooltip text="MindRoom's initial commit (a062d21fd) landed on July 29, 2025, sixteen months before this post." >}}nearly a year and a half ago{{< /tooltip >}}, I picked [Agno](https://github.com/agno-agi/agno) mostly for its built-in library of {{< tooltip text="At commit a0471bd2d (Nov 25, 2026), 87 built-in toolkit modules under src/mindroom/tools/ still imported Agno, out of 160 built-in toolkits total." >}}87 integrations{{< /tooltip >}} like GitHub, Gmail, Slack, and Docker.
By late October I'd already replaced Agno's runtime after piling up 126 workarounds (which I wrote about in [Roll your own, fork the rest]({{< ref "/post/roll-your-own-fork-the-rest" >}})), and this week I deleted the rest of it in about {{< tooltip text="21 hours 12 minutes from Wave 1 (#4378) to Wave 9 (#4419), deleting 233 Agno imports across 106 source files and all remaining AGNO_COMPAT markers." >}}21 hours{{< /tooltip >}} using my [parallel orchestrator setup]({{< ref "/post/orchestrating-orchestrators" >}}).[^waves]

With today's models, writing those integrations yourself is trivial, because popular APIs exist a thousand times over in the training data.
More importantly, owning all {{< tooltip text="160 built-in toolkits before the pass; five overlapping ones (confluence, jira, dynamic_workflow, python, web_browser_tools) were merged or retired without losing features, leaving 155." >}}155 toolkits{{< /tooltip >}} meant we were no longer stuck with Agno's one-function-per-endpoint layout.
In [my tests on native harness tools]({{< ref "/post/native-harness-tools" >}}), frontier models didn't care much whether tool names matched what they were trained on, while fixed per-request tokens mattered a lot.
Once MindRoom owned the files, I could redesign the whole catalog around that lesson.

## Shrink tool counts, then split reads from writes

Before the rewrite, our toolkits looked just like auto-converted REST APIs, with services like GitHub, Gmail, and Docker exposing twenty to forty separate functions each.
Grouping related verbs under an `action=` parameter cut default functions across all 155 toolkits from 729 down to 298 and {{< tooltip text="138,470 to 69,233 o200k_base tokens (-50.0%) in compact JSON across all built-in toolkits in schemas.json." >}}halved total schema size{{< /tooltip >}} without stripping features.[^catalog-numbers]
Often the consolidated tools ended up with cleaner parameters and fewer bugs than the wrappers they replaced.

{{< plot name="catalogReduction" caption="Schema token reduction across major MindRoom toolkits from Nov 24 to Nov 27 (o200k_base tokens, compact JSON). Labels show function counts before and after plus percentage drops. Hover for exact values." >}}

At first I considered collapsing every toolkit into a single mega-tool.
I quickly realized that was wrong.

Permissions and human approvals live at the function boundary.
If you want a read-only agent, the cleanest guard isn't a prompt asking it not to write.
It's never giving it the write function in the first place.
When reads and writes share one `action=` tool, a read-only agent still sees every write argument in its schema.
Your approval layer also has to parse arguments on every call just to tell a lookup from a delete.

{{< figure src="tool-boundaries.svg" caption="One function per endpoint bloats schemas, while one mega-tool mixes reads and writes. Splitting into read and write action pairs keeps schemas small and permission boundaries crisp." alt="Three-column comparison showing one function per endpoint with schema bloat on the left, one mega-tool with mixed reads and writes in the middle, and read and write action pairs separated by a red dashed safety boundary on the right." >}}

So I went the other direction on four built-in mega-tools (`triggers`, `desktop`, `browser`, and `matrix_api`) and split them into separate read and write functions, while bringing `workflow` down to the same read/write pair.[^mega-split]
Splitting them didn't even cost extra tokens: each schema actually got smaller, because the read function no longer documents write arguments and vice versa.

Large APIs don't stop at a single read/write pair either.
Our GitHub toolkit covers 39 actions across dozens of parameters, so collapsing it into two functions would still leave a huge write tool mixing issue comments with repository deletes.
We split it into five functions instead: two reads (repos and files vs issues and pull requests) and three write tiers (issues, pull requests, and repo mutations), keeping each schema small and separating safe writes from destructive ones.[^github-split]

## The hidden tax inside tool schemas

Shrinking function counts was half the savings.
Looking across all 155 toolkits at once exposed two schema leaks that hit almost any Python agent harness.

**Python's optional-type tax.**
When you annotate a parameter as `limit: int | None = None` in Python, standard JSON-schema generators emit `{"anyOf": [{"type": "integer"}, {"type": "null"}]}` instead of `"type": "integer"`.
That extra `null` branch is almost always redundant: the parameter is already absent from JSON Schema's `required` list, so omitting the key passes `None` in Python anyway.
I changed our schema generator to emit plain JSON types for optional parameters defaulting to `None`, while still accepting an explicit `null` at runtime if a model sends one.[^anyof]
In that single commit, `anyOf` blocks across the catalog dropped by {{< tooltip text="With function count held fixed at 315 across schemas.json in PR #4432: 1,037 to 298 anyOf blocks (-71.3%), saving 6,704 tokens (-8.7%)." >}}71%{{< /tooltip >}}, and a five-model A/B check on optional-heavy tool calls showed zero accuracy cost (40/40 before and 40/40 after).
Parameters where `null` carries real meaning stay untouched, like a SQL `limit: int | None = 10` where passing `null` means "return all rows".

**Repeated helper arguments.**
MindRoom adds two optional arguments to tools: `background_after` to push slow work into a background job, and `mindroom_output_path` to write large outputs to disk.
Repeating their full descriptions on every function burned nearly a hundred tokens per tool.
Explaining both once in the system prompt and letting fast local tools opt out cut that overhead by {{< tooltip text="background_after shrank from 47 to 28 tokens and mindroom_output_path from 49 to 24 tokens per function, plus opt-outs for fast built-ins (~72 to 73% total drop)." >}}almost three quarters{{< /tooltip >}}.[^meta-params]

Here's how all three changes shrink all 39 functions of our GitHub toolkit step by step, drawn to token scale (click any step to pause and inspect it, or hover any block to see its function and token count).

<div class="mr-schema-shrinker"></div>

Earlier that same week, before Wave 1 started, I also tightened MindRoom's default system prompt to drop stale instructions and hide sections an agent doesn't use.[^prompt-trim]
Combined with the tool rewrite, the fixed per-turn prefix of our representative Claude agent fixture (identical config and conversation history) {{< tooltip text="System messages fell from 2,968 to 1,215 tokens (-59.1%) and tool schemas from 3,909 to 1,740 tokens (-55.5%) in agent_anthropic.json (6,877 down to 2,955 tokens, -57.0%)." >}}dropped by more than half{{< /tooltip >}}, and its tool list shrank from 23 functions down to 9.
Even the calculator in that fixture went from eight functions (`add`, `subtract`, `multiply`, `divide`, `exponentiate`, `factorial`, `is_prime`, `square_root`) to one (`calculate`).

{{< plot name="agentRequest" caption="Fixed prefix sent on every step of MindRoom's representative Claude agent fixture (identical config and history, Nov 24 vs Nov 27). System prompt fell 59% and tool schemas fell 56%. Hover for exact counts." >}}

## Test with the dumbest model you'd use

Frontier models like Claude Opus 5.5 and GPT-6.2 Astra get almost any tool call right almost all the time, no matter how clunky or bloated the schema is.
If all your tests score 10/10 or 20/20, you have no signal and any difference disappears into the noise.

To evaluate tool schemas properly, you have to pick the dumbest model you can still reasonably do useful work with, and see where it starts failing.
For me, that means self-hosted models that run on typical consumer hardware.
Lately I've been experimenting a lot with Inkling 2 Mini, which has been great, and before that Qwen 3.8 27B was my go-to local model.

I added a small 12-task evaluation harness (`evals/tool_calling/`) that boots a real MindRoom agent with inline tools plus {{< tooltip text="Tools omitted from the main schema list. The model sees a one-line catalog entry and loads full definitions on demand via tool_search and call_tool." >}}deferred tools{{< /tooltip >}} and runs full multi-turn loops on smaller models.[^eval]
Three concrete mistakes showed up immediately.

**Negative warnings poison tool search.**
Our `chat_ui` catalog entry said "never controls the user's browser" to stop models from confusing it with the browser tool.
Because `tool_search` matches keywords, searching for `"browser"` kept ranking `chat_ui` right next to `browser`.
Deleting that negative clause fixed retrieval.

**Never default an action to a write.**
`matrix_message` defaulted `action` to `"send"`.
Whenever a model forgot to pass `action`, it defaulted to posting a message.
Making `action` required removed that footgun.[^explicit-action]

**Silent name collisions across toolkits.**
Before normalizing names, 47 function names collided across the catalog, including `search_web`, `run_sql_query`, `send_email`, and `crawl`.
Enabling two integrations silently shadowed one of them.
Prefixing integration functions as `<toolkit>_<verb>` took collisions from 47 to zero.[^collisions]

To see where consolidation stops helping and starts hurting, I ran a controlled 400-trial benchmark on our GitHub toolkit: the same 20 GitHub tasks across five models (`inkling-2:mini`, `qwen3.5-9b`, `gemma-4-26b`, `gemma-4-31b`, and `gpt-5-mini`), tested against four schema shapes covering the exact same 39 operations.[^github-eval]

{{< plot name="githubShapes" caption="Controlled 400-trial GitHub tool-calling benchmark across five models (20 tasks per arm, temperature 0). Top: exact first-try pass rate (thick green line is the five-model average; thin lines are individual models). Bottom: average prompt tokens per call on the same four shapes. Five functions match 39 at a third of the tokens, while 2 or 1 function drops accuracy by 10 to 14 points." >}}

Look at the shape of that curve.
Our five read/write functions tied the 39-function REST schema on exact first-try accuracy (93/100 each) while using a third of the prompt tokens, and even beat 39 functions on `inkling-2:mini` and `gemma-4-31b`.
Pushing further down to two functions or one mega-tool barely saved another couple hundred tokens, yet tanked average accuracy to 83% and 79%.

Two structural bugs show up in the failure logs whenever you over-merge a tool.
First, the parameter list swells to the union of every action (42 parameters in the single-tool arm), so smaller models leak wrong-action arguments like passing `branch` instead of `ref` or `issue_number` instead of `number`.
Second, JSON Schema's `required` list shrinks to the intersection of every action: the moment `create_repository` shares a tool with `edit_pull_request_comment`, you can't mark `repo_name` as required anymore, and models start dropping it.
Notice `gpt-5-mini` sitting flat at 95 to 100% across all four shapes: if you only tested on strong models, the 14-point mega-tool cliff would be completely invisible.

Across a separate 64-trial live A/B on eleven smaller search and web toolkits we consolidated into clean action dispatchers, four small models went from 58/64 to 64/64 passed while cutting prompt tokens by 23%.[^wave24-eval]

All of those rules now live in automated CI tests and a short Tool Design Rules section in `AGENTS.md`.[^ci-invariants]
A pull request can't merge if it adds a duplicate function name, an unprefixed integration function, or a mutating default action.

## Prompt caching doesn't make input tokens free

A common pushback against optimizing tool schemas is that prompt caching discounts input tokens by 90% or more, so fixed schema tokens barely affect your bill.
I checked my own MindRoom usage over the past seven days across {{< tooltip text="345,924 OpenRouter-priced requests out of 370,145 total requests over 7 days, valued at published OpenRouter list prices." >}}345,924 requests{{< /tooltip >}} to see if that's actually true.[^spend-data]

{{< plot name="spendBreakdown" caption="Share of estimated spend by billing bucket across 345,924 MindRoom requests over seven days (published OpenRouter list prices, Nov 20 to 27, 2026). Even with heavy prompt caching (91.8% of all tokens are cache reads), input and cache tokens account for 81% of total spend while output is 19%. Hover for request counts and cache-read share." >}}

Across all models combined, 91.8% of all tokens were cache reads, and yet input and cache tokens still accounted for 81% of total spend while output was only 19%.
On OpenAI (`GPT-6.2 Sol` and `Astra`) and Anthropic (`Claude Opus 5.5`), cached prefix reads and writes alone made up 74% to 87% of the bill.
Because an agent loop resends the entire prefix dozens or hundreds of times per task, a "cheap" cache read paid 50 times in a row still becomes the biggest line item.

You still need to keep perspective on what shrinking tool schemas saves.
In long coding threads (my median request size over that week was nearly 100k tokens), conversation history and tool outputs make up most of that cached prefix, so trimming a few thousand schema tokens won't cut your total bill in half.
It matters far more on short-to-medium loops, fresh subagents, cold cache writes, and local models where every extra thousand tokens slows down prefill directly.

## What owning 155 toolkits costs

When Slack, Gmail, or Spotify changes an endpoint, nobody upstream is going to patch it for us.
Most of Agno's {{< tooltip text="87 Agno-backed toolkit modules were rewritten natively in Waves 2 through 8." >}}87 toolkits{{< /tooltip >}} were thin REST wrappers around `httpx`, and MindRoom still uses official vendor SDKs where the protocol is complex, so I think the trade is worth it.
It's still more code to maintain.

Renaming 729 functions down to 298 also creates a silent failure mode for existing configs.
If someone has an approval rule on an old write function like `slack_post`, upgrading could let the renamed `slack_send` run unapproved.
So MindRoom carries a fail-closed rename table that rejects retired tool names in approval configs at startup and prints the replacement name.[^collisions]
That migration layer is extra code we wouldn't need if we'd never changed the names.

And we measured tokens across all 155 toolkits, not live accuracy across all 155.
Our controlled accuracy evidence covers GitHub (400 trials), our Wave 2 and 4 search/web consolidation (64 trials), and our `anyOf` unwrapping check (80 trials), not every integration in the catalog.

## What changes when you design tools for models

Wrapping a human API straight into an AI tool list feels fast, and then charges you tokens on every single turn.
Treating tool schemas as an interface built for models instead of humans cut half our catalog overhead, made read and write boundaries clean, and made our tools much easier for small local models to use.

[^waves]: At commit `a0471bd2d` (2026-11-25 14:27 PST), `src/` still had 233 Agno imports across 106 files (87 toolkit modules) and 47 `AGNO_COMPAT:` markers across 30 files (down from 126 reported on Oct 19). All dropped to 0 across nine waves in `mindroom-ai/mindroom`: Wave 1 [#4378](https://github.com/mindroom-ai/mindroom/pull/4378) (merged 2026-11-25 22:30 PST), Wave 2 [#4389](https://github.com/mindroom-ai/mindroom/pull/4389), Wave 3 [#4390](https://github.com/mindroom-ai/mindroom/pull/4390) and [#4408](https://github.com/mindroom-ai/mindroom/pull/4408), Wave 4 [#4388](https://github.com/mindroom-ai/mindroom/pull/4388), Wave 5 [#4394](https://github.com/mindroom-ai/mindroom/pull/4394), Wave 6 [#4401](https://github.com/mindroom-ai/mindroom/pull/4401), Wave 7 [#4392](https://github.com/mindroom-ai/mindroom/pull/4392), Wave 8 [#4403](https://github.com/mindroom-ai/mindroom/pull/4403), and Wave 9 [#4419](https://github.com/mindroom-ai/mindroom/pull/4419) (merged 2026-11-26 19:42 PST).

[^catalog-numbers]: Measured from `tests/fixtures/agno_parity/tools/schemas.json` as compact JSON tokenized with `tiktoken` `o200k_base` at commits `df7f97a04` (2026-11-24 13:16 PST) vs `295a31a16` (2026-11-27 17:34 PST): `github` 6,670 to 1,658 tokens (-75.1%), `gmail` 4,180 to 1,266 (-69.7%), `docker` 3,129 to 819 (-73.8%), and the nine Microsoft 365 toolkits (`outlook_mail`, `outlook_calendar`, `microsoft_files`, `microsoft_teams`, `microsoft_sharepoint`, `microsoft_todo`, `microsoft_onenote`, `microsoft_meetings`, `microsoft_people`, PR [#4435](https://github.com/mindroom-ai/mindroom/pull/4435)) from 17,408 to 7,168 tokens (-58.8%). With optional default-off functions enabled (`schemas_all_enabled.json`), the 155 toolkits total 317 functions with 0 duplicate names.

[^mega-split]: PR [#4458](https://github.com/mindroom-ai/mindroom/pull/4458) (`1943198dd`) and cleanup PR [#4471](https://github.com/mindroom-ai/mindroom/pull/4471), measured against `df7f97a04`: `triggers` 1 to 2 functions (-6.3% tokens), `desktop` 1 to 3 (`desktop_read`, `desktop_control`, `run_desktop_shell`, -6.7%), `browser` 1 to 2 (-13.2%), `matrix_api` 1 to 2 (-7.8%), and `workflow` 6 to 2 (-41.1%, consolidated to 1 in PR [#4436](https://github.com/mindroom-ai/mindroom/pull/4436) then split to read/write in #4458).

[^github-split]: On `main`, the 39 GitHub actions span 43 unique parameters (20 across reads, 29 across writes). The five functions are `github_read_repo` (11 actions, 13 parameters), `github_read_issues_prs` (10 actions, 16 parameters), `github_write_issues` (7 actions, 8 parameters), `github_write_pr` (4 actions, 16 parameters), and `github_write_repo` (7 actions, 14 parameters, including `delete_repository` and `delete_file`). We chose five from parameter overlap and approval risk tiers rather than sweeping 4 vs 5 vs 6, then benchmarked 39 vs 5 vs 2 vs 1 functions below.

[^anyof]: PR [#4432](https://github.com/mindroom-ai/mindroom/pull/4432) (`154614019`), measured directly against parent `154614019~1` on `schemas.json` (315 functions in both): `anyOf` dropped from 1,037 to 298 (-71.3%) and tokens from 77,143 to 70,439 (-8.7%). Plain JSON types are emitted only for derived two-member nullable unions defaulting to `None`, and OpenAI Responses serialization sets `strict: false` automatically when optional fields are present so omitted arguments aren't rejected. A live 5-model A/B eval on 8 optional-heavy tool cases (80 trials across `gemma-4-26b-a4b-it`, `gemma-4-31b-it`, `qwen3.5-9b`, `gpt-5-mini`, and local `inkling-2:mini`) scored 40/40 in both arms (100% accuracy parity) while cutting prompt tokens by 5% to 19%.

[^meta-params]: PR [#4424](https://github.com/mindroom-ai/mindroom/pull/4424) (`0ca55779b`). Hiding `mindroom_output_path` from a fast tool's schema still keeps automatic >50 KiB output-to-file protection active at runtime.

[^prompt-trim]: PR [#4332](https://github.com/mindroom-ai/mindroom/pull/4332) (`00fd8ff3a`, merged 2026-11-24 13:41 PST) and PR [#4345](https://github.com/mindroom-ai/mindroom/pull/4345). Fixture measured on `tests/fixtures/agno_parity/prompts/agent_anthropic.json` (`requests[0]`) at `df7f97a04` vs `295a31a16` (`o200k_base`).

[^eval]: PR [#4440](https://github.com/mindroom-ai/mindroom/pull/4440) (`d6c321073`) added `evals/tool_calling/`.

[^explicit-action]: PR [#4477](https://github.com/mindroom-ai/mindroom/pull/4477) (`dad71b234`, merged 2026-11-27 17:18 PST) removed the `action="send"` default on `matrix_message` and enforced required `action=` enums across the catalog in CI (with one read-only exception for `matrix_room`).

[^collisions]: PR [#4464](https://github.com/mindroom-ai/mindroom/pull/4464) (`0dbaeb16e`) normalized 74 functions across 42 integration toolkits and added fail-closed approval rename mappings in `src/mindroom/config/retired_tool_renames.py`.

[^github-eval]: Controlled single-turn benchmark (20 unambiguous GitHub tasks spanning all five groups, 4 arms, 5 models, 400 trials total, temperature 0 where supported, harness meta-parameter stripped from all arms so pure API shape is compared). Schema sizes (`o200k_base`): 39 functions 4,480 tokens (max 10 params/fn), 5 functions 1,488 tokens (max 15), 2 functions 1,338 tokens (max 28), 1 function 1,258 tokens (max 42). Exact first-try pass rates (out of 20) for 39 / 5 / 2 / 1 functions: `inkling-2:mini` 16 / 17 / 13 / 13, `qwen/qwen3.5-9b` 20 / 18 / 16 / 14, `google/gemma-4-26b-a4b-it` 19 / 18 / 15 / 14, `google/gemma-4-31b-it` 18 / 20 / 20 / 18, `openai/gpt-5-mini` 20 / 20 / 19 / 20. Totals across 100 trials per arm: 93 / 93 / 83 / 79 passed; wrong/leaked-parameter errors 0 / 0 / 1 / 7; missing-argument errors 3 / 3 / 8 / 9.

[^wave24-eval]: PR [#4439](https://github.com/mindroom-ai/mindroom/pull/4439) (`c4ea7f762`) consolidated 11 search, research, math, and web-scraping toolkits (including `calculator` 8 to 1, `serper` 4 to 2, `exa` 5 to 2, `brightdata` 4 to 1, `oxylabs` 4 to 1, `spider` 3 to 1). Live 4-model A/B eval across 16 cases (64 trials per arm): `gemma-4-26b-a4b-it` 14/16 to 16/16 (-19.1% prompt tokens), `gemma-4-31b-it` 14/16 to 16/16 (-30.6%), `qwen3.5-9b` 16/16 to 16/16 (-23.0%), `gpt-5-mini` 14/16 to 16/16 (-19.8%); total 58/64 to 64/64 (-23.4% prompt tokens).

[^spend-data]: Measured across 345,924 OpenRouter-priced MindRoom requests over seven days (Nov 20 to 27, 2026) using published OpenRouter list prices for prompt, completion, `input_cache_read`, and `input_cache_write` tokens. Token totals: 91.8% cache read, 5.9% uncached input, 1.8% cache write, 0.6% output; median request input size was 97,313 tokens (p90: 268,837). Spend shares: All models 29.7% cache read / 21.6% cache write / 30.0% uncached input / 18.7% output; `GPT-6.2 Sol` 40.1% / 41.2% / 0.1% / 18.6%; `Claude Opus 5.5` 38.7% / 35.7% / 2.7% / 22.9%; `GPT-6.2 Astra` 33.4% / 54.0% / 0.2% / 12.5%; `Claude Fable 5.2` 28.3% / 24.6% / 7.4% / 39.6%; `Gemini 4 Neon` 24.8% / 0.0% / 58.1% / 17.1%.

[^ci-invariants]: `tests/tool_system/test_toolkits.py` and `AGENTS.md` Tool Design Rules (PRs [#4464](https://github.com/mindroom-ai/mindroom/pull/4464), [#4473](https://github.com/mindroom-ai/mindroom/pull/4473), and [#4477](https://github.com/mindroom-ai/mindroom/pull/4477)).

<script src="tools-demo.js" defer></script>
