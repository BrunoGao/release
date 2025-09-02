#!/usr/bin/env python3
"""基础测试类 - 统一测试框架基础功能"""
import json,time,logging,traceback,requests,mysql.connector
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    status: str  # PASS, FAIL, ERROR
    execution_time: str
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class BaseTest(ABC):
    """基础测试类 - 所有测试的父类"""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        self.start_time = None
        self.end_time = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载测试配置"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "test_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "api": {"base_url": "http://localhost:5001", "timeout": 30},
            "database": {"host": "localhost", "port": 3306, "user": "root", "password": "123456", "database": "ljwx"},
            "test_data": {"device_sn": "TEST_DEVICE", "user_id": 1, "org_id": 1}
        }
    
    def setup(self):
        """测试前置操作"""
        self.start_time = datetime.now()
        self.logger.info(f"开始执行测试: {self.__class__.__name__}")
    
    def teardown(self):
        """测试后置操作"""
        self.end_time = datetime.now()
        execution_time = (self.end_time - self.start_time).total_seconds()
        self.logger.info(f"测试完成: {self.__class__.__name__} - 耗时: {execution_time:.2f}秒")
    
    @abstractmethod
    def run_test(self) -> TestResult:
        """运行测试 - 子类必须实现"""
        pass
    
    def execute(self) -> TestResult:
        """执行测试的统一入口"""
        try:
            self.setup()
            result = self.run_test()
            self.teardown()
            return result
        except Exception as e:
            self.logger.error(f"测试执行异常: {e}")
            self.logger.error(traceback.format_exc())
            return TestResult(
                test_name=self.__class__.__name__,
                status="ERROR",
                execution_time="0.00s",
                details={},
                error_message=str(e)
            )
    
    def api_request(self, endpoint: str, method: str = "POST", data: Dict = None, timeout: int = None) -> requests.Response:
        """统一API请求方法"""
        url = f"{self.config['api']['base_url']}{endpoint}"
        timeout = timeout or self.config['api']['timeout']
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            elif method.upper() == "GET":
                response = requests.get(url, params=data, timeout=timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            self.logger.info(f"API请求: {method} {url} - 状态码: {response.status_code}")
            return response
        except Exception as e:
            self.logger.error(f"API请求失败: {e}")
            raise
    
    def db_query(self, sql: str, params: tuple = None) -> List[Dict]:
        """统一数据库查询方法"""
        try:
            conn = mysql.connector.connect(**self.config['database'])
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            self.logger.error(f"数据库查询失败: {e}")
            raise
    
    def db_execute(self, sql: str, params: tuple = None) -> int:
        """统一数据库执行方法"""
        try:
            conn = mysql.connector.connect(**self.config['database'])
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return affected_rows
        except Exception as e:
            self.logger.error(f"数据库执行失败: {e}")
            raise
    
    def verify_api_response(self, response: requests.Response, expected_status: int = 200) -> bool:
        """验证API响应"""
        if response.status_code != expected_status:
            self.logger.error(f"API响应状态码错误: {response.status_code}, 期望: {expected_status}")
            return False
        return True
    
    def verify_data_exists(self, table: str, condition: str, params: tuple = None) -> bool:
        """验证数据是否存在"""
        sql = f"SELECT COUNT(*) as count FROM {table} WHERE {condition}"
        result = self.db_query(sql, params)
        return result[0]['count'] > 0 if result else False
    
    def get_execution_time(self) -> str:
        """获取执行时间"""
        if self.start_time and self.end_time:
            return f"{(self.end_time - self.start_time).total_seconds():.2f}s"
        return "0.00s" 