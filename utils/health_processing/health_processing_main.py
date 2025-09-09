#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康数据处理主执行脚本
统一调用个人和部门健康数据处理

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime
from typing import Dict, List

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from personal_health_processor import PersonalHealthProcessor
from department_health_processor import DepartmentHealthProcessor
from auth_manager import AuthManager, create_auth_manager

class HealthProcessingManager:
    """健康数据处理管理器"""
    
    def __init__(self, config_file: str = None):
        self.config = self.load_config(config_file)
        self.setup_logging()
        
        # 初始化认证管理器
        self.auth_manager = create_auth_manager(self.config)
        if self.auth_manager:
            self.logger.info("🔐 初始化认证管理器")
            if not self.auth_manager.login():
                raise Exception("初始认证失败，无法继续执行")
        else:
            self.logger.warning("⚠️ 未配置认证信息，将尝试无认证访问")
        
    def load_config(self, config_file: str = None) -> Dict:
        """加载配置文件"""
        default_config = {
            'ljwx_boot': {
                'base_url': 'http://localhost:8080',
                'token': None,
                'timeout': 30
            },
            'personal_processing': {
                'enabled': True,
                'generate_baseline': True,
                'generate_score': True,
                'generate_prediction': True,
                'generate_recommendation': True,
                'generate_profile': True,
                'baseline_days': 30,
                'score_days': 30,
                'prediction_days': 30,
                'profile_days': 90,
                'user_days': 30,
                'max_workers': 5
            },
            'department_processing': {
                'enabled': True,
                'generate_baseline': True,
                'generate_score': True,
                'generate_prediction': True,
                'generate_recommendation': True,
                'generate_profile': True,
                'baseline_days': 90,
                'score_days': 30,
                'prediction_days': 30,
                'profile_days': 180,
                'org_days': 30,
                'max_workers': 3
            },
            'output': {
                'save_results': True,
                'output_dir': './results',
                'generate_report': True
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                # 递归合并配置
                self.merge_config(default_config, file_config)
                print(f"✅ 已加载配置文件: {config_file}")
            except Exception as e:
                print(f"⚠️ 配置文件加载失败，使用默认配置: {str(e)}")
        else:
            if config_file:
                print(f"⚠️ 配置文件不存在，使用默认配置: {config_file}")
            else:
                print("📄 使用默认配置")
        
        return default_config
    
    def merge_config(self, default: Dict, custom: Dict) -> None:
        """递归合并配置"""
        for key, value in custom.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self.merge_config(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
    
    def setup_logging(self):
        """设置日志"""
        # 创建结果目录
        output_dir = self.config['output']['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # 配置日志
        log_file = os.path.join(output_dir, f'health_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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
    
    def process_personal_health(self) -> List:
        """处理个人健康数据"""
        if not self.config['personal_processing']['enabled']:
            self.logger.info("⏭️ 个人健康数据处理已禁用")
            return []
        
        self.logger.info("🚀 开始个人健康数据处理")
        
        try:
            processor = PersonalHealthProcessor(
                base_url=self.config['ljwx_boot']['base_url'],
                token=self.config['ljwx_boot']['token'],
                auth_manager=self.auth_manager
            )
            
            results = processor.process_all_users(self.config['personal_processing'])
            
            if self.config['output']['save_results'] and results:
                output_dir = self.config['output']['output_dir']
                output_file = os.path.join(output_dir, f'personal_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                processor.save_results(results, output_file)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 个人健康数据处理失败: {str(e)}")
            return []
    
    def process_department_health(self) -> List:
        """处理部门健康数据"""
        if not self.config['department_processing']['enabled']:
            self.logger.info("⏭️ 部门健康数据处理已禁用")
            return []
        
        self.logger.info("🚀 开始部门健康数据处理")
        
        try:
            processor = DepartmentHealthProcessor(
                base_url=self.config['ljwx_boot']['base_url'],
                token=self.config['ljwx_boot']['token']
            )
            
            results = processor.process_all_organizations(self.config['department_processing'])
            
            if self.config['output']['save_results'] and results:
                output_dir = self.config['output']['output_dir']
                output_file = os.path.join(output_dir, f'department_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                processor.save_results(results, output_file)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 部门健康数据处理失败: {str(e)}")
            return []
    
    def generate_summary_report(self, personal_results: List, department_results: List) -> str:
        """生成汇总报告"""
        report_lines = [
            "# 健康数据处理汇总报告",
            f"## 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # 个人健康数据统计
        if personal_results:
            total_users = len(personal_results)
            success_stats = {
                'baseline': sum(1 for r in personal_results if r.baseline_success),
                'score': sum(1 for r in personal_results if r.score_success),
                'prediction': sum(1 for r in personal_results if r.prediction_success),
                'recommendation': sum(1 for r in personal_results if r.recommendation_success),
                'profile': sum(1 for r in personal_results if r.profile_success)
            }
            error_users = sum(1 for r in personal_results if r.errors)
            
            report_lines.extend([
                "## 个人健康数据处理结果",
                f"- 总用户数: {total_users}",
                f"- 基线生成成功: {success_stats['baseline']} ({success_stats['baseline']/total_users*100:.1f}%)",
                f"- 评分生成成功: {success_stats['score']} ({success_stats['score']/total_users*100:.1f}%)",
                f"- 预测生成成功: {success_stats['prediction']} ({success_stats['prediction']/total_users*100:.1f}%)",
                f"- 建议生成成功: {success_stats['recommendation']} ({success_stats['recommendation']/total_users*100:.1f}%)",
                f"- 画像生成成功: {success_stats['profile']} ({success_stats['profile']/total_users*100:.1f}%)",
                f"- 有错误的用户: {error_users} ({error_users/total_users*100:.1f}%)",
                ""
            ])
        else:
            report_lines.extend([
                "## 个人健康数据处理结果",
                "- 未处理个人健康数据",
                ""
            ])
        
        # 部门健康数据统计
        if department_results:
            total_orgs = len(department_results)
            total_users = sum(r.user_count for r in department_results)
            success_stats = {
                'baseline': sum(1 for r in department_results if r.baseline_success),
                'score': sum(1 for r in department_results if r.score_success),
                'prediction': sum(1 for r in department_results if r.prediction_success),
                'recommendation': sum(1 for r in department_results if r.recommendation_success),
                'profile': sum(1 for r in department_results if r.profile_success)
            }
            error_orgs = sum(1 for r in department_results if r.errors)
            
            report_lines.extend([
                "## 部门健康数据处理结果",
                f"- 总组织数: {total_orgs}",
                f"- 涉及用户数: {total_users}",
                f"- 基线生成成功: {success_stats['baseline']} ({success_stats['baseline']/total_orgs*100:.1f}%)",
                f"- 评分生成成功: {success_stats['score']} ({success_stats['score']/total_orgs*100:.1f}%)",
                f"- 预测生成成功: {success_stats['prediction']} ({success_stats['prediction']/total_orgs*100:.1f}%)",
                f"- 建议生成成功: {success_stats['recommendation']} ({success_stats['recommendation']/total_orgs*100:.1f}%)",
                f"- 画像生成成功: {success_stats['profile']} ({success_stats['profile']/total_orgs*100:.1f}%)",
                f"- 有错误的组织: {error_orgs} ({error_orgs/total_orgs*100:.1f}%)",
                ""
            ])
        else:
            report_lines.extend([
                "## 部门健康数据处理结果",
                "- 未处理部门健康数据",
                ""
            ])
        
        # 配置信息
        report_lines.extend([
            "## 处理配置",
            f"- ljwx-boot 服务地址: {self.config['ljwx_boot']['base_url']}",
            f"- 个人数据处理: {'启用' if self.config['personal_processing']['enabled'] else '禁用'}",
            f"- 部门数据处理: {'启用' if self.config['department_processing']['enabled'] else '禁用'}",
            ""
        ])
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        if self.config['output']['generate_report']:
            output_dir = self.config['output']['output_dir']
            report_file = os.path.join(output_dir, f'health_processing_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
            
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"📊 汇总报告已生成: {report_file}")
                return report_file
            except Exception as e:
                self.logger.error(f"❌ 生成汇总报告失败: {str(e)}")
        
        return report_content
    
    def run_all(self) -> Dict:
        """执行完整的健康数据处理流程"""
        self.logger.info("🎯 开始完整健康数据处理流程")
        start_time = time.time()
        
        # 处理个人健康数据
        personal_results = self.process_personal_health()
        
        # 处理部门健康数据
        department_results = self.process_department_health()
        
        # 生成汇总报告
        report = self.generate_summary_report(personal_results, department_results)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"🎉 健康数据处理完成! 总耗时: {elapsed_time:.2f}秒")
        
        return {
            'personal_results': personal_results,
            'department_results': department_results,
            'report': report,
            'elapsed_time': elapsed_time
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='健康数据处理主程序')
    parser.add_argument('-c', '--config', help='配置文件路径', default='health_processing_config.json')
    parser.add_argument('-p', '--personal-only', action='store_true', help='仅处理个人健康数据')
    parser.add_argument('-d', '--department-only', action='store_true', help='仅处理部门健康数据')
    parser.add_argument('--base-url', help='ljwx-boot 服务地址', default='http://localhost:8080')
    parser.add_argument('--token', help='访问令牌')
    
    args = parser.parse_args()
    
    # 创建处理管理器
    manager = HealthProcessingManager(args.config)
    
    # 命令行参数覆盖配置
    if args.base_url != 'http://localhost:8080':
        manager.config['ljwx_boot']['base_url'] = args.base_url
    if args.token:
        manager.config['ljwx_boot']['token'] = args.token
    if args.personal_only:
        manager.config['department_processing']['enabled'] = False
    if args.department_only:
        manager.config['personal_processing']['enabled'] = False
    
    try:
        # 执行处理
        results = manager.run_all()
        
        # 输出结果摘要
        print("\n" + "="*60)
        print("🎉 健康数据处理完成!")
        print("="*60)
        
        if results['personal_results']:
            print(f"👤 个人数据: 处理 {len(results['personal_results'])} 个用户")
        
        if results['department_results']:
            total_users = sum(r.user_count for r in results['department_results'])
            print(f"🏢 部门数据: 处理 {len(results['department_results'])} 个组织，涉及 {total_users} 个用户")
        
        print(f"⏱️ 总耗时: {results['elapsed_time']:.2f}秒")
        print(f"📁 输出目录: {manager.config['output']['output_dir']}")
        
        if isinstance(results['report'], str) and results['report'].endswith('.md'):
            print(f"📊 汇总报告: {results['report']}")
        
        print("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断处理")
        return 130
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())