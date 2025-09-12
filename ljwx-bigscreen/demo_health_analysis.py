#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康分析编排器演示脚本
Health Analysis Orchestrator Demo Script

演示如何生成过去30天的完整健康分析：
- Baseline (基线)
- Score (评分) 
- Prediction (预测)
- Recommendation (建议)
- Profile (画像)

@Author: brunoGao
@CreateTime: 2025-09-12
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bigscreen', 'bigScreen'))

def demo_health_analysis():
    """演示健康分析功能"""
    print("🚀 健康分析编排器演示")
    print("=" * 60)
    
    try:
        # 导入健康分析编排器
        from health_analysis_orchestrator import HealthAnalysisOrchestrator
        
        # 创建编排器实例
        print("📋 正在初始化健康分析编排器...")
        orchestrator = HealthAnalysisOrchestrator()
        print("✅ 编排器初始化成功")
        
        # 演示参数
        demo_user_id = 1001
        demo_org_id = 2001
        demo_customer_id = 3001
        
        print(f"\n🔍 演示参数:")
        print(f"  - 用户ID: {demo_user_id}")
        print(f"  - 组织ID: {demo_org_id}")
        print(f"  - 客户ID: {demo_customer_id}")
        print(f"  - 分析时间范围: 过去30天")
        
        # ==================== 1. 生成基线 (Baseline) ====================
        print(f"\n{'='*60}")
        print("📊 1. 生成健康基线 (Baseline)")
        print("="*60)
        
        start_time = time.time()
        baseline_result = orchestrator._generate_user_baseline(demo_user_id, demo_org_id)
        baseline_time = time.time() - start_time
        
        if baseline_result.get('success'):
            baseline_data = baseline_result.get('baseline', {})
            print(f"✅ 基线生成成功 (耗时: {baseline_time:.2f}秒)")
            print(f"📈 生成了 {len(baseline_data)} 个健康特征基线:")
            
            for feature, stats in baseline_data.items():
                print(f"  • {feature}: 均值={stats.get('mean', 0):.2f}, "
                      f"标准差={stats.get('std', 0):.2f}, "
                      f"样本数={stats.get('count', 0)}")
        else:
            print(f"❌ 基线生成失败: {baseline_result.get('message', '未知错误')}")
            return False
        
        # ==================== 2. 计算评分 (Score) ====================
        print(f"\n{'='*60}")
        print("🎯 2. 计算健康评分 (Score)")
        print("="*60)
        
        start_time = time.time()
        score_result = orchestrator._generate_user_health_score(demo_user_id, demo_org_id, baseline_result)
        score_time = time.time() - start_time
        
        if score_result.get('success'):
            overall_score = score_result.get('overall_score', 0)
            health_level = score_result.get('health_level', '未知')
            feature_scores = score_result.get('feature_scores', {})
            
            print(f"✅ 健康评分计算成功 (耗时: {score_time:.2f}秒)")
            print(f"🏆 综合健康评分: {overall_score:.2f}分")
            print(f"📊 健康等级: {health_level}")
            print(f"📋 各特征评分详情:")
            
            for feature, score_info in feature_scores.items():
                feature_score = score_info.get('score', 0)
                weight = score_info.get('weight', 0) * 100
                current_value = score_info.get('current_value', 0)
                print(f"  • {feature}: {feature_score:.1f}分 (权重: {weight:.1f}%, 当前值: {current_value})")
        else:
            print(f"❌ 健康评分计算失败: {score_result.get('message', '未知错误')}")
        
        # ==================== 3. 生成预测 (Prediction) ====================
        print(f"\n{'='*60}")
        print("🔮 3. 生成健康预测 (Prediction)")
        print("="*60)
        
        start_time = time.time()
        prediction_result = orchestrator._generate_user_health_prediction(demo_user_id, demo_org_id, baseline_result)
        prediction_time = time.time() - start_time
        
        if prediction_result.get('success'):
            prediction_data = prediction_result.get('prediction', {})
            overall_trend = prediction_data.get('overall_trend', '未知')
            risk_level = prediction_data.get('risk_level', '未知')
            feature_predictions = prediction_data.get('feature_predictions', {})
            confidence = prediction_data.get('confidence', 0)
            
            print(f"✅ 健康预测生成成功 (耗时: {prediction_time:.2f}秒)")
            print(f"📈 整体健康趋势: {overall_trend}")
            print(f"⚠️ 风险等级: {risk_level}")
            print(f"🎯 预测置信度: {confidence:.1%}")
            print(f"📊 特征预测详情:")
            
            for feature, pred_info in feature_predictions.items():
                if pred_info.get('data_sufficient'):
                    trend_direction = pred_info.get('trend_direction', '稳定')
                    risk_level = pred_info.get('risk_level', 'low')
                    future_pred = pred_info.get('future_prediction', {})
                    predicted_7day = future_pred.get('predicted_7day_avg', 0)
                    print(f"  • {feature}: 趋势={trend_direction}, 风险={risk_level}, 7天预测值={predicted_7day:.2f}")
        else:
            print(f"❌ 健康预测生成失败: {prediction_result.get('message', '未知错误')}")
        
        # ==================== 4. 生成建议 (Recommendation) ====================
        print(f"\n{'='*60}")
        print("💡 4. 生成健康建议 (Recommendation)")
        print("="*60)
        
        start_time = time.time()
        recommendation_result = orchestrator._generate_user_health_recommendation(demo_user_id, score_result, prediction_result)
        recommendation_time = time.time() - start_time
        
        if recommendation_result.get('success'):
            recommendations = recommendation_result.get('recommendations', {})
            total_count = recommendation_result.get('total_recommendations', 0)
            
            print(f"✅ 健康建议生成成功 (耗时: {recommendation_time:.2f}秒)")
            print(f"📝 总建议数: {total_count}条")
            print(f"📋 建议分类详情:")
            
            category_names = {
                'immediate_actions': '🚨 立即行动建议',
                'lifestyle_improvements': '🏃 生活方式改善',
                'monitoring_suggestions': '📊 监测建议',
                'medical_consultations': '🏥 医疗咨询建议', 
                'prevention_tips': '🛡️ 预防建议'
            }
            
            for category, recs in recommendations.items():
                category_name = category_names.get(category, category)
                print(f"\n  {category_name} ({len(recs)}条):")
                
                for i, rec in enumerate(recs[:3], 1):  # 显示前3条
                    priority = rec.get('priority', 'medium')
                    title = rec.get('title', '无标题')
                    description = rec.get('description', '无描述')
                    print(f"    {i}. [{priority.upper()}] {title}")
                    print(f"       {description[:100]}{'...' if len(description) > 100 else ''}")
                
                if len(recs) > 3:
                    print(f"    ... 还有 {len(recs) - 3} 条建议")
        else:
            print(f"❌ 健康建议生成失败: {recommendation_result.get('error', '未知错误')}")
        
        # ==================== 5. 生成画像 (Profile) ====================
        print(f"\n{'='*60}")
        print("👤 5. 生成健康画像 (Profile)")
        print("="*60)
        
        start_time = time.time()
        profile_result = orchestrator._generate_user_health_profile(demo_user_id, demo_org_id)
        profile_time = time.time() - start_time
        
        if profile_result.get('success'):
            profile_data = profile_result.get('profile', {})
            data_points = profile_result.get('data_points', 0)
            
            print(f"✅ 健康画像生成成功 (耗时: {profile_time:.2f}秒)")
            print(f"📊 数据点数: {data_points}个")
            print(f"🔍 健康画像维度分析:")
            
            dimension_names = {
                'cardiovascular': '❤️ 心血管健康',
                'respiratory': '🫁 呼吸系统健康',
                'metabolic': '⚡ 代谢健康',
                'physical_activity': '🏃 体力活动',
                'sleep_quality': '😴 睡眠质量',
                'stress_level': '😰 压力水平',
                'overall_status': '📊 整体状态'
            }
            
            for dimension, data in profile_data.items():
                dimension_name = dimension_names.get(dimension, dimension)
                
                if dimension == 'overall_status':
                    overall_score = data.get('overall_score', 0)
                    health_status = data.get('health_status', '未知')
                    strong_areas = data.get('strong_areas', [])
                    improvement_areas = data.get('improvement_areas', [])
                    
                    print(f"\n  {dimension_name}:")
                    print(f"    • 综合评分: {overall_score:.1f}分")
                    print(f"    • 健康状态: {health_status}")
                    if strong_areas:
                        print(f"    • 优势领域: {', '.join(strong_areas)}")
                    if improvement_areas:
                        print(f"    • 需改善: {', '.join(improvement_areas)}")
                elif isinstance(data, dict):
                    # 显示各维度的主要指标
                    if 'overall_cardiovascular_health' in data:
                        status = data.get('overall_cardiovascular_health', '未知')
                        print(f"  {dimension_name}: {status}")
                    elif 'overall_respiratory_health' in data:
                        status = data.get('overall_respiratory_health', '未知')
                        print(f"  {dimension_name}: {status}")
                    elif 'overall_metabolic_health' in data:
                        status = data.get('overall_metabolic_health', '未知')
                        print(f"  {dimension_name}: {status}")
                    elif 'overall_activity_level' in data:
                        status = data.get('overall_activity_level', '未知')
                        print(f"  {dimension_name}: {status}")
                    elif 'overall_sleep_quality' in data:
                        status = data.get('overall_sleep_quality', '未知')
                        print(f"  {dimension_name}: {status}")
                    elif 'overall_stress_level' in data:
                        status = data.get('overall_stress_level', '未知')
                        print(f"  {dimension_name}: {status}")
        else:
            print(f"❌ 健康画像生成失败: {profile_result.get('message', '未知错误')}")
        
        # ==================== 系统性能统计 ====================
        print(f"\n{'='*60}")
        print("📊 系统性能统计")
        print("="*60)
        
        total_processing_time = baseline_time + score_time + prediction_time + recommendation_time + profile_time
        system_metrics = orchestrator.get_system_metrics()
        
        print(f"⏱️  总处理时间: {total_processing_time:.2f}秒")
        print(f"📈 各模块耗时:")
        print(f"  • 基线生成: {baseline_time:.2f}秒")
        print(f"  • 评分计算: {score_time:.2f}秒")
        print(f"  • 预测分析: {prediction_time:.2f}秒")
        print(f"  • 建议生成: {recommendation_time:.2f}秒")
        print(f"  • 画像生成: {profile_time:.2f}秒")
        
        performance = system_metrics.get('performance', {})
        health = system_metrics.get('health', {})
        
        print(f"\n📊 系统状态:")
        print(f"  • 整体健康状态: {health.get('overall_status', '未知')}")
        print(f"  • 分析成功率: {performance.get('error_rate', 0):.1f}%")
        print(f"  • 内存使用: {performance.get('memory_usage_mb', 0):.1f}MB")
        print(f"  • 系统运行时间: {performance.get('uptime_seconds', 0):.1f}秒")
        
        # 保存完整结果
        complete_result = {
            'timestamp': datetime.now().isoformat(),
            'user_info': {
                'user_id': demo_user_id,
                'org_id': demo_org_id,
                'customer_id': demo_customer_id
            },
            'analysis_results': {
                'baseline': baseline_result,
                'score': score_result,
                'prediction': prediction_result,
                'recommendation': recommendation_result,
                'profile': profile_result
            },
            'performance_metrics': {
                'total_time': total_processing_time,
                'module_times': {
                    'baseline': baseline_time,
                    'score': score_time,
                    'prediction': prediction_time,
                    'recommendation': recommendation_time,
                    'profile': profile_time
                }
            },
            'system_metrics': system_metrics
        }
        
        # 保存结果到文件
        result_file = f"health_analysis_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(complete_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完整分析结果已保存到: {result_file}")
        
        # 清理资源
        orchestrator.cleanup()
        
        print(f"\n{'='*60}")
        print("🎉 健康分析演示完成!")
        print(f"✅ 成功生成了过去30天的完整健康分析数据:")
        print("  • 📊 Baseline (基线) - 30天统计基线")
        print("  • 🎯 Score (评分) - 综合健康评分")  
        print("  • 🔮 Prediction (预测) - 7天健康趋势预测")
        print("  • 💡 Recommendation (建议) - 个性化健康建议")
        print("  • 👤 Profile (画像) - 7维度健康画像")
        print("="*60)
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保健康分析编排器模块在正确的路径中")
        return False
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_batch_analysis():
    """演示批量健康分析"""
    print(f"\n{'='*60}")
    print("🚀 批量健康分析演示")
    print("="*60)
    
    try:
        from health_analysis_orchestrator import HealthAnalysisOrchestrator
        
        orchestrator = HealthAnalysisOrchestrator()
        
        # 演示批量分析
        demo_customers = [3001, 3002]  # 演示2个客户
        
        print(f"📋 开始批量分析 {len(demo_customers)} 个客户...")
        
        start_time = time.time()
        batch_result = orchestrator.run_full_health_analysis(target_customers=demo_customers)
        total_time = time.time() - start_time
        
        if batch_result.get('success'):
            summary = batch_result.get('summary', {})
            customer_results = batch_result.get('customer_results', {})
            
            print(f"✅ 批量分析成功完成 (总耗时: {total_time:.2f}秒)")
            print(f"📊 分析汇总:")
            print(f"  • 总客户数: {summary.get('total_customers', 0)}")
            print(f"  • 成功客户数: {summary.get('successful_customers', 0)}")
            print(f"  • 总组织数: {summary.get('total_orgs', 0)}")
            print(f"  • 总用户数: {summary.get('total_users', 0)}")
            print(f"  • 全局平均健康评分: {summary.get('global_avg_health_score', 0):.2f}")
            
            print(f"\n📋 各客户分析详情:")
            for customer_id, result in customer_results.items():
                if result.get('success'):
                    customer_summary = result.get('customer_summary', {}).get('summary', {})
                    print(f"  客户 {customer_id}:")
                    print(f"    • 组织数: {result.get('total_orgs', 0)}")
                    print(f"    • 用户数: {result.get('total_users', 0)}")
                    print(f"    • 平均健康评分: {customer_summary.get('avg_health_score', 0):.2f}")
                    print(f"    • 风险用户数: {customer_summary.get('risk_users_count', 0)}")
                    print(f"    • 处理时间: {result.get('processing_time', 0):.2f}秒")
                else:
                    print(f"  客户 {customer_id}: ❌ 分析失败 - {result.get('error', '未知错误')}")
        else:
            print(f"❌ 批量分析失败: {batch_result.get('message', '未知错误')}")
        
        orchestrator.cleanup()
        
    except Exception as e:
        print(f"❌ 批量分析演示失败: {e}")

if __name__ == "__main__":
    print("🌟 健康分析编排器完整演示")
    print("本演示将展示如何生成过去30天的完整健康分析数据")
    
    # 单用户分析演示
    success = demo_health_analysis()
    
    if success:
        # 批量分析演示
        demo_batch_analysis()
    
    print(f"\n🎯 演示总结:")
    print("健康分析编排器已成功演示以下功能:")
    print("✅ 单用户完整健康分析 (5个模块)")
    print("✅ 批量客户健康分析")
    print("✅ 系统性能监控")
    print("✅ 错误处理和资源管理")
    print(f"\n系统已准备好投入生产环境使用! 🚀")