import json
import logging
import os
import sys
from pathlib import Path

from .config import RESP_PREVIEW


class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            base.update(record.extra)
        return json.dumps(base, ensure_ascii=False)


class KVFormatter(logging.Formatter):
    def format(self, record):
        parts = [self.formatTime(record, self.datefmt), f"level={record.levelname}"]
        msg = record.getMessage()
        if msg:
            parts.append(f"msg={msg}")
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for k, v in record.extra.items():
                parts.append(f"{k}={v}")
        return " ".join(parts)


def setup_logger(name: str = "zap_mcp") -> logging.Logger:
    level = os.environ.get("ZAP_MCP_LOG_LEVEL", "DEBUG").upper()  # Default to DEBUG
    json_mode = os.environ.get("ZAP_MCP_LOG_JSON", "0").lower() in ("1", "true", "yes")
    log_file = os.environ.get(
        "ZAP_MCP_LOG_FILE", "zap_mcp_debug.log"
    ).strip()  # Default log file in current directory
    log_http = os.environ.get("ZAP_MCP_LOG_HTTP", "1").lower() in (
        "1",
        "true",
        "yes",
    )  # Default to enabled

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.DEBUG))  # Default to DEBUG
    logger.handlers[:] = []

    formatter = (
        JsonFormatter()
        if json_mode
        else KVFormatter("%(asctime)s level=%(levelname)s msg=%(message)s")
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if log_file:
        # Ensure log file is created in current working directory
        log_path = os.path.join(os.getcwd(), log_file)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        print(f"Log file created: {log_path}")  # Inform user about log file location

    # Enable debug logging for HTTP libraries
    if log_http:
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)

    # Enable debug logging for FastAPI/Uvicorn
    logging.getLogger("fastapi").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)

    return logger
