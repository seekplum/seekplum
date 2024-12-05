# from https://medium.com/swlh/enhancing-gray-scale-images-using-numpy-open-cv-9e6234a4d10d
import pathlib
from typing import Literal

import cv2
import numpy as np


def max_filtering(window_size: int, img: np.ndarray) -> np.ndarray:
    wall = np.full((img.shape[0] + (window_size // 2) * 2, img.shape[1] + (window_size // 2) * 2), -1)
    wall[
        (window_size // 2) : wall.shape[0] - (window_size // 2), (window_size // 2) : wall.shape[1] - (window_size // 2)
    ] = img.copy()
    temp = np.full((img.shape[0] + (window_size // 2) * 2, img.shape[1] + (window_size // 2) * 2), -1)
    for y in range(0, wall.shape[0]):
        for x in range(0, wall.shape[1]):
            if wall[y, x] != -1:
                window = wall[
                    y - (window_size // 2) : y + (window_size // 2) + 1,
                    x - (window_size // 2) : x + (window_size // 2) + 1,
                ]
                num = np.amax(window)
                temp[y, x] = num
    return temp[
        (window_size // 2) : wall.shape[0] - (window_size // 2), (window_size // 2) : wall.shape[1] - (window_size // 2)
    ].copy()


def min_filtering(window_size: int, img: np.ndarray) -> np.ndarray:
    wall_min = np.full((img.shape[0] + (window_size // 2) * 2, img.shape[1] + (window_size // 2) * 2), 300)
    wall_min[
        (window_size // 2) : wall_min.shape[0] - (window_size // 2),
        (window_size // 2) : wall_min.shape[1] - (window_size // 2),
    ] = img.copy()
    temp_min = np.full((img.shape[0] + (window_size // 2) * 2, img.shape[1] + (window_size // 2) * 2), 300)
    for y in range(0, wall_min.shape[0]):
        for x in range(0, wall_min.shape[1]):
            if wall_min[y, x] != 300:
                window_min = wall_min[
                    y - (window_size // 2) : y + (window_size // 2) + 1,
                    x - (window_size // 2) : x + (window_size // 2) + 1,
                ]
                num_min = np.amin(window_min)
                temp_min[y, x] = num_min
    return temp_min[
        (window_size // 2) : wall_min.shape[0] - (window_size // 2),
        (window_size // 2) : wall_min.shape[1] - (window_size // 2),
    ].copy()


def background_subtraction(origin_img: np.ndarray, bg_img: np.ndarray) -> np.ndarray:
    tmp_img: np.ndarray = origin_img - bg_img
    return cv2.normalize(  # pylint: disable=no-member
        tmp_img, None, 0, 255, norm_type=cv2.NORM_MINMAX  # pylint: disable=no-member
    )  # type: ignore[call-overload]


def min_max_filtering(img: np.ndarray, mode: Literal[0, 1] = 0, window_size: int = 20) -> np.ndarray:
    if mode == 0:
        # max_filtering
        origin_img = max_filtering(window_size, img)
        # min_filtering
        bg_img = min_filtering(window_size, origin_img)
    else:
        # min_filtering
        origin_img = min_filtering(window_size, img)
        # max_filtering
        bg_img = max_filtering(window_size, origin_img)
    # subtraction
    return background_subtraction(img, bg_img)


def main() -> None:
    filename = "微信图片_20241204212014.jpg"

    image1 = cv2.imread(filename, 0)  # pylint: disable=no-member
    image2 = min_max_filtering(image1)

    tmp_path = pathlib.Path(filename)
    cv2.imwrite(f"{tmp_path.parent.as_posix()}/{tmp_path.name}__{tmp_path.suffix}", image2)  # pylint: disable=no-member


if __name__ == "__main__":
    main()
