import time
from io import BytesIO

import cv2
import requests


OVERLAY_SERVER_URL = (
    "https://19zraqksouh5uv-5000.proxy.runpod.net"
)
PROCESS_BATCH_URL = f"{OVERLAY_SERVER_URL}/process_batch"


def request_overlay_generation(batch, timing_dict):
    """切り出したoverlay画像を生成サーバへ送信する。"""

    files = {}

    start_time = time.perf_counter()

    for rect_id, image_np in batch:
        success, buffer = cv2.imencode(
            ".jpg",
            image_np,
            [int(cv2.IMWRITE_JPEG_QUALITY), 85],
        )

        if not success:
            continue

        files[str(rect_id)] = (
            "image.jpg",
            BytesIO(buffer.tobytes()),
            "image/jpeg",
        )

        timing_dict[str(rect_id)] = start_time

    try:
        requests.post(
            PROCESS_BATCH_URL,
            files=files,
            headers={"Accept": "multipart/mixed"},
        )

    except Exception as error:
        print(f"[Send] Error: {error}")


