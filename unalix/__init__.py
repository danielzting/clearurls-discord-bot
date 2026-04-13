"""
    Unalix is a small, dependency-free, fast Python package that implements
    the same regex rule processing mechanism used by the ClearURLs addon.
"""
from .core.url_cleaner import clear_url
from .core.coreutils import rulesets_from_files, rulesets_from_dict
from .core.homograph import detect_homograph
from .__version__ import __description__, __title__, __version__


__all__ = [
    "__description__",
    "__title__",
    "__version__",
    "clear_url",
    "rulesets_from_files",
    "rulesets_from_dict",
    "detect_homograph"
]

__locals = locals()

for __name in __all__:
    if not __name.startswith("__"):
        try:
            setattr(__locals[__name], "__module__", "unalix")
        except AttributeError:
            pass
