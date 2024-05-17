import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from translation.base import (
        BaseTranslationClass
    )
    from translation.bhashini import (
        BhashiniTranslationClass
    )
    from translation.dhruva import (
        DhruvaTranslationClass
    )
    from translation.google import (
        GoogleCloudTranslationClass
    )

# __all__ = [
#     "BaseTranslationClass",
#     "BhashiniTranslationClass",
#     "DhruvaTranslationClass",
#     "GoogleCloudTranslationClass",
# ]

_module_lookup = {
    "BaseTranslationClass" : "translation.base",
    "BhashiniTranslationClass": "translation.bhashini",
    "DhruvaTranslationClass": "translation.dhruva",
    "GoogleCloudTranslationClass": "translation.google"
}

def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = list(_module_lookup.keys())