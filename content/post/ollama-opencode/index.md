---
title: "Using gpt-oss:20b in OpenCode with a larger context and high reasoning"
subtitle: "Setting up a fully open and local agent workflow for private data"
summary: "I set up OpenAI's gpt-oss:20b in Ollama with a larger context window and high reasoning in OpenCode to process my private journal entries locally."
date: 2025-11-13
draft: false
featured: true
authors:
  - admin
tags:
  - python
  - ai
  - llm
  - ollama
  - local-first
  - open-source
  - opencode
categories:
  - "level:beginner"
---

I have hundreds of private journal entries stored locally, many with incorrect date formats.
The correct date is in the filename, so I wanted to use an LLM to batch update them.
However, I do not want to share my **private journal** with any third-party service.
Instead, I used [Ollama](https://ollama.com/) with `gpt-oss:20b` and [OpenCode](https://opencode.ai/) to do this all locally.

It took me too long to figure out how to get `gpt-oss:20b` working well in OpenCode, so I’m writing the steps down (partly for my future self).

In the end I could simply run the following command to batch update my journal entries:

```bash
for file in ./*.md; do
  opencode -m ollama/gpt-oss-20b-high-32k run \
    "Use the date in the filename \"${file}\" and correct the 'date:' entry in the YAML front matter of this file"
done
```

{{% callout note %}}
Yes, of course I could have scripted this without an LLM, but where’s the fun in that?
Also I might want to do more complex updates in the future on less structured data.
{{% /callout %}}

This post describes how to:

1. Create a **long-context** variant of `gpt-oss:20b` in Ollama.
2. Configure **OpenCode** to use that model with **high reasoning** enabled by default.

---

## 1. Create a long-context model in Ollama

Start an interactive session with `gpt-oss:20b`:

```bash
ollama run gpt-oss:20b
```

In the prompt:

```text
>>> /set parameter num_ctx 32768
>>> /save gpt-oss-20b-32k
>>> /bye
```

This:

* Sets the context window to **32k tokens** (`num_ctx 32768`).
* Saves a new model/tag named **`gpt-oss-20b-32k`** with that parameter stored.

Adjust `num_ctx` as needed for your GPU (e.g. `16384`, `65536`, etc.).

---

## 2. Configure OpenCode to use high reasoning

OpenCode talks to Ollama via the OpenAI-compatible API. In:

`~/.config/opencode/opencode.json`

add a provider configuration similar to:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": {
        "baseURL": "http://localhost:11434/v1",
        "apiKey": "ollama"
      },
      "models": {
        "gpt-oss-20b-high-32k": {
          "id": "gpt-oss-20b-32k",
          "options": {
            "extraBody": {
              "think": "high"
            }
          }
        }
      }
    }
  },

  "model": "ollama/gpt-oss-20b-high-32k"
}
```

Notes:

* `"id": "gpt-oss-20b-32k"` refers to the custom Ollama model with the larger context window.
* `"think": "high"` enables **high reasoning** for `gpt-oss:20b` on each request.

---

## 3. Select the model in OpenCode

Run OpenCode:

```bash
opencode
```

Inside OpenCode:

```text
> /models
```

Then select:

```text
ollama/gpt-oss-20b-high-32k
```

From this point, OpenCode uses `gpt-oss:20b` with:

* A **larger context window** (configured in Ollama), and
* **High reasoning** enabled by default (via `think: "high"`).
