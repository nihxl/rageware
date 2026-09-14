"""
RAGEWARE — Rage Engine unit tests.
Tests the exact escalation/decay/cooldown numbers from the spec.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rage_engine import RageEngine


def test_escalation():
    """Test rage escalation tiers with fake time."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    assert engine.get_rage() == 0

    # Simulate 5 minutes of distracting → should get +1
    clock[0] = 0
    engine.update('distracting', 0)  # start
    clock[0] = 5 * 60  # 5 minutes
    engine.update('distracting', 0)
    assert engine.get_rage() == 1, f"After 5min expected rage=1, got {engine.get_rage()}"

    # At 15 minutes → should get another +1 (total +2)
    clock[0] = 15 * 60
    engine.update('distracting', 0)
    assert engine.get_rage() == 2, f"After 15min expected rage=2, got {engine.get_rage()}"

    # At 25 minutes → should get +2 (total +4)
    clock[0] = 25 * 60
    engine.update('distracting', 0)
    assert engine.get_rage() == 4, f"After 25min expected rage=4, got {engine.get_rage()}"

    # At 35 minutes → should get +2 (total +6)
    clock[0] = 35 * 60
    engine.update('distracting', 0)
    assert engine.get_rage() == 6, f"After 35min expected rage=6, got {engine.get_rage()}"

    print("Escalation tiers pass")


def test_decay():
    """Test productive decay."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    engine.set_rage(6)

    # 5 minutes productive → -1
    clock[0] = 0
    engine.update('productive', 0)
    clock[0] = 5 * 60
    engine.update('productive', 0)
    assert engine.get_rage() == 5, f"After 5min productive expected rage=5, got {engine.get_rage()}"

    # Another 10 minutes productive → -2
    clock[0] = 5 * 60 + 10 * 60
    engine.update('productive', 0)
    assert engine.get_rage() == 3, f"After 10min productive expected rage=3, got {engine.get_rage()}"

    print("Productive decay passes")


def test_idle():
    """Test idle freeze and long-idle decay."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    engine.set_rage(5)

    # Idle for 3 minutes → freeze (rage stays at 5)
    clock[0] = 0
    result = engine.update('distracting', 200)  # idle_seconds > 180
    assert result is None, "Should return None when idle"
    assert engine.get_rage() == 5, f"Expected rage=5 during idle, got {engine.get_rage()}"

    # Idle for 10 minutes → -1
    clock[0] = 10 * 60
    engine.update('neutral', 700)  # idle_seconds > 600
    assert engine.get_rage() == 4, f"After 10min idle expected rage=4, got {engine.get_rage()}"

    print("Idle handling passes")


def test_repeat_offender():
    """Test repeat offender penalty."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)

    # Start distracting
    clock[0] = 0
    engine.update('distracting', 0)

    # Switch to productive (records distracting end)
    clock[0] = 60
    engine.update('productive', 0)

    # Return to distracting within 5 min → +2 penalty
    old_rage = engine.get_rage()
    clock[0] = 120  # 2 minutes later
    engine.update('distracting', 0)
    expected = old_rage + 2
    assert engine.get_rage() == expected, \
        f"Repeat offender: expected rage={expected}, got {engine.get_rage()}"

    print("Repeat offender penalty passes")


def test_cooldown():
    """Test notification cooldown by rage level."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    engine.set_rage(2)  # low rage → 60s cooldown

    clock[0] = 0
    engine.record_notification()

    clock[0] = 30
    assert not engine.can_notify(), "Should NOT notify at 30s (cooldown 60s for rage 0-3)"

    clock[0] = 61
    assert engine.can_notify(), "Should notify at 61s (cooldown 60s for rage 0-3)"

    # Mid rage → 40s cooldown
    engine.set_rage(5)
    clock[0] = 61
    engine.record_notification()

    clock[0] = 90
    assert not engine.can_notify(), "Should NOT notify at 90s (cooldown 40s for rage 4-6)"

    clock[0] = 102
    assert engine.can_notify(), "Should notify at 102s (cooldown 40s for rage 4-6)"

    # High rage → 25s cooldown
    engine.set_rage(8)
    clock[0] = 102
    engine.record_notification()

    clock[0] = 120
    assert not engine.can_notify(), "Should NOT notify at 120s (cooldown 25s for rage 7-10)"

    clock[0] = 128
    assert engine.can_notify(), "Should notify at 128s (cooldown 25s for rage 7-10)"

    print("Cooldown logic passes")


def test_clamp():
    """Test rage clamping to 0-10."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    engine.set_rage(10)
    engine.adjust_rage(5)
    assert engine.get_rage() == 10, f"Max clamp: expected 10, got {engine.get_rage()}"

    engine.set_rage(0)
    engine.adjust_rage(-5)
    assert engine.get_rage() == 0, f"Min clamp: expected 0, got {engine.get_rage()}"

    print("Rage clamping passes")


def test_injection():
    """Test demo mode injection."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)

    # Inject 25 minutes distracting
    clock[0] = 100
    event = engine.inject_distracting(25)
    assert event is not None, "inject_distracting should return an event"
    assert event['trigger'] == 'procrastination', f"Expected procrastination trigger, got {event['trigger']}"
    assert engine.get_rage() >= 4, f"After 25min inject expected rage>=4, got {engine.get_rage()}"

    print(f"Injection passes (rage after 25min inject: {engine.get_rage()})")


def test_reset():
    """Test rage reset."""
    clock = [0.0]
    def fake_time():
        return clock[0]

    engine = RageEngine(time_fn=fake_time)
    engine.set_rage(8)
    engine.reset()
    assert engine.get_rage() == 0, f"After reset expected rage=0, got {engine.get_rage()}"

    print("Reset passes")


if __name__ == "__main__":
    test_escalation()
    test_decay()
    test_idle()
    test_repeat_offender()
    test_cooldown()
    test_clamp()
    test_injection()
    test_reset()
    print("\nAll rage engine tests pass!")
