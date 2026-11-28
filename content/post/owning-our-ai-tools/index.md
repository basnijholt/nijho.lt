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

When I started building MindRoom {{< tooltip text="MindRoom's initial commit (a062d21fd) landed on July 29, 2025, sixteen months before this post." >}}nearly a year and a half ago{{< /tooltip >}}, one of the main reasons I picked [Agno](https://github.com/agno-agi/agno) was simply that it already supported so many tools and libraries.
I got {{< tooltip text="At commit a0471bd2d (Nov 25, 2026), 87 built-in toolkit modules under src/mindroom/tools/ still imported Agno, out of 160 built-in toolkits total." >}}87 integrations{{< /tooltip >}} out of the box, covering services like GitHub, Gmail, Slack, and Docker.

In October I wrote [Roll your own, fork the rest]({{< ref "/post/roll-your-own-fork-the-rest" >}}) after piling up 126 workarounds for Agno.
By the end of October I'd replaced Agno's runtime with code MindRoom owns, leaving Agno behind as MindRoom's tool library.

This week I deleted the rest of it.
By November 25, MindRoom still imported Agno in {{< tooltip text="233 import lines across 106 files under src/ (87 of them toolkit modules under src/mindroom/tools/), plus 47 remaining AGNO_COMPAT markers across 30 files." >}}106 source files{{< /tooltip >}}.[^agno-boundary]
Using the [parallel orchestrator setup]({{< ref "/post/orchestrating-orchestrators" >}}) I wrote about earlier this week, I split those remaining toolkits and document readers into nine waves of agent sessions.
From the first wave merging on November 25 to `import agno` raising `ModuleNotFoundError` on November 26 took about {{< tooltip text="21 hours 12 minutes from Wave 1 (#4378) to Wave 9 (#4419)." >}}21 hours{{< /tooltip >}}, and all 126 workarounds from October are now gone.[^waves]

It turns out that with today's models, adding these integrations yourself is trivial.
They're all popular services with well-known APIs that exist a thousand times over in the training data.
The main reason I depended on a framework for them in 2025 doesn't hold anymore.

Owning all {{< tooltip text="160 built-in toolkits before the pass; five overlapping ones (confluence, jira, dynamic_workflow, python, web_browser_tools) were merged or retired without losing features, leaving 155." >}}155 toolkits{{< /tooltip >}} also meant we were no longer stuck with Agno's one-function-per-endpoint layout.
In [my tests on native harness tools]({{< ref "/post/native-harness-tools" >}}), I found that frontier models don't care much whether tools match the names they were trained on, while fixed per-request tokens matter a lot.
Once MindRoom owned the files, I could redesign the whole catalog around that lesson.

## Shrink tool counts, then split reads from writes

Before the rewrite, our toolkits looked just like auto-converted REST APIs.
GitHub exposed 39 functions, Gmail exposed 26, Docker exposed 24, and our nine Microsoft 365 toolkits totaled 64.

Grouping related verbs under an `action=` parameter cut GitHub from 39 functions to 5 (-75% tokens), Gmail from 26 to 5 (-70%), and Microsoft 365 from 64 to 18 (-59%).[^catalog-numbers]
Across all 155 toolkits, default functions dropped from 729 to 298 (-59%), and total tool schemas fell from {{< tooltip text="138,470 to 69,233 o200k_base tokens (-50.0%) in compact JSON across all built-in toolkits in schemas.json." >}}138,470 tokens to 69,233{{< /tooltip >}} (-50%).
We didn't strip features to hit that number: the consolidated tools cover the same operations, often with cleaner parameters and fewer bugs than the wrappers they replaced.

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
I changed our schema generator to emit plain JSON types for optional parameters whose default is `None`, while still accepting explicit `null` values at runtime.[^anyof]
In that single commit, with function count held fixed at 315, `anyOf` blocks dropped from {{< tooltip text="1,037 to 298 anyOf blocks (-71.3%), saving 6,704 tokens (-8.7%) across schemas.json in PR #4432 alone." >}}1,037 to 298{{< /tooltip >}} (-71%) and shaved 6,704 tokens off the catalog.
Real nullable parameters stay untouched, like a SQL `limit: int | None = 10` where `null` means "return all rows".

**Repeated helper arguments.**
MindRoom adds two optional arguments to tools: `background_after` to push slow work into a background job, and `mindroom_output_path` to write large outputs to disk.
Repeating their full descriptions on every function burned 70 to 95 tokens per tool.
Explaining both once in the system prompt and letting fast local tools opt out cut injected meta-parameter overhead by {{< tooltip text="background_after shrank from 47 to 28 tokens and mindroom_output_path from 49 to 24 tokens per function, plus opt-outs for fast built-ins (~72 to 73% total drop)." >}}about 72%{{< /tooltip >}}.[^meta-params]

Here's how all three changes shrink our real GitHub toolkit step by step (click any step to pause and inspect it).

<div class="mr-schema-shrinker"></div>

Earlier that same week, before Wave 1 started, I also tightened MindRoom's default system prompt to drop stale instructions and hide sections an agent doesn't use.[^prompt-trim]
Combined with the tool rewrite, our representative Claude agent fixture (identical config and conversation history) dropped from {{< tooltip text="System messages fell from 2,968 to 1,215 tokens (-59.1%) and tool schemas from 3,909 to 1,740 tokens (-55.5%) in agent_anthropic.json." >}}6,877 fixed tokens per turn down to 2,955{{< /tooltip >}} (-57%), and from 23 tools down to 9.
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

To check whether tighter descriptions with concrete call examples helped small models, we ran a targeted 10-case slice of `chat_ui` and `browser` tasks before and after compacting those two toolkits.[^ab-eval]
`inkling-2:mini` went from 6/10 to 7/10 passed with mis-calls cut from 10 to 5, `gemma-4-31b-it` went from 4/10 to 6/10 passed (with 15 mis-calls in both arms), and `gpt-5-mini` stayed at 8/10 passed while first-try passes rose from 7/10 to 8/10, mis-calls fell from 1 to 0, and input tokens dropped 21%.
Ten cases is a small sanity check, not a full benchmark, so treat it as directional rather than proof.

All of those rules now live in automated CI tests and a short Tool Design Rules section in `AGENTS.md`.[^ci-invariants]
A pull request can't merge if it adds a duplicate function name, an unprefixed integration function, or a mutating default action.

## What owning 155 toolkits costs

When Slack, Gmail, or Spotify changes an endpoint, nobody upstream is going to patch it for us.
Most of Agno's {{< tooltip text="87 Agno-backed toolkit modules were rewritten natively in Waves 2 through 8." >}}87 toolkits{{< /tooltip >}} were thin REST wrappers around `httpx`, and MindRoom still uses official vendor SDKs where the protocol is complex, so I think the trade is worth it.
It's still more code to maintain.

Renaming 729 functions down to 298 also creates a silent failure mode for existing configs.
If someone has an approval rule on an old write function like `slack_post`, upgrading could let the renamed `slack_send` run unapproved.
So MindRoom carries a fail-closed rename table that rejects retired tool names in approval configs at startup and prints the replacement name.[^collisions]
That migration layer is extra code we wouldn't need if we'd never changed the names.

Finally, be careful what you read into the token numbers.
Providers discount cached input tokens, so cutting fixed prefixes by 50 to 57% trims dollar bills by less than half, even though it still lowers cache-write cost, latency, and context-window pressure (and helps much more on local models).
We also measured tokens across the entire catalog, not accuracy across all 155 toolkits before and after.

## What changes when you design tools for models

Wrapping a human API straight into an AI tool list feels fast, and then charges you tokens on every single turn.
Treating tool schemas as an interface built for models instead of humans cut half our catalog overhead, made read and write boundaries clean, and made our tools much easier for small local models to use.

[^agno-boundary]: Counted at commit `a0471bd2d` (2026-11-25 14:27 PST): `git grep -E '^\s*(from|import)\s+agno\b' a0471bd2d -- src/` returned 233 matches in 106 files (87 under `src/mindroom/tools/`), and `git grep 'AGNO_COMPAT:' a0471bd2d -- src/` returned 47 markers in 30 files (down from 126 reported on Oct 19 after replacing Agno's runtime). Both dropped to 0 in PR [#4419](https://github.com/mindroom-ai/mindroom/pull/4419) (`29d6c51c7`).

[^waves]: Agno removal PRs in `mindroom-ai/mindroom`: Wave 1 [#4378](https://github.com/mindroom-ai/mindroom/pull/4378) (merged 2026-11-25 22:30 PST), Wave 2 [#4389](https://github.com/mindroom-ai/mindroom/pull/4389), Wave 3 [#4390](https://github.com/mindroom-ai/mindroom/pull/4390) and [#4408](https://github.com/mindroom-ai/mindroom/pull/4408), Wave 4 [#4388](https://github.com/mindroom-ai/mindroom/pull/4388), Wave 5 [#4394](https://github.com/mindroom-ai/mindroom/pull/4394), Wave 6 [#4401](https://github.com/mindroom-ai/mindroom/pull/4401), Wave 7 [#4392](https://github.com/mindroom-ai/mindroom/pull/4392), Wave 8 [#4403](https://github.com/mindroom-ai/mindroom/pull/4403), and Wave 9 [#4419](https://github.com/mindroom-ai/mindroom/pull/4419) (merged 2026-11-26 19:42 PST).

[^catalog-numbers]: Measured from `tests/fixtures/agno_parity/tools/schemas.json` as compact JSON tokenized with `tiktoken` `o200k_base` at commits `df7f97a04` (2026-11-24 13:16 PST) vs `295a31a16` (2026-11-27 17:34 PST): `github` 6,670 to 1,658 tokens (-75.1%), `gmail` 4,180 to 1,266 (-69.7%), `docker` 3,129 to 819 (-73.8%), and the nine Microsoft 365 toolkits (`outlook_mail`, `outlook_calendar`, `microsoft_files`, `microsoft_teams`, `microsoft_sharepoint`, `microsoft_todo`, `microsoft_onenote`, `microsoft_meetings`, `microsoft_people`, PR [#4435](https://github.com/mindroom-ai/mindroom/pull/4435)) from 17,408 to 7,168 tokens (-58.8%). With optional default-off functions enabled (`schemas_all_enabled.json`), the 155 toolkits total 317 functions with 0 duplicate names.

[^mega-split]: PR [#4458](https://github.com/mindroom-ai/mindroom/pull/4458) (`1943198dd`) and cleanup PR [#4471](https://github.com/mindroom-ai/mindroom/pull/4471), measured against `df7f97a04`: `triggers` 1 to 2 functions (-6.3% tokens), `desktop` 1 to 3 (`desktop_read`, `desktop_control`, `run_desktop_shell`, -6.7%), `browser` 1 to 2 (-13.2%), `matrix_api` 1 to 2 (-7.8%), and `workflow` 6 to 2 (-41.1%, consolidated to 1 in PR [#4436](https://github.com/mindroom-ai/mindroom/pull/4436) then split to read/write in #4458).

[^github-split]: On `main`, the 39 GitHub actions span 43 unique parameters (20 across reads, 29 across writes). The five functions are `github_read_repo` (11 actions, 13 parameters), `github_read_issues_prs` (10 actions, 16 parameters), `github_write_issues` (7 actions, 8 parameters), `github_write_pr` (4 actions, 16 parameters), and `github_write_repo` (7 actions, 14 parameters, including `delete_repository` and `delete_file`). We picked that five-way split from parameter overlap and approval risk tiers rather than benchmarking 4 vs 5 vs 6 functions directly.

[^anyof]: PR [#4432](https://github.com/mindroom-ai/mindroom/pull/4432) (`154614019`), measured directly against parent `154614019~1` on `schemas.json` (315 functions in both): `anyOf` dropped from 1,037 to 298 (-71.3%) and tokens from 77,143 to 70,439 (-8.7%). Plain JSON types are emitted only for derived two-member nullable unions defaulting to `None`, and OpenAI Responses serialization sets `strict: false` automatically when optional fields are present so omitted arguments aren't rejected.

[^meta-params]: PR [#4424](https://github.com/mindroom-ai/mindroom/pull/4424) (`0ca55779b`). Hiding `mindroom_output_path` from a fast tool's schema still keeps automatic >50 KiB output-to-file protection active at runtime.

[^prompt-trim]: PR [#4332](https://github.com/mindroom-ai/mindroom/pull/4332) (`00fd8ff3a`, merged 2026-11-24 13:41 PST) and PR [#4345](https://github.com/mindroom-ai/mindroom/pull/4345). Fixture measured on `tests/fixtures/agno_parity/prompts/agent_anthropic.json` (`requests[0]`) at `df7f97a04` vs `295a31a16` (`o200k_base`).

[^eval]: PR [#4440](https://github.com/mindroom-ai/mindroom/pull/4440) (`d6c321073`) added `evals/tool_calling/`.

[^explicit-action]: PR [#4477](https://github.com/mindroom-ai/mindroom/pull/4477) (`dad71b234`, merged 2026-11-27 17:18 PST) removed the `action="send"` default on `matrix_message` and enforced required `action=` enums across the catalog in CI (with one read-only exception for `matrix_room`).

[^collisions]: PR [#4464](https://github.com/mindroom-ai/mindroom/pull/4464) (`0dbaeb16e`) normalized 74 functions across 42 integration toolkits and added fail-closed approval rename mappings in `src/mindroom/config/retired_tool_renames.py`.

[^ab-eval]: PR [#4467](https://github.com/mindroom-ai/mindroom/pull/4467) (`3cdb24e3f`), 10 targeted `chat_ui` (canvas) and `browser` cases comparing `1943198dd` against compacted schemas: `inkling-2:mini-vllm` 6/10 to 7/10 passed, mis-calls 10 to 5, input tokens 475,560 to 448,363 (-5.7%); `google/gemma-4-31b-it` 4/10 to 6/10 passed, 15 mis-calls in both arms; `openai/gpt-5-mini` 8/10 passed in both arms, first-try 7/10 to 8/10, mis-calls 1 to 0, input tokens 284,256 to 223,645 (-21.3%).

[^ci-invariants]: `tests/tool_system/test_toolkits.py` and `AGENTS.md` Tool Design Rules (PRs [#4464](https://github.com/mindroom-ai/mindroom/pull/4464), [#4473](https://github.com/mindroom-ai/mindroom/pull/4473), and [#4477](https://github.com/mindroom-ai/mindroom/pull/4477)).

<script src="tools-demo.js" defer></script>
