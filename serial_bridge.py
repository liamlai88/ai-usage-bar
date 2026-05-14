"""USB serial bridge — pushes the latest usage snapshot to an M5StickC
(or any device) over /dev/cu.usbserial-* every few seconds.

Format: one JSON line per push, terminated by \\n. The device parses on
newline. Handles disconnect/reconnect gracefully (so plugging the USB
back in or rebooting the device just works).
"""
import glob
import json
import threading
import time
from typing import Optional

import serial

from server import _latest_payload as _LATEST   # 复用 HTTP server 的缓存
from config import SERIAL_PORT, SERIAL_BAUD, SERIAL_PUSH_EVERY


def _auto_detect_port() -> Optional[str]:
    """Look for the first USB-serial device that looks like an M5Stick / ESP32."""
    patterns = [
        "/dev/cu.usbserial-*",
        "/dev/cu.wchusbserial*",
        "/dev/cu.SLAB_USBtoUART*",
    ]
    for p in patterns:
        hits = glob.glob(p)
        if hits:
            return sorted(hits)[0]
    return None


class SerialBridge:
    def __init__(self, port: Optional[str], baud: int, push_every: int):
        self._configured_port = port
        self._baud = baud
        self._push_every = push_every
        self._stop = False

    def _open(self) -> Optional[serial.Serial]:
        port = self._configured_port or _auto_detect_port()
        if not port:
            return None
        try:
            ser = serial.Serial(port, self._baud, timeout=0.2)
            return ser
        except Exception as e:
            print(f"[serial] open {port} failed: {e}", flush=True)
            return None

    def run(self):
        ser = None
        last_push = 0.0
        while not self._stop:
            if ser is None:
                ser = self._open()
                if ser is None:
                    # 设备未插，等下一轮
                    time.sleep(2)
                    continue
                else:
                    print(f"[serial] connected to {ser.port}", flush=True)

            try:
                now = time.time()
                if now - last_push >= self._push_every:
                    payload = json.dumps(_LATEST, separators=(",", ":")) + "\n"
                    ser.write(payload.encode("utf-8"))
                    ser.flush()
                    last_push = now
                time.sleep(0.5)
            except (serial.SerialException, OSError) as e:
                print(f"[serial] write failed: {e} — will retry", flush=True)
                try: ser.close()
                except Exception: pass
                ser = None
                time.sleep(2)

    def stop(self):
        self._stop = True


_thread: Optional[threading.Thread] = None
_bridge: Optional[SerialBridge] = None


def start():
    global _thread, _bridge
    if _thread is not None:
        return
    _bridge = SerialBridge(SERIAL_PORT, SERIAL_BAUD, SERIAL_PUSH_EVERY)
    _thread = threading.Thread(target=_bridge.run, daemon=True, name="SerialBridge")
    _thread.start()
    print(f"[serial] bridge started (push every {SERIAL_PUSH_EVERY}s)", flush=True)
