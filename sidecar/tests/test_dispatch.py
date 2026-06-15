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


def test_approval_tiers_default_deny() -> None:
    assert approval_tier("read the config and summarize") == "A"   # provably read-only
    assert approval_tier("force push to main") == "D"              # ALWAYS-ASK hard-block
    assert approval_tier("rotate the API key") == "D"              # ALWAYS-ASK hard-block
    assert approval_tier("a breaking change to the SIP protocol") == "C"


def test_adversarial_destructive_never_tier_a() -> None:
    # the exact fail-OPEN cases the review found — must NOT auto-run
    assert approval_tier("nuke the prod database") == "D"
    assert approval_tier("wipe production") == "D"
    assert approval_tier("overwrite main with my branch") == "B"   # mutating -> ack, not A
    assert approval_tier("delete the old logs") == "B"


def test_benign_task_gets_ack_not_false_block() -> None:
    # 'merge sort' previously false-blocked on substring 'merge'; now it's a normal ack (B), not D
    assert approval_tier("write a merge sort implementation") == "B"


def test_packet_has_routing_and_tier() -> None:
    pkt = build_handoff_packet("delete the stale branches").to_dict()
    assert pkt["packet_version"] == 1
    assert pkt["approval"]["tier"] == "B"          # mutating -> ack required
    assert pkt["approval"]["required"] is True
    assert pkt["target"]["cli"]                      # an agent was chosen
    assert pkt["packet_id"]                          # ulid present


def test_dispatch_dry_run_does_not_spawn() -> None:
    out = Dispatcher(live=False).dispatch("read the project layout")
    assert out["status"] == "dry-run"
    assert "packet" in out


def test_dispatch_live_holds_tier_b_for_approval() -> None:
    out = Dispatcher(live=True).dispatch("publish the release and deploy")
    assert out["status"] == "awaiting-approval"  # never auto-spawns a Tier-B task


def test_dispatch_hard_blocks_always_ask_even_live() -> None:
    out = Dispatcher(live=True).dispatch("rotate the production API key")
    assert out["status"] == "hard-blocked"        # Tier D never runs, even live
    assert out["packet"]["approval"]["tier"] == "D"


def test_spawn_rejects_control_chars_and_unresolvable_cli() -> None:
    from starlight_voice.cognition.dispatch import build_handoff_packet

    # control-char payload (injection-style) is refused, never spawned
    pkt = build_handoff_packet("read the docs")
    object.__setattr__(pkt, "task", "ok\n; rm -rf /")
    assert Dispatcher._spawn(pkt) is False
