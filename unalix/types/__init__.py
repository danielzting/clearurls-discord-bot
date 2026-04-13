from .objects import Dict, List
from .patterns import Pattern, Patterns
from .rulesets import Ruleset, Rulesets
from .urls import URL, URL_TYPES


__all__ = [
    "Dict",
    "List",
    "Pattern",
    "Patterns",
    "Ruleset",
    "Rulesets",
    "URL",
    "URL_TYPES"
]

__locals = locals()

for __name in __all__:
    try:
        setattr(__locals[__name], "__module__", "unalix.types")
    except AttributeError:
        pass
