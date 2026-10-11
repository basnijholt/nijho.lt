"""Which explicit reasoning effort matches the Codex backend's default? Reasoning tokens on a hard puzzle, 3 samples each."""
import asyncio
import statistics

from agno.agent import Agent
from mindroom import model_loading
from mindroom.config.main import Config
from mindroom.config.models import ModelConfig
from mindroom.constants import resolve_runtime_paths

PROMPT = (
    "A 5x5 grid has a robot at the top-left corner. It may move only right or down, and it must avoid the cells "
    "(2,2), (3,1) and (1,3) (rows and columns numbered from 0). How many distinct paths reach the bottom-right corner? "
    "Reply with just the number."
)
LEVELS = [None, "low", "medium", "high"]


async def one(model_id, level):
    extra = {"reasoning_effort": level} if level else None
    config = Config(models={"default": ModelConfig(provider="codex", id=model_id, extra_kwargs=extra)})
    m = model_loading.get_model_instance(config, resolve_runtime_paths(), "default", None)
    out = await Agent(model=m, telemetry=False).arun(PROMPT)
    return out.metrics.reasoning_tokens or 0


async def main():
    for model_id in ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"):
        for level in LEVELS:
            vals = await asyncio.gather(*(one(model_id, level) for _ in range(3)))
            print(f"{model_id} {level or 'default'}: reasoning tokens {vals} median {statistics.median(vals)}")


asyncio.run(main())
