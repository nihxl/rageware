"""
RAGEWARE — Main entrypoint.
Starts activity monitor, FastAPI server, rage engine loop, and Tkinter dashboard.
"""

import sys
import os
import time
import threading
import signal
from dotenv import load_dotenv

load_dotenv()

# Ensure rageware package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from activity_monitor import ActivityMonitor
from browser_server import run_server, set_activity_monitor
from rage_engine import RageEngine
from llm_manager import LLMManager
from notifier import Notifier
from lie_detector import LieDetector
from demo_mode import DemoClock, DemoMode
from dashboard import Dashboard


class RagewareApp:
    """Main application orchestrator."""

    def __init__(self):
        # Demo clock (injectable time source)
        self.demo_clock = DemoClock()

        # Core components
        self.monitor = ActivityMonitor()
        self.rage_engine = RageEngine(time_fn=self.demo_clock.now)
        self.llm = LLMManager()
        self.notifier = Notifier()

        # Lie detector
        self.lie_detector = LieDetector(
            activity_monitor=self.monitor,
            rage_engine=self.rage_engine,
            llm_manager=self.llm,
            notifier=self.notifier,
            time_fn=self.demo_clock.now,
        )

        # Demo mode
        self.demo = DemoMode(
            rage_engine=self.rage_engine,
            activity_monitor=self.monitor,
            llm_manager=self.llm,
            notifier=self.notifier,
            lie_detector=self.lie_detector,
            demo_clock=self.demo_clock,
        )

        # Dashboard
        self.dashboard = Dashboard(
            rage_engine=self.rage_engine,
            activity_monitor=self.monitor,
            llm_manager=self.llm,
            demo_mode_obj=self.demo,
            demo_clock=self.demo_clock,
        )

        # Wire browser server to activity monitor
        set_activity_monitor(self.monitor)

        # Control flag
        self._running = True

    def _monitor_loop(self):
        """Background thread: polls activity monitor and feeds rage engine."""
        self.dashboard.log_event("[System] Activity monitor started")
        while self._running:
            try:
                snapshot = self.monitor.poll()
                classification = snapshot.get('classification', 'neutral')
                idle_seconds = snapshot.get('idle_seconds', 0)

                # Feed to rage engine
                event = self.rage_engine.update(classification, idle_seconds)

                if event:
                    # Fill in app/website details from monitor
                    event['application'] = snapshot.get('app', 'unknown')
                    event['website'] = snapshot.get('domain', '') or ''
                    
                    # Capture screenshot if vision enabled
                    if getattr(config, 'ENABLE_VISION', False):
                        b64_img = self.monitor.capture_screen_base64()
                        if b64_img:
                            event['screenshot_base64'] = b64_img
                            print(f"[Vision] Screenshot attached to event ({len(b64_img)*3//4//1024} KB)")
                        else:
                            print("[Vision] No screenshot captured, sending text-only")

                    # Check if lie detector should prompt
                    if self.lie_detector.should_prompt():
                        msg = self.llm.generate_message(event)
                        self.lie_detector.send_prompt(msg)
                        self.rage_engine.record_notification()
                        self.dashboard.log_event(
                            f"[Rage {self.rage_engine.get_rage()}] {msg} [LIE DETECTOR]"
                        )
                    else:
                        msg = self.llm.generate_message(event)
                        self.notifier.send(msg, self.rage_engine.get_rage())
                        self.rage_engine.record_notification()
                        self.dashboard.log_event(
                            f"[Rage {self.rage_engine.get_rage()}] {msg}"
                        )

                # Periodic lie detector auto-check
                self.lie_detector.auto_check()

            except Exception as e:
                self.dashboard.log_event(f"[Error] Monitor: {e}")

            time.sleep(config.MONITOR_POLL_INTERVAL)

    def _server_thread(self):
        """Background thread: runs FastAPI server."""
        self.dashboard.log_event(
            f"[System] Browser server starting on {config.SERVER_HOST}:{config.SERVER_PORT}"
        )
        try:
            run_server()
        except Exception as e:
            self.dashboard.log_event(f"[Error] Server: {e}")

    def run(self):
        """Start all components and run the dashboard."""
        print("=" * 50)
        print("  RAGEWARE — AI Digital Heckler")
        print("=" * 50)
        print(f"  Browser server: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
        model_type = "Cloud (Gemini)" if config.DEFAULT_MODEL.startswith("gemini") else "Local (Ollama)"
        print(f"  LLM: {model_type} | Model: {config.DEFAULT_MODEL}")
        print(f"  Personality: {self.llm.get_personality()}")
        print("=" * 50)

        # Start FastAPI server
        server = threading.Thread(target=self._server_thread, daemon=True)
        server.start()

        # Start monitor loop
        monitor = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor.start()

        # Run dashboard on main thread (Tkinter requires main thread)
        try:
            self.dashboard.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            print("\n[RAGEWARE] Shutting down...")


def main():
    app = RagewareApp()
    app.run()


if __name__ == "__main__":
    main()
