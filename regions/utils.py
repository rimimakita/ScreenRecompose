
def crop_region_from_image(image_np, x1, y1, x2, y2):
    """画像から指定領域を安全に切り出す。"""

    height, width = image_np.shape[:2]

    x1 = max(0, min(width, x1))
    x2 = max(0, min(width, x2))

    y1 = max(0, min(height, y1))
    y2 = max(0, min(height, y2))

    return image_np[y1:y2, x1:x2]


def is_significantly_overlapping(box1, box2, threshold=0.1):
    """2つの矩形が一定以上重なっている場合にTrueを返す。"""

    x1, y1, x2, y2 = box1
    x1b, y1b, x2b, y2b = box2

    overlap_x1 = max(x1, x1b)
    overlap_y1 = max(y1, y1b)
    overlap_x2 = min(x2, x2b)
    overlap_y2 = min(y2, y2b)

    if overlap_x2 <= overlap_x1 or overlap_y2 <= overlap_y1:
        return False

    overlap_area = (
        (overlap_x2 - overlap_x1)
        * (overlap_y2 - overlap_y1)
    )

    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x2b - x1b) * (y2b - y1b)

    base_area = min(area1, area2)

    if base_area <= 0:
        return False

    return (overlap_area / base_area) >= threshold


def get_adjusted_box(result):
    """YOLO検出結果から余白込み座標を取得する。"""

    x1, y1, x2, y2 = map(int, result[:4])

    return (
        x1,
        y1,
        x2,
        y2
    )


# def get_adjusted_box(result, padding=5):
#     """YOLO検出結果から余白込み座標を取得する。"""

#     x1, y1, x2, y2 = map(int, result[:4])

#     return (
#         x1 - padding,
#         y1 - padding,
#         x2 + padding,
#         y2 + padding
#     )
