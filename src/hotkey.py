# src/hotkey.py
# -*- coding: utf-8 -*-
import sys
from PyQt6.QtCore import QAbstractNativeEventFilter

# 预定义变量防止报错
user32 = None
wintypes = None

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes # 显式导入 wintypes
    try:
        user32 = ctypes.windll.user32
    except:
        pass

class GlobalHotkeyManager(QAbstractNativeEventFilter):
    def __init__(self, app_callback):
        super().__init__()
        self.app_callback = app_callback
        self.hotkey_id = 1

    def register_hotkey(self, hwnd):
        if not user32: return False
        # Ctrl+Alt+M (0x4D)
        return user32.RegisterHotKey(int(hwnd), self.hotkey_id, 3, 0x4D)

    def unregister_hotkey(self, hwnd):
        if user32:
            user32.UnregisterHotKey(int(hwnd), self.hotkey_id)

    def nativeEventFilter(self, event_type, message):
        if event_type == "windows_generic_MSG" and wintypes:
            # 使用导入的 wintypes，而不是 ctypes.wintypes
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == 0x0312 and msg.wParam == self.hotkey_id:
                self.app_callback()
                return True, 0
        return False, 0
