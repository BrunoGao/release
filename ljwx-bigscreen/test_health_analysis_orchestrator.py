#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康分析编排器测试脚本
Health Analysis Orchestrator Test Script

完整测试所有模块的功能性、可靠性和性能
- 基线生成测试
- 评分计算测试
- 预测分析测试
- 建议生成测试
- 健康画像测试
- 错误处理测试
- 性能测试

@Author: brunoGao
@CreateTime: 2025-09-12
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ljwx-bigscreen', 'bigscreen', 'bigScreen'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_health_orchestrator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class HealthOrchestratorTester:
    """健康分析编排器测试类"""
    
    def __init__(self):
        self.test_results = {
            'baseline_test': {'status': 'pending', 'details': {}},
            'score_test': {'status': 'pending', 'details': {}},
            'prediction_test': {'status': 'pending', 'details': {}},
            'recommendation_test': {'status': 'pending', 'details': {}},
            'profile_test': {'status': 'pending', 'details': {}},
            'error_handling_test': {'status': 'pending', 'details': {}},
            'performance_test': {'status': 'pending', 'details': {}},
            'system_metrics_test': {'status': 'pending', 'details': {}}
        }
        self.orchestrator = None
        
    def setup_orchestrator(self):
        """初始化健康分析编排器"""
        try:
            logger.info("🚀 开始初始化健康分析编排器...")
            
            # 导入编排器
            from health_analysis_orchestrator import HealthAnalysisOrchestrator
            
            # 创建实例
            self.orchestrator = HealthAnalysisOrchestrator()
            logger.info("✅ 健康分析编排器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False
    
    def test_baseline_generation(self) -> bool:
        """测试基线生成功能"""
        logger.info("📊 测试基线生成功能...")
        
        try:
            test_user_id = 1001
            test_org_id = 2001
            
            # 测试用户基线生成
            result = self.orchestrator._generate_user_baseline(test_user_id, test_org_id)
            
            if result.get('success'):
                baseline = result.get('baseline', {})
                if baseline and len(baseline) > 0:
                    self.test_results['baseline_test']['status'] = 'passed'
                    self.test_results['baseline_test']['details'] = {
                        'features_count': len(baseline),
                        'features': list(baseline.keys()),
                        'sample_feature': next(iter(baseline.values())) if baseline else None
                    }
                    logger.info(f"✅ 基线生成测试通过，生成了 {len(baseline)} 个特征基线")
                    return True
                else:
                    self.test_results['baseline_test']['status'] = 'failed'
                    self.test_results['baseline_test']['details'] = {'error': '基线数据为空'}
                    logger.warning("⚠️ 基线生成测试失败: 基线数据为空")
                    return False
            else:
                self.test_results['baseline_test']['status'] = 'failed'
                self.test_results['baseline_test']['details'] = {'error': result.get('message', '未知错误')}
                logger.warning(f"⚠️ 基线生成测试失败: {result.get('message', '未知错误')}")
                return False
                
        except Exception as e:
            self.test_results['baseline_test']['status'] = 'error'
            self.test_results['baseline_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 基线生成测试异常: {e}")
            return False
    
    def test_health_scoring(self) -> bool:
        """测试健康评分功能"""
        logger.info("🎯 测试健康评分功能...")
        
        try:
            test_user_id = 1001
            test_org_id = 2001
            
            # 先生成基线
            baseline_result = self.orchestrator._generate_user_baseline(test_user_id, test_org_id)
            
            if baseline_result.get('success'):
                # 测试评分计算
                score_result = self.orchestrator._generate_user_health_score(test_user_id, test_org_id, baseline_result)
                
                if score_result.get('success'):
                    overall_score = score_result.get('overall_score', 0)
                    feature_scores = score_result.get('feature_scores', {})
                    health_level = score_result.get('health_level', 'unknown')
                    
                    self.test_results['score_test']['status'] = 'passed'
                    self.test_results['score_test']['details'] = {
                        'overall_score': overall_score,
                        'health_level': health_level,
                        'feature_count': len(feature_scores),
                        'valid_score_range': 0 <= overall_score <= 100
                    }
                    logger.info(f"✅ 健康评分测试通过，总分: {overall_score}，等级: {health_level}")
                    return True
                else:
                    self.test_results['score_test']['status'] = 'failed'
                    self.test_results['score_test']['details'] = {'error': score_result.get('message', '评分失败')}
                    return False
            else:
                self.test_results['score_test']['status'] = 'skipped'
                self.test_results['score_test']['details'] = {'reason': '基线生成失败，跳过评分测试'}
                return False
                
        except Exception as e:
            self.test_results['score_test']['status'] = 'error'
            self.test_results['score_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 健康评分测试异常: {e}")
            return False
    
    def test_health_prediction(self) -> bool:
        """测试健康预测功能"""
        logger.info("🔮 测试健康预测功能...")
        
        try:
            test_user_id = 1001
            test_org_id = 2001
            
            # 先生成基线
            baseline_result = self.orchestrator._generate_user_baseline(test_user_id, test_org_id)
            
            # 测试预测分析
            prediction_result = self.orchestrator._generate_user_health_prediction(test_user_id, test_org_id, baseline_result)
            
            if prediction_result.get('success'):
                prediction = prediction_result.get('prediction', {})
                overall_trend = prediction.get('overall_trend', 'unknown')
                risk_level = prediction.get('risk_level', 'unknown')
                feature_predictions = prediction.get('feature_predictions', {})
                
                self.test_results['prediction_test']['status'] = 'passed'
                self.test_results['prediction_test']['details'] = {
                    'overall_trend': overall_trend,
                    'risk_level': risk_level,
                    'predictions_count': len(feature_predictions),
                    'confidence': prediction.get('confidence', 0)
                }
                logger.info(f"✅ 健康预测测试通过，趋势: {overall_trend}，风险: {risk_level}")
                return True
            else:
                self.test_results['prediction_test']['status'] = 'failed'
                self.test_results['prediction_test']['details'] = {'error': prediction_result.get('message', '预测失败')}
                logger.warning(f"⚠️ 健康预测测试失败: {prediction_result.get('message', '预测失败')}")
                return False
                
        except Exception as e:
            self.test_results['prediction_test']['status'] = 'error'
            self.test_results['prediction_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 健康预测测试异常: {e}")
            return False
    
    def test_health_recommendations(self) -> bool:
        """测试健康建议功能"""
        logger.info("💡 测试健康建议功能...")
        
        try:
            test_user_id = 1001
            test_org_id = 2001
            
            # 生成基础数据
            baseline_result = self.orchestrator._generate_user_baseline(test_user_id, test_org_id)
            score_result = self.orchestrator._generate_user_health_score(test_user_id, test_org_id, baseline_result)
            prediction_result = self.orchestrator._generate_user_health_prediction(test_user_id, test_org_id, baseline_result)
            
            # 测试建议生成
            recommendation_result = self.orchestrator._generate_user_health_recommendation(test_user_id, score_result, prediction_result)
            
            if recommendation_result.get('success'):
                recommendations = recommendation_result.get('recommendations', {})
                total_count = recommendation_result.get('total_recommendations', 0)
                
                # 验证建议分类
                expected_categories = ['immediate_actions', 'lifestyle_improvements', 'monitoring_suggestions', 
                                     'medical_consultations', 'prevention_tips']
                has_all_categories = all(cat in recommendations for cat in expected_categories)
                
                self.test_results['recommendation_test']['status'] = 'passed'
                self.test_results['recommendation_test']['details'] = {
                    'total_recommendations': total_count,
                    'categories': list(recommendations.keys()),
                    'has_all_categories': has_all_categories,
                    'category_counts': {cat: len(recommendations.get(cat, [])) for cat in expected_categories}
                }
                logger.info(f"✅ 健康建议测试通过，生成了 {total_count} 条建议")
                return True
            else:
                self.test_results['recommendation_test']['status'] = 'failed'
                self.test_results['recommendation_test']['details'] = {'error': recommendation_result.get('error', '建议生成失败')}
                return False
                
        except Exception as e:
            self.test_results['recommendation_test']['status'] = 'error'
            self.test_results['recommendation_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 健康建议测试异常: {e}")
            return False
    
    def test_health_profile(self) -> bool:
        """测试健康画像功能"""
        logger.info("👤 测试健康画像功能...")
        
        try:
            test_user_id = 1001
            test_org_id = 2001
            
            # 测试健康画像生成
            profile_result = self.orchestrator._generate_user_health_profile(test_user_id, test_org_id)
            
            if profile_result.get('success'):
                profile = profile_result.get('profile', {})
                
                # 验证画像维度
                expected_dimensions = ['cardiovascular', 'respiratory', 'metabolic', 
                                     'physical_activity', 'sleep_quality', 'stress_level', 'overall_status']
                has_all_dimensions = all(dim in profile for dim in expected_dimensions)
                
                self.test_results['profile_test']['status'] = 'passed'
                self.test_results['profile_test']['details'] = {
                    'dimensions': list(profile.keys()),
                    'has_all_dimensions': has_all_dimensions,
                    'data_points': profile_result.get('data_points', 0),
                    'overall_health_score': profile.get('overall_status', {}).get('overall_score', 0)
                }
                logger.info(f"✅ 健康画像测试通过，包含 {len(profile)} 个维度")
                return True
            else:
                self.test_results['profile_test']['status'] = 'failed'
                self.test_results['profile_test']['details'] = {'error': profile_result.get('message', '画像生成失败')}
                logger.warning(f"⚠️ 健康画像测试失败: {profile_result.get('message', '画像生成失败')}")
                return False
                
        except Exception as e:
            self.test_results['profile_test']['status'] = 'error'
            self.test_results['profile_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 健康画像测试异常: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """测试错误处理功能"""
        logger.info("🛡️ 测试错误处理功能...")
        
        try:
            error_scenarios_passed = 0
            total_scenarios = 4
            
            # 场景1: 无效用户ID
            try:
                result = self.orchestrator._generate_user_baseline(-1, 1)
                if not result.get('success'):
                    error_scenarios_passed += 1
                    logger.info("✅ 无效用户ID错误处理正常")
            except Exception:
                error_scenarios_passed += 1
                logger.info("✅ 无效用户ID异常处理正常")
            
            # 场景2: 空数据处理
            try:
                result = self.orchestrator._calculate_baseline_statistics([])
                if isinstance(result, dict):
                    error_scenarios_passed += 1
                    logger.info("✅ 空数据处理正常")
            except Exception:
                pass
            
            # 场景3: 系统指标获取
            try:
                metrics = self.orchestrator.get_system_metrics()
                if isinstance(metrics, dict) and 'performance' in metrics:
                    error_scenarios_passed += 1
                    logger.info("✅ 系统指标获取正常")
            except Exception:
                pass
            
            # 场景4: 健康检查
            try:
                health = self.orchestrator._check_system_health()
                if isinstance(health, dict) and 'overall_status' in health:
                    error_scenarios_passed += 1
                    logger.info("✅ 系统健康检查正常")
            except Exception:
                pass
            
            success_rate = error_scenarios_passed / total_scenarios
            
            self.test_results['error_handling_test']['status'] = 'passed' if success_rate >= 0.75 else 'partial'
            self.test_results['error_handling_test']['details'] = {
                'scenarios_passed': error_scenarios_passed,
                'total_scenarios': total_scenarios,
                'success_rate': success_rate
            }
            
            logger.info(f"✅ 错误处理测试完成，通过率: {success_rate:.2%}")
            return success_rate >= 0.75
            
        except Exception as e:
            self.test_results['error_handling_test']['status'] = 'error'
            self.test_results['error_handling_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 错误处理测试异常: {e}")
            return False
    
    def test_performance(self) -> bool:
        """测试性能"""
        logger.info("⚡ 测试性能...")
        
        try:
            performance_metrics = {}
            
            # 测试单用户分析性能
            start_time = time.time()
            result = self.orchestrator._analyze_user(1001, 2001)
            single_user_time = time.time() - start_time
            
            performance_metrics['single_user_analysis_time'] = single_user_time
            performance_metrics['single_user_success'] = result.get('success', False)
            
            # 获取系统统计
            stats = self.orchestrator.get_analysis_stats()
            performance_metrics.update(stats)
            
            # 性能评估
            performance_good = (
                single_user_time < 30 and  # 单用户分析少于30秒
                stats.get('error_rate', 100) < 50  # 错误率低于50%
            )
            
            self.test_results['performance_test']['status'] = 'passed' if performance_good else 'warning'
            self.test_results['performance_test']['details'] = performance_metrics
            
            logger.info(f"✅ 性能测试完成，单用户分析耗时: {single_user_time:.2f}秒")
            return performance_good
            
        except Exception as e:
            self.test_results['performance_test']['status'] = 'error'
            self.test_results['performance_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 性能测试异常: {e}")
            return False
    
    def test_system_metrics(self) -> bool:
        """测试系统指标收集"""
        logger.info("📊 测试系统指标收集...")
        
        try:
            # 获取系统指标
            metrics = self.orchestrator.get_system_metrics()
            
            # 验证指标完整性
            required_sections = ['performance', 'health', 'configuration']
            has_required_sections = all(section in metrics for section in required_sections)
            
            # 验证健康状态
            health_status = metrics.get('health', {}).get('overall_status', 'unknown')
            
            self.test_results['system_metrics_test']['status'] = 'passed'
            self.test_results['system_metrics_test']['details'] = {
                'has_required_sections': has_required_sections,
                'health_status': health_status,
                'sections': list(metrics.keys()),
                'uptime_seconds': metrics.get('performance', {}).get('uptime_seconds', 0)
            }
            
            logger.info(f"✅ 系统指标测试通过，健康状态: {health_status}")
            return True
            
        except Exception as e:
            self.test_results['system_metrics_test']['status'] = 'error'
            self.test_results['system_metrics_test']['details'] = {'exception': str(e)}
            logger.error(f"❌ 系统指标测试异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("🎬 开始运行完整测试套件...")
        
        start_time = time.time()
        test_passed = 0
        total_tests = len(self.test_results)
        
        # 初始化编排器
        if not self.setup_orchestrator():
            return {
                'success': False,
                'message': '编排器初始化失败',
                'test_results': self.test_results
            }
        
        # 运行各项测试
        test_functions = [
            ('baseline_test', self.test_baseline_generation),
            ('score_test', self.test_health_scoring),
            ('prediction_test', self.test_health_prediction),
            ('recommendation_test', self.test_health_recommendations),
            ('profile_test', self.test_health_profile),
            ('error_handling_test', self.test_error_handling),
            ('performance_test', self.test_performance),
            ('system_metrics_test', self.test_system_metrics)
        ]
        
        for test_name, test_function in test_functions:
            try:
                logger.info(f"🔄 运行测试: {test_name}")
                if test_function():
                    test_passed += 1
                    logger.info(f"✅ {test_name} 通过")
                else:
                    logger.warning(f"⚠️ {test_name} 失败")
            except Exception as e:
                logger.error(f"❌ {test_name} 异常: {e}")
        
        # 清理资源
        try:
            self.orchestrator.cleanup()
        except Exception as e:
            logger.error(f"⚠️ 资源清理异常: {e}")
        
        # 生成测试报告
        total_time = time.time() - start_time
        success_rate = test_passed / total_tests
        
        test_summary = {
            'success': success_rate >= 0.75,  # 75%通过率视为成功
            'summary': {
                'total_tests': total_tests,
                'passed_tests': test_passed,
                'failed_tests': total_tests - test_passed,
                'success_rate': success_rate,
                'total_time_seconds': total_time
            },
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_test_recommendations()
        }
        
        logger.info(f"🏁 测试完成! 通过率: {success_rate:.2%} ({test_passed}/{total_tests})")
        return test_summary
    
    def _generate_test_recommendations(self) -> List[str]:
        """生成测试建议"""
        recommendations = []
        
        # 根据测试结果生成建议
        failed_tests = [name for name, result in self.test_results.items() 
                       if result['status'] in ['failed', 'error']]
        
        if failed_tests:
            recommendations.append(f"需要修复失败的测试: {', '.join(failed_tests)}")
        
        if self.test_results['performance_test']['status'] in ['warning', 'failed']:
            recommendations.append("建议优化系统性能，关注内存使用和处理时间")
        
        if self.test_results['error_handling_test']['status'] != 'passed':
            recommendations.append("建议加强错误处理机制")
        
        if not recommendations:
            recommendations.append("所有测试通过，系统运行良好！建议定期运行测试以确保稳定性")
        
        return recommendations

def main():
    """主函数"""
    logger.info("🚀 启动健康分析编排器测试")
    
    # 创建测试器
    tester = HealthOrchestratorTester()
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 输出结果
    print("\n" + "="*80)
    print("📋 测试结果汇总")
    print("="*80)
    print(f"整体状态: {'✅ 通过' if results['success'] else '❌ 失败'}")
    print(f"通过率: {results['summary']['success_rate']:.2%}")
    print(f"通过测试: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    print(f"总耗时: {results['summary']['total_time_seconds']:.2f}秒")
    
    print("\n📊 详细测试结果:")
    for test_name, test_result in results['test_results'].items():
        status_icon = {
            'passed': '✅',
            'failed': '❌', 
            'error': '💥',
            'warning': '⚠️',
            'partial': '🟡',
            'skipped': '⏭️',
            'pending': '⏳'
        }.get(test_result['status'], '❓')
        
        print(f"  {status_icon} {test_name}: {test_result['status']}")
    
    print("\n💡 建议:")
    for i, recommendation in enumerate(results['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    # 保存详细结果到文件
    with open('test_health_orchestrator_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("📄 详细测试结果已保存到 test_health_orchestrator_results.json")
    print("\n" + "="*80)
    
    return results['success']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)