import csv
import logging
from pathlib import Path
from typing import Dict

from rich.logging import RichHandler


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "trades.csv"


def setup_logger() -> logging.Logger:
    """Configure a basic logger with rich formatting."""
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    handler = RichHandler(markup=True)
    logger.addHandler(handler)
    return logger


def log_trade(data: Dict[str, str]) -> None:
    """Append trade information to the CSV log."""
    write_header = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(data)
