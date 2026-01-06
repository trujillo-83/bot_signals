from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List

from core.engine import load_config, run_engine
from services.logger import get_logger
from services.storage import write_json_atomic


NY_TZ = ZoneInfo("America/New_York")


def compute_config_hash(config_dir: str | Path = "config") -> str:
    config_dir = Path(config_dir)
    files = sorted([p for p in config_dir.rglob("*") if p.is_file()])

    h = hashlib.sha256()
    for p in files:
        h.update(str(p.relative_to(config_dir)).encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def now_ny_iso() -> str:
    return datetime.now(NY_TZ).isoformat(timespec="seconds")


def pick_symbols(universe: List[str], symbol: str | None, run_all: bool) -> List[str]:
    if run_all:
        return universe

    if symbol:
        # if user passes a symbol, run that one only
        return [symbol.strip().upper()]

    # default: first symbol only (YouTube-friendly)
    return [universe[0]] if universe else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config", help="Config folder path")
    parser.add_argument("--symbol", default=None, help="Run only this symbol (e.g., AAPL)")
    parser.add_argument("--all", action="store_true", help="Run full universe")
    args = parser.parse_args()

    run_id = uuid4().hex[:12]
    config_hash = compute_config_hash(args.config)

    logger = get_logger("bot_signals", run_id=run_id, config_hash=config_hash)

    # Clean console line for camera
    logger.info(f"RUN start | run_id={run_id} | cfg={config_hash} | ts_ny={now_ny_iso()}")

    cfg = load_config(args.config)
    symbols = pick_symbols(cfg.universe, args.symbol, args.all)

    logger.info(f"Universe loaded: {len(cfg.universe)} symbols | Running: {symbols}")
    logger.info(f"rule_version={cfg.signals.get('rule_version')}")

    signals_by_symbol = run_engine(cfg, symbols=symbols)

    payload: Dict[str, Any] = {
        "meta": {
            "run_id": run_id,
            "config_hash": config_hash,
            "timestamp_ny": now_ny_iso(),
            "timezone": "America/New_York",
            "rule_version": cfg.signals.get("rule_version"),
            "universe_count": len(cfg.universe),
            "symbols_ran": symbols,
        },
        "signals": signals_by_symbol,
    }

    ts_for_file = datetime.now(NY_TZ).strftime("%Y%m%d_%H%M%S")
    out_path = Path("artifacts/signals") / f"signals_{ts_for_file}_{run_id}.json"

    write_json_atomic(out_path, payload)

    # One clean summary line for camera
    if symbols:
        s0 = symbols[0]
        sig0 = signals_by_symbol[s0]
        logger.info(
            f"SUMMARY | symbol={s0} | action={sig0['action']} | conf={sig0['confidence']} | sl={sig0['sl']} | tp={sig0['tp']} | out={out_path.as_posix()}"
        )
    else:
        logger.info(f"SUMMARY | No symbols ran | out={out_path.as_posix()}")

    logger.info("RUN completed OK")

    # Ensure log flush/close
    for h in list(logger.handlers):
        try:
            h.flush()
            h.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
