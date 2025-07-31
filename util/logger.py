import logging
import colorlog
from logging import LoggerAdapter


def get_logger():
    logger = colorlog.getLogger("DesyncedWiki")
    if not logger.hasHandlers():
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)s:%(name)s:%(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        )

        logger.addHandler(handler)

    return logger


class PrefixAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        if self.extra and self.extra.get("prefix"):
            return f"{self.extra['prefix']} - {msg}", kwargs
        else:
            return msg, kwargs
