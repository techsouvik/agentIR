"""Structured logging configuration for AgentIR."""

import logging
import sys
from typing import cast

import structlog


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure structlog for CLI or programmatic execution."""
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=log_level,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True)
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "agentir") -> structlog.stdlib.BoundLogger:
    """Retrieve a configured bound logger."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
