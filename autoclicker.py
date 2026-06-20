import time

import win32api
import win32con

x, y = win32api.GetCursorPos()


def click():
    win32api.mouse_event(win32con.MOUSEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEVENTF_LEFTUP, x, y, 0, 0)
