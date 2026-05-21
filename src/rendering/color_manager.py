from collections import Counter


DEFAULT_COLOR = (128, 128, 128)

LABEL_COLORS = {}


def extract_background_color(label, image_np, rect):
    """指定領域から最頻出色を取得する。"""

    if image_np is None:
        return DEFAULT_COLOR

    x1, y1, x2, y2 = rect.left, rect.top, rect.right, rect.bottom
    region = image_np[y1:y2, x1:x2]

    if region.size == 0:
        return DEFAULT_COLOR

    pixels = region.reshape(-1, 3)
    color_counts = Counter(map(tuple, pixels))

    most_common = color_counts.most_common(1)

    if not most_common:
        return DEFAULT_COLOR

    color = most_common[0][0]

    LABEL_COLORS[label] = color

    return color
