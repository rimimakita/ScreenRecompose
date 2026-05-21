import pygame

from regions import rect_manager
from rendering.text_renderer import draw_text_if_possible
from rendering.color_manager import LABEL_COLORS, extract_background_color


def draw_chrome_tab(screen, image_np):
    """タブを描画する。"""

    tab = rect_manager.chrome_tab_info

    if tab is None:
        return

    color = LABEL_COLORS.get("chrome_tab")

    if color is None:
        color = extract_background_color(
            "chrome_tab",
            image_np,
            tab.rect
        )

    pygame.draw.rect(screen, color, tab.rect)

    icon_position = (tab.rect.left + 25, tab.rect.top)

    screen.blit(tab.surface, icon_position)

def draw_rectangles(screen, rects, height, image_np):
    """矩形、overlay画像、テキストを描画する。"""

    for rect_obj in rects:
        rect = rect_obj.rect

        if rect.bottom < 0 or rect.top > height:
            continue

        label = rect_obj.label
        color = LABEL_COLORS.get(label)

        if color is None:
            color = extract_background_color(
                label,
                image_np,
                rect
            )

        pygame.draw.rect(screen, color, rect)

        overlay_surface = rect_obj.overlay_surface

        if overlay_surface is not None:
            screen.blit(
                overlay_surface,
                get_surface_position(rect, overlay_surface)
            )

       
            draw_text_if_possible(
                screen,
                rect_obj,
                overlay_surface
            )


def get_surface_position(rect, surface, top_margin=12):
    """矩形内でoverlay画像を中央寄せに配置する座標を返す。"""
    x = rect.centerx - surface.get_width() // 2
    available_height = rect.height - top_margin
    y = rect.top + top_margin + (available_height - surface.get_height()) // 2

    return x, y

