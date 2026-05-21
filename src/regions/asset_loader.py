import os
import pygame
from paths import EOWL_DIR, OPENMOJI_DIR

words = []
icons = []


def load_all_words_from_eowl():
    """EOWL辞書から単語を読み込む。"""

    words = []

    for path in EOWL_DIR.glob("*.txt"):

        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                word = line.strip()

                if word and len(word) > 2:
                    words.append(word)

    return words


def load_all_icons_from_openmoji():
    """OpenMojiのアイコン画像をpygame.Surfaceとして読み込む。"""

    icons = []

    for path in OPENMOJI_DIR.glob("*.png"):

        try:
            icon_surface = pygame.image.load(str(path)).convert_alpha()
            icons.append(icon_surface)

        except Exception as error:
            print(f"[IconLoadError] {path.name}: {error}")

    return icons



def initialize_assets():
    """単語辞書とアイコン画像を初期化する。"""
    global words, icons

    words = load_all_words_from_eowl()
    icons = load_all_icons_from_openmoji()
