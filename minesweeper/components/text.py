import time
from typing import Tuple, Union

import pygame


class TextBoard(pygame.sprite.Sprite):
    """文字板"""

    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
    ) -> None:
        super(TextBoard, self).__init__()
        self._text = text
        self.font = font
        self.position = position
        self.color = color

    @property
    def text(self) -> str:
        return self._text

    def draw(self, screen: pygame.surface.Surface) -> None:
        text_render = self.font.render(self.text, True, self.color)
        screen.blit(text_render, self.position)

    def update(self, text: str) -> None:
        self._text = text


class TimeTextBoard(TextBoard):
    def __init__(
        self,
        font: pygame.font.Font,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
    ):
        self.font = font
        self.position = position
        self.color = color
        self._text = "0"
        self._running = False
        self._start_time = self.now

    @property
    def text(self) -> str:
        return self._text.zfill(4)

    @property
    def now(self):
        return time.time()

    @property
    def running(self):
        return self._running

    def reset(self):
        self._text = "0"

    def update_start_time(self, start_time: Union[None, int] = None) -> None:
        self._start_time = start_time or self.now

    @property
    def use_time(self) -> str:
        return str(int(self.now - self._start_time)).zfill(4)

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False
