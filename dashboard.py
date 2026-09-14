"""
RAGEWARE — Tkinter Dashboard.
Rage bar, personality dropdown, activity status, demo injection panel, event log.
"""

import tkinter as tk
from tkinter import ttk
import threading
import config
import personalities


class Dashboard:
    """Main Tkinter dashboard for RAGEWARE."""

    def __init__(self, rage_engine, activity_monitor, llm_manager, demo_mode_obj, demo_clock):
        self.rage = rage_engine
        self.monitor = activity_monitor
        self.llm = llm_manager
        self.demo = demo_mode_obj
        self.clock = demo_clock

        self.root = None
        self._event_log_lines: list[str] = []
        self._max_log_lines = 100

    def log_event(self, message: str) -> None:
        """Add a line to the event log. Thread-safe via root.after."""
        self._event_log_lines.append(message)
        if len(self._event_log_lines) > self._max_log_lines:
            self._event_log_lines = self._event_log_lines[-self._max_log_lines:]
        # Schedule UI update on main thread
        if self.root:
            try:
                self.root.after(0, self._update_event_log)
            except Exception:
                pass

    def _update_event_log(self):
        """Update the event log text widget."""
        if hasattr(self, '_log_text'):
            self._log_text.config(state='normal')
            self._log_text.delete('1.0', tk.END)
            self._log_text.insert('1.0', '\n'.join(self._event_log_lines[-50:]))
            self._log_text.see(tk.END)
            self._log_text.config(state='disabled')

    def build(self) -> tk.Tk:
        """Build and return the Tkinter root window. Call mainloop() on it."""
        self.root = tk.Tk()
        self.root.title("🔥 RAGEWARE — AI Digital Heckler")
        self.root.geometry("520x720")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'),
                        foreground='#e94560', background='#1a1a2e')
        style.configure('Info.TLabel', font=('Segoe UI', 10),
                        foreground='#eee', background='#1a1a2e')
        style.configure('Rage.TLabel', font=('Segoe UI', 14, 'bold'),
                        foreground='#ff6b6b', background='#1a1a2e')
        style.configure('Status.TLabel', font=('Segoe UI', 9),
                        foreground='#aaa', background='#16213e')
        style.configure('Demo.TButton', font=('Segoe UI', 9),
                        padding=4)
        style.configure('Section.TLabelframe', background='#16213e',
                        foreground='#eee')
        style.configure('Section.TLabelframe.Label', font=('Segoe UI', 10, 'bold'),
                        foreground='#e94560', background='#16213e')

        main_frame = tk.Frame(self.root, bg='#1a1a2e', padx=10, pady=5)
        main_frame.pack(fill='both', expand=True)

        # ── Title ──
        ttk.Label(main_frame, text="🔥 RAGEWARE", style='Title.TLabel').pack(pady=(5, 2))

        # ── Rage Bar Section ──
        rage_frame = ttk.LabelFrame(main_frame, text="RAGE LEVEL", style='Section.TLabelframe')
        rage_frame.pack(fill='x', pady=5)

        self._rage_label = ttk.Label(rage_frame, text="0 / 10", style='Rage.TLabel')
        self._rage_label.pack(pady=(5, 2))

        # Canvas-based rage bar for color control
        self._rage_canvas = tk.Canvas(rage_frame, height=28, bg='#0f3460',
                                       highlightthickness=0)
        self._rage_canvas.pack(fill='x', padx=10, pady=(0, 8))

        # ── Activity Status ──
        status_frame = ttk.LabelFrame(main_frame, text="CURRENT ACTIVITY",
                                       style='Section.TLabelframe')
        status_frame.pack(fill='x', pady=5)

        inner = tk.Frame(status_frame, bg='#16213e', padx=8, pady=5)
        inner.pack(fill='x')

        self._app_label = ttk.Label(inner, text="App: —", style='Status.TLabel')
        self._app_label.pack(anchor='w')
        self._domain_label = ttk.Label(inner, text="Domain: —", style='Status.TLabel')
        self._domain_label.pack(anchor='w')
        self._class_label = ttk.Label(inner, text="Classification: —", style='Status.TLabel')
        self._class_label.pack(anchor='w')
        self._idle_label = ttk.Label(inner, text="Idle: 0s", style='Status.TLabel')
        self._idle_label.pack(anchor='w')

        # ── Personality Dropdown ──
        pers_frame = ttk.LabelFrame(main_frame, text="PERSONALITY",
                                     style='Section.TLabelframe')
        pers_frame.pack(fill='x', pady=5)

        pers_inner = tk.Frame(pers_frame, bg='#16213e', padx=8, pady=5)
        pers_inner.pack(fill='x')

        self._personality_var = tk.StringVar(value=self.llm.get_personality())
        personality_keys = personalities.get_personality_names()
        display_names = [personalities.get_display_name(k) for k in personality_keys]
        self._key_by_display = dict(zip(display_names, personality_keys))

        current_display = personalities.get_display_name(self.llm.get_personality())
        self._personality_var.set(current_display)

        pers_combo = ttk.Combobox(pers_inner, textvariable=self._personality_var,
                                   values=display_names, state='readonly', width=30)
        pers_combo.pack(side='left', padx=(0, 10))
        pers_combo.bind('<<ComboboxSelected>>', self._on_personality_change)

        # ── Model Dropdown ──
        model_frame = ttk.LabelFrame(main_frame, text="AI MODEL",
                                     style='Section.TLabelframe')
        model_frame.pack(fill='x', pady=5)

        model_inner = tk.Frame(model_frame, bg='#16213e', padx=8, pady=5)
        model_inner.pack(fill='x')

        self._model_var = tk.StringVar(value=self.llm.get_model())
        model_combo = ttk.Combobox(model_inner, textvariable=self._model_var,
                                   values=config.MODELS, state='readonly', width=30)
        model_combo.pack(side='left', padx=(0, 10))
        model_combo.bind('<<ComboboxSelected>>', self._on_model_change)

        # ── Demo Mode Panel ──
        demo_frame = ttk.LabelFrame(main_frame, text="DEMO MODE",
                                     style='Section.TLabelframe')
        demo_frame.pack(fill='x', pady=5)

        demo_inner = tk.Frame(demo_frame, bg='#16213e', padx=8, pady=5)
        demo_inner.pack(fill='x')

        # Demo clock toggle
        self._demo_clock_var = tk.BooleanVar(value=False)
        demo_clock_btn = tk.Checkbutton(demo_inner, text="⏱ Demo Clock (1s = 1min)",
                                         variable=self._demo_clock_var,
                                         command=self._toggle_demo_clock,
                                         bg='#16213e', fg='#eee',
                                         selectcolor='#0f3460',
                                         activebackground='#16213e',
                                         activeforeground='#eee',
                                         font=('Segoe UI', 9))
        demo_clock_btn.pack(anchor='w', pady=(0, 5))

        # Injection buttons - 2 columns
        btn_frame = tk.Frame(demo_inner, bg='#16213e')
        btn_frame.pack(fill='x')

        buttons = [
            ("▶ Open YouTube", self._inject_open_youtube),
            ("⏩ +10 min YouTube", self._inject_10min_youtube),
            ("⏩ +25 min YouTube", self._inject_25min_youtube),
            ("💻 Switch to VS Code", self._inject_switch_vscode),
            ("🔍 Trigger Lie Detector", self._inject_lie_detector),
            ("🔄 Reset Rage", self._inject_reset_rage),
        ]

        for i, (text, cmd) in enumerate(buttons):
            row, col = divmod(i, 2)
            btn = ttk.Button(btn_frame, text=text, command=cmd, style='Demo.TButton')
            btn.grid(row=row, column=col, padx=3, pady=2, sticky='ew')

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # ── Event Log ──
        log_frame = ttk.LabelFrame(main_frame, text="EVENT LOG",
                                    style='Section.TLabelframe')
        log_frame.pack(fill='both', expand=True, pady=5)

        self._log_text = tk.Text(log_frame, height=8, bg='#0f3460', fg='#aaa',
                                  font=('Consolas', 8), wrap='word',
                                  state='disabled', borderwidth=0)
        self._log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Start refresh loop
        self._refresh()

        return self.root

    def _refresh(self):
        """Periodic UI refresh."""
        try:
            # Update rage bar
            rage = self.rage.get_rage()
            self._rage_label.config(text=f"{rage} / 10")

            # Draw rage bar on canvas
            self._rage_canvas.delete('all')
            w = self._rage_canvas.winfo_width()
            if w > 1:
                fill_w = int((rage / 10.0) * w)
                # Color gradient: green → yellow → red
                if rage <= 3:
                    color = '#00cc66'
                elif rage <= 6:
                    color = '#ffaa00'
                else:
                    color = '#e94560'
                self._rage_canvas.create_rectangle(0, 0, fill_w, 28, fill=color,
                                                    outline='')
                # Grid lines
                for i in range(1, 10):
                    x = int((i / 10.0) * w)
                    self._rage_canvas.create_line(x, 0, x, 28, fill='#1a1a2e',
                                                   width=1)

            # Update activity status
            state = self.monitor.get_state()
            self._app_label.config(text=f"App: {state.get('app', '—')}")
            domain = state.get('domain') or '—'
            self._domain_label.config(text=f"Domain: {domain}")
            classification = state.get('classification', '—')
            class_colors = {'productive': '#00cc66', 'distracting': '#e94560',
                           'neutral': '#aaa'}
            self._class_label.config(
                text=f"Classification: {classification.upper()}",
                foreground=class_colors.get(classification, '#aaa')
            )
            idle = state.get('idle_seconds', 0)
            self._idle_label.config(text=f"Idle: {idle:.0f}s | Activity: {state.get('activity_level', '—')}")

        except Exception as e:
            pass  # Don't crash the UI loop

        if self.root:
            self.root.after(config.DASHBOARD_REFRESH_MS, self._refresh)

    def _on_personality_change(self, event=None):
        display = self._personality_var.get()
        key = self._key_by_display.get(display, 'toxic_friend')
        self.llm.set_personality(key)
        self.log_event(f"[Personality] Switched to {display}")

    def _on_model_change(self, event=None):
        model = self._model_var.get()
        self.llm.set_model(model)
        self.log_event(f"[Model] Switched to {model}")

    def _toggle_demo_clock(self):
        result = self.demo.toggle_demo_clock()
        self.log_event(f"[Demo] {result}")

    def _inject_open_youtube(self):
        threading.Thread(target=self._run_injection,
                        args=("Open YouTube", self.demo.inject_open_youtube),
                        daemon=True).start()

    def _inject_10min_youtube(self):
        threading.Thread(target=self._run_injection,
                        args=("+10min YouTube",
                              lambda: self.demo.inject_youtube_minutes(10)),
                        daemon=True).start()

    def _inject_25min_youtube(self):
        threading.Thread(target=self._run_injection,
                        args=("+25min YouTube",
                              lambda: self.demo.inject_youtube_minutes(25)),
                        daemon=True).start()

    def _inject_switch_vscode(self):
        threading.Thread(target=self._run_injection,
                        args=("Switch to VS Code", self.demo.inject_switch_vscode),
                        daemon=True).start()

    def _inject_lie_detector(self):
        threading.Thread(target=self._run_injection,
                        args=("Lie Detector", self.demo.inject_lie_detector),
                        daemon=True).start()

    def _inject_reset_rage(self):
        self.demo.inject_reset_rage()
        self.log_event("[Demo] Rage reset to 0")

    def _run_injection(self, name: str, fn):
        """Run an injection function and log the result."""
        try:
            result = fn()
            self.log_event(f"[Demo] {name}: {result}")
        except Exception as e:
            self.log_event(f"[Demo] {name} ERROR: {e}")

    def run(self):
        """Build and run the dashboard. Blocks until window is closed."""
        root = self.build()
        root.mainloop()
