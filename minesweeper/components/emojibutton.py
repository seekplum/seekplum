from typing import Tuple

import pygame

from minesweeper import settings


class EmojiButton(pygame.sprite.Sprite):
    def __init__(self, images: dict, status_code: int = 0):
        super(EmojiButton, self).__init__()
        # 导入图片
        self.images: dict = images
        self.image: pygame.surface.Surface = self.images["face_normal"]
        self.rect: pygame.rect.Rect = self.image.get_rect()
        self.rect.left, self.rect.top = self.position()
        # 表情按钮的当前状态
        self.status_code = status_code

    def position(self) -> Tuple[int, int]:
        return (settings.SCREENSIZE[0] - int(settings.GRIDSIZE * 1.25)) // 2, (
            settings.GRIDSIZE * 2 - int(settings.GRIDSIZE * 1.25)
        ) // 2

    def draw(self, screen: pygame.surface.Surface):
        """画到屏幕上"""
        # 状态码为0, 代表正常的表情
        if self.status_code == 0:
            self.image: pygame.surface.Surface = self.images["face_normal"]
        # 状态码为1, 代表失败的表情
        elif self.status_code == 1:
            self.image: pygame.surface.Surface = self.images["face_fail"]
        # 状态码为2, 代表成功的表情
        elif self.status_code == 2:
            self.image: pygame.surface.Surface = self.images["face_success"]
        # 绑定图片到屏幕
        screen.blit(self.image, self.rect)

    def setstatus(self, status_code: int):
        """设置当前的按钮的状态"""
        self.status_code = status_code
