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
    return (m2.input_tokens or 0) + (getattr(m2, 'cache_read_tokens', 0) or 0) + (getattr(m2, 'cache_write_tokens', 0) or 0)


async def main():
    for provider, model in (("vertexai_claude", "claude-sonnet-5-5"),):
        base = await usage(provider, model, None, None)
        for mode in ("standard", "minimal"):
            system = open(f"/work/tmp/sys-{model}-{mode}.txt").read()
            with_system = await usage(provider, model, system, None)
            with_tools = await usage(provider, model, None, functions(model, mode))
            print(f"{model} {mode}: system prompt {with_system - base} tokens, tool definitions {with_tools - base} tokens (baseline request {base})")


asyncio.run(main())
