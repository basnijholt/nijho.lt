---
title: "I built my own SOTA file-based RAG and Markdown Memory system with Git integration"
subtitle: "Why I rejected vector DBs and web UIs in favor of Markdown, Git, and a simple folder."
summary: "I wanted my AI agents to remember me and read my documents, but existing solutions required complex APIs or opaque databases. After my ambitious AI Journal project hit the wall of local model limitations, I took a different approach: clone LlamaIndex, LangChain, Letta, Mem0, and PydanticAI, study how SOTA systems work, and re-implement the best parts with minimal dependencies and ONNX instead of PyTorch."
date: 2025-12-15
draft: false
featured: true
authors:
  - admin
tags:
  - python
  - ai
  - rag
  - memory
  - local-first
  - open-source
  - agent-cli
  - aijournal
  - openai
  - chromadb
  - onnx
categories:
  - Software Development
  - AI
  - level:intermediate
image:
  caption: "The architecture of a file-based memory system"
  focal_point: "Smart"
  placement: 2
  preview_only: false
---

{{< toc >}}

## 1. The Amnesia Problem

If you've read my posts on [agentic coding]({{< ref "/post/agentic-coding" >}}) or my [local AI journey]({{< ref "/post/local-ai-journey" >}}), you know I am all-in on using AI to control my computer and write software.
But there has been a glaring hole in my setup: **Context**.

LLMs are brilliant but amnesiac.
Every time I start a new chat, the model forgets who I am, what I'm working on, and that I prefer [functional Python code]({{< ref "/post/functional-python" >}}) over object-oriented styles.
Worse, it also forgets the thing I just told it five minutes ago in another window.

The industry solution to this is RAG (Retrieval-Augmented Generation) and Memory.
But when I looked at the available tools, I hit a wall.

Most solutions fell into two buckets:
1.  **SaaS / Web UIs:** Upload your files to a cloud service or use a specific web chat interface that locks you in.
2.  **Developer Libraries:** "Just use LangChain/LlamaIndex!" they say. Great, now I have to write a Python script every time I want to ask a question about a PDF?

I didn't want a library. I didn't want a web UI.
**I wanted a folder.**
I wanted to drop a file into `~/my-docs`, and have my AI instantly know about it.
And I wanted my AI's "memory" to be a file I can edit, not a hidden vector in a database I can't inspect.

So I decided to build my own file-based solution.

