from starlight_voice.environment import EnvironmentDoctor


def test_doctor_reports_readiness_shape() -> None:
    report = EnvironmentDoctor().report()

    assert "platform" in report
    assert "tools" in report
    assert "optional_packages" in report
    assert "readiness" in report
    assert isinstance(report["readiness"]["build_shell"], bool)
