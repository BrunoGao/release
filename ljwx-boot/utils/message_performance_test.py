#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LJWX消息系统V2性能测试脚本 - Python版本

功能特性:
1. 全面的性能测试套件 (TPS, 延迟, 吞吐量, 并发)
2. V1/V2系统对比测试
3. 实时性能监控和可视化报告
4. 多种测试场景支持
5. 自动化压力测试
6. 详细的HTML报告生成

使用方法:
python message_performance_test.py --host localhost:8080 --concurrent-users 50 --requests-per-user 100

作者: jjgao
项目: ljwx-boot
创建时间: 2025-09-10
"""

import asyncio
import aiohttp
import argparse
import json
import time
import statistics
import logging
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Template

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('message_performance_test.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """测试配置"""
    host: str = "localhost:8080"
    concurrent_users: int = 50
    requests_per_user: int = 100
    warmup_requests: int = 100
    request_timeout: int = 30
    test_duration_minutes: int = 5
    enable_v1_test: bool = True
    enable_v2_test: bool = True
    enable_stress_test: bool = True
    enable_database_test: bool = True
    output_dir: str = "performance_reports"

@dataclass
class PerformanceMetrics:
    """性能指标"""
    version: str
    total_requests: int
    success_requests: int
    failed_requests: int
    total_time_ms: int
    tps: float
    success_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_codes: Dict[str, int]
    test_time: datetime
    response_times: List[float]

class MessagePerformanceTester:
    """消息系统性能测试器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.base_url = f"http://{config.host}"
        self.v1_api_prefix = "/api/v1/messages"
        self.v2_api_prefix = "/api/v2/messages"
        
        # 性能指标收集
        self.metrics = {}
        self.response_times = []
        self.error_codes = {}
        self.request_lock = threading.Lock()
        
        # 创建输出目录
        Path(config.output_dir).mkdir(exist_ok=True)
        
    async def run_performance_test(self) -> Dict[str, PerformanceMetrics]:
        """运行完整的性能测试套件"""
        logger.info("🚀 启动LJWX消息系统V2性能测试")
        
        results = {}
        
        try:
            # 1. 系统预热
            await self.warmup_system()
            
            # 2. V1系统测试
            if self.config.enable_v1_test:
                logger.info("📊 开始V1系统性能测试...")
                results['V1'] = await self.performance_test("V1", self.v1_api_prefix)
            
            # 3. V2系统测试  
            if self.config.enable_v2_test:
                logger.info("📊 开始V2系统性能测试...")
                results['V2'] = await self.performance_test("V2", self.v2_api_prefix)
            
            # 4. 生成对比报告
            if len(results) > 1:
                self.generate_comparison_report(results)
            
            # 5. 数据库性能测试
            if self.config.enable_database_test:
                await self.database_performance_test()
            
            # 6. 压力测试
            if self.config.enable_stress_test:
                await self.stress_test()
            
            logger.info("✅ 性能测试完成")
            
        except Exception as e:
            logger.error(f"❌ 性能测试执行失败: {e}")
            raise
            
        return results
    
    async def warmup_system(self):
        """系统预热"""
        logger.info(f"🔥 系统预热中... ({self.config.warmup_requests} 个请求)")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            tasks = []
            for _ in range(self.config.warmup_requests):
                task = self.send_request(session, "GET", "/actuator/health", None)
                tasks.append(task)
            
            # 执行预热请求（忽略结果和错误）
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 等待系统稳定
        await asyncio.sleep(5)
        logger.info("✅ 系统预热完成")
    
    async def performance_test(self, version: str, api_prefix: str) -> PerformanceMetrics:
        """执行性能测试"""
        logger.info(f"🧪 开始 {version} 系统性能测试")
        
        # 重置计数器
        self.reset_counters()
        
        start_time = time.time()
        
        # 创建异步任务
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
        ) as session:
            tasks = []
            for user_id in range(self.config.concurrent_users):
                task = self.execute_user_scenario(session, user_id, api_prefix)
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time_ms = int((end_time - start_time) * 1000)
        
        # 构建性能结果
        return self.build_performance_metrics(version, total_time_ms)
    
    async def execute_user_scenario(self, session: aiohttp.ClientSession, user_id: int, api_prefix: str):
        """执行单用户测试场景"""
        import random
        
        for i in range(self.config.requests_per_user):
            try:
                # 随机选择测试场景
                scenario = random.randint(0, 4)
                
                if scenario == 0:
                    await self.test_create_message(session, api_prefix, user_id)
                elif scenario == 1:
                    await self.test_query_messages(session, api_prefix, user_id)
                elif scenario == 2:
                    await self.test_batch_operations(session, api_prefix, user_id)
                elif scenario == 3:
                    await self.test_message_status(session, api_prefix, user_id)
                else:
                    await self.test_message_statistics(session, api_prefix, user_id)
                
                # 模拟用户行为间隔
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
            except Exception as e:
                logger.debug(f"用户 {user_id} 请求失败: {e}")
    
    async def test_create_message(self, session: aiohttp.ClientSession, api_prefix: str, user_id: int):
        """测试消息创建"""
        message_data = {
            "deviceSn": f"TEST_DEVICE_{user_id}",
            "title": f"性能测试消息 {int(time.time() * 1000)}",
            "message": f"这是用户 {user_id} 的性能测试消息内容",
            "messageType": "notification",
            "senderType": "system", 
            "receiverType": "device",
            "customerId": 1,
            "urgency": "medium",
            "priority": 3,
            "requireAck": False
        }
        
        await self.send_request(session, "POST", api_prefix, message_data)
    
    async def test_query_messages(self, session: aiohttp.ClientSession, api_prefix: str, user_id: int):
        """测试消息查询"""
        query_params = f"?customerId=1&page=1&pageSize=20&deviceSn=TEST_DEVICE_{user_id}"
        await self.send_request(session, "GET", api_prefix + query_params, None)
    
    async def test_batch_operations(self, session: aiohttp.ClientSession, api_prefix: str, user_id: int):
        """测试批量操作"""
        batch_data = []
        for i in range(10):
            batch_data.append({
                "deviceSn": f"BATCH_DEVICE_{user_id}_{i}",
                "title": f"批量测试消息 {i}",
                "message": f"批量测试内容 {i}",
                "messageType": "notification",
                "senderType": "system",
                "receiverType": "device",
                "customerId": 1
            })
        
        await self.send_request(session, "POST", api_prefix + "/batch", batch_data)
    
    async def test_message_status(self, session: aiohttp.ClientSession, api_prefix: str, user_id: int):
        """测试消息状态更新"""
        message_id = user_id + 1000
        status_data = {
            "messageStatus": "acknowledged",
            "updateTime": datetime.now().isoformat()
        }
        
        await self.send_request(session, "PUT", f"{api_prefix}/{message_id}", status_data)
    
    async def test_message_statistics(self, session: aiohttp.ClientSession, api_prefix: str, user_id: int):
        """测试消息统计"""
        query_params = "?customerId=1&startDate=2025-09-01&endDate=2025-09-10"
        await self.send_request(session, "GET", api_prefix + "/statistics" + query_params, None)
    
    async def send_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, data: Any):
        """发送HTTP请求并记录性能指标"""
        request_start = time.time()
        
        with self.request_lock:
            self.metrics.setdefault('total_requests', 0)
            self.metrics['total_requests'] += 1
        
        try:
            url = self.base_url + endpoint
            
            if method == "GET":
                async with session.get(url) as response:
                    await response.text()
                    status_code = response.status
            else:
                json_data = json.dumps(data) if data else None
                headers = {'Content-Type': 'application/json'} if json_data else {}
                
                async with session.request(method, url, data=json_data, headers=headers) as response:
                    await response.text()
                    status_code = response.status
            
            # 记录响应时间
            response_time = (time.time() - request_start) * 1000  # 转换为毫秒
            
            with self.request_lock:
                self.response_times.append(response_time)
                
                # 记录成功/失败
                if 200 <= status_code < 300:
                    self.metrics.setdefault('success_requests', 0)
                    self.metrics['success_requests'] += 1
                else:
                    self.metrics.setdefault('failed_requests', 0)
                    self.metrics['failed_requests'] += 1
                    self.error_codes[str(status_code)] = self.error_codes.get(str(status_code), 0) + 1
            
        except Exception as e:
            response_time = (time.time() - request_start) * 1000
            
            with self.request_lock:
                self.response_times.append(response_time)
                self.metrics.setdefault('failed_requests', 0)
                self.metrics['failed_requests'] += 1
                self.error_codes['EXCEPTION'] = self.error_codes.get('EXCEPTION', 0) + 1
    
    async def database_performance_test(self):
        """数据库性能测试"""
        logger.info("🗃️ 开始数据库性能测试...")
        
        # 测试批量插入
        await self.test_bulk_insert()
        
        # 测试复杂查询
        await self.test_complex_queries()
        
        # 测试并发读写
        await self.test_concurrent_read_write()
        
        logger.info("✅ 数据库性能测试完成")
    
    async def test_bulk_insert(self):
        """测试大批量插入"""
        logger.info("测试批量插入性能 (1000条记录)...")
        
        batch_data = []
        for i in range(1000):
            batch_data.append({
                "deviceSn": f"BULK_TEST_{i}",
                "title": f"批量插入测试 {i}",
                "message": f"批量插入测试内容 {i}",
                "messageType": "notification",
                "senderType": "system",
                "receiverType": "device", 
                "customerId": 1
            })
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            await self.send_request(session, "POST", self.v2_api_prefix + "/bulk", batch_data)
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            tps = 1000 * 1000 / duration_ms if duration_ms > 0 else 0
            logger.info(f"批量插入完成: {duration_ms:.0f} ms, TPS: {tps:.2f}")
    
    async def test_complex_queries(self):
        """测试复杂查询"""
        logger.info("测试复杂查询性能...")
        
        complex_queries = [
            "?customerId=1&messageType=notification&messageStatus=pending&startDate=2025-09-01&endDate=2025-09-10",
            "?deviceSn=TEST_DEVICE_1&urgency=high&priority=5", 
            "?orgId=1&senderType=system&receiverType=device&requireAck=true"
        ]
        
        async with aiohttp.ClientSession() as session:
            for query in complex_queries:
                start_time = time.time()
                await self.send_request(session, "GET", self.v2_api_prefix + query, None)
                end_time = time.time()
                logger.info(f"复杂查询完成: {(end_time - start_time) * 1000:.0f} ms")
    
    async def test_concurrent_read_write(self):
        """测试并发读写"""
        logger.info("测试并发读写性能...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 并发写操作
            for i in range(20):
                task = self.test_create_message(session, self.v2_api_prefix, i)
                tasks.append(task)
            
            # 并发读操作
            for i in range(30):
                task = self.test_query_messages(session, self.v2_api_prefix, i)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("并发读写测试完成")
    
    async def stress_test(self):
        """压力测试"""
        logger.info(f"🔥 开始压力测试 (持续{self.config.test_duration_minutes}分钟)...")
        
        test_duration = self.config.test_duration_minutes * 60  # 转换为秒
        start_time = time.time()
        stress_requests = 0
        request_lock = threading.Lock()
        
        async def stress_worker(session: aiohttp.ClientSession, worker_id: int):
            nonlocal stress_requests
            import random
            
            while time.time() - start_time < test_duration:
                try:
                    await self.test_create_message(session, self.v2_api_prefix, random.randint(0, 1000))
                    with request_lock:
                        stress_requests += 1
                    await asyncio.sleep(0.1)  # 控制请求频率
                except Exception:
                    pass  # 压力测试中忽略个别错误
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(20):  # 20个并发工作者
                task = stress_worker(session, i)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        actual_duration = time.time() - start_time
        avg_tps = stress_requests / actual_duration if actual_duration > 0 else 0
        
        logger.info(f"压力测试完成: 总请求 {stress_requests}, 平均TPS {avg_tps:.2f}")
    
    def build_performance_metrics(self, version: str, total_time_ms: int) -> PerformanceMetrics:
        """构建性能指标"""
        total_requests = self.metrics.get('total_requests', 0)
        success_requests = self.metrics.get('success_requests', 0) 
        failed_requests = self.metrics.get('failed_requests', 0)
        
        # 计算统计指标
        response_times_sorted = sorted(self.response_times)
        
        avg_response_time = statistics.mean(self.response_times) if self.response_times else 0
        min_response_time = min(self.response_times) if self.response_times else 0
        max_response_time = max(self.response_times) if self.response_times else 0
        
        p95_index = int(len(response_times_sorted) * 0.95)
        p99_index = int(len(response_times_sorted) * 0.99)
        p95_response_time = response_times_sorted[p95_index] if response_times_sorted else 0
        p99_response_time = response_times_sorted[p99_index] if response_times_sorted else 0
        
        tps = total_requests * 1000 / total_time_ms if total_time_ms > 0 else 0
        success_rate = success_requests * 100 / total_requests if total_requests > 0 else 0
        
        return PerformanceMetrics(
            version=version,
            total_requests=total_requests,
            success_requests=success_requests,
            failed_requests=failed_requests,
            total_time_ms=total_time_ms,
            tps=tps,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            error_codes=self.error_codes.copy(),
            test_time=datetime.now(),
            response_times=self.response_times.copy()
        )
    
    def reset_counters(self):
        """重置计数器"""
        self.metrics.clear()
        self.response_times.clear()
        self.error_codes.clear()
    
    def generate_comparison_report(self, results: Dict[str, PerformanceMetrics]):
        """生成对比报告"""
        logger.info("📊 生成性能对比报告...")
        
        # 生成文本报告
        self.generate_text_report(results)
        
        # 生成可视化图表
        self.generate_charts(results)
        
        # 生成HTML报告
        self.generate_html_report(results)
    
    def generate_text_report(self, results: Dict[str, PerformanceMetrics]):
        """生成文本格式报告"""
        report_lines = []
        report_lines.append("═" * 70)
        report_lines.append("              LJWX消息系统性能对比报告")
        report_lines.append("═" * 70)
        report_lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"并发用户: {self.config.concurrent_users} 用户")
        report_lines.append(f"总请求数: {self.config.concurrent_users * self.config.requests_per_user} 请求")
        report_lines.append("─" * 70)
        
        # 各版本性能指标
        for version, metrics in results.items():
            report_lines.append(f"\n📊 {version}系统性能指标:")
            report_lines.append(f"   TPS:           {metrics.tps:.2f} 请求/秒")
            report_lines.append(f"   成功率:        {metrics.success_rate:.2f}%")
            report_lines.append(f"   平均响应时间:  {metrics.avg_response_time:.2f} ms")
            report_lines.append(f"   P95响应时间:   {metrics.p95_response_time:.0f} ms")
            report_lines.append(f"   P99响应时间:   {metrics.p99_response_time:.0f} ms")
            report_lines.append(f"   最大响应时间:  {metrics.max_response_time:.0f} ms")
            report_lines.append(f"   总执行时间:    {metrics.total_time_ms / 1000:.2f} 秒")
        
        # 性能对比（如果有多个版本）
        if len(results) >= 2:
            versions = list(results.keys())
            v1_metrics = results[versions[0]]
            v2_metrics = results[versions[1]]
            
            report_lines.append("\n🚀 性能提升对比:")
            
            tps_improvement = self.calculate_improvement(v1_metrics.tps, v2_metrics.tps)
            response_improvement = self.calculate_improvement(
                v1_metrics.avg_response_time, v2_metrics.avg_response_time, lower_is_better=True
            )
            p95_improvement = self.calculate_improvement(
                v1_metrics.p95_response_time, v2_metrics.p95_response_time, lower_is_better=True
            )
            
            report_lines.append(f"   TPS提升:       {tps_improvement:.1f}% ({v1_metrics.tps:.2f} → {v2_metrics.tps:.2f})")
            report_lines.append(f"   响应时间优化:  {response_improvement:.1f}% ({v1_metrics.avg_response_time:.2f} ms → {v2_metrics.avg_response_time:.2f} ms)")
            report_lines.append(f"   P95延迟优化:   {p95_improvement:.1f}% ({v1_metrics.p95_response_time:.0f} ms → {v2_metrics.p95_response_time:.0f} ms)")
            
            overall_improvement = (tps_improvement + response_improvement + p95_improvement) / 3
            grade = self.get_performance_grade(overall_improvement)
            report_lines.append(f"   整体性能提升:  {overall_improvement:.1f}% ({grade})")
        
        report_lines.append("\n" + "═" * 70)
        
        # 输出到控制台和文件
        report_text = "\n".join(report_lines)
        logger.info(report_text)
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file = Path(self.config.output_dir) / f"performance-report-{timestamp}.txt"
        report_file.write_text(report_text, encoding='utf-8')
        logger.info(f"📝 文本报告已保存: {report_file}")
    
    def generate_charts(self, results: Dict[str, PerformanceMetrics]):
        """生成可视化图表"""
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('LJWX消息系统性能对比', fontsize=16, fontweight='bold')
            
            versions = list(results.keys())
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
            
            # TPS对比
            ax1 = axes[0, 0]
            tps_values = [results[v].tps for v in versions]
            bars1 = ax1.bar(versions, tps_values, color=colors[:len(versions)])
            ax1.set_title('TPS (事务/秒)')
            ax1.set_ylabel('TPS')
            for i, v in enumerate(tps_values):
                ax1.text(i, v + max(tps_values) * 0.01, f'{v:.1f}', ha='center')
            
            # 响应时间对比
            ax2 = axes[0, 1]
            response_times = {
                'Average': [results[v].avg_response_time for v in versions],
                'P95': [results[v].p95_response_time for v in versions],
                'P99': [results[v].p99_response_time for v in versions]
            }
            
            x = range(len(versions))
            width = 0.25
            for i, (label, values) in enumerate(response_times.items()):
                ax2.bar([xi + i * width for xi in x], values, width, 
                       label=label, color=colors[i])
            
            ax2.set_title('响应时间对比 (ms)')
            ax2.set_ylabel('响应时间 (ms)')
            ax2.set_xticks([xi + width for xi in x])
            ax2.set_xticklabels(versions)
            ax2.legend()
            
            # 成功率对比
            ax3 = axes[1, 0]
            success_rates = [results[v].success_rate for v in versions]
            bars3 = ax3.bar(versions, success_rates, color=colors[:len(versions)])
            ax3.set_title('成功率 (%)')
            ax3.set_ylabel('成功率 (%)')
            ax3.set_ylim(0, 105)
            for i, v in enumerate(success_rates):
                ax3.text(i, v + 1, f'{v:.1f}%', ha='center')
            
            # 响应时间分布图
            ax4 = axes[1, 1]
            for i, version in enumerate(versions):
                metrics = results[version]
                if len(metrics.response_times) > 0:
                    ax4.hist(metrics.response_times, bins=50, alpha=0.7, 
                            label=f'{version} 响应时间', color=colors[i])
            
            ax4.set_title('响应时间分布')
            ax4.set_xlabel('响应时间 (ms)')
            ax4.set_ylabel('频次')
            ax4.legend()
            
            plt.tight_layout()
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            chart_file = Path(self.config.output_dir) / f"performance-charts-{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 性能图表已保存: {chart_file}")
            
        except ImportError:
            logger.warning("⚠️  matplotlib 未安装，跳过图表生成")
        except Exception as e:
            logger.error(f"❌ 生成图表失败: {e}")
    
    def generate_html_report(self, results: Dict[str, PerformanceMetrics]):
        """生成HTML格式报告"""
        html_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LJWX消息系统性能测试报告</title>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; border-bottom: 2px solid #4ecdc4; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .metrics-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4ecdc4; }
        .metric-item { display: flex; justify-content: space-between; margin: 8px 0; }
        .metric-label { font-weight: bold; color: #666; }
        .metric-value { color: #333; }
        .improvement { color: #28a745; font-weight: bold; }
        .degradation { color: #dc3545; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4ecdc4; color: white; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .success { background-color: #28a745; color: white; }
        .warning { background-color: #ffc107; color: black; }
        .error { background-color: #dc3545; color: white; }
        .footer { margin-top: 40px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 LJWX消息系统V2性能测试报告</h1>
        
        <div style="text-align: center; margin: 20px 0; color: #666;">
            <p>测试时间: {{ test_time }} | 并发用户: {{ concurrent_users }} | 总请求: {{ total_requests }}</p>
        </div>
        
        <h2>📊 性能指标概览</h2>
        <div class="metrics-grid">
            {% for version, metrics in results.items() %}
            <div class="metrics-card">
                <h3>{{ version }} 系统</h3>
                <div class="metric-item">
                    <span class="metric-label">TPS (事务/秒):</span>
                    <span class="metric-value">{{ "%.2f"|format(metrics.tps) }}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">成功率:</span>
                    <span class="metric-value">{{ "%.2f"|format(metrics.success_rate) }}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">平均响应时间:</span>
                    <span class="metric-value">{{ "%.2f"|format(metrics.avg_response_time) }} ms</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">P95响应时间:</span>
                    <span class="metric-value">{{ "%.0f"|format(metrics.p95_response_time) }} ms</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">P99响应时间:</span>
                    <span class="metric-value">{{ "%.0f"|format(metrics.p99_response_time) }} ms</span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if comparison %}
        <h2>🚀 性能提升分析</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>V1系统</th>
                <th>V2系统</th>
                <th>提升幅度</th>
                <th>状态</th>
            </tr>
            <tr>
                <td>TPS (事务/秒)</td>
                <td>{{ "%.2f"|format(comparison.v1_tps) }}</td>
                <td>{{ "%.2f"|format(comparison.v2_tps) }}</td>
                <td>{{ "%.1f"|format(comparison.tps_improvement) }}%</td>
                <td><span class="status {{ 'success' if comparison.tps_improvement > 0 else 'error' }}">{{ 'UP' if comparison.tps_improvement > 0 else 'DOWN' }}</span></td>
            </tr>
            <tr>
                <td>平均响应时间</td>
                <td>{{ "%.2f"|format(comparison.v1_response_time) }} ms</td>
                <td>{{ "%.2f"|format(comparison.v2_response_time) }} ms</td>
                <td>{{ "%.1f"|format(comparison.response_improvement) }}%</td>
                <td><span class="status {{ 'success' if comparison.response_improvement > 0 else 'error' }}">{{ 'BETTER' if comparison.response_improvement > 0 else 'WORSE' }}</span></td>
            </tr>
            <tr>
                <td>P95响应时间</td>
                <td>{{ "%.0f"|format(comparison.v1_p95) }} ms</td>
                <td>{{ "%.0f"|format(comparison.v2_p95) }} ms</td>
                <td>{{ "%.1f"|format(comparison.p95_improvement) }}%</td>
                <td><span class="status {{ 'success' if comparison.p95_improvement > 0 else 'error' }}">{{ 'BETTER' if comparison.p95_improvement > 0 else 'WORSE' }}</span></td>
            </tr>
        </table>
        
        <div style="margin: 20px 0; padding: 15px; background: #e8f4f8; border-radius: 8px;">
            <strong>整体性能评级:</strong> 
            <span class="status success">{{ comparison.grade }}</span>
            (平均提升: {{ "%.1f"|format(comparison.overall_improvement) }}%)
        </div>
        {% endif %}
        
        <div class="footer">
            <p>LJWX消息系统V2 - 性能测试报告 | 生成时间: {{ test_time }}</p>
        </div>
    </div>
</body>
</html>
        '''
        
        try:
            # 准备模板数据
            template_data = {
                'results': results,
                'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'concurrent_users': self.config.concurrent_users,
                'total_requests': self.config.concurrent_users * self.config.requests_per_user,
                'comparison': None
            }
            
            # 如果有多个版本，添加对比数据
            if len(results) >= 2:
                versions = list(results.keys())
                v1_metrics = results[versions[0]]
                v2_metrics = results[versions[1]]
                
                tps_improvement = self.calculate_improvement(v1_metrics.tps, v2_metrics.tps)
                response_improvement = self.calculate_improvement(
                    v1_metrics.avg_response_time, v2_metrics.avg_response_time, lower_is_better=True
                )
                p95_improvement = self.calculate_improvement(
                    v1_metrics.p95_response_time, v2_metrics.p95_response_time, lower_is_better=True
                )
                overall_improvement = (tps_improvement + response_improvement + p95_improvement) / 3
                
                template_data['comparison'] = {
                    'v1_tps': v1_metrics.tps,
                    'v2_tps': v2_metrics.tps,
                    'tps_improvement': tps_improvement,
                    'v1_response_time': v1_metrics.avg_response_time,
                    'v2_response_time': v2_metrics.avg_response_time,
                    'response_improvement': response_improvement,
                    'v1_p95': v1_metrics.p95_response_time,
                    'v2_p95': v2_metrics.p95_response_time,
                    'p95_improvement': p95_improvement,
                    'overall_improvement': overall_improvement,
                    'grade': self.get_performance_grade(overall_improvement)
                }
            
            # 渲染模板
            template = Template(html_template)
            html_content = template.render(**template_data)
            
            # 保存HTML报告
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            html_file = Path(self.config.output_dir) / f"performance-report-{timestamp}.html"
            html_file.write_text(html_content, encoding='utf-8')
            
            logger.info(f"📄 HTML报告已保存: {html_file}")
            
        except ImportError:
            logger.warning("⚠️  Jinja2 未安装，跳过HTML报告生成")
        except Exception as e:
            logger.error(f"❌ 生成HTML报告失败: {e}")
    
    def calculate_improvement(self, old_value: float, new_value: float, lower_is_better: bool = False) -> float:
        """计算性能提升百分比"""
        if old_value == 0:
            return 0.0
        
        if lower_is_better:
            improvement = (old_value - new_value) / old_value * 100
        else:
            improvement = (new_value - old_value) / old_value * 100
        
        return round(improvement, 1)
    
    def get_performance_grade(self, improvement: float) -> str:
        """获取性能等级"""
        if improvement >= 50:
            return "🏆 卓越"
        elif improvement >= 30:
            return "🥇 优秀"
        elif improvement >= 15:
            return "🥈 良好"
        elif improvement >= 5:
            return "🥉 一般"
        else:
            return "❌ 需改进"

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LJWX消息系统V2性能测试')
    parser.add_argument('--host', default='localhost:8080', help='测试目标主机')
    parser.add_argument('--concurrent-users', type=int, default=50, help='并发用户数')
    parser.add_argument('--requests-per-user', type=int, default=100, help='每用户请求数')
    parser.add_argument('--warmup-requests', type=int, default=100, help='预热请求数')
    parser.add_argument('--test-duration', type=int, default=5, help='压力测试持续时间(分钟)')
    parser.add_argument('--output-dir', default='performance_reports', help='报告输出目录')
    parser.add_argument('--disable-v1', action='store_true', help='禁用V1测试')
    parser.add_argument('--disable-v2', action='store_true', help='禁用V2测试')
    parser.add_argument('--disable-stress', action='store_true', help='禁用压力测试')
    parser.add_argument('--disable-database', action='store_true', help='禁用数据库测试')
    
    args = parser.parse_args()
    
    # 构建测试配置
    config = TestConfig(
        host=args.host,
        concurrent_users=args.concurrent_users,
        requests_per_user=args.requests_per_user,
        warmup_requests=args.warmup_requests,
        test_duration_minutes=args.test_duration,
        output_dir=args.output_dir,
        enable_v1_test=not args.disable_v1,
        enable_v2_test=not args.disable_v2,
        enable_stress_test=not args.disable_stress,
        enable_database_test=not args.disable_database
    )
    
    # 创建并运行测试器
    tester = MessagePerformanceTester(config)
    
    try:
        results = await tester.run_performance_test()
        logger.info("🎉 所有性能测试已完成")
        return 0
    except Exception as e:
        logger.error(f"💥 测试执行失败: {e}")
        return 1

if __name__ == '__main__':
    # 检查依赖
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
        from jinja2 import Template
    except ImportError as e:
        logger.warning(f"⚠️  可选依赖缺失: {e}")
        logger.warning("运行 'pip install matplotlib seaborn pandas jinja2' 以启用完整功能")
    
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)