{{% callout note %}}
**TL;DR:** I built [`agent-cli`](https://github.com/basnijholt/agent-cli) features that combine two ideas:

1. **File-based storage:** Documents in a folder, memories as Markdown files with Git versioning.
2. **OpenAI-compatible proxy:** Works with *any* OpenAI-compatible tool—Cursor, Cline, Open WebUI, LibreChat, Lobe Chat, your terminal—without lock-in.

Tools like Open WebUI have built-in RAG, but that forces you to use only Open WebUI.
My proxy means I can switch tools whenever I want, and they all share the same memory and document index.
{{% /callout %}}

## 2. Learning from failure: AI Journal

I have to be honest: this isn't my first attempt at building a memory system.

A few months ago, I built [**AI Journal**](https://github.com/basnijholt/aijournal)—an ambitious local-first journaling app where an AI would read your entries and build a "living self-model" of who you are.
It had sophisticated features: a structured "persona core," typed "claim atoms" with evidence links, four organizational layers (L1→L4), recency-aware scoring with decay functions, and Git-based time travel to "ask questions of your younger self."

The architecture was solid.
The problem was simpler: **local models aren't good enough yet.**

I designed the whole thing to run entirely on Ollama with my RTX 3090.
But even with a 24GB GPU, the models couldn't reliably extract structured claims, handle the multi-step reconciliation, or maintain coherence across long conversations.
The vision was right; the execution hit the wall of current local LLM capabilities.

The lesson wasn't that my ideas were wrong—it's that I tried to build the whole cathedral at once instead of laying bricks.
This time, I took a different approach: **tackle it problem by problem.**
Instead of designing a complete system upfront, I would re-implement small, proven elements of memory and RAG systems, ensuring every technical detail is solid and research-backed.
The experience and UX would be my own, but the algorithms would be stolen from the best.

## 3. How I studied SOTA: Clone, read, re-implement

My approach was methodical.
I cloned five major frameworks into the same workspace as `agent-cli`:

- **[LlamaIndex](https://github.com/run-llama/llama_index)**: The OG RAG framework
- **[LangChain](https://github.com/langchain-ai/langchain)**: The kitchen-sink approach
- **[Letta](https://github.com/letta-ai/letta)** (formerly MemGPT): Stateful agents with long-term memory
- **[Mem0](https://github.com/mem0ai/mem0)**: Focused specifically on memory extraction
- **[PydanticAI](https://github.com/pydantic/pydantic-ai)**: Clean, typed agent framework

I then used an army of AI models to help me understand the architectures:

- **GPT-5.1** and **Codex Max** for implementation
- **Gemini 3 Pro** for its massive context window to ingest entire codebases
- **Opus 4.5** for architectural reasoning
- **ChatGPT Pro** (with Deep Research) to validate my understanding against papers and documentation

This sounds excessive, but it saved me from repeating the AI Journal disaster.
Instead of guessing how two-stage retrieval should work, I could read exactly how LlamaIndex implements it.
Instead of inventing my own memory reconciliation, I could study how Letta handles contradictions.

{{% callout note %}}
**The key insight:** These frameworks are incredibly over-engineered for my use case, but the *core algorithms* are gold.
My job was to extract the essence and re-implement it cleanly.
{{% /callout %}}

## 4. The dependency problem: Why ONNX over PyTorch

One thing became immediately clear when studying these frameworks: **they're massive**.

Installing LlamaIndex with all its dependencies pulls in PyTorch.
PyTorch alone is **2-3GB**.
Add transformers, sentence-transformers, and the kitchen sink, and you're looking at an **8GB+ environment** just to ask questions about some PDFs.

This is insane for a CLI tool.

One of my core design goals was **minimal dependencies**.
I wanted `agent-cli` to install in seconds, not minutes.
I wanted it to work on my Mac, my NixOS server, and my friend's laptop without downloading half the internet.

The solution: **ONNX Runtime**.

ONNX Runtime is ~200MB and runs inference on basically anything—CPU, CUDA, even Apple Silicon.
For embeddings, I use `text-embedding-3-small` via OpenAI's API (cheap and fast) or local ONNX models.
For re-ranking, I use a cross-encoder exported to ONNX (`Xenova/ms-marco-MiniLM-L-6-v2`).

The result: `pip install agent-cli[rag]` takes about 30 seconds and adds ~300MB.
Compare that to the multi-gigabyte behemoths of the "production-ready" frameworks.

{{< detail-tag "Click to see the dependency comparison" >}}
**Typical RAG framework install:**
```
pytorch==2.x           ~2.5GB
transformers           ~500MB
sentence-transformers  ~300MB
langchain              ~200MB
chromadb               ~100MB
+ various deps         ~500MB
─────────────────────────────
Total: ~4-8GB
```

**agent-cli[rag] install:**
```
onnxruntime            ~200MB
chromadb               ~100MB
fastapi + uvicorn      ~20MB
watchfiles             ~5MB
─────────────────────────────
Total: ~350MB
```
{{< /detail-tag >}}

## 5. RAG: Just let me grep it (kind of)

My requirement for RAG was simple: **Files on disk are the source of truth.**

I didn't want to manage an ingestion pipeline or trigger APIs.
I implemented a [RAG proxy](https://github.com/basnijholt/agent-cli/blob/main/docs/architecture/rag.md) that uses OS-level file watchers (`watchfiles`).
Here is the workflow:

1.  I drop a PDF, Markdown, or Python file into `~/rag_docs`.
2.  The system detects the `Create` event.
3.  It chunks the text and embeds it into a local ChromaDB instance.
4.  It's immediately searchable.

### The Architecture: OpenAI Compatibility

The "secret sauce" isn't the retrieval itself; it's how I expose it.
Instead of building a custom chat app, I built an **OpenAI-compatible proxy**.

```python
# The proxy intercepts the chat request
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # 1. Search local docs for query
    # 2. Inject context into system prompt
    # 3. Forward to real LLM (OpenAI/Ollama)
    return await process_chat_request(...)
```

This means I can set `OPENAI_BASE_URL=http://localhost:8000/v1` in virtually *any* tool—my terminal, a web UI, or an IDE—and that tool instantly gains the ability to "read" my document folder.

### Two-Stage Retrieval: The SOTA approach

This is where studying LlamaIndex paid off.
Standard "semantic search" (using just embeddings/bi-encoders) is often disappointing.
It finds text that *looks* similar but isn't actually relevant.

LlamaIndex, Cohere, and academic papers all converge on the same solution: **Two-Stage Retrieval**.

1.  **Fast Stage:** Retrieve 3x candidates using standard embeddings (`text-embedding-3-small` or local models).
2.  **Smart Stage:** Use a **Cross-Encoder** to re-rank the results.

A cross-encoder looks at the query and the document *together* and outputs a relevance score.
It's computationally heavier, but since I'm running this locally on my RTX 3090 (or even CPU via ONNX), the 50ms latency penalty is worth it for results that are actually useful.

I didn't invent this—I just implemented it cleanly without the 8GB dependency tax.

## 6. Memory: Files over Databases

This is where my approach diverges most from standard tools like Mem0.
Most memory systems treat memories as database rows.
If the AI remembers "User likes pizza," that's a vector in a DB.
If it hallucinates and records "User hates pizza," good luck fixing it.
You need to write a script to query the DB and delete the row.

**I hate data I can't touch.**

My memory system stores every fact as a **Markdown file** with YAML front matter.

```markdown
---
id: "550e8400-e29b-41d4-a716-446655440000"
role: "memory"
created_at: "2025-12-15T10:00:00Z"
conversation_id: "default"
---
The user prefers using 'uv' for Python package management.
```

### Git Integration: Time Travel for your Brain 🕰️

Because memories are just files, I added a feature that I haven't seen anywhere else: **Automatic Git Versioning**.

Every time the AI learns a new fact, updates an old one, or deletes a contradiction, the system automatically commits the change to a local git repository.

This leads to incredible capabilities:
1.  **Inspectability:** I can `git log` and see exactly *when* the AI learned something.
2.  **Correction:** If the AI learns something wrong, I open the markdown file in VS Code, edit it, and save.
3.  **Reversion:** Agent hallucinated wildly yesterday? `git reset --hard HEAD~1`.

### The Reconciliation Loop (learned from Letta)

The logic for storing memories isn't just "append to file."
Studying Letta (MemGPT) taught me that memory systems need active **reconciliation**.
When I say "Actually, I switched to poetry," the system:

1.  **Retrieves** existing memories about package managers.
2.  **Decides** (using a lightweight LLM) whether to `ADD`, `UPDATE`, or `DELETE`.
3.  **Executes** the file operation (moving the old fact to a `deleted/` folder for audit trails).

This keeps the memory bank clean and contradictory-free, unlike simple vector stores that just accumulate conflicting junk over time.

## 7. Why building this was necessary

You might ask: "Bas, why write thousands of lines of code for this? Why not just use ChatGPT's memory or install LangChain?"

Three reasons: **Privacy**, **Integration**, and **Dependencies**.

### Privacy
I want to feed my AI my financial records, my health data, and my private journals.
I am not comfortable sending that to OpenAI's long-term storage or some VC-backed startup's vector cloud.
With `agent-cli`, the vectors live in `~/.cache/agent-cli/chroma`, the files live in `~/documents`, and the only thing leaving my machine is the specific context needed for a specific query (if I use a cloud model) or nothing at all (if I use Ollama).

### Integration
By building this as an API proxy, I solved the "fragmented tools" problem.
Any tool that supports custom OpenAI-compatible endpoints works out of the box:

- **`agent-cli chat`** in the terminal
- **Cursor** or **Cline** for agentic coding
- **Open WebUI**, **LibreChat**, or **Lobe Chat** in the browser

Because my system speaks "OpenAI," all of these tools share the *same* memory and the *same* document index.
If I tell the terminal agent "I'm working on Project X," and then switch to Cursor, Cursor knows about Project X.
I can try a new chat UI tomorrow without losing anything—just point it to `localhost:8000`.

### Dependencies
I refuse to accept that asking questions about a PDF requires downloading 8GB of PyTorch.
By carefully choosing ONNX Runtime over the PyTorch ecosystem, I kept the entire install lightweight and fast.
This matters when you want to run the system on a cheap VPS or your friend's laptop.

## 8. Try it yourself

The entire system is open-source and available in [`agent-cli`](https://github.com/basnijholt/agent-cli).

If you want to try the RAG proxy with your own documents:

```bash
# Install with RAG support (~300MB, not 8GB!)
uv tool install "agent-cli[rag]"

# Start the proxy watching your documents folder
agent-cli rag-proxy \
  --docs-folder ~/my-documents \
  --openai-api-key sk-...
```

Then just point your chat app to `http://localhost:8000/v1`.

For the memory system:

```bash
# Install with Memory support
uv tool install "agent-cli[memory]"

# Start the memory proxy
agent-cli memory proxy \
    --memory-path ./my-brain \
    --openai-api-key sk-...
```

## 9. What I learned

This journey reinforced a few beliefs:

1. **Lay bricks, don't build cathedrals.** AI Journal failed not because the ideas were wrong, but because I tried to build a complete system before validating individual components. This time I tackled problems one at a time—chunking, retrieval, re-ranking, memory reconciliation—and only combined them once each piece worked.

2. **Study implementations, not just papers.** Reading about two-stage retrieval is one thing. Reading how LlamaIndex actually implements it—the edge cases, the defaults, the performance tradeoffs—is far more valuable. Clone the repos. Read the code.

3. **Dependencies matter.** The difference between a 300MB install and an 8GB install is the difference between a tool people actually use and a tool that rots in a GitHub repo. ONNX Runtime over PyTorch was one of the best decisions I made.

4. **Files are the ultimate API.** By stripping away the complex databases and proprietary interfaces, I ended up with a system that is robust, version-controllable, and surprisingly simple to reason about.

5. **Use the best model for each job.** I used five different AI models during development, each with different strengths. Gemini 3 Pro for ingesting entire codebases, Opus 4.5 for architectural reasoning, Codex Max for implementation. The days of loyalty to a single model are over.

Now, if only I could get the AI to remember to run the tests before pushing to production... (Wait, I can just add that to the memory!)
