"""Check that the effort settings are accepted, and how much each one reasons on a small puzzle."""
import asyncio
from agno.agent import Agent
from mindroom.config.models import ModelConfig
from mindroom.config.main import Config
from mindroom.constants import resolve_runtime_paths
from mindroom import model_loading

CASES = [
    ("codex", "gpt-6-astra", {}), ("codex", "gpt-6-astra", {"reasoning_effort": "low"}), ("codex", "gpt-6-astra", {"reasoning_effort": "high"}),
    ("vertexai_claude", "claude-sonnet-5-5", {}), ("vertexai_claude", "claude-sonnet-5-5", {"output_config": {"effort": "low"}}),
    ("vertexai_claude", "claude-sonnet-5-5", {"output_config": {"effort": "high"}}),
]
PROMPT = "How many of the integers from 1 to 200 are divisible by 3 or 5 but not by 15? Reply with just the number."

async def one(provider, model_id, extra):
    config = Config(models={"default": ModelConfig(provider=provider, id=model_id, extra_kwargs=extra or None)})
    try:
        model = model_loading.get_model_instance(config, resolve_runtime_paths(), "default", None)
        out = await Agent(model=model, telemetry=False).arun(PROMPT)
        m = out.metrics
        return f"{model_id} {extra}: {out.status} {(out.content or '')[:20]!r} out={getattr(m, 'output_tokens', None)} reasoning={getattr(m, 'reasoning_tokens', None)}"
    except Exception as exc:  # noqa: BLE001
        return f"{model_id} {extra}: ERROR {type(exc).__name__}: {str(exc)[:200]}"

async def main():
    for line in await asyncio.gather(*(one(*c) for c in CASES)):
        print(line)

asyncio.run(main())
