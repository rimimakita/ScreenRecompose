from pynput import mouse
from multiprocessing import Queue, Manager
import pyautogui
import threading
import time


def click_process(q: Queue, shared_position_data, stop_event):
    def on_click(x, y, button, pressed):
        if pressed:
            try:
                shared_position_data['x'] = recttop_x
                shared_position_data['y'] = recttop_y
            except:
                pass

        if stop_event.is_set():
            print("[CLICK] stop_event を検知し、リスナーを停止")
            return False  # → listener.stop() と同義（終了条件）

    listener = mouse.Listener(on_click=on_click)
    listener.start()
    while not stop_event.is_set():
        time.sleep(0.1)
    listener.stop()
    listener.join()
    print("[CLICK] 終了しました")


