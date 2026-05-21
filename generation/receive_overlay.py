import base64
import time

import cv2
import numpy as np
import requests

from generation.overlay_surface_setter import safe_set_overlay_surface
from generation.send_batch import OVERLAY_SERVER_URL


GET_RESULTS_URL = f"{OVERLAY_SERVER_URL}/get_results"
REQUEST_TIMEOUT = 10.0
RETRY_INTERVAL = 0.05


def decode_base64_to_np(base64_str):
    """Base64形式の画像をOpenCVで扱えるNumPy配列に変換する。"""

    image_data = base64.b64decode(base64_str)
    image_array = np.frombuffer(image_data, np.uint8)

    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


def overlay_receive_loop(stop_event, timing_dict):
    """生成サーバからoverlay画像を受信し、対応する矩形に反映し続ける。"""

    while not stop_event.is_set():
        try:
            response = requests.get(
                GET_RESULTS_URL,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 204:
                continue

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                time.sleep(RETRY_INTERVAL)
                continue

            try:
                results = response.json()

            except Exception as error:
                print(f"[OverlayReceive] JSON decode error: {error}")
                continue

            for item in results:
                try:
                    full_id = str(item["id"])
                    base_id = int(full_id.split("_")[0])

                    caption = item["caption"]
                    image_np = decode_base64_to_np(item["image"])

                    safe_set_overlay_surface(base_id, image_np, caption)

                    if full_id in timing_dict:
                        timing_dict.pop(full_id)

                    else:
                        print(f"[Overlay] ID {full_id} → timing_dict に送信記録なし")

                except Exception as error:
                    print(f"[OverlayReceive] Item error: {error}")

        except Exception as error:
            print(f"[OverlayReceive] Error: {error}")

