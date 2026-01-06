from __future__ import annotations

import logging
from pathlib import Path


class ContextFilter(logging.Filter):
    """Inject run context into every log record."""
    def __init__(self, run_id: str, config_hash: str) -> None:
        super().__init__()
        self.run_id = run_id
        self.config_hash = config_hash

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self.run_id
        record.config_hash = self.config_hash
        return True


def get_logger(
    name: str,
    run_id: str,
    config_hash: str,
    log_path: str = "logs/bot.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Console: clean (readable for humans / YouTube)
    File: verbose (audit trail: run_id + cfg on every line)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    # Console formatter (simple)
    console_fmt = "%(asctime)s | %(levelname)s | %(message)s"
    # File formatter (full context)
    file_fmt = "%(asctime)s | %(levelname)s | run_id=%(run_id)s | cfg=%(config_hash)s | %(name)s | %(message)s"

    datefmt = "%Y-%m-%d %H:%M:%S"

    console_formatter = logging.Formatter(fmt=console_fmt, datefmt=datefmt)
    file_formatter = logging.Formatter(fmt=file_fmt, datefmt=datefmt)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(console_formatter)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(file_formatter)

    ctx_filter = ContextFilter(run_id=run_id, config_hash=config_hash)
    logger.addFilter(ctx_filter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.propagate = False
    return logger
