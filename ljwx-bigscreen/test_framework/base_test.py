#!/usr/bin/env python3
"""自动化测试框架基础类"""
import mysql.connector
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class BaseTestFramework(ABC):
    """测试框架基础类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config() #测试配置
        self.test_results = [] #测试结果集合
        self.setup_logging() #日志配置
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'api_base_url': 'http://localhost:5001',
            'db_config': {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root', 
                'password': '123456',
                'database': 'lj-06'
            },
            'test_timeout': 30,
            'retry_count': 3,
            'cleanup_test_data': True
        }
    
    def setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'test_log_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_db_connection(self):
        """获取数据库连接"""
        return mysql.connector.connect(**self.config['db_config'])
    
    def execute_db_query(self, query: str, params: tuple = None) -> List[tuple]:
        """执行数据库查询"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"数据库查询失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def execute_db_update(self, query: str, params: tuple = None) -> int:
        """执行数据库更新操作"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"数据库更新失败: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def make_api_request(self, endpoint: str, method: str = 'POST', data: Dict = None, headers: Dict = None) -> Dict:
        """发起API请求"""
        url = f"{self.config['api_base_url']}{endpoint}"
        headers = headers or {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.config['test_timeout'])
            elif method.upper() == 'GET':
                response = requests.get(url, params=data, headers=headers, timeout=self.config['test_timeout'])
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def wait_for_condition(self, condition_func, timeout: int = 30, interval: int = 1) -> bool:
        """等待条件满足"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False
    
    def generate_test_device_sn(self) -> str:
        """生成测试设备序列号"""
        return f"TEST_{self.__class__.__name__}_{int(time.time())}"
    
    def cleanup_test_data(self, device_sn: str):
        """清理测试数据"""
        if not self.config['cleanup_test_data']:
            return
            
        tables = ['t_user_health_data', 't_alert_info', 't_device_message']
        for table in tables:
            try:
                count = self.execute_db_update(f"DELETE FROM {table} WHERE device_sn = %s", (device_sn,))
                self.logger.info(f"清理{table}: {count}条记录")
            except Exception as e:
                self.logger.error(f"清理{table}失败: {e}")
    
    def add_test_result(self, test_name: str, success: bool, details: Dict = None):
        """添加测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': datetime.now(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{test_name}: {status}")
        
        if not success and details:
            self.logger.error(f"失败详情: {details}")
    
    def generate_report(self) -> str:
        """生成测试报告"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed
        
        report = f"""
🔍 {self.__class__.__name__} 自动化测试报告
{'='*80}
📊 测试概况:
   - 总测试数: {total}
   - 通过数量: {passed} ✅
   - 失败数量: {failed} ❌
   - 成功率: {(passed/total*100):.1f}%

⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 详细结果:
"""
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report += f"\n{i:2d}. {result['test_name']} - {status}"
            if not result['success'] and result['details']:
                report += f"\n    错误: {result['details'].get('error', 'Unknown error')}"
        
        return report
    
    @abstractmethod
    def run_tests(self) -> List[Dict]:
        """运行测试套件 - 子类必须实现"""
        pass 