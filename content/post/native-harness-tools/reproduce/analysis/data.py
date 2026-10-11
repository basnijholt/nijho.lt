"""Read the published measurements in results/: trials.csv, one row per trial, and requests.csv, one row per request."""

import csv
from collections import defaultdict
from functools import cache
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"


@cache
def _trials() -> dict[str, list[dict[str, str]]]:
    by_configuration = defaultdict(list)
    for row in csv.DictReader(open(RESULTS / "trials.csv")):
        by_configuration[row["configuration"]].append(row)
    return by_configuration


@cache
def _requests() -> dict[tuple[str, str, str], list[dict[str, str]]]:
    by_trial = defaultdict(list)
    for row in csv.DictReader(open(RESULTS / "requests.csv")):
        by_trial[row["configuration"], row["task"], row["trial"]].append(row)
    return by_trial


def configurations() -> list[str]:
    return sorted(_trials())


def trials(configuration: str) -> list[dict[str, str]]:
    """Every trial of one configuration; ``tokens`` is empty for a trial with a request the provider gave no usage for."""
    if configuration not in _trials():
        raise ValueError(f"no trials for {configuration}")
    return _trials()[configuration]


def requests(configuration: str) -> list[list[dict[str, int]]]:
    """The requests of each trial with complete usage, in order, with integer counts."""
    return [
        [{key: int(value) for key, value in r.items() if key.endswith("_tokens")} for r in _requests()[t["configuration"], t["task"], t["trial"]]]
        for t in trials(configuration)
        if t["tokens"]
    ]
