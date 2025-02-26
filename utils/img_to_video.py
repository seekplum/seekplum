import cv2
import os


# 图片文件夹路径
image_folder = '/tmp/'
# 输出视频路径
video_name = '/tmp/3.mp4'

# 获取图片列表
images = ["1.png", "2.png"]

# 读取第一张图片，获取尺寸
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape

# 创建视频写入对象
video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 1, (width, height))

# 将图片写入视频
for image in images:
    video.write(cv2.imread(os.path.join(image_folder, image)))

# 释放资源
video.release()
print(f"视频已生成: {video_name}")
