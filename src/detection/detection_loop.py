import time
from multiprocessing import Queue
from queue import Full

import numpy as np
import torch

from paths import MODEL_DIR, YOLOV5_DIR

from detection.screen_capture import (
    get_window_bounds,
    capture_window_half_resolution,
    estimate_vertical_scroll,
)




def load_yolo_model():
    model_path = MODEL_DIR / "SC_sites_val_1065.pt"
    return torch.hub.load(
        str(YOLOV5_DIR),
        "custom",
        source="local",
        path=str(model_path)
    )


def detect_objects(model, image):
    """
    YOLOv5で物体検出を行い、
    list形式の検出結果を返す。
    """

    results = model(image, size=320)

    dataframe = results.pandas().xyxy[0]
    dataframe.iloc[:, :4] = dataframe.iloc[:, :4].astype(int)

    return dataframe.values.tolist()

def send_detection_result(queue, image, detections, scroll_offset_y):
    try:
        queue.put_nowait((
            image[:, :, ::-1].copy(),
            detections,
            scroll_offset_y,
            time.time()
        ))
    except Full:
        print("[YOLO] Queue is full.")


def capture_detection_loop(queue: Queue, stop_event):
    """
    スクリーンショット取得と YOLO 推論を繰り返し実行し、
    結果を Queue に送信する。
    """
    model = load_yolo_model()
    bounds = get_window_bounds()

    if bounds is None:
        print("Target window not found.")
        return

    _, _, capture_width, capture_height = bounds

    previous_image = capture_window_half_resolution(
        capture_width,
        capture_height
    )

    detections = detect_objects(model, previous_image)

    send_detection_result(queue, previous_image, detections, None)

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


        detections = detect_objects(model, current_image)

        send_detection_result(queue, current_image, detections, scroll_offset_y)

        previous_image = current_image.copy()

    print("[YOLO] Stop event detected.")
