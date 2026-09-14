import time
import threading
from typing import Dict, Any, Optional
import config

class RageEngine:
    def __init__(self, time_fn=time.time):
        self._time = time_fn
        self._lock = threading.Lock()
        
        # State
        self.rage: int = 0
        self._distracting_start: Optional[float] = None
        self._productive_start: Optional[float] = None
        self._last_distracting_end: Optional[float] = None
        self._last_notification_time: float = 0.0
        self._last_escalation_rage: int = 0
        self._notification_count: int = 0
        self._idle_start: Optional[float] = None
        self._is_idle: bool = False
        self._last_classification: str = 'neutral'
        self._cumulative_distracting_minutes: float = 0.0
        
        self._awarded_thresholds: set = set()
        self._long_idle_decay_applied: bool = False

    def update(self, classification: str, idle_seconds: float) -> Optional[Dict[str, Any]]:
        """Called every poll cycle with the current classification and idle time."""
        with self._lock:
            now = self._time()
            trigger = None
            
            # 1. Handle idle state
            if idle_seconds >= getattr(config, 'IDLE_THRESHOLD_SECONDS', 180):
                if not self._is_idle:
                    self._is_idle = True
                    self._idle_start = now
                
                if self._idle_start is not None and (now - self._idle_start) >= getattr(config, 'IDLE_LONG_THRESHOLD_SECONDS', 600):
                    if not self._long_idle_decay_applied:
                        self._adjust_rage(-1)
                        self._long_idle_decay_applied = True
                
                return None
            else:
                self._is_idle = False
                self._idle_start = None
                self._long_idle_decay_applied = False

            # 2. Handle distracting
            if classification == 'distracting':
                self._productive_start = None
                
                if self._distracting_start is None:
                    self._distracting_start = now
                    
                # Repeat offender
                repeat_window = getattr(config, 'REPEAT_OFFENDER_WINDOW_SECONDS', 300)
                if self._last_distracting_end is not None:
                    if (now - self._last_distracting_end) < repeat_window:
                        self._adjust_rage(2)
                        self._last_distracting_end = None
                        trigger = 'returning_offender'
                    else:
                        self._last_distracting_end = None

                self._cumulative_distracting_minutes = (now - self._distracting_start) / 60.0
                
                # Escalation tiers (5, 15, 25, 35, 45...)
                thresholds_to_check = [5, 15] + [25 + i * 10 for i in range(10)]
                for t in thresholds_to_check:
                    if self._cumulative_distracting_minutes >= t and t not in self._awarded_thresholds:
                        self._awarded_thresholds.add(t)
                        if t == 5:
                            self._adjust_rage(1)
                        elif t == 15:
                            self._adjust_rage(1)
                        else:
                            self._adjust_rage(2)
                
                self._last_classification = 'distracting'
                
                if trigger or self._can_notify_unlocked():
                    trigger = trigger or 'procrastination'
                    return self._build_event(trigger)
                return None
                
            # 3. Handle productive
            elif classification == 'productive':
                if self._last_classification == 'distracting':
                    self._last_distracting_end = now
                    
                self._distracting_start = None
                self._cumulative_distracting_minutes = 0.0
                self._awarded_thresholds.clear()
                self._last_classification = 'productive'
                
                if self._productive_start is None:
                    self._productive_start = now
                    
                productive_minutes = (now - self._productive_start) / 60.0
                
                decay_applied = False
                if productive_minutes >= 10:
                    self._adjust_rage(-2)
                    decay_applied = True
                elif productive_minutes >= 5:
                    self._adjust_rage(-1)
                    decay_applied = True
                    
                if decay_applied:
                    self._productive_start = now  # tick again
                    if self._can_notify_unlocked():
                        return self._build_event('productive_streak')

                return None
                
            # 4. Handle neutral
            else:
                if self._last_classification == 'distracting':
                    self._last_distracting_end = now
                self._distracting_start = None
                self._cumulative_distracting_minutes = 0.0
                self._awarded_thresholds.clear()
                
                self._last_classification = classification
                return None

    def _build_event(self, trigger: str) -> Dict[str, Any]:
        return {
            'trigger': trigger,
            'application': '',
            'website': '',
            'duration_minutes': self._cumulative_distracting_minutes if trigger != 'productive_streak' else 0.0,
            'rage_level': self.rage,
            'previous_warnings': self._notification_count,
        }
        
    def _adjust_rage(self, delta: int) -> None:
        self.rage = max(0, min(10, self.rage + delta))

    def can_notify(self) -> bool:
        """Check if cooldown has elapsed."""
        with self._lock:
            return self._can_notify_unlocked()

    def _can_notify_unlocked(self) -> bool:
        now = self._time()
        cooldown = 60
        if self.rage >= 7:
            cooldown = 25
        elif self.rage >= 4:
            cooldown = 40
            
        return (now - self._last_notification_time) >= cooldown

    def record_notification(self) -> None:
        """Mark that a notification was just sent."""
        with self._lock:
            self._last_notification_time = self._time()
            self._notification_count += 1

    def adjust_rage(self, delta: int, bypass_cooldown: bool = False) -> None:
        """Manually adjust rage by delta."""
        with self._lock:
            self._adjust_rage(delta)

    def set_rage(self, value: int) -> None:
        """Set rage to exact value."""
        with self._lock:
            self.rage = max(0, min(10, value))

    def get_rage(self) -> int:
        """Return current rage level."""
        with self._lock:
            return self.rage

    def get_notification_count(self) -> int:
        """Return total notification count."""
        with self._lock:
            return self._notification_count

    def get_state(self) -> Dict[str, Any]:
        """Return full state dict for dashboard/debugging."""
        with self._lock:
            return {
                'rage': self.rage,
                'is_idle': self._is_idle,
                'last_classification': self._last_classification,
                'cumulative_distracting_minutes': self._cumulative_distracting_minutes,
                'notification_count': self._notification_count,
                'awarded_thresholds': list(self._awarded_thresholds)
            }

    def inject_distracting(self, minutes: float) -> Dict[str, Any]:
        """Demo mode: simulate N minutes of distracting activity."""
        with self._lock:
            now = self._time()
            if not self._distracting_start:
                self._distracting_start = now
            self._distracting_start -= (minutes * 60.0)
            
        event = self.update('distracting', 0)
        if event is None:
            with self._lock:
                event = self._build_event('procrastination')
        return event

    def inject_productive(self, minutes: float) -> Dict[str, Any]:
        """Demo mode: simulate N minutes of productive activity."""
        with self._lock:
            now = self._time()
            if not self._productive_start:
                self._productive_start = now
            self._productive_start -= (minutes * 60.0)
            
        event = self.update('productive', 0)
        if event is None:
            with self._lock:
                event = self._build_event('productive_streak')
        return event

    def reset(self) -> None:
        """Reset all state to initial values."""
        with self._lock:
            self.rage = 0
            self._distracting_start = None
            self._productive_start = None
            self._last_distracting_end = None
            self._last_notification_time = 0.0
            self._last_escalation_rage = 0
            self._notification_count = 0
            self._idle_start = None
            self._is_idle = False
            self._last_classification = 'neutral'
            self._cumulative_distracting_minutes = 0.0
            self._awarded_thresholds.clear()
            self._long_idle_decay_applied = False
