import random
from typing import List, Tuple

import pygame

from minesweeper import settings
from minesweeper.components.mine import Mine


class MinesweeperMap:
    """扫雷地图"""

    def __init__(self, images: dict) -> None:
        # 雷型矩阵
        self.mines_matrix: List[Mine] = []
        for j in range(settings.GAME_MATRIX_SIZE[1]):
            mines_line = []
            for i in range(settings.GAME_MATRIX_SIZE[0]):
                position = (
                    i * settings.GRIDSIZE + settings.BORDERSIZE,
                    (j + 2) * settings.GRIDSIZE,
                )
                mines_line.append(Mine(images=images, position=position))
            self.mines_matrix.append(mines_line)
        # 游戏当前的状态
        self.status_code = -1
        # 记录鼠标按下时的位置和按的键
        self.mouse_pos = None
        self.mouse_pressed = None
        self.is_first_left_click = False

    def random_mine(self):
        # 随机埋雷
        for i in random.sample(
            range(settings.GAME_MATRIX_SIZE[0] * settings.GAME_MATRIX_SIZE[1]),
            settings.NUM_MINES,
        ):
            self.mines_matrix[i // settings.GAME_MATRIX_SIZE[0]][
                i % settings.GAME_MATRIX_SIZE[0]
            ].burymine()

    def draw(self, screen: pygame.surface.Surface) -> None:
        """画出当前的游戏状态图"""
        for row in self.mines_matrix:
            for item in row:
                item.draw(screen)

    def setstatus(self, status_code: int) -> None:
        """设置当前的游戏状态"""
        # 0: 正在进行游戏, 1: 游戏结束, -1: 游戏还没开始
        self.status_code = status_code

    def update(
        self,
        mouse_pressed: List[int] = None,
        mouse_pos: List[int] = None,
        type_: str = "down",
    ) -> None:
        """根据玩家的鼠标操作情况更新当前的游戏状态地图"""
        assert type_ in ["down", "up"]
        # 记录鼠标按下时的位置和按的键
        if type_ == "down" and mouse_pos is not None and mouse_pressed is not None:
            self.mouse_pos = mouse_pos
            self.mouse_pressed = mouse_pressed
        # 鼠标点击的范围不在游戏地图内, 无响应
        if (
            self.mouse_pos[0] < settings.BORDERSIZE
            or self.mouse_pos[0] > settings.SCREENSIZE[0] - settings.BORDERSIZE
            or self.mouse_pos[1] < settings.GRIDSIZE * 2
            or self.mouse_pos[1] > settings.SCREENSIZE[1] - settings.BORDERSIZE
        ):
            return
        # 鼠标点击在游戏地图内, 代表开始游戏(即可以开始计时了)
        if self.status_code == -1:
            self.status_code = 0
        # 如果不是正在游戏中, 按鼠标是没有用的
        if self.status_code != 0:
            return
        # 鼠标位置转矩阵索引
        coord_x = (self.mouse_pos[0] - settings.BORDERSIZE) // settings.GRIDSIZE
        coord_y = self.mouse_pos[1] // settings.GRIDSIZE - 2
        mine_clicked = self.mines_matrix[coord_y][coord_x]
        # 鼠标按下
        if type_ == "down":
            # 鼠标左右键同时按下
            if self.mouse_pressed[0] and self.mouse_pressed[2]:
                if mine_clicked.opened and mine_clicked.num_mines_around > 0:
                    mine_clicked.setstatus(status_code=4)
                    num_flags = 0
                    coords_around = self.getaround(coord_y, coord_x)
                    for (j, i) in coords_around:
                        if self.mines_matrix[j][i].status_code == 2:
                            num_flags += 1
                    if num_flags == mine_clicked.num_mines_around:
                        for (j, i) in coords_around:
                            if self.mines_matrix[j][i].status_code == 0:
                                self.openmine(i, j)
                    else:
                        for (j, i) in coords_around:
                            if self.mines_matrix[j][i].status_code == 0:
                                self.mines_matrix[j][i].setstatus(status_code=5)
        # 鼠标释放
        else:
            # 鼠标左键
            if self.mouse_pressed[0] and not self.mouse_pressed[2]:
                if not self.is_first_left_click:
                    self.random_mine()
                    self.is_first_left_click = True
                if not (mine_clicked.status_code == 2 or mine_clicked.status_code == 3):
                    if self.openmine(coord_x, coord_y):
                        self.setstatus(status_code=1)
            # 鼠标右键
            elif self.mouse_pressed[2] and not self.mouse_pressed[0]:
                if mine_clicked.status_code == 0:
                    mine_clicked.setstatus(status_code=2)
                elif mine_clicked.status_code == 2:
                    mine_clicked.setstatus(status_code=3)
                elif mine_clicked.status_code == 3:
                    mine_clicked.setstatus(status_code=0)
            # 鼠标左右键同时按下
            elif self.mouse_pressed[0] and self.mouse_pressed[2]:
                mine_clicked.setstatus(status_code=1)
                coords_around = self.getaround(coord_y, coord_x)
                for (j, i) in coords_around:
                    if self.mines_matrix[j][i].status_code == 5:
                        self.mines_matrix[j][i].setstatus(status_code=0)

    def openmine(self, x: int, y: int) -> bool:
        """打开雷"""
        mine_clicked = self.mines_matrix[y][x]
        if mine_clicked.is_mine_flag:
            for row in self.mines_matrix:
                for item in row:
                    if not item.is_mine_flag and item.status_code == 2:
                        item.setstatus(status_code=7)
                    elif item.is_mine_flag and item.status_code == 0:
                        item.setstatus(status_code=1)
            mine_clicked.setstatus(status_code=6)
            return True
        mine_clicked.setstatus(status_code=1)
        coords_around = self.getaround(y, x)
        num_mines = 0
        for (j, i) in coords_around:
            num_mines += int(self.mines_matrix[j][i].is_mine_flag)
        mine_clicked.setnumminesaround(num_mines)
        if num_mines == 0:
            for (j, i) in coords_around:
                if self.mines_matrix[j][i].num_mines_around == -1:
                    self.openmine(i, j)
        return False

    def getaround(self, row: int, col: int) -> List[Tuple[int, int]]:
        """获得坐标点的周围坐标点"""
        coords = []
        for j in range(
            max(0, row - 1), min(row + 1, settings.GAME_MATRIX_SIZE[1] - 1) + 1
        ):
            for i in range(
                max(0, col - 1), min(col + 1, settings.GAME_MATRIX_SIZE[0] - 1) + 1
            ):
                if j == row and i == col:
                    continue
                coords.append((j, i))
        return coords

    @property
    def gaming(self) -> bool:
        """是否正在游戏中"""
        return self.status_code == 0

    @property
    def flags(self) -> int:
        """被标记为雷的雷数目"""
        num_flags = 0
        for row in self.mines_matrix:
            for item in row:
                num_flags += int(item.status_code == 2)
        return num_flags

    @property
    def openeds(self) -> int:
        """已经打开的雷的数目"""
        num_openeds = 0
        for row in self.mines_matrix:
            for item in row:
                num_openeds += int(item.opened)
        return num_openeds
