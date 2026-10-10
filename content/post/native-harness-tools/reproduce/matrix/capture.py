"""Capture one standard-mode and one minimal-mode request per model, with MindRoom's full provider request log on."""
import asyncio
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, "/work/rrsi-minimal")
import matrix_eval as mx  # noqa: E402

provider, model, namespace = sys.argv[1:4]
cell_dir = Path("/work/rrsi-minimal/capture") / model.replace(".", "_")
cell_dir.mkdir(parents=True, exist_ok=True)
config = mx.write_config(cell_dir, provider, model, namespace)
cfg = yaml.safe_load(config.read_text())
cfg["debug"] = {"log_llm_requests": True, "llm_request_log_dir": str(cell_dir / "llm_requests")}
config.write_text(yaml.safe_dump(cfg, sort_keys=False))
mx.RUNS = cell_dir / "jobs"  # keep capture trials out of the eval results


async def main(rt):
    client = await mx.mclient.client_for(mx.EVAL_USER, mx.EVAL_PASSWORD)
    try:
        for mode in ("standard", "minimal"):
            await mx.one_trial(rt, client, f"capture-{mode}", mode, 0, "find_files_h0")
    finally:
        await client.close()


with mx.Runtime(cell_dir, namespace, config) as rt:
    asyncio.run(main(rt))
print("logs:", sorted(str(p) for p in (cell_dir / "llm_requests").rglob("*") if p.is_file())[:5])
