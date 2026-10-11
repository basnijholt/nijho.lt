"""Send one tiny request to each candidate earlier model and report whether it answers."""
import asyncio
from agno.agent import Agent
from mindroom.config.models import ModelConfig
from mindroom.config.main import Config
from mindroom.constants import resolve_runtime_paths
from mindroom import model_loading

CANDIDATES = [
    ("vertexai_claude", "claude-opus-4-8"), ("vertexai_claude", "claude-opus-4-7"), ("vertexai_claude", "claude-opus-4-6"),
    ("vertexai_claude", "claude-sonnet-5"), ("vertexai_claude", "claude-sonnet-4-5"), ("vertexai_claude", "claude-opus-5"),
    ("codex", "gpt-5.6-sol"), ("codex", "gpt-5.6-luna"), ("codex", "gpt-5.5"), ("codex", "gpt-6-terra"),
]

async def one(provider, model_id):
    config = Config(models={"default": ModelConfig(provider=provider, id=model_id)})
    paths = resolve_runtime_paths()
    try:
        model = model_loading.get_model_instance(config, paths, "default", None)
        out = await Agent(model=model, telemetry=False).arun("Reply with the single word: ok")
        return f"{provider}/{model_id}: {str(out.status)} {repr((out.content or '')[:40])}"
    except Exception as exc:  # noqa: BLE001
        return f"{provider}/{model_id}: ERROR {type(exc).__name__}: {str(exc)[:160]}"

async def main():
    for line in await asyncio.gather(*(one(p, m) for p, m in CANDIDATES)):
        print(line)

asyncio.run(main())
