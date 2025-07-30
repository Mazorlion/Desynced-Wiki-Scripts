import logging
import colorlog
from logging import LoggerAdapter


def initLogger(level=logging.INFO):
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

    logger = colorlog.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


class PrefixAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        if self.extra and self.extra.get("prefix"):
            return f"{self.extra['prefix']} - {msg}", kwargs
        else:
            return msg, kwargs
