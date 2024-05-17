import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vectorstores.base import (
        BaseVectorStore
    )
    from vectorstores.marqo import (
        MarqoVectorStore
    )

# __all__ = [
#     "BaseVectorStore",
#     "MarqoVectorStores"
# ]

_module_lookup = {
    "BaseVectorStore" : "vectorstores.base",
    "MarqoVectorStore": "vectorstores.marqo"
}

def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = list(_module_lookup.keys())