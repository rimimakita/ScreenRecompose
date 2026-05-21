import time
from io import BytesIO
import threading

import cv2
import pygame
import requests

from generation.send_batch import request_overlay_generation
from regions.chrome_tab_builder import create_chrome_tab_info, FALLBACK_CHROME_TAB_INFO
from regions import amazon_name_rule
from regions import amazon_recommend_rule
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
        rect = amazon_recommend_rule.create_rect(result, add_overlay_crops)
        stored_scroll_rectangles.append(rect)

    elif label in ("amazon_name", "amazon_address"):
        rect = amazon_name_rule.create_rect(result)
        stored_amazon_name_rectangles.append(rect)

def handle_scrolled_result(result, updated_rects, window_height, add_overlay_crops):
    """スクロール後のresultを処理する。"""

    label = result[6]

    if label == "chrome_tab":
        return

    if label in ("amazon_name", "amazon_address"):
        should_add_new_rect = amazon_name_rule.update_rect(
            result,
            stored_amazon_name_rectangles
        )

        if should_add_new_rect:
            rect = amazon_name_rule.create_rect(result)
            stored_amazon_name_rectangles.append(rect)

        return

    if label == "amazon_recommend":
        should_add_new_rect = amazon_recommend_rule.update_rect(
            updated_rects,
            result,
            window_height,
            add_overlay_crops
        )

        if should_add_new_rect:
            rect = amazon_recommend_rule.create_rect(result, add_overlay_crops)
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
        
        crops = amazon_recommend_rule.build_crops(
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



        

# stored_scroll_rectangles = []  # ← 描画済み＋保持用
# stored_fixed_rectangles = []  # ← 固定エリア用（0～90pxなど）
# stored_amazon_name_rectangles = []

# FIXED_THRESHOLD_Y = 90  # 上部固定領域のしきい値（Y座標）
# FIXED_LABELS = {'chrome_tab', 'chrome_bookmark'}
# MARGIN_KEEP_RECT = 1500
# OVERLAY_LABELS = {'amazon_recommend'}
# loaded_icons = None
# chrome_tab_surface = None
# font = None  # 初期化は後で
# TAB = 6
# OVERLAY_W_TH = 330  # 横4分割に切り替える幅の閾値

# overlay_lock = threading.Lock()

# def fast_sanitize_caption(s: str) -> str:
#     if not s:
#         return ""

#     # 改行系を潰す（wrap処理にも優しい）
#     s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")

#     # フォントに無い文字が来ても□になりにくいように、ASCII以外は '?' に倒す
#     # （英語主体ならこれが最速＆一番堅い）
#     out = []
#     for ch in s:
#         o = ord(ch)
#         if 32 <= o <= 126:          # printable ASCII
#             out.append(ch)
#         elif ch == " ":             # 念のため
#             out.append(" ")
#         else:
#             out.append("?")
#     s = "".join(out).strip()

#     # 速度最優先なら、スペース潰しは省略してOK
#     # s = " ".join(s.split())

#     return s


# def safe_set_overlay_surface(target_id, overlay_np, caption_text):
#     with overlay_lock:
#         for rect in stored_scroll_rectangles:
#             if rect.id == target_id:
#                 expected = getattr(rect, "overlay_expected", 1) 
                
#                 if expected == 1:
#                     target_width = int(rect.rect.width * 0.86)

#                 elif expected == 4:
#                     if rect.rect.width > OVERLAY_W_TH:
#                         target_width = int(rect.rect.width * 0.23)
#                     else:
#                         target_width = int(rect.rect.width * 0.44)


#                 resized_np = cv2.resize(
#                     overlay_np,
#                     (target_width, target_width),
#                     interpolation=cv2.INTER_NEAREST
#                 )

#                 overlay_rgb = cv2.cvtColor(resized_np, cv2.COLOR_BGR2RGB)

#                 surface = pygame.image.frombuffer(
#                     overlay_rgb.tobytes(),
#                     (overlay_rgb.shape[1], overlay_rgb.shape[0]),
#                     "RGB"
#                 )

#                 rect.overlay_surfaces.append(surface)


#                 rect.text_line = fast_sanitize_caption(caption_text)

#                 return

#         # ★ rect が見つからなかった場合
#         print(f"[OverlaySet] DROP: rect id={target_id} not found")



# # .txtファイルをすべて読み込む
# def load_all_words_from_eowl():
#     words = []
#     for filename in os.listdir("./EOWL-v1.1.2/LF Delimited Format"):
#         if filename.endswith(".txt"):
#             path = os.path.join("./EOWL-v1.1.2/LF Delimited Format", filename)
#             with open(path, "r", encoding="utf-8") as f:
#                 for line in f:
#                     word = line.strip()
#                     if word and len(word) > 2:  # 空行と短すぎる単語を除外
#                         words.append(word)
#     return words

# # 単語をロードしてランダムに1語選ぶ
# words = load_all_words_from_eowl()


# def load_all_icons_from_openmoji():
#     icons = []
#     for filename in os.listdir("./openmoji-72x72-color"):
#         if filename.endswith(".png"):
#             path = os.path.join("./openmoji-72x72-color", filename)
#             try:
#                 icon_surface = pygame.image.load(path).convert_alpha()
#                 icons.append(icon_surface)
#             except Exception as e:
#                 print(f"[IconLoadError] {filename}: {e}")
#     return icons

# def set_loaded_icons(icons):
#     global loaded_icons
#     loaded_icons = icons



# def build_chrome_tab_overlay_surface(size):
#     surface = pygame.Surface(size, pygame.SRCALPHA)
#     width, height = size
#     center_y = height // 2

#     left_margin = 2
#     right_margin = 2
#     icon_size = 19
#     bg_size = 16
#     spacing = 4
#     bar_color = (80, 80, 80)
#     text_color = (200, 200, 200)
#     section_width = (width - 130) // TAB

#     selected_words = random.sample(words, TAB) if len(words) >= TAB else words[:]
#     selected_icons = random.sample(loaded_icons, TAB) if len(loaded_icons) >= TAB else loaded_icons[:]
#     item_count = min(TAB, len(selected_words), len(selected_icons))

#     for i in range(item_count):
#         section_left = left_margin + i * section_width
#         section_right = section_left + section_width

#         cursor_x = section_left

#         # 背景（角丸）
#         bg_y = center_y - bg_size // 2
#         pygame.draw.rect(surface, (255, 255, 255), (cursor_x, bg_y, bg_size, bg_size), border_radius=4)

#         # アイコン
#         icon = pygame.transform.smoothscale(selected_icons[i], (icon_size, icon_size))
#         icon_x = cursor_x + (bg_size - icon_size) // 2
#         icon_y = center_y - icon_size // 2
#         surface.blit(icon, (icon_x, icon_y))

#         cursor_x += bg_size + spacing

#         # --- バーの位置をセクション内に含める
#         bar_width = 1
#         bar_spacing = spacing * 3 # ← テキストとバーの間隔を確保
#         bar_x = section_right - bar_spacing

#         # --- テキスト（バーの手前に収まるように）

#         word = selected_words[i]
#         max_text_width = bar_x - cursor_x
#         trimmed = word
#         while True:
#             text_surface = font.render(trimmed.capitalize(), True, text_color)
#             if text_surface.get_width() <= max_text_width or len(trimmed) <= 1:
#                 break
#             trimmed = trimmed[:-1]

#         text_surface = font.render(trimmed.capitalize(), True, text_color)
#         text_y = center_y - text_surface.get_height() // 2
#         surface.blit(text_surface, (cursor_x, text_y))

#         # --- 縦線（バーをタブの右端に描画）
#         line_y1 = center_y - icon_size // 2
#         line_y2 = center_y + icon_size // 2
#         pygame.draw.line(surface, bar_color, (bar_x, line_y1), (bar_x, line_y2), width=bar_width)

#     # --- 「＋」マークの描画
#     plus_font = pygame.font.SysFont("Arial", int(font.get_height() * 1.3))
#     plus_surface = plus_font.render("+", True, text_color)
#     plus_y = center_y - plus_surface.get_height() // 2
#     plus_x = left_margin + item_count * section_width + spacing + right_margin
#     surface.blit(plus_surface, (plus_x, plus_y))

#     return surface



# def center_distance(r1, r2):
#     cx1 = (r1[0] + r1[2]) / 2
#     cy1 = (r1[1] + r1[3]) / 2
#     cx2 = (r2[0] + r2[2]) / 2
#     cy2 = (r2[1] + r2[3]) / 2
#     return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

# def send_to_colab(batch,timing_dict):
#     files = {}
#     t_start = time.perf_counter()  # 計測開始
#     for rect_id, image_np in batch:
#         is_success, buffer = cv2.imencode(".jpg", image_np, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
#         if not is_success:
#             continue
#         files[str(rect_id)] = ('image.jpg', BytesIO(buffer.tobytes()), 'image/jpeg')
#         timing_dict[str(rect_id)] = t_start  # ← 🔧 送信時刻を記録（文字列にするのが無難）

#     try:
#         headers = {"Accept": "multipart/mixed"}
#         requests.post(
#             "https://19zraqksouh5uv-5000.proxy.runpod.net/process_batch",
#             files=files,
#             headers=headers)
#         # t_end = time.perf_counter()  # 計測終了
#         # print(f"[Request] サーバ送信時間: {t_end - t_start:.4f} 秒")
#     except Exception as e:
#         print(f"[Send] Error: {e}")


# def is_significantly_overlapping(rect1, rect2, area_ratio_threshold=0.1):
#     x1, y1, x2, y2 = rect1
#     x1b, y1b, x2b, y2b = rect2

#     # 重なり領域の座標
#     xi1 = max(x1, x1b)
#     yi1 = max(y1, y1b)
#     xi2 = min(x2, x2b)
#     yi2 = min(y2, y2b)

#     # 重なっていない
#     if xi2 <= xi1 or yi2 <= yi1:
#         return False

#     # 重なりの面積
#     overlap_area = (xi2 - xi1) * (yi2 - yi1)

#     # rect1 と rect2 それぞれの面積
#     area1 = (x2 - x1) * (y2 - y1)
#     area2 = (x2b - x1b) * (y2b - y1b)

#     # 小さい方を基準に重なり率を計算
#     base_area = min(area1, area2)
#     if base_area <= 0:
#         return False

#     return (overlap_area / base_area) >= area_ratio_threshold


# def calc_merged_box(new_box, old_box):

#     # --- unpack from old_box
#     old_x1, old_y1, old_x2, old_y2 = old_box
#     x1, y1, x2, y2 = new_box


#     old_w = old_x2 - old_x1
#     old_h = old_y2 - old_y1

#     new_w = x2 - x1
#     new_h = y2 - y1
#     widen_ratio_limit=1.2

#     # ===== 横方向：更新するかどうか =====
#     # 幅に応じて MAX_W を決める
#     if new_w < 270 and old_w < 270:
#         MAX_W = 230
#     else:
#         MAX_W = 720

#     if new_w > old_w:
#         # new の方が広いときだけ比率チェック
#         if new_w <= old_w * widen_ratio_limit:
#             # そこまで極端に大きくない → new を採用
#             base_x1, base_x2 = x1, x2
#         else:
#             # 極端に広がっている → old を維持
#             base_x1, base_x2 = old_x1, old_x2
#     else:
#         # old の方が広い or 同じ → もともとの方を使う
#         base_x1, base_x2 = old_x1, old_x2

#     base_w = base_x2 - base_x1

#     if base_w <= MAX_W:
#         # そのままでOK
#         final_x1, final_x2 = base_x1, base_x2
#     else:
#         # 中心を保ったまま、幅を MAX_W にクリップ
#         center_x = (base_x1 + base_x2) / 2.0
#         half_w = MAX_W / 2.0

#         final_x1 = int(round(center_x - half_w))
#         final_x2 = final_x1 + MAX_W
        
#     # ===== 縦方向：315 に収める =====
#     MAX_H = 300

#     # 長い方の高さをベースにする
#     if new_h > old_h:
#         base_y1, base_y2 = y1, y2
#     else:
#         base_y1, base_y2 = old_y1, old_y2

#     base_h = base_y2 - base_y1

#     if base_h <= MAX_H:
#         # そのままでOK
#         final_y1, final_y2 = base_y1, base_y2
#     else:
#         # 中心を保ったまま、高さを MAX_H にクリップ
#         center = (base_y1 + base_y2) / 2.0

#         half = MAX_H / 2.0
#         final_y1 = int(round(center - half))
#         final_y2 = final_y1 + MAX_H

#     final_w = final_x2 - final_x1
#     final_h = final_y2 - final_y1
#     return final_x1, final_y1, final_w, final_h




# def crop_region_from_image(image_np: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
#     # 範囲外を防ぐためのクリッピング
#     h, w = image_np.shape[:2]
#     x1_clipped = max(0, min(w, x1))
#     x2_clipped = max(0, min(w, x2))
#     y1_clipped = max(0, min(h, y1))
#     y2_clipped = max(0, min(h, y2))

#     # 切り出し
#     return image_np[y1_clipped:y2_clipped, x1_clipped:x2_clipped]


# def choose_overlay_count(width: int) -> int:
#     # width > 300 のときは従来通り常に4
#     if width > OVERLAY_W_TH:
#         return 4
#     # width <= 300 のとき：1/5で1枚、4/5で4枚
#     return 1 if random.random() < 0.2 else 4

# def build_overlay_crops(image_np, x1, y1, x2, y2, count):
#     """
#     count に応じて切り出し画像リストを返す
#     - count == 1: 元範囲のまま1枚
#     - count == 4:
#         - (x2-x1) >= 300: 横方向に4等分（1x4）
#         - (x2-x1) < 300 : 十字に4等分（2x2）
#     """
#     width = x2 - x1
#     height = y2 - y1

#     if count != 4:
#         # 今回の仕様では count は 1 or 4 想定だけど、安全にフォールバック
#         return [crop_region_from_image(image_np, x1, y1, x2, y2)]

#     crops = []

#     if width >= OVERLAY_W_TH:
#         # 横4等分（左→右の順）
#         # 端数が出ても最後に吸収させる
#         w = width
#         step = w // 4
#         xs = [x1 + step * i for i in range(4)]
#         xe = [x1 + step * (i + 1) for i in range(4)]
#         xe[-1] = x2  # 端数吸収

#         for i in range(4):
#             cx1 = int(xs[i])
#             cx2 = int(xe[i])
#             crops.append(crop_region_from_image(image_np, cx1, y1, cx2, y2))

#     else:
#         # 十字に4等分（2x2）
#         mid_x = x1 + width // 2
#         mid_y = y1 + height // 2

#         # 順番は [TL, TR, BL, BR] にしておく（i=0..3）
#         boxes = [
#             (x1,    y1,    mid_x, mid_y),  # top-left
#             (mid_x, y1,    x2,    mid_y),  # top-right
#             (x1,    mid_y, mid_x, y2),     # bottom-left
#             (mid_x, mid_y, x2,    y2),     # bottom-right
#         ]
#         for (cx1, cy1, cx2, cy2) in boxes:
#             crops.append(crop_region_from_image(image_np, int(cx1), int(cy1), int(cx2), int(cy2)))

#     return crops



# def update_stored_rectangles(new_rects, scroll_offset_y, window_height, timing_dict=None, image_np=None):
#     global chrome_tab_surface  # 必要、かつ安全
#     global stored_fixed_rectangles, stored_scroll_rectangles, stored_amazon_name_rectangles
#     overlay_batch = []

#     with overlay_lock:  # 🔒 全体を保護
#         if scroll_offset_y is None:
#             print("[update_stored_rectangles] 初期化が発生しました (scroll_offset_y is None)")
#             # 初期化
#             stored_scroll_rectangles.clear()
#             stored_amazon_name_rectangles.clear()
            
#             for rect in new_rects:
#                 x1, y1, x2, y2, color, label = rect

#                 rect_id = next_rect_id()
#                 height = y2 - y1
                
                
#                 # ✅ chrome_tabのSurfaceを一度だけ作成
#                 if label == 'chrome_tab' and not stored_fixed_rectangles:
#                     obj = RectObject(x1, y1, x2, y2, color, label=label, overlay_surfaces=[], rect_id=rect_id, text_lines=[])
#                     stored_fixed_rectangles.append(obj)
                    
#                     width = x2 - x1
#                     chrome_tab_surface = build_chrome_tab_overlay_surface((width, height))
                    
                    
#                 elif label == 'amazon_recommend':
#                     count = 1  # デフォルト
#                     if height > 180:
#                         width = x2 - x1
#                         count = choose_overlay_count(width)
#                         crops = build_overlay_crops(image_np, x1, y1, x2, y2, count)
#                         for i, crop_img in enumerate(crops):
#                             overlay_batch.append((f"{rect_id}_{i}", crop_img))
                        
#                     obj = RectObjectA(
#                         x1, y1, x2, y2, color,
#                         overlay_expected=count,   
#                         overlay_surfaces=[],
#                         rect_id=rect_id
#                     )
#                     stored_scroll_rectangles.append(obj)


#                 elif label in ('amazon_name', 'amazon_address'):
#                     # ✅ amazon_name は座標＋色だけ別グローバルに保持
#                     # ---- ★ 高さ補正処理（最小高さ 35px）----
#                     MIN_H = 35
#                     height = y2 - y1

#                     if height < MIN_H:
#                         diff = MIN_H - height
#                         half = diff // 2

#                         # 上下に均等に広げる
#                         new_y1 = y1 - half
#                         new_y2 = y2 + (diff - half)

#                         # 必要なら座標の上限チェック（画面上にはみ出す場合）
#                         # new_y1 = max(0, new_y1)

#                         y1, y2 = new_y1, new_y2
#                     # ---- ★ 幅補正（最小幅 138px / x1固定でx2だけ動かす）----
#                     MIN_W = 140
#                     width = x2 - x1
#                     if width < MIN_W:
#                         x2 = x1 + MIN_W

#                     stored_amazon_name_rectangles.append((x1, y1, x2, y2, color))

#             if overlay_batch:
#                 threading.Thread(target=send_to_colab, args=(overlay_batch, timing_dict)).start()


#             if not stored_fixed_rectangles:
#                 fx1, fy1, fx2, fy2 = 90, 0, 660, 35  # fallback 矩形（固定）

#                 fallback = RectObject(
#                     fx1, fy1, fx2, fy2,
#                     color=(0, 0, 0),      # 黒
#                     label='chrome_tab',
#                     rect_id=next_rect_id(),
#                 )

#                 # ★ fallback 矩形のサイズを使う
#                 chrome_tab_surface = build_chrome_tab_overlay_surface((fx2 - fx1, fy2 - fy1))

#                 stored_fixed_rectangles.append(fallback)

#             return

#         # スクロール移動
#         for obj in stored_scroll_rectangles:
#             obj.move(scroll_offset_y)

#         MARGIN_FIX = 0  # 端でブレるなら 20〜50 くらいに
#         for obj in stored_scroll_rectangles:
#             if obj.rect.bottom <= -MARGIN_FIX or obj.rect.top >= window_height + MARGIN_FIX:
#                 obj.fix = True
            
#         for i, (x1, y1, x2, y2, color) in enumerate(stored_amazon_name_rectangles):
#                 stored_amazon_name_rectangles[i] = (
#                     x1,
#                     y1 + scroll_offset_y,
#                     x2,
#                     y2 + scroll_offset_y,
#                     color,
#                 )

#         # 矩形リストをコピーして比較＆更新
#         updated_rects = stored_scroll_rectangles[:]

#         for new in new_rects:
#             x1, y1, x2, y2, color, label = new

#             if label in FIXED_LABELS:
#                 continue

            

#             if label in ('amazon_name', 'amazon_address'):
#                 # 既存 amazon_name 全てと x 範囲が重ならない場合だけ新規追加
#                 if all(x2 <= ox1 or ox2 <= x1
#                        for (ox1, oy1, ox2, oy2, ocolor) in stored_amazon_name_rectangles):
#                     MIN_H = 35
#                     height = y2 - y1

#                     if height < MIN_H:
#                         diff = MIN_H - height
#                         half = diff // 2

#                         # 上下に均等に広げる
#                         new_y1 = y1 - half
#                         new_y2 = y2 + (diff - half)

#                         # 必要なら座標の上限チェック（画面上にはみ出す場合）
#                         # new_y1 = max(0, new_y1)

#                         y1, y2 = new_y1, new_y2

#                     # ---- ★ 幅補正（最小幅 138px / x1固定でx2だけ動かす）----
#                     MIN_W = 140
#                     width = x2 - x1
#                     if width < MIN_W:
#                         x2 = x1 + MIN_W

#                     stored_amazon_name_rectangles.append((x1, y1, x2, y2,  color))

#                 continue


           
#             new_box = (x1, y1, x2, y2)
#             keep_new = True

#             for old_obj in updated_rects:
#                 if old_obj.rect.bottom <= 0 or  old_obj.rect.top >= window_height :
#                     continue

#                 old_box = (
#                     old_obj.rect.left, old_obj.rect.top,
#                     old_obj.rect.right, old_obj.rect.bottom
#                 )
#                 if is_significantly_overlapping(new_box, old_box):
#                     keep_new = False

#                     if not old_obj.fix:
#                         old_height = old_obj.rect.bottom - old_obj.rect.top
#                         final_x, final_y, final_w, final_h = calc_merged_box(new_box, old_box)
#                         old_obj.rect.update(final_x, final_y, final_w, final_h)
                       
#                         new_height = y2 - y1
#                         if (
#                                 old_height <= 180 and 
#                                 new_height > 180 and 
#                                 label in OVERLAY_LABELS and 
#                                 not old_obj.overlay_surfaces
#                         ):
#                             width = x2 - x1
#                             count = choose_overlay_count(width)
#                             old_obj.overlay_expected = count
#                             crops = build_overlay_crops(image_np, x1, y1, x2, y2, count)
#                             for i, crop_img in enumerate(crops):
#                                 overlay_batch.append((f"{old_obj.id}_{i}", crop_img))
                            
#                     break

#             if keep_new:
#                 rect_id = next_rect_id()
#                 height = y2 - y1
#                 count = 1  # ★デフォルト
#                 if label in OVERLAY_LABELS and height > 180:
#                     width = x2 - x1
#                     count = choose_overlay_count(width)
#                     crops = build_overlay_crops(image_np, x1, y1, x2, y2, count)
#                     for i, crop_img in enumerate(crops):
#                         overlay_batch.append((f"{rect_id}_{i}", crop_img))

#                 obj = RectObjectA(
#                     x1, y1, x2, y2, color,
#                     overlay_expected=count, 
#                     overlay_surfaces=[],
#                     rect_id=rect_id
#                 )
#                 updated_rects.append(obj)


#         # 画面外を掃除
#         stored_scroll_rectangles[:] = [
#             r for r in updated_rects
#             if r.rect.bottom >= -MARGIN_KEEP_RECT and r.rect.top <= window_height + MARGIN_KEEP_RECT
#         ]
#         stored_scroll_rectangles[:] = updated_rects

#     # 🔓 ロック外で送信
#     if overlay_batch:
#         threading.Thread(target=send_to_colab, args=(overlay_batch, timing_dict)).start()
