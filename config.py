"""
RAGEWARE — Configuration constants.
All tunable numbers in one place.
"""
import os

# ─── Rage Engine ────────────────────────────────────────────────
RAGE_MIN = 0
RAGE_MAX = 10

# Escalation thresholds (cumulative distracting minutes → rage delta)
# Format: (min_minutes, max_minutes, rage_delta)
ESCALATION_TIERS = [
    (0, 5, 1),    # 0-5 min: +1
    (5, 15, 1),   # 5-15 min: +1 (cumulative +2)
    (15, 25, 2),  # 15-25 min: +2 (cumulative +4)
]
# After 25 min: +2 every 10 min
ESCALATION_POST_25_INTERVAL = 10  # minutes
ESCALATION_POST_25_DELTA = 2

# Repeat offender: return to distracting within this window
REPEAT_OFFENDER_WINDOW_SECONDS = 300  # 5 minutes
REPEAT_OFFENDER_PENALTY = 2

# Productive decay
PRODUCTIVE_DECAY_5MIN = -1   # every 5 continuous productive minutes
PRODUCTIVE_DECAY_10MIN = -2  # every 10 continuous productive minutes (replaces 5-min tick)

# Idle thresholds
IDLE_THRESHOLD_SECONDS = 180     # 3 min — freeze rage
IDLE_LONG_THRESHOLD_SECONDS = 600  # 10 min — decay by 1
IDLE_LONG_DECAY = -1

# ─── Cooldowns (minimum seconds between notifications) ──────────
COOLDOWN_LOW = 60     # rage 0-3
COOLDOWN_MID = 40     # rage 4-6
COOLDOWN_HIGH = 25    # rage 7-10

# ─── Activity Monitor ──────────────────────────────────────────
MONITOR_POLL_INTERVAL = 3  # seconds between activity polls
ACTIVITY_HIGH_THRESHOLD = 5    # idle < 5s → "high"
ACTIVITY_LOW_THRESHOLD = 30    # idle 5-30s → "low", >30s → "idle"

# ─── Lie Detector ──────────────────────────────────────────────
LIE_DETECTOR_CHANCE = 0.33           # ~1 in 3 chance to attach buttons
LIE_DETECTOR_MIN_RAGE = 3           # only trigger at rage >= 3
LIE_DETECTOR_WINDOW_SECONDS = 120   # look back 2 minutes
LIE_DETECTOR_DISTRACTING_RATIO = 0.5  # >50% distracting = lie
LIE_DETECTED_PENALTY = 3            # rage +3 on lie
LIE_HONEST_REWARD = -1              # rage -1 on truth
LIE_DETECTOR_AUTO_INTERVAL = 300    # 5 min auto-check interval

# ─── LLM Manager ──────────────────────────────────────────────
MODELS = [
    "gemini-3.8-flash",        # Google Cloud (fast)
    "gemini-3.5-flash-lite",   # Google Cloud (fastest, cheapest)
    "gemini-3.1-pro",          # Google Cloud (smartest)
    "llava",                   # Local Ollama (vision)
    "gemma4:12b",              # Local Ollama (reasoning)
]
DEFAULT_MODEL = "gemini-3.8-flash"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
LLM_TIMEOUT = 30.0  # seconds (cloud models are fast, local may need more)
LLM_MAX_TOKENS = 256  # Enough for short heckles

# ─── Vision ───────────────────────────────────────────────────
ENABLE_VISION = True
VISION_MAX_SIZE = (1024, 1024)

# ─── Browser Server ───────────────────────────────────────────
SERVER_HOST = "localhost"
SERVER_PORT = 8765

# ─── Demo Mode ─────────────────────────────────────────────────
DEMO_TIME_MULTIPLIER = 60  # 1 real second = 60 simulated seconds (1 sim minute)

# ─── Productive Apps (process names, lowercase) ───────────────
PRODUCTIVE_APPS = {
    "code.exe",          # VS Code
    "devenv.exe",        # Visual Studio
    "pycharm64.exe",     # PyCharm
    "idea64.exe",        # IntelliJ
    "windowsterminal.exe",
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
    "git.exe",
    "python.exe",
    "node.exe",
    "wt.exe",            # Windows Terminal
}

# ─── Dashboard ────────────────────────────────────────────────
DASHBOARD_REFRESH_MS = 500  # how often Tkinter refreshes display
