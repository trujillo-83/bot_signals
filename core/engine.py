from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any

import yaml


@dataclass(frozen=True)
class EngineConfig:
    signals: dict
    risk: dict
    universe: List[str]


def load_universe_csv(path: str | Path) -> List[str]:
    path = Path(path)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        symbols = []
        for row in reader:
            s = (row.get("symbol") or "").strip()
            if s:
                symbols.append(s)
    return symbols


def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_dir: str | Path = "config") -> EngineConfig:
    config_dir = Path(config_dir)
    signals = load_yaml(config_dir / "signals.yml")
    risk = load_yaml(config_dir / "risk.yml")
    universe = load_universe_csv(config_dir / "universe.csv")
    return EngineConfig(signals=signals, risk=risk, universe=universe)


def generate_dummy_signal(symbol: str) -> Dict[str, Any]:
    """
    IMPORTANT: Signal standard format MUST be:
      {action, confidence, sl, tp, reason[], debug{}}

    Dummy rules:
      - Always HOLD
      - confidence 50
      - sl/tp null (None)
    """
    # Keep key order stable for readability and diffs
    return {
        "action": "HOLD",
        "confidence": 50,
        "sl": None,
        "tp": None,
        "reason": [
            "Episode 1 dummy signal",
            "Architecture-only: indicators/rules not implemented yet",
        ],
        "debug": {
            "symbol": symbol,
            "source": "engine:dummy_v1",
        },
    }



def run_engine(cfg: EngineConfig, symbols: List[str] | None = None) -> Dict[str, Any]:
    """
    Returns a dict of signals keyed by symbol.
    If symbols is None -> uses cfg.universe
    """
    use_symbols = symbols if symbols is not None else cfg.universe

    out: Dict[str, Any] = {}
    for sym in use_symbols:
        out[sym] = generate_dummy_signal(sym)
    return out
