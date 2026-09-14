import ctypes
from ctypes import wintypes
import time
import threading
import psutil
import win32gui
import win32process
import io
import base64
try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import config
import domain_classifier

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD)
    ]

class ActivityMonitor:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(ActivityMonitor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.current_app = ""
        self.current_title = ""
        self.current_domain = None
        self.idle_seconds = 0.0
        self.activity_level = "idle"
        self.activity_history = []
        self._lock = threading.Lock()
        self._initialized = True

    def get_active_window(self) -> tuple[str, str]:
        """Returns (process_name, window_title) of the foreground window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return ('unknown', '')
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                process_name = proc.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                process_name = 'unknown'
                
            title = win32gui.GetWindowText(hwnd)
            return (process_name, title)
        except Exception:
            return ('unknown', '')

    def get_idle_seconds(self) -> float:
        """Uses ctypes to call GetLastInputInfo to determine idle time."""
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                tick_count = ctypes.windll.kernel32.GetTickCount()
                # Calculate difference and handle potential DWORD wrap-around
                millis = (tick_count - lii.dwTime) & 0xFFFFFFFF
                return millis / 1000.0
            return 0.0
        except Exception:
            return 0.0

    def get_activity_level(self) -> str:
        """Returns activity level based on current idle_seconds."""
        with self._lock:
            idle_secs = self.idle_seconds
            
        high_thresh = getattr(config, 'ACTIVITY_HIGH_THRESHOLD', 5)
        low_thresh = getattr(config, 'ACTIVITY_LOW_THRESHOLD', 30)
        
        if idle_secs < high_thresh:
            return 'high'
        elif idle_secs < low_thresh:
            return 'low'
        else:
            return 'idle'

    def update_domain(self, domain: str) -> None:
        """Called by browser_server when a domain ping arrives. Thread-safe."""
        with self._lock:
            self.current_domain = domain

    def poll(self) -> dict:
        """Single poll cycle to update state and history."""
        app, title = self.get_active_window()
        idle_secs = self.get_idle_seconds()
        
        high_thresh = getattr(config, 'ACTIVITY_HIGH_THRESHOLD', 5)
        low_thresh = getattr(config, 'ACTIVITY_LOW_THRESHOLD', 30)
        
        if idle_secs < high_thresh:
            activity_lvl = 'high'
        elif idle_secs < low_thresh:
            activity_lvl = 'low'
        else:
            activity_lvl = 'idle'
            
        with self._lock:
            self.current_app = app
            self.current_title = title
            self.idle_seconds = idle_secs
            self.activity_level = activity_lvl
            
            classification = 'neutral'
            productive_apps = getattr(config, 'PRODUCTIVE_APPS', set())
            browser_apps = {'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe', 'vivaldi.exe'}
            
            if self.current_app in productive_apps:
                classification = 'productive'
            
            # For browser processes, prefer domain classification
            if self.current_app in browser_apps and self.current_domain:
                domain_class = domain_classifier.classify(self.current_domain)
                if domain_class != 'neutral':
                    classification = domain_class
                    
            snapshot = {
                'timestamp': time.time(),
                'app': self.current_app,
                'title': self.current_title,
                'domain': self.current_domain,
                'idle_seconds': self.idle_seconds,
                'activity_level': self.activity_level,
                'classification': classification
            }
            
            self.activity_history.append(snapshot)
            
            # Trim to last 5 minutes
            cutoff_time = time.time() - 300
            self.activity_history = [
                h for h in self.activity_history if h['timestamp'] >= cutoff_time
            ]
            
            return snapshot

    def get_recent_history(self, seconds: int = 120) -> list[dict]:
        """Return activity snapshots from the last `seconds` seconds. Thread-safe."""
        with self._lock:
            cutoff = time.time() - seconds
            return [h for h in self.activity_history if h['timestamp'] >= cutoff]

    def get_state(self) -> dict:
        """Return current state as a dict for dashboard display. Thread-safe."""
        with self._lock:
            classification = 'neutral'
            if self.activity_history:
                classification = self.activity_history[-1].get('classification', 'neutral')
                
            return {
                'app': self.current_app,
                'title': self.current_title,
                'domain': self.current_domain,
                'idle_seconds': self.idle_seconds,
                'activity_level': self.activity_level,
                'classification': classification,
            }

    def capture_screen_base64(self) -> str | None:
        """Capture the foreground window (or full screen), resize, return as base64 JPEG."""
        if not HAS_PIL:
            return None
        
        # If we've already determined capture doesn't work, skip
        if getattr(self, '_capture_disabled', False):
            return None
            
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        
        img = None
        
        # Method 1: PrintWindow on the foreground window
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                print(f"[Vision] PrintWindow target: hwnd={hwnd} '{title[:50]}' ({w}x{h})")
                if w > 0 and h > 0:
                    import win32ui
                    import win32con
                    wDC = win32gui.GetWindowDC(hwnd)
                    dcObj = win32ui.CreateDCFromHandle(wDC)
                    memDC = dcObj.CreateCompatibleDC()
                    bmp = win32ui.CreateBitmap()
                    bmp.CreateCompatibleBitmap(dcObj, w, h)
                    memDC.SelectObject(bmp)
                    # PW_RENDERFULLCONTENT = 2
                    result = ctypes.windll.user32.PrintWindow(hwnd, memDC.GetSafeHdc(), 2)
                    if result == 1:
                        bmpinfo = bmp.GetInfo()
                        bmpstr = bmp.GetBitmapBits(True)
                        from PIL import Image
                        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
                        print(f"[Vision] PrintWindow OK: captured {img.size[0]}x{img.size[1]}")
                    else:
                        print(f"[Vision] PrintWindow returned {result} (failed)")
                    memDC.DeleteDC()
                    dcObj.DeleteDC()
                    win32gui.ReleaseDC(hwnd, wDC)
                    win32gui.DeleteObject(bmp.GetHandle())
            else:
                print("[Vision] No foreground window (hwnd=0)")
        except Exception as e:
            print(f"[Vision] PrintWindow error: {e}")
        
        # Method 2: PIL ImageGrab (full screen)
        if img is None:
            print("[Vision] Trying ImageGrab fallback...")
            try:
                img = ImageGrab.grab()
                print(f"[Vision] ImageGrab OK: {img.size[0]}x{img.size[1]}")
            except Exception as e:
                print(f"[Vision] ImageGrab failed: {e}")
        
        # If nothing worked, disable future attempts and warn once
        if img is None:
            self._capture_disabled = True
            print("[Monitor] Screen capture unavailable (access denied). "
                  "Run from a standalone terminal for screenshot support. "
                  "Continuing without vision.")
            return None
        
        # Resize and encode
        max_size = getattr(config, 'VISION_MAX_SIZE', (1024, 1024))
        img.thumbnail(max_size)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        kb_size = len(b64_str) * 3 // 4 // 1024
        print(f"[Vision] Encoded: {img.size[0]}x{img.size[1]} → {kb_size} KB base64")
        return b64_str

