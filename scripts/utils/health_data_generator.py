#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康数据生成脚本 (Python版本)
功能：先登录获取token，然后生成过去一个月的baseline, score, prediction, recommendation, profile
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import argparse

# 配置参数
class Config:
    BASE_URL = "http://localhost:9998"
    USERNAME = "admin" 
    PASSWORD = "admin123"
    DAYS = 30
    TIMEOUT = 30

class Colors:
    """终端颜色定义"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class Logger:
    """日志工具类"""
    
    @staticmethod
    def info(message: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    @staticmethod
    def success(message: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    @staticmethod
    def warning(message: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    @staticmethod
    def error(message: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    @staticmethod
    def debug(message: str):
        print(f"{Colors.PURPLE}[DEBUG]{Colors.NC} {message}")

class HealthDataGenerator:
    """健康数据生成器"""
    
    def __init__(self, base_url: str = Config.BASE_URL, username: str = Config.USERNAME, 
                 password: str = Config.PASSWORD, days: int = Config.DAYS):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.days = days
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.session.timeout = Config.TIMEOUT
        
        # 健康数据类型定义
        self.data_types = [
            ("baseline", "健康基线数据"),
            ("score", "健康评分数据"), 
            ("prediction", "健康预测数据"),
            ("recommendation", "健康建议数据"),
            ("profile", "健康档案数据")
        ]
    
    def check_service(self) -> bool:
        """检查服务是否可用"""
        Logger.info("检查ljwx-boot服务状态...")
        
        try:
            response = self.session.get(f"{self.base_url}/actuator/health")
            if response.status_code == 200:
                Logger.success("服务正常运行")
                return True
            else:
                Logger.error(f"服务返回状态码: {response.status_code}")
                return False
        except Exception as e:
            Logger.error(f"服务不可访问: {str(e)}")
            Logger.error("请确保ljwx-boot已启动并运行在正确端口")
            return False
    
    def login(self) -> bool:
        """登录获取token"""
        Logger.info("开始登录获取token...")
        
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        # 尝试多个可能的登录接口
        login_endpoints = [
            "/auth/login",
            "/api/auth/login", 
            "/api/login",
            "/login"
        ]
        
        for endpoint in login_endpoints:
            try:
                Logger.debug(f"尝试登录接口: {endpoint}")
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 尝试多种token字段名
                    token_fields = ['token', 'access_token', 'accessToken', 'jwt']
                    for field in token_fields:
                        if field in data:
                            self.token = data[field]
                            break
                        elif 'data' in data and isinstance(data['data'], dict) and field in data['data']:
                            self.token = data['data'][field]
                            break
                    
                    if self.token:
                        Logger.success("登录成功，token已获取")
                        self.session.headers.update({
                            "Authorization": f"Bearer {self.token}"
                        })
                        return True
                        
            except Exception as e:
                Logger.debug(f"登录接口 {endpoint} 失败: {str(e)}")
                continue
        
        Logger.warning("无法获取token，将尝试直接访问API（可能不需要登录）")
        return True  # 继续执行，可能API不需要认证
    
    def api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """执行API请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                response = self.session.get(url)
            
            # 尝试解析JSON响应
            try:
                return {
                    "status_code": response.status_code,
                    "data": response.json(),
                    "text": response.text
                }
            except:
                return {
                    "status_code": response.status_code,
                    "data": {},
                    "text": response.text
                }
                
        except Exception as e:
            return {
                "status_code": 0,
                "data": {},
                "text": f"请求异常: {str(e)}"
            }
    
    def generate_health_data(self, data_type: str, description: str) -> bool:
        """生成健康数据"""
        Logger.info(f"开始生成{description}...")
        
        # 尝试多个可能的API接口
        endpoints = [
            f"/api/health/task/execute/{data_type}?days={self.days}",
            f"/api/health/task/{data_type}?days={self.days}",
            f"/health/task/execute/{data_type}?days={self.days}",
            f"/api/health/generate/{data_type}?days={self.days}"
        ]
        
        for endpoint in endpoints:
            Logger.debug(f"尝试API接口: {endpoint}")
            response = self.api_request("POST", endpoint)
            
            # 检查响应
            if response["status_code"] == 200:
                data = response["data"]
                
                # 检查业务状态码
                code = data.get("code", data.get("status", 200))
                message = data.get("message", data.get("msg", "success"))
                
                if code in [200, 0] or "success" in str(message).lower() or "完成" in str(message) or "执行" in str(message):
                    Logger.success(f"{description}生成完成")
                    return True
                elif code == 401:
                    Logger.warning(f"{description}需要认证，尝试重新登录...")
                    if self.login():
                        continue  # 重试当前接口
                else:
                    Logger.error(f"{description}生成失败: {message}")
                    Logger.debug(f"完整响应: {response['text']}")
            elif response["status_code"] == 401:
                Logger.warning("认证失败，尝试重新登录...")
                if self.login():
                    continue  # 重试当前接口
            elif response["status_code"] == 404:
                Logger.debug(f"接口不存在: {endpoint}")
                continue  # 尝试下一个接口
            else:
                Logger.debug(f"接口返回: {response['status_code']} - {response['text']}")
                continue  # 尝试下一个接口
        
        Logger.error(f"{description}生成失败: 所有API接口都无法访问")
        return False
    
    def verify_data(self):
        """验证生成的数据（通过数据库查询）"""
        Logger.info("验证生成的数据...")
        
        try:
            import subprocess
            
            sql_query = f"""
            SELECT 
                '基线数据' as data_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT user_id) as users,
                DATE(MAX(create_time)) as latest_date
            FROM t_health_baseline 
            WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL {self.days} DAY)
            UNION ALL
            SELECT 
                '评分数据' as data_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT user_id) as users,
                DATE(MAX(create_time)) as latest_date
            FROM t_health_score 
            WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL {self.days} DAY)
            UNION ALL
            SELECT 
                '预测数据' as data_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT user_id) as users,
                DATE(MAX(create_time)) as latest_date
            FROM t_health_prediction 
            WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL {self.days} DAY)
            UNION ALL
            SELECT 
                '建议数据' as data_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT user_id) as users,
                DATE(MAX(create_time)) as latest_date
            FROM t_health_recommendation 
            WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL {self.days} DAY)
            UNION ALL
            SELECT 
                '档案数据' as data_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT user_id) as users,
                DATE(MAX(create_time)) as latest_date
            FROM t_health_profile 
            WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL {self.days} DAY);
            """
            
            result = subprocess.run([
                "mysql", "-h127.0.0.1", "-uroot", "-p123456", 
                "-e", sql_query, "test"
            ], capture_output=True, text=True, stderr=subprocess.DEVNULL)
            
            if result.returncode == 0:
                print("\n" + "="*50)
                print("📊 数据验证结果")
                print("="*50)
                print(result.stdout)
            else:
                Logger.warning("无法验证数据库数据，请手动检查")
                
        except Exception as e:
            Logger.warning(f"数据验证失败: {str(e)}")
    
    def run(self) -> bool:
        """运行主流程"""
        print("========================================")
        print("🏥 健康数据生成脚本 (Python版本)")
        print("========================================")
        print(f"📅 生成时间范围: 过去 {self.days} 天")
        print(f"🌐 服务地址: {self.base_url}")
        print(f"👤 用户名: {self.username}")
        print("")
        
        # 1. 检查服务状态
        if not self.check_service():
            return False
        
        # 2. 登录获取token
        if not self.login():
            Logger.error("登录失败，无法继续")
            return False
        
        print("")
        print("开始生成健康数据...")
        print("========================================")
        
        # 3. 按顺序生成各类健康数据
        success_count = 0
        total_count = len(self.data_types)
        
        for data_type, description in self.data_types:
            if self.generate_health_data(data_type, description):
                success_count += 1
            time.sleep(2)  # 避免请求过于频繁
        
        print("")
        print("========================================")
        print("📊 生成结果统计")
        print("========================================")
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            Logger.success("所有健康数据生成完成！")
        else:
            Logger.warning("部分健康数据生成失败，请检查日志")
        
        # 4. 验证生成的数据
        print("")
        self.verify_data()
        
        # 5. 输出访问信息
        print("")
        print("========================================")
        print("🔗 访问地址")
        print("========================================")
        print(f"📖 API文档: {self.base_url}/doc.html")
        print(f"📊 健康监控: {self.base_url}/actuator/health")
        print(f"🎯 任务管理: {self.base_url}/api/health/task/")
        print("")
        print("💡 提示：")
        print("  - 可以通过管理界面查看生成的数据")
        print("  - 数据生成可能需要一些时间处理") 
        print("  - 如有失败，可以重新运行此脚本")
        print("========================================")
        
        return success_count > 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='健康数据生成脚本')
    parser.add_argument('--url', default=Config.BASE_URL, help='API基础URL')
    parser.add_argument('--username', default=Config.USERNAME, help='用户名')
    parser.add_argument('--password', default=Config.PASSWORD, help='密码')
    parser.add_argument('--days', type=int, default=Config.DAYS, help='生成数据的天数')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    generator = HealthDataGenerator(
        base_url=args.url,
        username=args.username, 
        password=args.password,
        days=args.days
    )
    
    try:
        success = generator.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        Logger.warning("用户中断执行")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"执行异常: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()