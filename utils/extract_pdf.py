"""
pip install pymupdf
"""

import os
import time
import re

import fitz


def extract_pic_from_pdf(path: str, pic_path: str) -> None:
    """从pdf中提取图片"""
    base_name = (
        os.path.basename(path).replace("\\", "_").replace("/", "_").replace(":", "_")
    )
    ts_begin = time.time()
    # 使用正则表达式来查找图片
    pattern_xo = re.compile(r"\/Type(?=\s*\/XObject)")
    pattern_img = re.compile(r"\/Subtype(?=\s*\/Image)")

    # 打开pdf
    doc = fitz.open(path)
    # 图片计数
    img_count = 0
    xref_len = doc.xref_length()

    # 打印PDF的信息
    print(f"文件名: {path}, 页数: {len(doc)}, 对象: {xref_len - 1}")
    # 遍历每一个对象
    for i in range(1, xref_len):
        # 定义对象字符串
        text = doc.xref_object(i)
        # 使用正则表达式查看是否是对象
        is_xo = re.search(pattern_xo, text)
        if not is_xo:
            continue
        # 使用正则表达式查看是否是图片
        is_img = re.search(pattern_img, text)
        if not is_img:
            continue
        img_count += 1
        # 根据索引生成图像
        pix = fitz.Pixmap(doc, i)
        # 根据pdf的路径生成图片的名称
        new_name = f"{base_name}_img{img_count}.png"
        new_img_path = os.path.join(pic_path, new_name)
        # 如果pix.n<5,可以直接存为PNG
        if pix.n < 5:
            pix.writePNG(new_img_path)
        # 否则先转换CMYK
        else:
            pix0 = fitz.Pixmap(fitz.csRGB, pix)
            pix0.writePNG(new_img_path)
    ts_used = time.time() - ts_begin
    print(f"运行时间: {ts_used:.3f}s")
    print(f"提取了 {img_count} 张图片")


def main():
    # pdf路径
    path = "/tmp/test1.pdf"
    pic_path = "/tmp/test-pdf"
    # 创建保存图片的文件夹
    if os.path.exists(pic_path):
        print("文件夹已存在，请重新创建新文件夹！")
        return
    os.mkdir(pic_path)
    extract_pic_from_pdf(path, pic_path)


if __name__ == "__main__":
    main()
