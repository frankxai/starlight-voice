"""Canonical audio boundary for realtime voice transports.

Perplexity's published Realtime lessons make one rule non-negotiable: establish
one sample-rate/channel/encoding contract before the first outbound chunk and
keep it for the session. This module is dependency-free so capture adapters can
validate and normalize fixtures without importing a voice provider SDK.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Sequence
from dataclasses import dataclass


class AudioContractError(ValueError):
    """Raised when source audio cannot be canonicalized safely."""


@dataclass(frozen=True)
class AudioContract:
    sample_rate: int = 48_000
    channels: int = 1
    sample_width_bytes: int = 2

    def __post_init__(self) -> None:
        if (self.sample_rate, self.channels, self.sample_width_bytes) != (48_000, 1, 2):
            raise AudioContractError("canonical audio must be 48 kHz mono signed PCM16")

    def samples_for_ms(self, duration_ms: int) -> int:
        if duration_ms <= 0:
            raise AudioContractError("chunk duration must be positive")
        samples = self.sample_rate * duration_ms
        if samples % 1000:
            raise AudioContractError("chunk duration must produce a whole sample count")
        return samples // 1000

    def bytes_for_ms(self, duration_ms: int) -> int:
        return self.samples_for_ms(duration_ms) * self.channels * self.sample_width_bytes


CANONICAL_AUDIO = AudioContract()


def canonical_transport_kwargs() -> dict[str, int | bool]:
    """Pipecat local-transport settings that enforce the session audio boundary.

    LocalAudioTransport uses signed 16-bit PCM internally. Pinning both directions here makes
    unsupported devices fail at transport startup instead of silently drifting off contract.
    """
    return {
        "audio_in_enabled": True,
        "audio_out_enabled": True,
        "audio_in_sample_rate": CANONICAL_AUDIO.sample_rate,
        "audio_out_sample_rate": CANONICAL_AUDIO.sample_rate,
        "audio_in_channels": CANONICAL_AUDIO.channels,
        "audio_out_channels": CANONICAL_AUDIO.channels,
    }


def _validate_channels(channels: Sequence[Sequence[float]], source_rate: int) -> int:
    if source_rate <= 0:
        raise AudioContractError("source sample rate must be positive")
    if not channels:
        raise AudioContractError("at least one audio channel is required")
    length = len(channels[0])
    if length == 0:
        raise AudioContractError("audio channels cannot be empty")
    if any(len(channel) != length for channel in channels):
        raise AudioContractError("audio channels must have equal lengths")
    return length


def _clamp(sample: float) -> float:
    value = float(sample)
    if not math.isfinite(value):
        raise AudioContractError("audio samples must be finite")
    return max(-1.0, min(1.0, value))


def _resample_linear(samples: Sequence[float], source_rate: int, target_rate: int) -> list[float]:
    if source_rate == target_rate:
        return list(samples)
    target_length = max(1, round(len(samples) * target_rate / source_rate))
    if target_length == 1 or len(samples) == 1:
        return [float(samples[0])]

    scale = (len(samples) - 1) / (target_length - 1)
    output: list[float] = []
    for index in range(target_length):
        position = index * scale
        left = int(position)
        right = min(left + 1, len(samples) - 1)
        fraction = position - left
        output.append(float(samples[left]) * (1.0 - fraction) + float(samples[right]) * fraction)
    return output


def canonicalize_audio(
    channels: Sequence[Sequence[float]],
    *,
    source_rate: int,
) -> list[float]:
    """Downmix, clamp and resample source channels to the canonical mono boundary."""

    length = _validate_channels(channels, source_rate)
    mono = [_clamp(sum(float(channel[index]) for channel in channels) / len(channels)) for index in range(length)]
    return [_clamp(sample) for sample in _resample_linear(mono, source_rate, CANONICAL_AUDIO.sample_rate)]


def float32_to_pcm16le(samples: Sequence[float]) -> bytes:
    """Encode normalized samples as signed 16-bit little-endian PCM."""

    encoded = []
    for sample in samples:
        value = _clamp(sample)
        integer = -32768 if value <= -1.0 else round(value * 32767)
        encoded.append(integer)
    return struct.pack(f"<{len(encoded)}h", *encoded)
