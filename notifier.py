import threading
import config

try:
    from win11toast import toast
    HAS_WIN11TOAST = True
except ImportError:
    HAS_WIN11TOAST = False


class Notifier:
    """Sends Windows 11 toast notifications."""
    
    def __init__(self):
        self._on_lie_detector_response = None  # callback
    
    def set_lie_detector_callback(self, callback):
        """Set callback for lie detector button responses.
        callback(choice: str) where choice is 'Coding', 'Studying', 'Taking a break', or 'Other'
        """
        self._on_lie_detector_response = callback
    
    def send(self, message: str, rage_level: int = 0) -> None:
        """Send a simple toast notification.
        Title changes based on rage level:
        - 0-3: 'RAGEWARE'
        - 4-6: 'RAGEWARE ⚠️'
        - 7-10: '🔥 RAGEWARE 🔥'
        
        Run in a thread to avoid blocking.
        If win11toast is not available, print to console as fallback.
        """
        def _send():
            title = 'RAGEWARE'
            if rage_level >= 7:
                title = '🔥 RAGEWARE 🔥'
            elif rage_level >= 4:
                title = 'RAGEWARE ⚠️'
            
            if HAS_WIN11TOAST:
                try:
                    toast(title, message, duration='short')
                except Exception as e:
                    print(f'[Notifier] Toast failed: {e}')
                    print(f'[Notifier] {title}: {message}')
            else:
                print(f'[Notifier] {title}: {message}')
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_with_buttons(self, message: str, rage_level: int = 0) -> None:
        """Send a toast with lie-detector action buttons.
        Buttons: 'Coding', 'Studying', 'Taking a break', 'Other'
        
        When a button is clicked, call self._on_lie_detector_response(choice).
        
        With win11toast, use the `buttons` parameter:
        toast(title, message, buttons=['Coding', 'Studying', 'Taking a break', 'Other'], ...)
        
        The toast() function returns a dict with 'arguments' key containing the button clicked.
        Run in a thread. On button click, invoke the callback.
        
        If win11toast is not available, print the message and simulate a response.
        """
        def _send():
            title = 'RAGEWARE — What are you doing?'
            if HAS_WIN11TOAST:
                try:
                    result = toast(title, message, 
                                   buttons=['Coding', 'Studying', 'Taking a break', 'Other'],
                                   duration='long')
                    if result and isinstance(result, dict):
                        choice = result.get('arguments', '')
                        if choice and self._on_lie_detector_response:
                            self._on_lie_detector_response(choice)
                except Exception as e:
                    print(f'[Notifier] Button toast failed: {e}')
                    print(f'[Notifier] {title}: {message}')
            else:
                print(f'[Notifier] {title}: {message}')
                print(f'[Notifier] Buttons: [Coding] [Studying] [Taking a break] [Other]')
        
        threading.Thread(target=_send, daemon=True).start()
