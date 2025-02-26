import io
from typing import BinaryIO, Optional, Tuple

from PIL import Image


class ImageProcessor:
    def __init__(self, binary_io: BinaryIO, fmt: Optional[str] = None) -> None:
        self.im = Image.open(binary_io)
        self.format = fmt or self.im.format  # without dot
        self.quality = 100

    def resize(self, width: int, height: int) -> None:
        size = (width, height)
        self.im = self.im.resize(size, resample=Image.Resampling.LANCZOS)

    def resize_if_larger(self, max_size: Tuple[int, int]) -> None:
        max_width, max_height = max_size
        width, height = self.im.size
        if width < max_width and height < max_height:
            # 不超过则不缩放
            return
        # 等比例缩放
        ratio = width / height  # 宽高比
        if width > max_width:
            width = max_width
            height = int(max_width / ratio)
        if height > max_height:
            height = max_height
            width = int(max_height * ratio)
        self.resize(width, height)

    def is_square(self) -> bool:
        width, height = self.im.size
        return width == height

    def _get_background(self, width: int, height: int) -> Image.Image:
        if self.format and self.format.startswith("PNG"):
            background = Image.new("RGBA", size=(width, height), color=(0, 0, 0, 0))  # 透明
        else:
            background = Image.new("RGB", size=(width, height), color=(255, 255, 255))  # 白色
        return background

    def square(self) -> None:
        width, height = self.im.size
        if self.is_square():
            return

        max_val = max(width, height)
        background = self._get_background(max_val, max_val)
        if width == max_val:
            point = (max_val - height) // 2
            box = (0, point)
        else:
            point = (max_val - width) // 2
            box = (point, 0)
        background.paste(self.im, box)
        self.im = background

    def resize_by_aspect_ratio(self, aspect_ratio: Tuple[int, int]) -> None:
        target_width, target_height = aspect_ratio

        cur_width, cur_height = self.im.size
        cur_aspect_ratio = cur_width / cur_height

        if cur_aspect_ratio > target_width / target_height:
            new_height = int(cur_width / target_width * target_height)
            padding_height = (new_height - cur_height) // 2
            background = self._get_background(cur_width, new_height)
            background.paste(self.im, (0, padding_height))
        else:
            new_width = int(cur_height / target_height * target_width)
            padding_width = (new_width - cur_width) // 2
            background = self._get_background(new_width, cur_height)
            background.paste(self.im, (padding_width, 0))

        self.im = background

    def mirror(self) -> None:
        self.im = self.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    def compress(self, target_size: int, step: int = 2) -> None:
        quality = 100
        img_bytes = io.BytesIO()
        if self.format == "PNG":
            self.im.save(img_bytes, format="PNG", optimize=True)
            if img_bytes.tell() < target_size:
                # 如果png本身就小于目标大小，则不压缩
                return
            # 将png的RGBA四通道转换为RGB三通道，否则无法保存成jpg
            self.im = self.im.convert("RGB")
            self.format = "JPEG"
        else:
            self.im.save(img_bytes, format=self.format, quality=100)

        while img_bytes.tell() >= target_size:
            quality -= step
            if quality <= 0:
                break
            img_bytes = io.BytesIO()
            self.im.save(img_bytes, format="JPEG", quality=quality)  # 使用JPEG格式压缩

        self.quality = quality
        # self.im = Image.open(img_bytes)

    def get_bytes(self) -> bytes:
        img_bytes = io.BytesIO()
        fmt = self.format
        if fmt and fmt.lower() == "gif":
            fmt = "PNG"
        self.im.save(img_bytes, format=fmt, quality=self.quality)
        return img_bytes.getvalue()


if __name__ == "__main__":
    with open("/tmp/test.png", "rb") as fp:
        file_binaryio = io.BytesIO(fp.read())
    processor = ImageProcessor(file_binaryio)
    processor.resize(1024, 1024)
    processor.im.save("/tmp/test1.png")
