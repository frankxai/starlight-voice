"""Production audio lanes must use the one canonical local-transport builder."""

import inspect


def test_component_and_s2s_graphs_share_canonical_transport_builder() -> None:
    from starlight_voice.voice_engines import _assemble
    from starlight_voice.voice_loop import build_graph

    assert "_local_audio_transport()" in inspect.getsource(build_graph)
    assert "_local_audio_transport()" in inspect.getsource(_assemble)
