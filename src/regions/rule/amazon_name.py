from regions.rect_object import RectObject
from regions.utils import get_adjusted_box

def normalize_amazon_text_rect(x1, y1, x2, y2):
        """amazon_name / amazon_address 用の矩形サイズを最低サイズに補正する。"""

        min_height = 35
        min_width = 140

        height = y2 - y1
        if height < min_height:
            diff = min_height - height
            half = diff // 2
            y1 -= half
            y2 += diff - half

        width = x2 - x1
        if width < min_width:
            x2 = x1 + min_width

        return x1, y1, x2, y2


def update_rect(
    updated_rects,
    result,
    window_height=None,
    add_overlay_crops=None
):
    """
    amazon_name 用の矩形を追加できるか判定する。
    既存のamazon_name矩形と横方向に重複する場合は、
    上側の矩形の座標に更新してFalseを返す。
    重複しない場合はTrueを返す。
    """

    x1, y1, x2, y2 = get_adjusted_box(result)

    for old_rect in updated_rects:
        if old_rect.label != "amazon_name":
            continue

        is_overlapping_x = not (
            x2 <= old_rect.rect.left or old_rect.rect.right <= x1
        )

        if not is_overlapping_x:
            continue

        if y1 < old_rect.rect.top:
            old_rect.rect.top = y1
            old_rect.rect.bottom = y2

        return False

    return True

def create_rect(result, add_overlay_crops=None):
    """amazon_name / amazon_address 用のRectObjectを作成する。"""

    x1, y1, x2, y2 = get_adjusted_box(result)

    x1, y1, x2, y2 = normalize_amazon_text_rect(
        x1, y1, x2, y2
    )

    return RectObject(
        x1, y1, x2, y2,
        label="amazon_name",
    )
