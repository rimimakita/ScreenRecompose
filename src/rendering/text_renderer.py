def wrap_text_to_two_lines(text, TEXT_FONT, max_width):
    """指定幅に収まるようにテキストを最大2行に分割する。"""
    words = text.split()
    lines = ["", ""]

    for word in words:
        candidate = f"{lines[0]} {word}".strip()

        if TEXT_FONT.size(candidate)[0] <= max_width:
            lines[0] = candidate
            continue

        candidate = f"{lines[1]} {word}".strip()

        if font.size(candidate)[0] <= max_width:
            lines[1] = candidate
        else:
            lines[1] += "..."
            break

    return [line for line in lines if line]

def draw_text_if_possible(screen, rect, surface):
    """overlay画像と重ならない場合のみ、矩形上部にテキストを描画する。"""
    TEXT_FONT = pygame.font.SysFont("Arial", 13, bold=True)
    if not rect.text_line:
        return

    text_x = rect.rect.left + 7
    text_y = rect.rect.top + 5
    max_width = rect.rect.width - 14

    lines = wrap_text_to_two_lines(rect.text_line, TEXT_FONT, max_width)
    text_height = len(lines) * TEXT_FONT.get_height()

    if surface is not None:
        image_top = rect.rect.centery - surface.get_height() // 2
        text_bottom = text_y + text_height

        if text_bottom > image_top:
            return

    for index, line in enumerate(lines):
        text_surface = TEXT_FONT.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (text_x, text_y + index * font.get_height()))
