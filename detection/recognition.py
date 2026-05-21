import time
from multiprocessing import Queue
from queue import Full

import cv2
import mss
import numpy as np
import torch
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowListOptionOnScreenOnly,
)


def get_window_bounds(app_name="Google Chrome", title_substr=None):
    """
    指定アプリの表示中ウィンドウを探索し、
    最も優先度の高いウィンドウの座標を返す。

    Returns:
        (x, y, width, height) または None
    """
    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )

    candidates = []

    for window in window_list:
        owner_name = window.get("kCGWindowOwnerName", "") or ""
        window_title = window.get("kCGWindowName", "") or ""
        bounds = window.get("kCGWindowBounds", {}) or {}
        layer = window.get("kCGWindowLayer", 0)

        if owner_name != app_name or layer != 0:
            continue

        x = int(bounds.get("X", 0))
        y = int(bounds.get("Y", 0))
        width = int(bounds.get("Width", 0))
        height = int(bounds.get("Height", 0))

        if width <= 0 or height <= 0:
            continue

        score = width * height

        if title_substr and title_substr in window_title:
            score += 10_000_000

        candidates.append(((x, y, width, height), score))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0][0]


def capture_window_half_resolution(width, height):
    """
    対象ウィンドウをキャプチャし、
    半分の解像度へリサイズした画像を返す。
    """
    bounds = get_window_bounds()

    if bounds is None:
        print("Target window not found.")
        return None

    x, y, _, _ = bounds

    with mss.mss() as sct:
        monitor = {
            "top": y,
            "left": x,
            "width": width,
            "height": height,
        }

        screenshot = sct.grab(monitor)

        image = np.frombuffer(
            screenshot.rgb,
            dtype=np.uint8
        ).reshape((screenshot.height, screenshot.width, 3))

        resized_image = cv2.resize(
            image,
            (screenshot.width // 2, screenshot.height // 2),
            interpolation=cv2.INTER_LINEAR
        )

        return resized_image


def detection_results_to_list(results):
    """
    YOLOv5 の推論結果を list 形式へ変換する。
    """
    dataframe = results.pandas().xyxy[0]
    dataframe.iloc[:, :4] = dataframe.iloc[:, :4].astype(int)

    return dataframe.values.tolist()


def estimate_vertical_scroll(previous_image, current_image, threshold=1.0):
    """
    位相相関を用いて縦方向のスクロール量を推定する。

    Returns:
        int: スクロール量
        0: スクロールなし
        None: 推定失敗
    """
    previous_gray = cv2.cvtColor(previous_image, cv2.COLOR_BGR2GRAY)
    current_gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)

    height, width = previous_gray.shape

    top = 140
    bottom = height
    left = int(width * 0.3)
    right = int(width * 0.7)

    previous_crop = previous_gray[top:bottom, left:right]
    current_crop = current_gray[top:bottom, left:right]

    shift, response = cv2.phaseCorrelate(
        np.float32(previous_crop),
        np.float32(current_crop)
    )

    if response < 0.3:
        return None

    scroll_y = shift[1]

    if abs(scroll_y) <= threshold:
        return 0

    return int(round(scroll_y))


def capture_and_detect_loop(queue: Queue, stop_event):
    """
    スクリーンショット取得と YOLO 推論を繰り返し実行し、
    結果を Queue に送信する。
    """
    model_path = "./models/SC_sites_val_1065.pt"

    model = torch.hub.load(
        "./yolov5",
        "custom",
        source="local",
        path=model_path
    )

    bounds = get_window_bounds()

    if bounds is None:
        print("Target window not found.")
        return

    _, _, capture_width, capture_height = bounds

    previous_image = capture_window_half_resolution(
        capture_width,
        capture_height
    )

    initial_results = model(previous_image, size=320)

    try:
        queue.put_nowait((
            previous_image[:, :, ::-1].copy(),
            detection_results_to_list(initial_results),
            None,
            time.time()
        ))
    except Full:
        print("[YOLO] Queue is full.")

    while not stop_event.is_set():

        current_image = capture_window_half_resolution(
            capture_width,
            capture_height
        )

        if current_image is None:
            continue

        if np.array_equal(current_image, previous_image):
            continue

        scroll_offset_y = estimate_vertical_scroll(
            previous_image,
            current_image
        )

        results = model(current_image, size=320)

        try:
            queue.put_nowait((
                current_image[:, :, ::-1].copy(),
                detection_results_to_list(results),
                scroll_offset_y,
                time.time()
            ))
        except Full:
            print("[YOLO] Queue is full.")

        previous_image = current_image.copy()

    print("[YOLO] Stop event detected.")
