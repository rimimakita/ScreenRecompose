import random

from regions.rect_object import RectObject
from regions.utils import crop_region_from_image, is_significantly_overlapping
from regions.utils import get_adjusted_box


OVERLAY_WIDTH_THRESHOLD = 330

def create_rect(result, add_overlay_crops):
    """amazon_recommend 用のRectObjectを作成する。"""

    x1, y1, x2, y2 = get_adjusted_box(result)

    new_rect = RectObject(
        x1, y1, x2, y2,
        label="amazon_recommend",
    )

    if new_rect.rect.height > 180:
        add_overlay_crops(new_rect)

    return new_rect

def update_rect(
    updated_rects,
    result,
    window_height,
    add_overlay_crops
):
    """
    raw_rect が既存の recommend 矩形に対応する場合は更新する。
    既存矩形に対応しなければ True を返す。
    """
    x1, y1, x2, y2 = get_adjusted_box(result)
    new_box = (x1, y1, x2, y2)
    new_height = y2 - y1

    for old_rect in updated_rects:
        if old_rect.label != "amazon_recommend":
            continue
        if old_rect.rect.bottom <= 0 or old_rect.rect.top >= window_height:
            old_rect.fix = True
            continue

        old_box = (
            old_rect.rect.left,
            old_rect.rect.top,
            old_rect.rect.right,
            old_rect.rect.bottom,
        )

        if not is_significantly_overlapping(new_box, old_box):
            continue

        if old_rect.fix:
            return False

        old_height = old_rect.rect.height

        merged_x, merged_y, merged_w, merged_h = calc_recommend_merged_box(
            new_box,
            old_box
        )

        old_rect.rect.update(merged_x, merged_y, merged_w, merged_h)

        needs_overlay = (
            old_height <= 180
            and new_height > 180
            and not old_rect.overlay_surface
        )

        if needs_overlay:
            add_overlay_crops(old_rect)

        return False

    return True


def build_crops(image_np, rect_obj):
    """amazon_recommend 用の overlay crop を生成する。"""
    rect = rect_obj.rect

    x1 = rect.left
    y1 = rect.top
    x2 = rect.right
    y2 = rect.bottom


    width = x2 - x1
    height = y2 - y1

    # 横長 → 横4分割
    if width >= OVERLAY_WIDTH_THRESHOLD:
        step = width // 4
        crops = []

        for index in range(4):
            crop_x1 = x1 + step * index
            crop_x2 = x2 if index == 3 else x1 + step * (index + 1)

            crops.append(
                crop_region_from_image(image_np, crop_x1, y1, crop_x2, y2)
            )
        rect_obj.overlay_expected = 4
        return crops

    # それ以外 → ランダムで1枚
    if random.random() < 0.2:
        crop = [
            crop_region_from_image(image_np, x1, y1, x2, y2)
        ]
        rect_obj.overlay_expected = 1
        return crop
    

    # それ以外 → 2x2で4分割
    mid_x = x1 + width // 2
    mid_y = y1 + height // 2

    split_boxes = [
        (x1, mid_y, mid_x, y2),
        (mid_x, mid_y, x2, y2),
        (x1, y1, mid_x, mid_y),
        (mid_x, y1, x2, mid_y),
    ]

    crops = []

    for crop_x1, crop_y1, crop_x2, crop_y2 in split_boxes:
        crops.append(
            crop_region_from_image(
                image_np,
                crop_x1,
                crop_y1,
                crop_x2,
                crop_y2,
            )
        )
    rect_obj.overlay_expected = 4

    return crops


def calc_recommend_merged_box(new_box, old_box):
    """過剰な拡大を防ぎながらamazon_recommend矩形を結合する。"""

    old_x1, old_y1, old_x2, old_y2 = old_box
    x1, y1, x2, y2 = new_box

    old_width = old_x2 - old_x1
    old_height = old_y2 - old_y1

    new_width = x2 - x1
    new_height = y2 - y1

    widen_ratio_limit = 1.2

    max_width = 230 if new_width < 270 and old_width < 270 else 720

    if (
        new_width > old_width
        and new_width <= old_width * widen_ratio_limit
    ):
        base_x1, base_x2 = x1, x2

    else:
        base_x1, base_x2 = old_x1, old_x2

    base_width = base_x2 - base_x1

    if base_width > max_width:
        center_x = (base_x1 + base_x2) / 2
        half_width = max_width / 2

        base_x1 = int(round(center_x - half_width))
        base_x2 = base_x1 + max_width

    max_height = 300

    if new_height > old_height:
        base_y1, base_y2 = y1, y2

    else:
        base_y1, base_y2 = old_y1, old_y2

    base_height = base_y2 - base_y1

    if base_height > max_height:
        center_y = (base_y1 + base_y2) / 2
        half_height = max_height / 2

        base_y1 = int(round(center_y - half_height))
        base_y2 = base_y1 + max_height

    return (
        base_x1,
        base_y1,
        base_x2 - base_x1,
        base_y2 - base_y1,
    )

