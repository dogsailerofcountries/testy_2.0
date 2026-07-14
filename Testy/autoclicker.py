import time

import pynput
import win32api
import win32con

running = True
x, y = win32api.GetCursorPos()


def click():
    while running:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        time.sleep(0.3)


def stop():
    running = False


with pynput.keyboard.GlobalHotKeys({"<ctrl>+<alt>+f": click}) as h:
    h.join()
