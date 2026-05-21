import time
from io import BytesIO
import threading

import cv2
import pygame
import requests

from generation.send_batch import request_overlay_generation
from regions.rule.chrome_tab_builder import create_chrome_tab_info, FALLBACK_CHROME_TAB_INFO
from regions.rule import amazon_name
from regions.rule import amazon_recommend
from rendering.color_manager import LABEL_COLORS

# =========================================================
# Constants
# =========================================================

FIXED_LABELS = {"chrome_tab", "chrome_bookmark"}

OVERLAY_TARGET_LABELS = {"amazon_recommend"}

MAX_KEEP_MARGIN = 1500

overlay_lock = threading.Lock()
# =========================================================
# Shared state
# =========================================================

stored_scroll_rectangles = []
stored_amazon_name_rectangles = []
chrome_tab_info = None


def handle_initial_result(result, add_overlay_crops):
    """初期検出時のresultを処理する。"""

    global chrome_tab_info

    label = result[6]

    if label == "chrome_tab":
        chrome_tab_info = create_chrome_tab_info(result)

    elif label == "amazon_recommend":
        rect = amazon_recommend.create_rect(result, add_overlay_crops)
        stored_scroll_rectangles.append(rect)

    elif label in ("amazon_name", "amazon_address"):
        rect = amazon_name.create_rect(result)
        stored_amazon_name_rectangles.append(rect)

def handle_scrolled_result(result, updated_rects, window_height, add_overlay_crops):
    """スクロール後のresultを処理する。"""

    label = result[6]

    if label == "chrome_tab":
        return

    if label in ("amazon_name", "amazon_address"):
        should_add_new_rect = amazon_name.update_rect(
            result,
            stored_amazon_name_rectangles
        )

        if should_add_new_rect:
            rect = amazon_name.create_rect(result)
            stored_amazon_name_rectangles.append(rect)

        return

    if label == "amazon_recommend":
        should_add_new_rect = amazon_recommend.update_rect(
            updated_rects,
            result,
            window_height,
            add_overlay_crops
        )

        if should_add_new_rect:
            rect = amazon_recommend.create_rect(result, add_overlay_crops)
            updated_rects.append(rect)


def update_stored_rectangles(detection_results, scroll_offset_y, window_height, timing_dict=None, image_np=None):
    """検出結果とスクロール量をもとに、保持している矩形情報を更新する。"""

    global chrome_tab_info
    global stored_scroll_rectangles, stored_amazon_name_rectangles

    overlay_batch = []


    def add_overlay_crops(rect_obj):
        """overlay生成用cropをバッチへ追加する。"""
        if image_np is None:
            return
        
        crops = amazon_recommend.build_crops(
            image_np,
            rect_obj
        )

        for i, crop_img in enumerate(crops):
            overlay_batch.append((f"{rect_obj.id}_{i}", crop_img))

    with overlay_lock:
        if scroll_offset_y is None:
            
            stored_scroll_rectangles.clear()
            stored_amazon_name_rectangles.clear()
            LABEL_COLORS.clear()
            chrome_tab_info = None

            for result in detection_results:
                handle_initial_result(result, add_overlay_crops)

            
            if chrome_tab_info is None:
                chrome_tab_info = create_chrome_tab_info(None)

        else:
            for rect in stored_scroll_rectangles:
                rect.move(scroll_offset_y)

        
            for rect in stored_amazon_name_rectangles:
                rect.move(scroll_offset_y)

            updated_rects = stored_scroll_rectangles[:]

            for result in detection_results:
                handle_scrolled_result(
                    result,
                    updated_rects,
                    window_height,
                    add_overlay_crops
                )


            stored_scroll_rectangles[:] = [
                rect for rect in updated_rects
                if (
                        rect.rect.bottom >= -MAX_KEEP_MARGIN
                        and rect.rect.top <= window_height + MAX_KEEP_MARGIN
                )
            ]

        should_send_overlay = bool(overlay_batch)

    if should_send_overlay:
        threading.Thread(
            target=request_overlay_generation,
            args=(overlay_batch, timing_dict)
        ).start()
