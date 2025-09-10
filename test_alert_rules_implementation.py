#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
告警规则系统实施完整性测试和验证
全面测试数据库、后端服务、前端组件和性能监控

@Author: Claude Code
@CreateTime: 2025-09-10
@Description: 验证告警规则系统的完整实施情况
"""

import os
import sys
import json
import time
import requests
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    success: bool
    message: str
    details: Optional[Dict] = None
    execution_time: float = 0.0
    
@dataclass 
class ValidationReport:
    """验证报告数据类"""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    test_results: List[TestResult] = None
    overall_success: bool = False
    execution_time: float = 0.0
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.recommendations is None:
            self.recommendations = []

class AlertRulesImplementationValidator:
    """告警规则系统实施验证器"""
    
    def __init__(self, base_path: str = "/Users/brunogao/work/codes/93/release"):
        self.base_path = Path(base_path)
        self.results = []
        self.start_time = time.time()
        
        # 核心文件路径
        self.key_files = {
            # 数据库迁移
            "database_migration": "database_migrations/alert_rules_comprehensive_upgrade.sql",
            
            # 后端服务 - ljwx-boot
            "alert_rule_engine": "ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/AlertRuleEngineService.java",
            "cache_manager": "ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/AlertRulesCacheManager.java", 
            "message_publisher": "ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/UnifiedMessagePublisher.java",
            "performance_controller": "ljwx-boot/ljwx-boot-admin/src/main/java/com/ljwx/admin/controller/monitor/AlertPerformanceController.java",
            
            # 前端服务 - ljwx-bigscreen
            "cache_subscriber": "ljwx-bigscreen/bigscreen/bigScreen/alert_rules_cache_subscriber.py",
            "high_performance_generator": "ljwx-bigscreen/bigscreen/bigScreen/high_performance_alert_generator.py",
            
            # 前端界面 - ljwx-admin
            "alert_rule_wizard": "ljwx-admin/src/views/health/alert-rules/components/AlertRuleWizard.vue",
            "rules_management": "ljwx-admin/src/views/health/alert-rules/index.vue",
            "performance_dashboard": "ljwx-admin/src/views/monitor/alert-performance/index.vue"
        }
        
    def run_comprehensive_validation(self) -> ValidationReport:
        """运行综合验证测试"""
        logger.info("开始告警规则系统实施完整性验证...")
        
        # 1. 文件存在性验证
        self._validate_file_existence()
        
        # 2. 数据库迁移验证
        self._validate_database_migration()
        
        # 3. 后端服务验证
        self._validate_backend_services()
        
        # 4. 前端组件验证
        self._validate_frontend_components()
        
        # 5. API接口验证
        self._validate_api_endpoints()
        
        # 6. 配置完整性验证
        self._validate_configuration()
        
        # 7. 性能监控验证
        self._validate_performance_monitoring()
        
        # 生成报告
        return self._generate_validation_report()
    
    def _validate_file_existence(self):
        """验证关键文件存在性"""
        logger.info("验证关键文件存在性...")
        
        for file_key, file_path in self.key_files.items():
            start_time = time.time()
            full_path = self.base_path / file_path
            
            if full_path.exists():
                file_size = full_path.stat().st_size
                result = TestResult(
                    test_name=f"文件存在性检查: {file_key}",
                    success=True,
                    message=f"文件存在，大小: {file_size} bytes",
                    details={"file_path": str(full_path), "size": file_size},
                    execution_time=time.time() - start_time
                )
            else:
                result = TestResult(
                    test_name=f"文件存在性检查: {file_key}",
                    success=False,
                    message=f"文件不存在: {full_path}",
                    details={"expected_path": str(full_path)},
                    execution_time=time.time() - start_time
                )
            
            self.results.append(result)
            logger.info(f"✓ {result.test_name}: {'PASS' if result.success else 'FAIL'}")
    
    def _validate_database_migration(self):
        """验证数据库迁移脚本"""
        logger.info("验证数据库迁移脚本...")
        
        start_time = time.time()
        migration_file = self.base_path / self.key_files["database_migration"]
        
        if not migration_file.exists():
            self.results.append(TestResult(
                test_name="数据库迁移脚本验证",
                success=False,
                message="迁移脚本文件不存在",
                execution_time=time.time() - start_time
            ))
            return
        
        try:
            content = migration_file.read_text(encoding='utf-8')
            
            # 检查关键SQL语句
            required_elements = [
                "ALTER TABLE `t_alert_rules`",
                "rule_category",
                "condition_expression",
                "time_window_seconds",
                "priority_level",
                "enabled_channels",
                "CREATE TABLE `t_alert_cache_sync`",
                "CREATE TABLE `t_alert_rule_performance`"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                result = TestResult(
                    test_name="数据库迁移脚本验证",
                    success=True,
                    message="迁移脚本包含所有必要的表结构变更",
                    details={
                        "file_size": len(content),
                        "required_elements": required_elements
                    },
                    execution_time=time.time() - start_time
                )
            else:
                result = TestResult(
                    test_name="数据库迁移脚本验证", 
                    success=False,
                    message=f"迁移脚本缺少必要元素: {missing_elements}",
                    details={"missing_elements": missing_elements},
                    execution_time=time.time() - start_time
                )
                
            self.results.append(result)
            
        except Exception as e:
            self.results.append(TestResult(
                test_name="数据库迁移脚本验证",
                success=False,
                message=f"读取迁移脚本失败: {str(e)}",
                execution_time=time.time() - start_time
            ))
        
        logger.info(f"✓ 数据库迁移脚本验证: {'PASS' if self.results[-1].success else 'FAIL'}")
    
    def _validate_backend_services(self):
        """验证后端服务实现"""
        logger.info("验证后端服务实现...")
        
        service_validations = [
            ("AlertRuleEngineService", "alert_rule_engine", [
                "evaluateRules",
                "getCachedRules", 
                "compileRules",
                "getCacheStats"
            ]),
            ("AlertRulesCacheManager", "cache_manager", [
                "updateAlertRulesCache",
                "batchUpdateCache",
                "healthCheck"
            ]),
            ("UnifiedMessagePublisher", "message_publisher", [
                "publishAlert",
                "buildUnifiedMessage",
                "routeChannels",
                "getMessageStats"
            ]),
            ("AlertPerformanceController", "performance_controller", [
                "getPerformanceStats",
                "getCacheHealth",
                "clearAllCache",
                "getSystemLoad"
            ])
        ]
        
        for service_name, file_key, required_methods in service_validations:
            self._validate_java_service(service_name, file_key, required_methods)
    
    def _validate_java_service(self, service_name: str, file_key: str, required_methods: List[str]):
        """验证Java服务实现"""
        start_time = time.time()
        
        service_file = self.base_path / self.key_files[file_key]
        
        if not service_file.exists():
            self.results.append(TestResult(
                test_name=f"Java服务验证: {service_name}",
                success=False,
                message=f"服务文件不存在: {service_file}",
                execution_time=time.time() - start_time
            ))
            return
        
        try:
            content = service_file.read_text(encoding='utf-8')
            
            # 检查类定义
            class_patterns = [
                f"class {service_name}",
                f"public class {service_name}"
            ]
            
            has_class = any(pattern in content for pattern in class_patterns)
            if not has_class:
                self.results.append(TestResult(
                    test_name=f"Java服务验证: {service_name}",
                    success=False,
                    message=f"未找到类定义: {service_name}",
                    execution_time=time.time() - start_time
                ))
                return
            
            # 检查必要方法
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            # 检查注解
            required_annotations = ["@Service", "@Component", "@RestController"]
            has_annotation = any(annotation in content for annotation in required_annotations)
            
            success = not missing_methods and has_annotation
            message = "服务实现验证通过"
            
            if missing_methods:
                message = f"缺少方法: {missing_methods}"
            elif not has_annotation:
                message = "缺少Spring注解"
            
            result = TestResult(
                test_name=f"Java服务验证: {service_name}",
                success=success,
                message=message,
                details={
                    "file_size": len(content),
                    "missing_methods": missing_methods,
                    "has_spring_annotation": has_annotation
                },
                execution_time=time.time() - start_time
            )
            
            self.results.append(result)
            
        except Exception as e:
            self.results.append(TestResult(
                test_name=f"Java服务验证: {service_name}",
                success=False,
                message=f"验证失败: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_frontend_components(self):
        """验证前端组件实现"""
        logger.info("验证前端组件实现...")
        
        # Python组件验证
        python_components = [
            ("AlertRulesCacheSubscriber", "cache_subscriber", [
                "start_subscriber",
                "get_alert_rules", 
                "get_cache_stats",
                "health_check"
            ]),
            ("HighPerformanceAlertGenerator", "high_performance_generator", [
                "start_workers",
                "submit_health_data",
                "get_performance_stats"
            ])
        ]
        
        for component_name, file_key, required_methods in python_components:
            self._validate_python_component(component_name, file_key, required_methods)
        
        # Vue组件验证
        vue_components = [
            ("AlertRuleWizard", "alert_rule_wizard", [
                "currentStep",
                "ruleConfig",
                "saveRule",
                "nextStep",
                "previousStep"
            ]),
            ("AlertRulesManagement", "rules_management", [
                "rulesList",
                "searchRules",
                "loadRulesList",
                "toggleRuleStatus"
            ]),
            ("AlertPerformanceDashboard", "performance_dashboard", [
                "performanceData",
                "loadPerformanceData",
                "initCharts",
                "refreshData"
            ])
        ]
        
        for component_name, file_key, required_elements in vue_components:
            self._validate_vue_component(component_name, file_key, required_elements)
    
    def _validate_python_component(self, component_name: str, file_key: str, required_methods: List[str]):
        """验证Python组件实现"""
        start_time = time.time()
        
        component_file = self.base_path / self.key_files[file_key]
        
        if not component_file.exists():
            self.results.append(TestResult(
                test_name=f"Python组件验证: {component_name}",
                success=False,
                message=f"组件文件不存在: {component_file}",
                execution_time=time.time() - start_time
            ))
            return
        
        try:
            content = component_file.read_text(encoding='utf-8')
            
            # 检查类定义
            has_class = f"class {component_name}" in content
            if not has_class:
                self.results.append(TestResult(
                    test_name=f"Python组件验证: {component_name}",
                    success=False,
                    message=f"未找到类定义: {component_name}",
                    execution_time=time.time() - start_time
                ))
                return
            
            # 检查必要方法
            missing_methods = []
            for method in required_methods:
                if f"def {method}" not in content:
                    missing_methods.append(method)
            
            success = not missing_methods
            message = "Python组件实现验证通过" if success else f"缺少方法: {missing_methods}"
            
            result = TestResult(
                test_name=f"Python组件验证: {component_name}",
                success=success,
                message=message,
                details={
                    "file_size": len(content),
                    "missing_methods": missing_methods
                },
                execution_time=time.time() - start_time
            )
            
            self.results.append(result)
            
        except Exception as e:
            self.results.append(TestResult(
                test_name=f"Python组件验证: {component_name}",
                success=False,
                message=f"验证失败: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_vue_component(self, component_name: str, file_key: str, required_elements: List[str]):
        """验证Vue组件实现"""
        start_time = time.time()
        
        component_file = self.base_path / self.key_files[file_key]
        
        if not component_file.exists():
            self.results.append(TestResult(
                test_name=f"Vue组件验证: {component_name}",
                success=False,
                message=f"组件文件不存在: {component_file}",
                execution_time=time.time() - start_time
            ))
            return
        
        try:
            content = component_file.read_text(encoding='utf-8')
            
            # 检查Vue组件结构
            has_template = "<template>" in content
            has_script = "<script" in content
            has_style = "<style" in content or "scoped" in content
            
            if not (has_template and has_script):
                self.results.append(TestResult(
                    test_name=f"Vue组件验证: {component_name}",
                    success=False,
                    message="Vue组件缺少基本结构(template/script)",
                    execution_time=time.time() - start_time
                ))
                return
            
            # 检查必要元素
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            success = not missing_elements
            message = "Vue组件实现验证通过" if success else f"缺少元素: {missing_elements}"
            
            result = TestResult(
                test_name=f"Vue组件验证: {component_name}",
                success=success,
                message=message,
                details={
                    "file_size": len(content),
                    "has_template": has_template,
                    "has_script": has_script,
                    "has_style": has_style,
                    "missing_elements": missing_elements
                },
                execution_time=time.time() - start_time
            )
            
            self.results.append(result)
            
        except Exception as e:
            self.results.append(TestResult(
                test_name=f"Vue组件验证: {component_name}",
                success=False,
                message=f"验证失败: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_api_endpoints(self):
        """验证API接口定义"""
        logger.info("验证API接口定义...")
        
        start_time = time.time()
        
        # 检查性能监控控制器的API端点
        controller_file = self.base_path / self.key_files["performance_controller"]
        
        if not controller_file.exists():
            self.results.append(TestResult(
                test_name="API接口验证",
                success=False,
                message="性能监控控制器文件不存在",
                execution_time=time.time() - start_time
            ))
            return
        
        try:
            content = controller_file.read_text(encoding='utf-8')
            
            # 检查必要的API端点
            required_endpoints = [
                "@GetMapping(\"/performance/stats\")",
                "@GetMapping(\"/cache/health\")",
                "@DeleteMapping(\"/cache/all\")",
                "@GetMapping(\"/system/load\")",
                "@GetMapping(\"/threadpool/status\")"
            ]
            
            missing_endpoints = []
            for endpoint in required_endpoints:
                if endpoint not in content:
                    missing_endpoints.append(endpoint)
            
            success = not missing_endpoints
            message = "API接口定义验证通过" if success else f"缺少端点: {missing_endpoints}"
            
            result = TestResult(
                test_name="API接口验证",
                success=success,
                message=message,
                details={
                    "missing_endpoints": missing_endpoints,
                    "total_endpoints": len(required_endpoints)
                },
                execution_time=time.time() - start_time
            )
            
            self.results.append(result)
            
        except Exception as e:
            self.results.append(TestResult(
                test_name="API接口验证",
                success=False,
                message=f"验证失败: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_configuration(self):
        """验证配置完整性"""
        logger.info("验证配置完整性...")
        
        start_time = time.time()
        
        # 检查ljwx-bigscreen的缓存订阅器配置
        cache_subscriber_file = self.base_path / self.key_files["cache_subscriber"]
        
        config_checks = []
        
        if cache_subscriber_file.exists():
            try:
                content = cache_subscriber_file.read_text(encoding='utf-8')
                
                # 检查Redis配置
                redis_configs = [
                    "redis_bigscreen",
                    "redis_boot", 
                    "db=0",
                    "db=1",
                    "alert_rules_channel"
                ]
                
                missing_configs = [config for config in redis_configs if config not in content]
                
                config_checks.append({
                    "component": "缓存订阅器Redis配置",
                    "success": not missing_configs,
                    "details": {"missing": missing_configs}
                })
                
            except Exception as e:
                config_checks.append({
                    "component": "缓存订阅器配置",
                    "success": False,
                    "details": {"error": str(e)}
                })
        
        # 汇总配置验证结果
        all_success = all(check["success"] for check in config_checks)
        
        result = TestResult(
            test_name="配置完整性验证",
            success=all_success,
            message="配置验证通过" if all_success else "存在配置问题",
            details={"checks": config_checks},
            execution_time=time.time() - start_time
        )
        
        self.results.append(result)
    
    def _validate_performance_monitoring(self):
        """验证性能监控实现"""
        logger.info("验证性能监控实现...")
        
        start_time = time.time()
        
        # 检查性能监控相关文件
        monitoring_files = [
            ("性能监控控制器", "performance_controller"),
            ("性能监控面板", "performance_dashboard"),
            ("缓存性能监控", "cache_subscriber")
        ]
        
        monitoring_results = []
        
        for monitor_name, file_key in monitoring_files:
            file_path = self.base_path / self.key_files[file_key]
            
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # 根据文件类型检查不同的性能监控元素
                    if "Controller" in monitor_name:
                        # Java控制器检查
                        required_elements = ["getCacheStats", "getSystemLoad", "getPerformanceStats"]
                    elif "面板" in monitor_name:
                        # Vue面板检查
                        required_elements = ["performance_stats", "loadPerformanceData", "echarts"]
                    else:
                        # Python组件检查
                        required_elements = ["get_cache_stats", "performance_stats", "hit_rate"]
                    
                    missing_elements = [elem for elem in required_elements if elem not in content]
                    
                    monitoring_results.append({
                        "monitor": monitor_name,
                        "success": not missing_elements,
                        "missing": missing_elements
                    })
                    
                except Exception as e:
                    monitoring_results.append({
                        "monitor": monitor_name,
                        "success": False,
                        "error": str(e)
                    })
            else:
                monitoring_results.append({
                    "monitor": monitor_name,
                    "success": False,
                    "missing_file": True
                })
        
        all_success = all(result["success"] for result in monitoring_results)
        
        result = TestResult(
            test_name="性能监控实现验证",
            success=all_success,
            message="性能监控实现验证通过" if all_success else "性能监控实现存在问题",
            details={"monitoring_results": monitoring_results},
            execution_time=time.time() - start_time
        )
        
        self.results.append(result)
    
    def _generate_validation_report(self) -> ValidationReport:
        """生成验证报告"""
        logger.info("生成验证报告...")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - passed_tests
        overall_success = failed_tests == 0
        execution_time = time.time() - self.start_time
        
        # 生成建议
        recommendations = []
        
        if failed_tests > 0:
            recommendations.append(f"共有 {failed_tests} 个测试失败，需要修复相关问题")
            
            # 分析失败原因并给出具体建议
            file_not_found_count = sum(1 for result in self.results 
                                     if not result.success and "不存在" in result.message)
            
            if file_not_found_count > 0:
                recommendations.append(f"有 {file_not_found_count} 个文件缺失，请检查实施完整性")
            
            missing_methods_count = sum(1 for result in self.results 
                                      if not result.success and "缺少" in result.message)
            
            if missing_methods_count > 0:
                recommendations.append(f"有 {missing_methods_count} 个组件缺少必要方法，请完善实现")
        
        if overall_success:
            recommendations.append("所有核心组件实施完成，可以进行下一步测试")
            recommendations.append("建议进行性能测试和端到端集成测试")
        else:
            recommendations.append("请先修复失败的测试项，再进行后续步骤")
        
        report = ValidationReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            test_results=self.results,
            overall_success=overall_success,
            execution_time=execution_time,
            recommendations=recommendations
        )
        
        return report
    
    def print_detailed_report(self, report: ValidationReport):
        """打印详细报告"""
        print("\n" + "="*80)
        print("告警规则系统实施验证报告")
        print("="*80)
        
        print(f"\n📊 测试概览:")
        print(f"   总测试数: {report.total_tests}")
        print(f"   通过测试: {report.passed_tests}")
        print(f"   失败测试: {report.failed_tests}")
        print(f"   成功率: {report.passed_tests/report.total_tests*100:.1f}%")
        print(f"   执行时间: {report.execution_time:.2f}秒")
        print(f"   整体状态: {'✅ 成功' if report.overall_success else '❌ 失败'}")
        
        print(f"\n📋 详细测试结果:")
        for i, result in enumerate(report.test_results, 1):
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"   {i:2d}. {result.test_name}: {status}")
            print(f"       消息: {result.message}")
            print(f"       耗时: {result.execution_time:.3f}秒")
            if result.details:
                print(f"       详情: {json.dumps(result.details, ensure_ascii=False, indent=8)}")
        
        print(f"\n💡 建议:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"   {i}. {recommendation}")
        
        print("\n" + "="*80)
        
    def save_report_to_file(self, report: ValidationReport, output_file: str = None):
        """保存报告到文件"""
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"alert_rules_validation_report_{timestamp}.json"
        
        output_path = self.base_path / output_file
        
        # 转换为可序列化的字典
        report_dict = asdict(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"验证报告已保存到: {output_path}")
        return output_path

def main():
    """主函数"""
    print("🚀 开始告警规则系统实施完整性验证...")
    
    # 创建验证器
    validator = AlertRulesImplementationValidator()
    
    try:
        # 运行验证
        report = validator.run_comprehensive_validation()
        
        # 打印报告
        validator.print_detailed_report(report)
        
        # 保存报告
        report_file = validator.save_report_to_file(report)
        
        # 返回状态码
        sys.exit(0 if report.overall_success else 1)
        
    except Exception as e:
        logger.error(f"验证过程发生异常: {e}")
        print(f"❌ 验证失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()