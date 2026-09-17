"""Canonical audio boundary tests derived from the Perplexity Realtime engineering lessons."""

import struct
from types import SimpleNamespace

import pytest

from starlight_voice.audio_contract import (
    CANONICAL_AUDIO,
    AudioContract,
    AudioContractError,
    canonical_transport_kwargs,
    canonicalize_audio,
    float32_to_pcm16le,
)


def test_canonicalize_resamples_stereo_to_48khz_mono() -> None:
    left = [0.0, 0.5, 1.0, 0.5]
    right = [0.0, -0.5, -1.0, -0.5]

    samples = canonicalize_audio([left, right], source_rate=24_000)

    assert len(samples) == 8
    assert samples == pytest.approx([0.0] * 8, abs=1e-7)
    assert CANONICAL_AUDIO.sample_rate == 48_000
    assert CANONICAL_AUDIO.channels == 1


def test_canonicalize_clamps_normalized_samples() -> None:
    samples = canonicalize_audio([[2.0, -2.0, 0.25]], source_rate=48_000)

    assert samples == pytest.approx([1.0, -1.0, 0.25])


def test_float32_to_pcm16le_encodes_signed_little_endian() -> None:
    payload = float32_to_pcm16le([-1.0, 0.0, 1.0])

    assert struct.unpack("<3h", payload) == (-32768, 0, 32767)


def test_chunk_size_is_explicit_for_realtime_frames() -> None:
    assert CANONICAL_AUDIO.samples_for_ms(20) == 960
    assert CANONICAL_AUDIO.bytes_for_ms(20) == 1920


@pytest.mark.parametrize(
    "overrides",
    [
        {"sample_rate": 44_100},
        {"channels": 2},
        {"sample_width_bytes": 4},
    ],
)
def test_contract_rejects_noncanonical_overrides(overrides) -> None:
    with pytest.raises(AudioContractError, match="canonical"):
        AudioContract(**overrides)


def test_canonicalizer_does_not_accept_a_runtime_contract_override() -> None:
    with pytest.raises(TypeError):
        canonicalize_audio(
            [[0.0] * 480],
            source_rate=48_000,
            contract=SimpleNamespace(sample_rate=44_100),
        )


def test_local_transport_is_pinned_to_the_canonical_pcm_boundary() -> None:
    assert canonical_transport_kwargs() == {
        "audio_in_enabled": True,
        "audio_out_enabled": True,
        "audio_in_sample_rate": 48_000,
        "audio_out_sample_rate": 48_000,
        "audio_in_channels": 1,
        "audio_out_channels": 1,
    }


@pytest.mark.parametrize(
    ("channels", "source_rate"),
    [([], 48_000), ([[0.0], [0.0, 1.0]], 48_000), ([[0.0]], 0)],
)
def test_canonicalize_rejects_malformed_audio(channels, source_rate) -> None:
    with pytest.raises(AudioContractError):
        canonicalize_audio(channels, source_rate=source_rate)
