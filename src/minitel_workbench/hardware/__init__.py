"""The device side: capability profiles, adapter detection, and links.

Everything here is optional to the running application. A telephone-only user
(the primary audience) never touches it, and importing it never requires
``pyserial``.
"""

from .capability import CapabilityLevel, CapabilityProfile, profile_for_model
from .detect import DetectedAdapter, find_minitel_adapters
from .link import LoopbackLink

__all__ = [
    "CapabilityLevel",
    "CapabilityProfile",
    "profile_for_model",
    "DetectedAdapter",
    "find_minitel_adapters",
    "LoopbackLink",
]
