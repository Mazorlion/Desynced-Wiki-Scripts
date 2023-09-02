from logging import LoggerAdapter


class PrefixAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        if self.extra.get("prefix"):
            return f"{self.extra['prefix']} - {msg}", kwargs
        else:
            return msg, kwargs
