import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from storage.base import (
        BaseStorageClass
    )
    from storage.aws import (
        AwsS3BucketClass
    )
    from storage.gcp import (
        GcpBucketClass
    )
    from storage.oci import (
        OciBucketClass
    )

# __all__ = [
#     "BaseStorageClass",
#     "AwsS3BucketClass",
#     "GcpBucketClass",
#     "OciBucketClass",
# ]

_module_lookup = {
    "BaseStorageClass" : "storage.base",
    "AwsS3BucketClass": "storage.aws",
    "GcpBucketClass": "storage.gcp",
    "OciBucketClass": "storage.oci"
}

def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = list(_module_lookup.keys())