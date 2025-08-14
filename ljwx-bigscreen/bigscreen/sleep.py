import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 示例睡眠数据
sleep_data = {
    "code": 0,
    "data": [
        {"type": 1, "endTimeStamp": 1733337840000, "startTimeStamp": 1733330640000},  # 浅睡
        {"type": 2, "endTimeStamp": 1733355840000, "startTimeStamp": 1733337840000}   # 深睡
    ],
    "name": "sleep",
    "type": "history"
}

# 颜色映射
sleep_colors = {1: 'skyblue', 2: 'lightgreen'}
sleep_labels = {1: '浅睡眠', 2: '深睡眠'}

# 处理数据
sleep_intervals = []
for entry in sleep_data["data"]:
    start = datetime.fromtimestamp(entry["startTimeStamp"] / 1000)
    end = datetime.fromtimestamp(entry["endTimeStamp"] / 1000)
    sleep_intervals.append((start, end, entry["type"]))

# 绘制甘特图
fig, ax = plt.subplots(figsize=(10, 4))

# 已添加的标签，用于避免重复添加图例
added_labels = set()

for i, (start, end, sleep_type) in enumerate(sleep_intervals):
    label = sleep_labels[sleep_type] if sleep_labels[sleep_type] not in added_labels else None
    ax.barh(
        y=0, 
        left=start, 
        width=(end - start).total_seconds() / 3600, 
        color=sleep_colors[sleep_type], 
        edgecolor='black', 
        label=label
    )
    added_labels.add(sleep_labels[sleep_type])  # 记录已添加的标签

# 时间格式化
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.set_xlim(min([start for start, _, _ in sleep_intervals]), max([end for _, end, _ in sleep_intervals]))
ax.set_yticks([])
ax.set_xlabel('时间')
ax.set_title('睡眠数据可视化')
ax.legend()

# 显示图表
plt.tight_layout()
plt.show()