from dataclasses import dataclass
from .config import Config

@dataclass
class Context:
    config: Config = None
    config_is_fallback_runtime: bool = False
    config_file: str = None


ctx: Context = Context()


def app_ctx() -> Context:
    global ctx
    return ctx
