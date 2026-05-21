"""メモ：build_chrome_tab_surface関数は役割ごとにもう少し細分化する"""
import random
import pygame

from regions import asset_loader
from regions.rect_object import ChromeTabInfo
from regions.utils import get_adjusted_box


TAB_COUNT = 6
FALLBACK_CHROME_TAB_INFO = (
    90, 0, 660, 35,
    None,
    None,
    "chrome_tab",
)


def create_chrome_tab_info(result):
    """chrome_tab 用のChromeTabInfoを作成する。"""
    if result == None:
        x1, y1, x2, y2 = 90, 0, 660, 35
    else:
        x1, y1, x2, y2 = get_adjusted_box(result)

    rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)

    return ChromeTabInfo(
        rect=rect,
        surface=build_chrome_tab_surface((rect.width, rect.height)),
    )

def build_chrome_tab_surface(size):
    """Chromeタブ風のoverlay用surfaceを生成する。"""

    font = pygame.font.SysFont("Arial", 14)

    surface = pygame.Surface(size, pygame.SRCALPHA)

    width, height = size
    center_y = height // 2

    icon_size = 19
    background_size = 16

    spacing = 4
    right_margin = 2
    left_margin = 2

    bar_color = (80, 80, 80)
    text_color = (200, 200, 200)

    section_width = max(1, (width - 130) // TAB_COUNT)

    selected_words = (
        random.sample(asset_loader.words, TAB_COUNT)
        if len(asset_loader.words) >= TAB_COUNT
        else asset_loader.words[:]
    )

    selected_icons = (
        random.sample(asset_loader.icons, TAB_COUNT)
        if len(asset_loader.icons) >= TAB_COUNT
        else asset_loader.icons[:]
    )

    item_count = min(TAB_COUNT, len(selected_words), len(selected_icons))

    for index in range(item_count):
        section_left = left_margin + index * section_width
        section_right = section_left + section_width

        cursor_x = section_left

        background_y = center_y - background_size // 2

        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (cursor_x, background_y, background_size, background_size),
            border_radius=4,
        )

        icon = pygame.transform.smoothscale(
            selected_icons[index],
            (icon_size, icon_size),
        )

        icon_x = cursor_x + (background_size - icon_size) // 2
        icon_y = center_y - icon_size // 2

        surface.blit(icon, (icon_x, icon_y))

        cursor_x += background_size + spacing

        bar_x = section_right - spacing * 3
        max_text_width = bar_x - cursor_x

        trimmed = selected_words[index]

        while True:
            text_surface = font.render(
                trimmed.capitalize(),
                True,
                text_color,
            )

            if text_surface.get_width() <= max_text_width or len(trimmed) <= 1:
                break

            trimmed = trimmed[:-1]

        text_surface = font.render(
            trimmed.capitalize(),
            True,
            text_color,
        )

        text_y = center_y - text_surface.get_height() // 2

        surface.blit(text_surface, (cursor_x, text_y))

        pygame.draw.line(
            surface,
            bar_color,
            (bar_x, center_y - icon_size // 2),
            (bar_x, center_y + icon_size // 2),
            width=1,
        )

    plus_font = pygame.font.SysFont(
        "Arial",
        int(font.get_height() * 1.3),
    )

    plus_surface = plus_font.render("+", True, text_color)

    plus_x = (
        left_margin
        + item_count * section_width
        + spacing
        + right_margin
    )

    plus_y = center_y - plus_surface.get_height() // 2

    surface.blit(plus_surface, (plus_x, plus_y))

    return surface
