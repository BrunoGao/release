"""
测试服务器 - 直接运行，无依赖
"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import random
import datetime

app = FastAPI(title="LJWX BigScreen Test")
templates = Jinja2Templates(directory="templates")

# 生成模拟数据的函数
def generate_mock_statistics():
    return {
        "total_users": random.randint(500, 1000),
        "active_devices": random.randint(400, 800),
        "health_data_count": random.randint(10000, 50000),
        "pending_alerts": random.randint(5, 25),
        "unread_messages": random.randint(0, 15),
        "alert_trend": random.choice(["+5%", "-2%", "+8%", "+0%"]),
        "device_trend": random.choice(["+3%", "-1%", "+12%", "+0%"]),
        "health_trend": random.choice(["+15%", "+8%", "+25%", "+0%"]),
        "message_trend": random.choice(["+2%", "-3%", "+10%", "+0%"])
    }

def generate_mock_alerts(count=10):
    alerts = []
    alert_types = ["心率异常", "血压异常", "血氧异常", "体温异常", "设备离线"]
    alert_levels = ["高", "中", "低"]
    statuses = ["待处理", "处理中", "已处理"]
    names = ["张三", "李四", "王五", "赵六", "钱七"]
    depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
    
    for i in range(count):
        timestamp = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 1440))
        alerts.append({
            "alert_id": f"ALT{random.randint(100000, 999999)}",
            "user_name": random.choice(names),
            "dept_name": random.choice(depts),
            "alert_type": random.choice(alert_types),
            "alert_level": random.choice(alert_levels),
            "alert_status": random.choice(statuses),
            "alert_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "health_id": f"H{random.randint(100000, 999999)}",
            "deviceSn": f"DEV{random.randint(10000, 99999)}"
        })
    return alerts

def generate_mock_health_data(count=30):
    health_data = []
    names = ["张三", "李四", "王五", "赵六", "钱七"]
    depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
    
    for i in range(count):
        timestamp = datetime.datetime.now() - datetime.timedelta(hours=random.randint(1, 48))
        health_data.append({
            "health_id": f"H{random.randint(100000, 999999)}",
            "user_name": random.choice(names),
            "dept_name": random.choice(depts),
            "deviceSn": f"DEV{random.randint(10000, 99999)}",
            "heart_rate": random.randint(60, 100),
            "blood_oxygen": random.randint(95, 99),
            "temperature": round(random.uniform(36.0, 37.5), 1),
            "pressure_high": random.randint(110, 140),
            "pressure_low": random.randint(70, 90),
            "step": random.randint(5000, 15000),
            "distance": round(random.uniform(3.0, 12.0), 1),
            "calorie": round(random.uniform(200, 800), 1),
            "stress": random.randint(20, 80),
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return health_data

# API 路由
@app.get("/api/statistics/overview")
async def get_statistics_overview():
    return generate_mock_statistics()

@app.get("/api/alerts")
async def get_alerts():
    return generate_mock_alerts()

@app.get("/get_health_data_by_orgIdAndUserId")
async def get_health_data():
    return generate_mock_health_data()

@app.get("/api/personal/realtime-health")
async def get_personal_realtime_health():
    return {
        "status": "success",
        "data": {
            "heart_rate": random.randint(65, 90),
            "blood_oxygen": random.randint(96, 99),
            "temperature": round(random.uniform(36.2, 36.8), 1),
            "pressure_high": random.randint(110, 130),
            "pressure_low": random.randint(70, 85),
            "step": random.randint(8000, 12000),
            "distance": round(random.uniform(5.0, 10.0), 1),
            "calorie": round(random.uniform(300, 600), 1),
            "stress": random.randint(30, 70),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@app.get("/api/health/trends/analysis")
async def get_health_trends():
    return {
        "status": "success",
        "data": {
            "heart_rate": {
                "trend": random.choice(["上升", "下降", "稳定"]),
                "change_percentage": random.randint(-10, 15),
                "average": random.randint(70, 85)
            },
            "blood_oxygen": {
                "trend": random.choice(["上升", "下降", "稳定"]),
                "change_percentage": random.randint(-5, 8),
                "average": random.randint(96, 99)
            },
            "activity": {
                "step_trend": random.choice(["上升", "下降", "稳定"]),
                "step_average": random.randint(8000, 12000),
                "calorie_average": random.randint(300, 600)
            }
        }
    }

@app.get("/api/personal/alerts")
async def get_personal_alerts():
    return generate_mock_alerts(3)

@app.get("/get_personal_info")
async def get_personal_info():
    names = ["张三", "李四", "王五", "赵六"]
    depts = ["研发部", "销售部", "市场部", "人事部"]
    return {
        "user_name": random.choice(names),
        "real_name": random.choice(names),
        "dept_name": random.choice(depts),
        "deviceSn": "DEV12345",
        "device_status": random.choice(["在线", "离线"]),
        "phone": f"1{random.randint(3000000000, 8999999999)}",
        "email": "user@company.com"
    }

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("pages/main_optimized.html", {
        "request": request,
        "BIGSCREEN_TITLE": "智能健康数据分析平台",
        "BIGSCREEN_VERSION": "v2.0.0"
    })

@app.get("/main", response_class=HTMLResponse) 
async def main_page(request: Request):
    return templates.TemplateResponse("pages/main_optimized.html", {
        "request": request,
        "BIGSCREEN_TITLE": "智能健康数据分析平台",
        "BIGSCREEN_VERSION": "v2.0.0"
    })

@app.get("/personal", response_class=HTMLResponse)
async def personal_page(request: Request):
    return templates.TemplateResponse("pages/personal_optimized.html", {
        "request": request,
        "BIGSCREEN_TITLE": "个人健康数据监控",
        "BIGSCREEN_VERSION": "v2.0.0"
    })

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run("test_server:app", host="0.0.0.0", port=7777, reload=True)