from dataclasses import dataclass

@dataclass
class AppCtx:
    main: object = None

_app_ctx: AppCtx = AppCtx()

def app_ctx() -> AppCtx:
    """Get the application context."""
    global _app_ctx
    return _app_ctx