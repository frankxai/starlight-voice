from starlight_voice.cognition.dispatch import Dispatcher, approval_tier, build_handoff_packet
from starlight_voice.cognition.fleet import complexity_score, select_agent


def test_complexity_routes_trivial_to_opencode() -> None:
    agent = select_agent(complexity_score("fix a typo in the readme"))
    assert agent.cli == "opencode"


def test_complexity_routes_high_to_fable5_seat() -> None:
    agent = select_agent(complexity_score("refactor the auth module across the repo and fix the test suite"))
    assert agent.model == "claude-fable-5"  # 7-8 seat = Fable 5 (Terminal-Bench leader)


def test_substrate_routes_to_deepagent() -> None:
    agent = select_agent(complexity_score("a breaking change to the SIP protocol schema migration"))
    assert agent.cli == "dcode"


def test_approval_tiers() -> None:
    assert approval_tier("read the config and summarize") == "A"
    assert approval_tier("force push to main") == "B"
    assert approval_tier("rotate the API key") == "C"


def test_packet_has_routing_and_tier() -> None:
    pkt = build_handoff_packet("delete the stale branches").to_dict()
    assert pkt["packet_version"] == 1
    assert pkt["approval"]["tier"] == "B"          # 'delete' -> ack required
    assert pkt["approval"]["required"] is True
    assert pkt["target"]["cli"]                      # an agent was chosen
    assert pkt["packet_id"]                          # ulid present


def test_dispatch_dry_run_does_not_spawn() -> None:
    out = Dispatcher(live=False).dispatch("rename a variable")
    assert out["status"] == "dry-run"
    assert "packet" in out


def test_dispatch_live_holds_tier_b_for_approval() -> None:
    out = Dispatcher(live=True).dispatch("publish the release and deploy")
    assert out["status"] == "awaiting-approval"  # never auto-spawns a Tier-B task
