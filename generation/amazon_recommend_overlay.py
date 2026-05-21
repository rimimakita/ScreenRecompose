import pygame
from regions.amazon_recommend_rule import OVERLAY_WIDTH_THRESHOLD

def get_overlay_width(rect):
    """amazon_recommend 用のoverlay画像幅を決める。"""

    expected_count = getattr(rect, "overlay_expected", 1)

    if expected_count == 1:
        return int(rect.rect.width * 0.86)

    if rect.rect.width > OVERLAY_WIDTH_THRESHOLD:
        return int(rect.rect.width * 0.23)

    return int(rect.rect.width * 0.44)


def build_grid_surface(surfaces, gap=3):
    """4枚のSurfaceを2×2に並べて合成する。"""
    top_left, top_right, bottom_left, bottom_right = surfaces

    column_width = max(top_left.get_width(), bottom_left.get_width())
    row_height = max(top_left.get_height(), top_right.get_height())

    total_width = column_width * 2 + gap
    total_height = row_height * 2 + gap

    composite = pygame.Surface((total_width, total_height), pygame.SRCALPHA)

    composite.blit(top_left, (0, 0))
    composite.blit(top_right, (column_width + gap, 0))
    composite.blit(bottom_left, (0, row_height + gap))
    composite.blit(bottom_right, (column_width + gap, row_height + gap))

    return composite


def build_horizontal_surface(surfaces, spacing=0):
    """複数のSurfaceを横並びに合成する。"""
    total_width = sum(surface.get_width() for surface in surfaces) + spacing * (len(surfaces) - 1)
    max_height = max(surface.get_height() for surface in surfaces)

    composite = pygame.Surface((total_width, max_height), pygame.SRCALPHA)

    x = spacing
    for surface in surfaces:
        y = max_height // 2 - surface.get_height() // 2
        composite.blit(surface, (x, y))
        x += surface.get_width() + spacing

    return composite


def build_overlay_surface(rect, surfaces):
    """複数のoverlay画像を1枚のSurfaceに合成する。"""
    surface_count = len(surfaces)

    if surface_count == 1:
        return surfaces[0]

    if surface_count == 4 and rect.width <= OVERLAY_WIDTH_THRESHOLD:
        return build_grid_surface(surfaces)

    return build_horizontal_surface(surfaces)
