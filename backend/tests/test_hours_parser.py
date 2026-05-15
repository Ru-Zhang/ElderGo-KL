from app.utils.hours_parser import parse_hours_summary


def test_parse_hours_summary_usj7_style() -> None:
    raw = """Station open: 06:00 am
Station closed: 12:00 am (Mon - Sat) / 11:25 pm (Sunday & PH)
Last Train to Gombak: 12:12 am (Mon - Sat) / 11:42 pm (Sunday & PH)
Last Train to Putra Height: 12:07 am (Mon - Sat) / 11:49 pm (Sunday & PH)"""
    parsed = parse_hours_summary(raw)
    assert parsed is not None
    assert len(parsed.open) == 1
    assert len(parsed.close) == 2
    assert len(parsed.last_trains) == 2
    assert parsed.last_trains[0].to == "Gombak"
