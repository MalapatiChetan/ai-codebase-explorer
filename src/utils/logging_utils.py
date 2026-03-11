"""Helpers for consistent, low-noise logging."""

import logging
import warnings


def configure_library_log_levels() -> None:
    """Reduce noisy third-party logs during analyze/indexing flows."""
    noisy_loggers = [
        "httpx",
        "httpcore",
        "urllib3",
        "sentence_transformers",
        "huggingface_hub",
        "faiss",
        "faiss.loader",
        "transformers",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    warnings.filterwarnings(
        "ignore",
        message="Warning: You are sending unauthenticated requests to the HF Hub.*",
    )


def log_step(logger: logging.Logger, step: int, message: str) -> None:
    """Emit a standardized step log line."""
    logger.info(f"[STEP {step}] {message}")
