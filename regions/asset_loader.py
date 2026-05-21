import os
import pygame

words = []
icons = []

def load_all_words_from_eowl():
    """EOWL辞書から単語を読み込む。"""

    words = []
    base_dir = "data/EOWL-v1.1.2/LF Delimited Format"

    for filename in os.listdir(base_dir):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(base_dir, filename)

        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                word = line.strip()

                if word and len(word) > 2:
                    words.append(word)

    return words


def load_all_icons_from_openmoji():
    """OpenMojiのアイコン画像をpygame.Surfaceとして読み込む。"""

    icons = []

    for filename in os.listdir("data/openmoji-72x72-color"):
        if not filename.endswith(".png"):
            continue

        path = os.path.join("data/openmoji-72x72-color", filename)

        try:
            icon_surface = pygame.image.load(path).convert_alpha()
            icons.append(icon_surface)

        except Exception as error:
            print(f"[IconLoadError] {filename}: {error}")

    return icons


def initialize_assets():
    """単語辞書とアイコン画像を初期化する。"""
    global words, icons

    words = load_all_words_from_eowl()
    icons = load_all_icons_from_openmoji()
