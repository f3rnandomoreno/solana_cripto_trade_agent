import csv
import logging
from pathlib import Path
from typing import Dict
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "trades.csv"
APP_LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logger() -> logging.Logger:
    """Configure a logger with both console and file output with rotation."""
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with Rich formatting
    console_handler = RichHandler(markup=True)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation - cuando el archivo llega a 10MB, 
    # se crea trading_bot.log.1, trading_bot.log.2, etc. 
    # Se mantienen los últimos 5 archivos, los más antiguos se eliminan
    file_handler = RotatingFileHandler(
        APP_LOG_FILE, 
        maxBytes=10 * 1024 * 1024,  # 10MB por archivo
        backupCount=5,  # mantener 5 archivos de respaldo
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_trade(data: Dict[str, str]) -> None:
    """Append trade information to the CSV log."""
    write_header = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(data)
