"""
模拟数据服务 - 为API提供测试数据
"""
import random
from datetime import datetime, timedelta
from typing import List
from ..schemas.bigscreen import (
    HealthScoreResponse, StatisticsOverviewResponse, AlertInfoResponse,
    DeviceInfoResponse, MessageInfoResponse, HealthDataResponse, 
    UserInfoResponse, HealthBaselineResponse, HealthRecommendationResponse
)

class MockDataService:
    """模拟数据生成服务"""
    
    @staticmethod
    def generate_health_score() -> HealthScoreResponse:
        """生成模拟健康评分"""
        return HealthScoreResponse(
            overall_score=random.randint(75, 95),
            heart_rate_score=random.randint(80, 95),
            blood_oxygen_score=random.randint(85, 98),
            temperature_score=random.randint(85, 95),
            pressure_score=random.randint(75, 90),
            step_score=random.randint(70, 90),
            calorie_score=random.randint(75, 85),
            stress_score=random.randint(70, 85),
            sleep_score=random.randint(75, 90)
        )
    
    @staticmethod
    def generate_statistics_overview() -> StatisticsOverviewResponse:
        """生成模拟统计概览"""
        return StatisticsOverviewResponse(
            total_users=random.randint(500, 1000),
            active_devices=random.randint(400, 800),
            health_data_count=random.randint(10000, 50000),
            pending_alerts=random.randint(5, 25),
            unread_messages=random.randint(0, 15),
            alert_trend=random.choice(["+5%", "-2%", "+8%", "+0%"]),
            device_trend=random.choice(["+3%", "-1%", "+12%", "+0%"]),
            health_trend=random.choice(["+15%", "+8%", "+25%", "+0%"]),
            message_trend=random.choice(["+2%", "-3%", "+10%", "+0%"])
        )
    
    @staticmethod
    def generate_alerts(count: int = 10) -> List[AlertInfoResponse]:
        """生成模拟告警列表"""
        alerts = []
        alert_types = ["心率异常", "血压异常", "血氧异常", "体温异常", "设备离线"]
        alert_levels = ["高", "中", "低"]
        statuses = ["待处理", "处理中", "已处理"]
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
        depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
        
        for i in range(count):
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))
            alerts.append(AlertInfoResponse(
                alert_id=f"ALT{random.randint(100000, 999999)}",
                user_name=random.choice(names),
                dept_name=random.choice(depts),
                alert_type=random.choice(alert_types),
                alert_level=random.choice(alert_levels),
                alert_status=random.choice(statuses),
                alert_timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                health_id=f"H{random.randint(100000, 999999)}",
                deviceSn=f"DEV{random.randint(10000, 99999)}"
            ))
        return alerts
    
    @staticmethod
    def generate_devices(count: int = 20) -> List[DeviceInfoResponse]:
        """生成模拟设备列表"""
        devices = []
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
        depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
        statuses = ["在线", "离线", "异常"]
        
        for i in range(count):
            last_seen = datetime.now() - timedelta(minutes=random.randint(1, 60))
            devices.append(DeviceInfoResponse(
                deviceSn=f"DEV{random.randint(10000, 99999)}",
                user_name=random.choice(names),
                dept_name=random.choice(depts),
                device_status=random.choice(statuses),
                last_seen=last_seen.strftime("%Y-%m-%d %H:%M:%S"),
                battery_level=random.randint(20, 100)
            ))
        return devices
    
    @staticmethod
    def generate_messages(count: int = 15) -> List[MessageInfoResponse]:
        """生成模拟消息列表"""
        messages = []
        message_types = ["系统通知", "健康提醒", "设备告警", "定期报告"]
        contents = [
            "您的健康数据已更新",
            "设备电量不足，请及时充电",
            "检测到心率异常，请注意休息",
            "您的今日运动目标已完成",
            "定期健康报告已生成"
        ]
        senders = ["系统", "健康管理", "设备管理", "数据分析"]
        
        for i in range(count):
            timestamp = datetime.now() - timedelta(hours=random.randint(1, 24))
            messages.append(MessageInfoResponse(
                message_id=f"MSG{random.randint(100000, 999999)}",
                message_type=random.choice(message_types),
                content=random.choice(contents),
                sender=random.choice(senders),
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                read_status=random.choice([True, False])
            ))
        return messages
    
    @staticmethod
    def generate_health_data(count: int = 30) -> List[HealthDataResponse]:
        """生成模拟健康数据列表"""
        health_data = []
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
        depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
        
        for i in range(count):
            timestamp = datetime.now() - timedelta(hours=random.randint(1, 48))
            health_data.append(HealthDataResponse(
                health_id=f"H{random.randint(100000, 999999)}",
                user_name=random.choice(names),
                dept_name=random.choice(depts),
                deviceSn=f"DEV{random.randint(10000, 99999)}",
                heart_rate=random.randint(60, 100),
                blood_oxygen=random.randint(95, 99),
                temperature=round(random.uniform(36.0, 37.5), 1),
                pressure_high=random.randint(110, 140),
                pressure_low=random.randint(70, 90),
                step=random.randint(5000, 15000),
                distance=round(random.uniform(3.0, 12.0), 1),
                calorie=round(random.uniform(200, 800), 1),
                stress=random.randint(20, 80),
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ))
        return health_data
    
    @staticmethod
    def generate_users(count: int = 50) -> List[UserInfoResponse]:
        """生成模拟用户列表"""
        users = []
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "陈明", "林峰"]
        depts = ["研发部", "销售部", "市场部", "人事部", "财务部"]
        
        for i in range(count):
            users.append(UserInfoResponse(
                user_id=f"U{random.randint(100000, 999999)}",
                user_name=random.choice(names),
                dept_name=random.choice(depts),
                org_id=f"ORG{random.randint(1000, 9999)}",
                deviceSn=f"DEV{random.randint(10000, 99999)}",
                phone=f"1{random.randint(3000000000, 8999999999)}",
                email=f"user{i}@company.com"
            ))
        return users
    
    @staticmethod
    def generate_health_baseline() -> HealthBaselineResponse:
        """生成模拟健康基线"""
        return HealthBaselineResponse(
            baseline_score=random.randint(75, 85),
            trend=random.choice(["上升", "下降", "稳定"]),
            comparison={
                "last_week": random.randint(-5, 10),
                "last_month": random.randint(-8, 15)
            },
            factors={
                "heart_rate": random.randint(70, 90),
                "blood_oxygen": random.randint(85, 95),
                "temperature": random.randint(80, 90),
                "pressure": random.randint(75, 85),
                "step": random.randint(60, 80),
                "sleep": random.randint(70, 85)
            }
        )
    
    @staticmethod
    def generate_health_recommendations() -> List[HealthRecommendationResponse]:
        """生成模拟健康建议"""
        recommendations = [
            HealthRecommendationResponse(
                id=f"REC{random.randint(1000, 9999)}",
                title="建议增加有氧运动",
                content="根据您的心率数据，建议每天进行30分钟有氧运动",
                priority="高",
                category="运动建议"
            ),
            HealthRecommendationResponse(
                id=f"REC{random.randint(1000, 9999)}",
                title="注意血压监测",
                content="您的血压数据显示轻微偏高，建议定期监测",
                priority="中",
                category="健康监测"
            ),
            HealthRecommendationResponse(
                id=f"REC{random.randint(1000, 9999)}",
                title="改善睡眠质量",
                content="建议调整作息时间，保证充足睡眠",
                priority="中",
                category="生活方式"
            )
        ]
        return recommendations