"""メモ：label固有の追加情報は meta に入れる。"""
import itertools
from dataclasses import dataclass
import pygame


_rect_id_counter = itertools.count()

def next_rect_id():
    return next(_rect_id_counter)

@dataclass
class ChromeTabInfo:
    rect: pygame.Rect
    surface: pygame.Surface

    
class RectObject:
    """矩形情報とoverlay関連情報を保持する共通オブジェクト。"""

    def __init__(
        self,
        x1,
        y1,
        x2,
        y2,
        label=None,
        rect_id=None,
    ):
        self.rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)

        # self.color = color
        self.label = label

        self.id = rect_id if rect_id is not None else next_rect_id()

        # 状態管理
        self.fix = False

        # overlay関連
        self.overlay_expected = 1
        self.overlay_parts = []
        self.overlay_surface = None

        # 描画用
        self.text_line = None

    def move(self, dy):
        """矩形を縦方向に移動する。"""

        self.rect.move_ip(0, dy)

    def is_overlay_ready(self):
        """overlay画像が必要枚数そろっているかを返す。"""

        return len(self.overlay_parts) == self.overlay_expected
