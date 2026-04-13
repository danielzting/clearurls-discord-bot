from .paths import (
    PATH_PACKAGE_DATA,
    PATH_RULESETS
)
from .rulesets import IGNORED_PROVIDERS

__all__ = [
    "PATH_PACKAGE_DATA",
    "PATH_RULESETS",
    "IGNORED_PROVIDERS"
]

__locals = locals()

for __name in __all__:
    try:
        setattr(__locals[__name], "__module__", "unalix.config")
    except AttributeError:
        pass
