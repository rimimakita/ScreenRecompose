import cv2
import pygame

from regions.rect_manager import (
    overlay_lock,
    stored_scroll_rectangles
)
from generation.amazon_recommend_overlay import get_overlay_width, build_overlay_surface

def safe_set_overlay_surface(target_id, overlay_np, caption_text):
    """受信した生成画像を矩形に対応づけ、そろったら完成済みSurfaceを保存する。"""

    with overlay_lock:
        for rect in stored_scroll_rectangles:
            if rect.id != target_id:
                continue

            expected_count = getattr(rect, "overlay_expected", 1)

            target_width = get_overlay_width(rect)
            surface = create_surface(overlay_np, target_width)

            rect.overlay_parts.append(surface)

            if len(rect.overlay_parts) == expected_count:
                rect.text_line = sanitize_caption(caption_text)
                rect.overlay_surface = build_overlay_surface(
                    rect.rect,
                    rect.overlay_parts,
                )
                rect.overlay_parts.clear()

            return

    print(f"[OverlaySet] DROP: rect id={target_id} not found")



def create_surface(overlay_np, target_width):
    """生成画像を指定サイズにリサイズし、Pygame Surfaceに変換する。"""

    resized = cv2.resize(
        overlay_np,
        (target_width, target_width),
        interpolation=cv2.INTER_NEAREST,
    )

    overlay_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    surface = pygame.image.frombuffer(
        overlay_rgb.tobytes(),
        (overlay_rgb.shape[1], overlay_rgb.shape[0]),
        "RGB",
    ).convert_alpha()

    return surface

def sanitize_caption(text: str) -> str:
    """caption文字列を安全な表示可能ASCII文字列に正規化する。"""

    if not text:
        return ""

    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")

    sanitized = []
    for char in text:
        code = ord(char)

        if 32 <= code <= 126:
            sanitized.append(char)
        else:
            sanitized.append("?")

    return "".join(sanitized).strip()
