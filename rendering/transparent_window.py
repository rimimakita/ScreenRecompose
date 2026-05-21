import os
import threading
import time
from multiprocessing import Queue
from queue import Empty

import cv2
import pygame

from regions import rect_manager
from generation.receive_overlay import overlay_receive_loop
from rendering import draw
from regions import asset_loader



os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"


def np_to_surface(image_bgr):
    """BGR形式のNumPy画像をPygame用のSurfaceに変換する。"""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    height, width = image_rgb.shape[:2]
    return pygame.image.frombuffer(image_rgb.tobytes(), (width, height), "RGB")


# def is_clicked_rect(x1, y1, x2, y2, click_x, click_y):
#     """クリック位置が矩形内にあるか判定する。"""
#     if click_x is None or click_y is None:
#         return False

#     return x1 < click_x < x2 and y1 < click_y < y2



def start_overlay_receiver(stop_event, timing_dict):
    """サーバからoverlay画像を受信するスレッドを起動する。"""
    receive_thread = threading.Thread(
        target=overlay_receive_loop,
        args=(stop_event, timing_dict),
        daemon=True
    )
    receive_thread.start()

def render_screen(
    screen,
    image_bgr,
    scroll_clip,
    height
):
    """画面全体を描画する。"""

    surface = np_to_surface(image_bgr)
    screen.blit(surface, (0, 0))

    draw.draw_chrome_tab(screen, image_bgr)

    screen.set_clip(scroll_clip)

    draw.draw_rectangles(
        screen,
        rect_manager.stored_scroll_rectangles,
        height,
        image_bgr
    )

    draw.draw_rectangles(
        screen,
        rect_manager.stored_amazon_name_rectangles,
        height,
        image_bgr
    )

    screen.set_clip(None)

    pygame.display.update()


def transparent_window(queue: Queue, shared_position_data, stop_event):
    """Pygameウィンドウ上に検出矩形とoverlay画像を描画する。"""
    
    # 描画処理全体で使う共有状態を用意する
    timing_dict = {}

    # Pygameを初期化
    pygame.init()
    clock = pygame.time.Clock()

    # overlay生成結果を受け取るスレッドを開始する
    start_overlay_receiver(stop_event, timing_dict)

    # 最初の画像を受け取り、ウィンドウサイズを決める
    first_item = None

    while not stop_event.is_set():
        try:
            first_item = queue.get(timeout=1)
            break
        except Empty:
            print("[描画側] 最初のQueue待機中...")
            continue

    if first_item is None:
        print("[描画側] stop_eventを検知したため終了")
        pygame.quit()
        return

    image_bgr, detection_results, scroll_offset_y, start_time = first_item

    width, height = np_to_surface(image_bgr).get_size()

    # 最初の画像サイズに合わせてPygameウィンドウを作成する
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Replacement Viewer")

    # スクロール対象領域だけを切り抜いて描画するための範囲を作成する
    scroll_clip = pygame.Rect(0, 90, width, height - 90)

    # タブや置き換え表示に使う素材を読み込む
    asset_loader.initialize_assets()

    while not stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_event.set()
                break

        if first_item is not None:
            item = first_item
            first_item = None
        else:
            try:
                item = queue.get(timeout=1)
            except Empty:
                clock.tick(30)
                continue

        image_bgr, detection_results, scroll_offset_y, start_time = item

        rect_manager.update_stored_rectangles(
            detection_results,
            scroll_offset_y,
            height,
            timing_dict=timing_dict,
            image_np=image_bgr
        )

       
        render_screen(
            screen,
            image_bgr,
            scroll_clip,
            height
        )

        elapsed_time = time.time() - start_time
        print(f"[全体処理時間] スクショ～描画完了まで: {elapsed_time:.3f}秒")

        clock.tick(30)

    pygame.quit()

