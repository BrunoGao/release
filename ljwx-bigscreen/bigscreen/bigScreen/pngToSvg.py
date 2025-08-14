from PIL import Image
import svgwrite

# 打开图片并将其转换为灰度
image = Image.open("/Users/bg/Downloads/ljwx_logo.png").convert("L")

# 创建 SVG 文件
dwg = svgwrite.Drawing("output.svg", profile="tiny")
for y in range(image.size[1]):
    for x in range(image.size[0]):
        brightness = image.getpixel((x, y))
        if brightness < 128:  # 仅处理暗色像素
            dwg.add(dwg.rect(insert=(x, y), size=(1, 1), fill="black"))

dwg.save()