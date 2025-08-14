import pandas as pd


import sys
import os

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修改导入
from bigScreen.models import WorkerHealthBaseline, WorkerHealthAnomaly, UserHealthData

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# Define your database URL
DATABASE_URL = "mysql+pymysql://root:aV5mV7kQ%21%40%23@localhost:3306/panis_boot"

# Create an engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()

# Define your model (assuming it matches the Django model)
Base = declarative_base()


# Query using SQLAlchemy
data = pd.DataFrame(session.query(
    UserHealthData.device_sn,
    UserHealthData.timestamp,
    UserHealthData.heart_rate,
    UserHealthData.pressure_high,
    UserHealthData.pressure_low,
    UserHealthData.blood_oxygen,
    UserHealthData.temperature
).filter(
    UserHealthData.timestamp.between("2024-12-01", "2025-01-05"),
    UserHealthData.device_sn.between("CRFTQ23409001893", "CRFTQ23409001899")
).all(), columns=[
    "device_sn", "timestamp", "heart_rate", "pressure_high", "pressure_low", "blood_oxygen", "temperature"
])

print(data.size)

# 添加时间段标签
def assign_time_period(row):
    hour = row.hour
    if 6 <= hour < 9:
        return "morning"
    elif 9 <= hour < 12:
        return "forenoon"
    elif 12 <= hour < 14:
        return "noon"
    elif 14 <= hour < 18:
        return "afternoon"
    else:
        return "night"

data["time_period"] = data["timestamp"].apply(lambda x: assign_time_period(x))

# 计算每个时间段的基线
baselines = []
for (device_sn, period), group in data.groupby(["device_sn", "time_period"]):
    for feature in ["heart_rate", "pressure_high", "pressure_low", "blood_oxygen", "temperature"]:
        group[feature] = group[feature].astype(float)
        mean_value = group[feature].mean()
        std_value = group[feature].std()
        min_value = group[feature].min()
        max_value = group[feature].max()
        baselines.append({
            "device_sn": device_sn,
            "time_period": period,
            "feature_name": feature,
            "mean_value": round(mean_value, 2),
            "std_value": round(std_value, 2),
            "min_value": round(min_value, 2),
            "max_value": round(max_value, 2)
        })

# 保存基线数据
baseline_df = pd.DataFrame(baselines)
baseline_df.to_csv("worker_health_baseline.csv", index=False)
print(baseline_df)


# Save baseline data to the database using SQLAlchemy
for _, row in baseline_df.iterrows():
    baseline_record = WorkerHealthBaseline(
        device_sn=row["device_sn"],
        time_period=row["time_period"],
        feature_name=row["feature_name"],
        mean_value=row["mean_value"],
        std_value=row["std_value"],
        min_value=row["min_value"],
        max_value=row["max_value"]
    )
    session.add(baseline_record)
session.commit()

# 加载基线数据
#aseline_df = pd.read_csv("worker_health_baseline.csv")

# 模拟上传数据
uploaded_data = pd.DataFrame({
    "device_sn": ["device_sn"] * 5,
    "timestamp": pd.date_range("2024-12-01 08:00", periods=5, freq="h"),
    "heart_rate": [65, 110, 130, 90, 80],
    "pressure_high": [130, 140, 150, 135, 120],
    "gas_concentration": [0.8, 1.2, 0.9, 0.7, 0.5]
})

# 添加时间段标签
uploaded_data["time_period"] = uploaded_data["timestamp"].apply(lambda x: assign_time_period(x))

# 检测异常
anomalies = []
for _, row in uploaded_data.iterrows():
    for feature in ["heart_rate", "pressure_high", "gas_concentration"]:
        period = row["time_period"]
        value = row[feature]
        device_sn = row["device_sn"]
        baseline = baseline_df[(baseline_df["device_sn"] == device_sn) &
                               (baseline_df["time_period"] == period) &
                               (baseline_df["feature_name"] == feature)]
        if not baseline.empty:
            mean = baseline["mean_value"].values[0]
            std = baseline["std_value"].values[0]
            if value < mean - 2 * std or value > mean + 2 * std:
                anomaly_type = "low" if value < mean - 2 * std else "high"
                anomalies.append({
                    "device_sn": device_sn,
                    "timestamp": row["timestamp"],
                    "feature_name": feature,
                    "value": value,
                    "anomaly_type": anomaly_type
                })

# 输出异常数据
anomalies_df = pd.DataFrame(anomalies)
anomalies_df.to_csv("worker_health_anomalies.csv", index=False)
print(anomalies_df)

# Save anomaly data to the database using SQLAlchemy
for anomaly in anomalies:
    anomaly_record = WorkerHealthAnomaly(
        device_sn=anomaly["device_sn"],
        timestamp=anomaly["timestamp"],
        feature_name=anomaly["feature_name"],
        value=anomaly["value"],
        anomaly_type=anomaly["anomaly_type"]
    )
    session.add(anomaly_record)
session.commit()