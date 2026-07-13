"""Per-model capability profiles.

The app keeps an internal profile for each terminal and quietly does the right
thing with it — it never lectures the user about what their Minitel can't do
(Constitution rules V, VI, VII). Higher capability levels are strictly additive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CapabilityLevel(IntEnum):
    """What a terminal can render. Each level *includes* the ones below it."""

    L1_MONOCHROME = 1  # text + semigraphics, monochrome
    L2_COLOUR = 2  # colour attributes
    L3_DRCS = 3  # downloadable character sets
    L4_EXTENDED = 4  # double-height/width, blink, etc. (future)


@dataclass(frozen=True)
class CapabilityProfile:
    """A terminal's serial and display capabilities."""

    model: str
    display_level: CapabilityLevel
    #: Symmetric DIN speeds the model is documented to support.
    din_speeds: tuple[int, ...] = (1200,)
    #: The safe default the app should start at.
    default_speed: int = 1200
    data_bits: int = 7
    parity: str = "even"  # "even" | "odd" | "none"
    stop_bits: int = 1
    #: Highest speed empirically verified clean against real hardware, if known.
    verified_max_speed: int | None = None
    notes: str = ""

    @property
    def framing(self) -> str:
        p = {"even": "E", "odd": "O", "none": "N"}[self.parity]
        return f"{self.data_bits}{p}{self.stop_bits}"


# The terminal this project was born on, plus a conservative generic fallback.
# Later models get richer profiles as owners report benchmark results.
_PROFILES: dict[str, CapabilityProfile] = {
    "nfz300": CapabilityProfile(
        model="La Radiotechnique Minitel 9 (NFZ 300)",
        display_level=CapabilityLevel.L1_MONOCHROME,
        din_speeds=(1200,),
        default_speed=1200,
        verified_max_speed=1200,
        notes="First-generation Minitel 1, reversible modem (1984). "
        "Peripheral DIN port VERIFIED against hardware (benchmark sweep): "
        "1200 7E1 renders clean; 300 produces no output; 4800 and 9600 garble. "
        "Maximum verified clean speed 1200 baud.",
    ),
    "generic": CapabilityProfile(
        model="Minitel (unrecognised model)",
        display_level=CapabilityLevel.L1_MONOCHROME,
        din_speeds=(300, 1200),
        default_speed=1200,
        notes="Safe defaults. Run the benchmark to discover the true maximum.",
    ),
}


def profile_for_model(model_key: str | None) -> CapabilityProfile:
    """Return a known profile, falling back to conservative generic defaults."""
    if model_key is None:
        return _PROFILES["generic"]
    return _PROFILES.get(model_key.lower(), _PROFILES["generic"])
