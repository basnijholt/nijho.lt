"""Exact token cost of the system prompt and the tool definitions in each mode, from each provider's own counts."""
import asyncio
import json

from agno.agent import Agent
from agno.tools.function import Function
from mindroom import model_loading
from mindroom.config.main import Config
from mindroom.config.models import ModelConfig
from mindroom.constants import resolve_runtime_paths


def functions(model, mode):
    out = []
    for t in json.load(open(f"/work/tmp/tools-{model}-{mode}.json")):
        spec = t.get("function", t)  # Anthropic requests keep the schema under input_schema, OpenAI ones under parameters
        f = Function(name=spec["name"], description=spec.get("description"), parameters=spec.get("parameters") or spec.get("input_schema") or {"type": "object", "properties": {}})
        f.entrypoint = lambda **_: "ok"
        out.append(f)
    return out


async def usage(provider, model, system, tools):
    config = Config(models={"default": ModelConfig(provider=provider, id=model)})
    m = model_loading.get_model_instance(config, resolve_runtime_paths(), "default", None)
    agent = Agent(model=m, telemetry=False, system_message=system or None, tools=tools or None, build_context=bool(system))
    out = await agent.arun("Reply with the single word ok and do not call any tool.")
    m2 = out.metrics
    print(f"  {model}: input {m2.input_tokens}, cache read {m2.cache_read_tokens}, cache write {m2.cache_write_tokens}")
    if provider == "codex":
        # OpenAI counts cached input inside input_tokens already.
        return m2.input_tokens or 0
    # Anthropic reports cache reads and writes beside the uncached input.
    return (m2.input_tokens or 0) + (m2.cache_read_tokens or 0) + (m2.cache_write_tokens or 0)


async def main():
    for provider, model in (("vertexai_claude", "claude-sonnet-5-5"), ("codex", "gpt-6-astra")):
        base = await usage(provider, model, None, None)
        for mode in ("standard", "minimal"):
            system = open(f"/work/tmp/sys-{model}-{mode}.txt").read()
            with_system = await usage(provider, model, system, None)
            with_tools = await usage(provider, model, None, functions(model, mode))
            # The parts are measured apart; the whole request checks that they add up.
            with_both = await usage(provider, model, system, functions(model, mode))
            print(f"{model} {mode}: system prompt {with_system - base} tokens, tool definitions {with_tools - base} tokens, together {with_both - base} (baseline request {base})")


asyncio.run(main())
