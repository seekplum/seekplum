import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# 图片素材路径
class ImagesPath:
    def __init__(self):
        self.bmp_keys = list(map(str, range(9))) + [
            "ask",
            "blank",
            "blood",
            "error",
            "flag",
            "mine",
        ]
        self.face_keys = ["face_normal", "face_fail", "face_success"]

    def __getitem__(self, name):
        if name in self.bmp_keys:
            return os.path.join(ROOT, "resources/images", f"{name}.bmp")
        if name in self.face_keys:
            return os.path.join(ROOT, "resources/images", f"{name}.png")
        raise KeyError(name)

    def keys(self):
        return self.bmp_keys + self.face_keys

    def __iter__(self):
        for name in self.bmp_keys + self.face_keys:
            yield name, self[name]

    items = __iter__

    def __getattr__(self, name):
        return self[name]


images_path = ImagesPath()


# 字体路径
FONT_PATH = os.path.join(ROOT, "resources/font/font.TTF")
FONT_SIZE = 40

# BGM路径
BGM_PATH = os.path.join(ROOT, "resources/music/bgm.mp3")

# 游戏相关参数
FPS = 60
GRIDSIZE = 20
NUM_MINES = 99
GAME_MATRIX_SIZE = (30, 16)
BORDERSIZE = 5
SCREENSIZE = (
    GAME_MATRIX_SIZE[0] * GRIDSIZE + BORDERSIZE * 2,
    (GAME_MATRIX_SIZE[1] + 2) * GRIDSIZE + BORDERSIZE,
)

# 颜色
BACKGROUND_COLOR = (225, 225, 225)
RED = (200, 0, 0)
