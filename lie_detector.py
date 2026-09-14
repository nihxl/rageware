"""
RAGEWARE — Lie Detector.
Detects contradictions between what the user claims they're doing
and what they're actually doing.
"""

import time
import random
import threading
import config


class LieDetector:
    """Compares user claims against observed activity."""

    def __init__(self, activity_monitor, rage_engine, llm_manager, notifier, time_fn=None):
        self.monitor = activity_monitor
        self.rage = rage_engine
        self.llm = llm_manager
        self.notifier = notifier
        self.time_fn = time_fn or time.time

        self._last_prompt_time: float = 0.0
        self._last_claim: str | None = None
        self._last_claim_time: float = 0.0
        self._lock = threading.Lock()

        # Wire up the notifier callback
        self.notifier.set_lie_detector_callback(self._on_response)

    def should_prompt(self) -> bool:
        """Decide whether to attach lie-detector buttons to the next notification.
        Conditions:
        - Rage >= LIE_DETECTOR_MIN_RAGE (3)
        - Random chance ~1 in 3
        - Haven't prompted in the last 60 seconds
        """
        now = self.time_fn()
        if self.rage.get_rage() < config.LIE_DETECTOR_MIN_RAGE:
            return False
        if (now - self._last_prompt_time) < 60:
            return False
        return random.random() < config.LIE_DETECTOR_CHANCE

    def send_prompt(self, message: str) -> None:
        """Send a notification with lie-detector action buttons."""
        self._last_prompt_time = self.time_fn()
        self.notifier.send_with_buttons(message, self.rage.get_rage())

    def _on_response(self, choice: str) -> None:
        """Handle user's response to lie-detector prompt."""
        with self._lock:
            self._last_claim = choice
            self._last_claim_time = self.time_fn()

        # Check for contradiction
        is_lie, actual_app, actual_domain = self._check_contradiction(choice)

        if is_lie:
            # LIE DETECTED — rage +3, immediate notification
            self.rage.adjust_rage(config.LIE_DETECTED_PENALTY, bypass_cooldown=True)
            msg = self.llm.generate_lie_response(
                is_lie=True,
                claimed=choice,
                actual_app=actual_app,
                actual_domain=actual_domain or "",
            )
            self.notifier.send(f"🚨 LIE DETECTED: {msg}", self.rage.get_rage())
            self.rage.record_notification()
        else:
            # Honest — rage -1, positive acknowledgment
            self.rage.adjust_rage(config.LIE_HONEST_REWARD)
            msg = self.llm.generate_lie_response(
                is_lie=False,
                claimed=choice,
                actual_app=actual_app,
                actual_domain=actual_domain or "",
            )
            self.notifier.send(f"✅ {msg}", self.rage.get_rage())
            self.rage.record_notification()

    def _check_contradiction(self, claim: str) -> tuple[bool, str, str | None]:
        """Check if the user's claim matches observed activity.

        Returns (is_lie, actual_app, actual_domain).

        A lie is detected if:
        - User claims 'Coding' or 'Studying'
        - But >50% of last 2 minutes was on distracting domains/apps
        """
        history = self.monitor.get_recent_history(config.LIE_DETECTOR_WINDOW_SECONDS)

        if not history:
            # No data — give benefit of the doubt
            state = self.monitor.get_state()
            return False, state.get("app", "unknown"), state.get("domain")

        # Count distracting vs total
        distracting_count = sum(
            1 for snap in history if snap.get("classification") == "distracting"
        )
        total = len(history)
        distracting_ratio = distracting_count / total if total > 0 else 0

        # Most recent snapshot for reporting
        latest = history[-1] if history else {}
        actual_app = latest.get("app", "unknown")
        actual_domain = latest.get("domain")

        # Claims that imply productive work
        productive_claims = {"Coding", "Studying"}

        if claim in productive_claims and distracting_ratio > config.LIE_DETECTOR_DISTRACTING_RATIO:
            return True, actual_app, actual_domain

        # "Taking a break" or "Other" — not a lie, just acknowledged
        return False, actual_app, actual_domain

    def auto_check(self) -> None:
        """Automatic contradiction check — call periodically.
        If user previously claimed to be working but is now on distracting content,
        fire a proactive "you said you were working" notification.
        """
        with self._lock:
            claim = self._last_claim
            claim_time = self._last_claim_time

        if not claim:
            return

        now = self.time_fn()
        # Only auto-check if claim was recent (within last 10 min)
        if (now - claim_time) > 600:
            return

        # Only auto-check productive claims
        if claim not in {"Coding", "Studying"}:
            return

        is_lie, actual_app, actual_domain = self._check_contradiction(claim)

        if is_lie and self.rage.can_notify():
            self.rage.adjust_rage(2, bypass_cooldown=True)
            msg = self.llm.generate_message({
                "trigger": "lie_detected",
                "application": actual_app,
                "website": actual_domain or "",
                "duration_minutes": round((now - claim_time) / 60),
                "rage_level": self.rage.get_rage(),
                "previous_warnings": self.rage.get_notification_count(),
            })
            self.notifier.send(f"🚨 {msg}", self.rage.get_rage())
            self.rage.record_notification()
            # Clear the claim so we don't keep firing
            with self._lock:
                self._last_claim = None

    def force_trigger(self) -> None:
        """Demo mode: force a lie-detector prompt immediately."""
        msg = self.llm.generate_message({
            "trigger": "procrastination",
            "application": self.monitor.get_state().get("app", "unknown"),
            "website": self.monitor.get_state().get("domain", ""),
            "duration_minutes": 0,
            "rage_level": self.rage.get_rage(),
            "previous_warnings": self.rage.get_notification_count(),
        })
        self._last_prompt_time = self.time_fn()
        self.notifier.send_with_buttons(msg, self.rage.get_rage())
