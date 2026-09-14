"""
RAGEWARE — Demo Mode.
Simulated clock + manual event injection for live demos.
"""

import time
import threading
import config


class DemoClock:
    """A simulated clock that advances faster than real time.

    1 real second = config.DEMO_TIME_MULTIPLIER simulated seconds.
    When disabled, falls through to real time.time().
    """

    def __init__(self):
        self.enabled = False
        self.multiplier = config.DEMO_TIME_MULTIPLIER
        self._real_start: float = 0.0
        self._sim_start: float = 0.0
        self._lock = threading.Lock()

    def enable(self, multiplier: int | None = None) -> None:
        """Enable demo clock. Optionally set multiplier."""
        with self._lock:
            if multiplier is not None:
                self.multiplier = multiplier
            self._real_start = time.time()
            self._sim_start = time.time()  # Simulated time starts from "now"
            self.enabled = True

    def disable(self) -> None:
        """Disable demo clock, return to real time."""
        with self._lock:
            self.enabled = False

    def toggle(self, multiplier: int | None = None) -> bool:
        """Toggle demo clock. Returns new state."""
        if self.enabled:
            self.disable()
        else:
            self.enable(multiplier)
        return self.enabled

    def now(self) -> float:
        """Get current time — simulated if enabled, real otherwise."""
        with self._lock:
            if not self.enabled:
                return time.time()
            real_elapsed = time.time() - self._real_start
            sim_elapsed = real_elapsed * self.multiplier
            return self._sim_start + sim_elapsed

    def is_enabled(self) -> bool:
        return self.enabled


class DemoMode:
    """Provides injection functions for live demos.

    Each injection directly manipulates the Rage Engine's internal state
    and immediately runs the normal pipeline (event → rage → LLM/fallback → notification).
    """

    def __init__(self, rage_engine, activity_monitor, llm_manager, notifier,
                 lie_detector, demo_clock: DemoClock):
        self.rage = rage_engine
        self.monitor = activity_monitor
        self.llm = llm_manager
        self.notifier = notifier
        self.lie_detector = lie_detector
        self.clock = demo_clock

    def inject_open_youtube(self) -> str:
        """Simulate opening YouTube. Sets domain and fires initial event."""
        self.monitor.update_domain("youtube.com")
        # Simulate a short distracting period
        event = self.rage.inject_distracting(1)
        event["application"] = "chrome.exe"
        event["website"] = "youtube.com"
        msg = self.llm.generate_message(event)
        self.notifier.send(msg, self.rage.get_rage())
        self.rage.record_notification()
        return msg

    def inject_youtube_minutes(self, minutes: int = 10) -> str:
        """Simulate N minutes on YouTube."""
        self.monitor.update_domain("youtube.com")
        event = self.rage.inject_distracting(minutes)
        event["application"] = "chrome.exe"
        event["website"] = "youtube.com"
        msg = self.llm.generate_message(event)
        self.notifier.send(msg, self.rage.get_rage())
        self.rage.record_notification()
        return msg

    def inject_switch_vscode(self) -> str:
        """Simulate switching to VS Code."""
        self.monitor.update_domain("")
        event = self.rage.inject_productive(1)
        if event:
            event["application"] = "code.exe"
            event["website"] = ""
            msg = self.llm.generate_message(event)
        else:
            msg = "Switched to VS Code. Rage holding."
        self.notifier.send(msg, self.rage.get_rage())
        self.rage.record_notification()
        return msg

    def inject_productive_minutes(self, minutes: int = 10) -> str:
        """Simulate N minutes of productive work."""
        self.monitor.update_domain("")
        event = self.rage.inject_productive(minutes)
        if event:
            event["application"] = "code.exe"
            event["website"] = ""
            msg = self.llm.generate_message(event)
        else:
            msg = "Still working. Rage decaying."
        self.notifier.send(msg, self.rage.get_rage())
        self.rage.record_notification()
        return msg

    def inject_lie_detector(self) -> str:
        """Force a lie-detector prompt."""
        self.lie_detector.force_trigger()
        return "Lie detector triggered"

    def inject_reset_rage(self) -> str:
        """Reset rage to 0."""
        self.rage.reset()
        return "Rage reset to 0"

    def toggle_demo_clock(self) -> str:
        """Toggle the demo clock."""
        is_on = self.clock.toggle()
        return f"Demo clock {'ON' if is_on else 'OFF'} (1s = {self.clock.multiplier}s sim)"
