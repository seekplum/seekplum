import sys
from typing import Dict, Tuple

import pygame

from minesweeper import settings
from minesweeper.components.emojibutton import EmojiButton
from minesweeper.components.gamemap import MinesweeperMap
from minesweeper.components.text import TextBoard, TimeTextBoard


def load_images() -> Dict[str, pygame.surface.Surface]:
    # 导入所有图片
    images = {}
    images_path = settings.images_path
    for key in images_path.bmp_keys:
        image = pygame.image.load(images_path[key]).convert()
        images[key] = pygame.transform.smoothscale(
            image, (settings.GRIDSIZE, settings.GRIDSIZE)
        )
    for key in images_path.face_keys:
        image = pygame.image.load(images_path[key])
        images[key] = pygame.transform.smoothscale(
            image, (int(settings.GRIDSIZE * 1.25), int(settings.GRIDSIZE * 1.25))
        )
    return images


def main():
    """主函数"""
    # 游戏初始化
    pygame.init()
    # 设置窗口大小
    screen = pygame.display.set_mode(settings.SCREENSIZE)
    # 设置标题
    pygame.display.set_caption("mine sweeper —— seekplum")

    # 导入并播放背景音乐
    # pygame.mixer.music.load(settings.BGM_PATH)
    # pygame.mixer.music.play(-1)

    # 载入字体
    font = pygame.font.Font(settings.FONT_PATH, settings.FONT_SIZE)

    images = load_images()
    emoji_button = EmojiButton(images)
    fontsize: Tuple[int, int] = font.size(str(settings.NUM_MINES))
    remaining_mine_board = TextBoard(
        str(settings.NUM_MINES),
        font,
        (30, (settings.GRIDSIZE * 2 - fontsize[1]) // 2 - 2),
        settings.RED,
    )
    fontsize: Tuple[int, int] = font.size("000")
    time_board = TimeTextBoard(
        font,
        (
            settings.SCREENSIZE[0] - 30 - fontsize[0],
            (settings.GRIDSIZE * 2 - fontsize[1]) // 2 - 2,
        ),
        settings.RED,
    )

    # 实例化游戏地图
    minesweeper_map = MinesweeperMap(images)
    # 游戏主循环
    clock = pygame.time.Clock()

    while True:
        screen.fill(settings.BACKGROUND_COLOR)
        # 按键检测 pygame.event.Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 退出
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:  # 按下鼠标
                mouse_pos = event.pos
                # macOSX 下获取触摸板点击不是很灵
                mouse_pressed: Tuple[bool, bool, bool] = pygame.mouse.get_pressed()
                if not any(mouse_pressed):
                    # 未识别出按键类型，默认为右键
                    mouse_pressed = (False, False, True)

                minesweeper_map.update(
                    mouse_pressed=mouse_pressed, mouse_pos=mouse_pos, type_="down"
                )
            elif event.type == pygame.MOUSEBUTTONUP:  # 鼠标松开
                minesweeper_map.update(type_="up")
                if emoji_button.rect.collidepoint(pygame.mouse.get_pos()):
                    minesweeper_map = MinesweeperMap(images)
                    time_board.reset()
                    time_board.stop()
                    remaining_mine_board.update(str(settings.NUM_MINES))
                    emoji_button.setstatus(status_code=0)
        # 更新时间显示
        if minesweeper_map.gaming:
            if not time_board.running:
                time_board.start()
                time_board.update_start_time()
            time_board.update(time_board.use_time)
        # 更新剩余雷的数目显示
        remianing_mines = max(settings.NUM_MINES - minesweeper_map.flags, 0)
        remaining_mine_board.update(
            str(remianing_mines).zfill(len(str(settings.NUM_MINES)))
        )
        # 更新表情
        if minesweeper_map.status_code == 1:
            emoji_button.setstatus(status_code=1)
        if (
            minesweeper_map.openeds + minesweeper_map.flags
            == settings.GAME_MATRIX_SIZE[0] * settings.GAME_MATRIX_SIZE[1]
        ):
            minesweeper_map.status_code = 1
            emoji_button.setstatus(status_code=2)
        # 显示当前的游戏状态地图
        minesweeper_map.draw(screen)
        emoji_button.draw(screen)
        remaining_mine_board.draw(screen)
        time_board.draw(screen)
        # 更新屏幕
        pygame.display.update()
        clock.tick(settings.FPS)


if __name__ == "__main__":
    main()
