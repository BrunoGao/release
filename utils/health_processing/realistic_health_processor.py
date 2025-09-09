#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现实可用的健康数据处理器
基于ljwx-boot实际可用的API和数据库

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from auth_manager import AuthManager, create_auth_manager
from database_helper import DatabaseHelper
from ljwx_boot_task_processor import LjwxBootTaskProcessor, TaskProcessingResult

@dataclass
class HealthProcessingReport:
    """健康数据处理报告"""
    timestamp: str
    total_users: int
    processing_results: List[TaskProcessingResult]
    data_analysis: Dict
    health_insights: Dict
    recommendations: List[str]
    processing_time: float
    
class RealisticHealthProcessor:
    """现实可用的健康数据处理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.setup_logging()
        
        # 初始化认证管理器
        self.auth_manager = create_auth_manager(config)
        if self.auth_manager:
            self.logger.info("🔐 初始化认证管理器")
            if not self.auth_manager.login():
                raise Exception("初始认证失败，无法继续执行")
        else:
            raise Exception("认证配置不完整")
        
        # 初始化处理器
        self.task_processor = LjwxBootTaskProcessor(
            config['ljwx_boot']['base_url'],
            self.auth_manager
        )
        self.db_helper = DatabaseHelper()
        
    def setup_logging(self):
        """设置日志"""
        output_dir = self.config.get('output', {}).get('output_dir', './results')
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        log_file = os.path.join(output_dir, f'realistic_health_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"📋 日志文件: {log_file}")
    
    def process_health_data(self) -> HealthProcessingReport:
        """处理健康数据"""
        self.logger.info("🚀 开始现实健康数据处理")
        start_time = time.time()
        
        # 1. 数据状态分析
        self.logger.info("📊 执行数据状态分析...")
        data_analysis = self.task_processor.analyze_current_data_status()
        
        # 2. 触发数据处理任务
        self.logger.info("🔄 触发数据处理任务...")
        processing_results = self.task_processor.trigger_data_processing_tasks()
        
        # 3. 生成健康洞察
        self.logger.info("🔍 生成健康洞察...")
        health_insights = self.task_processor.generate_health_insights()
        
        # 4. 获取用户数据
        active_users = self.db_helper.get_active_users(30)
        
        # 5. 生成建议
        recommendations = self.generate_comprehensive_recommendations(
            data_analysis, processing_results, health_insights, active_users
        )
        
        processing_time = time.time() - start_time
        
        # 创建报告
        report = HealthProcessingReport(
            timestamp=datetime.now().isoformat(),
            total_users=len(active_users),
            processing_results=processing_results,
            data_analysis=data_analysis,
            health_insights=health_insights,
            recommendations=recommendations,
            processing_time=processing_time
        )
        
        self.logger.info(f"🎉 现实健康数据处理完成，耗时: {processing_time:.2f}秒")
        return report
    
    def generate_comprehensive_recommendations(self, data_analysis: Dict, 
                                            processing_results: List[TaskProcessingResult],
                                            health_insights: Dict, 
                                            active_users: List) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 基于数据分析的建议
        analysis_recs = data_analysis.get('recommendations', [])
        recommendations.extend(analysis_recs)
        
        # 基于处理结果的建议
        failed_tasks = [r for r in processing_results if not r.success]
        if failed_tasks:
            failed_types = [r.task_type for r in failed_tasks]
            recommendations.append(f"⚠️ 以下任务执行失败: {', '.join(failed_types)}，建议检查")
        
        # 基于健康洞察的建议
        summary = health_insights.get('summary', {})
        if summary.get('active_users', 0) > 0:
            recommendations.append(f"👥 发现{summary['active_users']}个活跃用户，数据质量良好")
        
        if summary.get('baseline_features', 0) < 9:  # 应该有9个健康特征
            missing = 9 - summary.get('baseline_features', 0)
            recommendations.append(f"📊 缺少{missing}个特征的基线数据，建议执行基线生成")
        
        # 用户数据建议
        if len(active_users) > 0:
            avg_data_count = sum(u['health_data_count'] for u in active_users) / len(active_users)
            if avg_data_count < 50:
                recommendations.append(f"📈 用户平均数据量({avg_data_count:.0f})偏低，建议提醒用户增加数据上传")
        
        # 系统优化建议
        recommendations.append("🔧 建议定期执行: 1)缓存清理 2)基线更新 3)评分计算")
        recommendations.append("📅 建议设置定时任务，每日自动处理健康数据")
        
        return recommendations
    
    def save_report(self, report: HealthProcessingReport, output_file: str = None) -> str:
        """保存处理报告"""
        if output_file is None:
            output_dir = self.config.get('output', {}).get('output_dir', './results')
            output_file = f"{output_dir}/realistic_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # 转换为可序列化的格式
            report_data = {
                'timestamp': report.timestamp,
                'total_users': report.total_users,
                'processing_results': [
                    {
                        'task_type': r.task_type,
                        'success': r.success,
                        'message': r.message,
                        'execution_time': r.execution_time,
                        'data': r.data
                    }
                    for r in report.processing_results
                ],
                'data_analysis': report.data_analysis,
                'health_insights': report.health_insights,
                'recommendations': report.recommendations,
                'processing_time': report.processing_time
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"📁 处理报告已保存: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ 保存报告失败: {str(e)}")
            return ""
    
    def generate_markdown_summary(self, report: HealthProcessingReport) -> str:
        """生成Markdown摘要报告"""
        lines = [
            "# 健康数据处理报告",
            f"## 处理时间: {report.timestamp}",
            "",
            "## 摘要",
            f"- 活跃用户数: {report.total_users}",
            f"- 处理任务数: {len(report.processing_results)}",
            f"- 成功任务数: {sum(1 for r in report.processing_results if r.success)}",
            f"- 总耗时: {report.processing_time:.2f}秒",
            ""
        ]
        
        # 任务执行结果
        lines.extend([
            "## 任务执行结果",
            "| 任务类型 | 状态 | 耗时(秒) | 说明 |",
            "|---------|------|---------|-----|"
        ])
        
        for result in report.processing_results:
            status = "✅" if result.success else "❌"
            lines.append(f"| {result.task_type} | {status} | {result.execution_time:.2f} | {result.message} |")
        
        lines.append("")
        
        # 健康洞察
        if report.health_insights.get('summary'):
            summary = report.health_insights['summary']
            lines.extend([
                "## 健康数据概览",
                f"- 活跃用户: {summary.get('active_users', 0)}",
                f"- 基线特征: {summary.get('baseline_features', 0)}/9",
                f"- 评分特征: {summary.get('score_features', 0)}/9", 
                f"- 归档表数量: {summary.get('archive_tables', 0)}",
                ""
            ])
        
        # 用户洞察
        user_insights = report.health_insights.get('user_insights', [])
        if user_insights:
            lines.extend([
                "## 用户健康数据统计",
                "| 用户ID | 用户名 | 总记录数 | 心率 | 血氧 | 体温 | 血压 | 压力 | 步数 |",
                "|-------|--------|---------|-----|-----|-----|-----|-----|-----|"
            ])
            
            for insight in user_insights:
                features = insight['features_available']
                lines.append(f"| {insight['user_id']} | {insight['user_name']} | {insight['total_records']} | "
                           f"{features['heart_rate']} | {features['blood_oxygen']} | {features['temperature']} | "
                           f"{features['pressure']} | {features['stress']} | {features['step']} |")
            lines.append("")
        
        # 建议
        if report.recommendations:
            lines.extend([
                "## 处理建议",
                ""
            ])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        # 数据状态
        if report.data_analysis.get('database_status'):
            lines.extend([
                "## 数据库状态",
                "| 表名 | 状态 | 记录数 |",
                "|------|------|-------|"
            ])
            for table, info in report.data_analysis['database_status'].items():
                status = "✅" if info.get('exists') else "❌"
                count = info.get('record_count', 'N/A')
                lines.append(f"| {table} | {status} | {count} |")
        
        return "\n".join(lines)
    
    def save_markdown_summary(self, report: HealthProcessingReport, output_file: str = None) -> str:
        """保存Markdown摘要"""
        if output_file is None:
            output_dir = self.config.get('output', {}).get('output_dir', './results')
            output_file = f"{output_dir}/realistic_health_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            markdown_content = self.generate_markdown_summary(report)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"📄 Markdown摘要已保存: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ 保存Markdown摘要失败: {str(e)}")
            return ""

def main():
    """主函数"""
    # 加载配置
    try:
        with open('health_processing_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        return 1
    
    try:
        # 创建处理器
        processor = RealisticHealthProcessor(config)
        
        # 执行处理
        report = processor.process_health_data()
        
        # 保存报告
        json_file = processor.save_report(report)
        md_file = processor.save_markdown_summary(report)
        
        # 输出结果摘要
        print("\n" + "="*60)
        print("🎉 健康数据处理完成!")
        print("="*60)
        print(f"👥 活跃用户: {report.total_users}")
        print(f"📋 执行任务: {len(report.processing_results)}")
        print(f"✅ 成功任务: {sum(1 for r in report.processing_results if r.success)}")
        print(f"⏱️ 总耗时: {report.processing_time:.2f}秒")
        
        if json_file:
            print(f"📁 详细报告: {json_file}")
        if md_file:
            print(f"📄 摘要报告: {md_file}")
        
        print("\n💡 主要建议:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {rec}")
        
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())