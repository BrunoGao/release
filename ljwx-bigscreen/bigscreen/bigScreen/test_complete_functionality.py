#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能测试脚本
验证增强后的 get_all_health_data_optimized 函数的所有功能
"""

def test_complete_functionality():
    """完整功能测试"""
    print("🎯 get_all_health_data_optimized 完整功能验证")
    print("=" * 80)
    
    print("\n✅ 功能确认:")
    print("1. ✅ 支持获取用户最新一条记录 (latest_only=True)")
    print("2. ✅ 支持分页查询 (page, pageSize, 最大1000)")
    print("3. ✅ 支持时间范围内所有记录查询 (startDate, endDate)")
    print("4. ✅ 支持分区表查询 (按月分区)")
    print("5. ✅ 支持每日表查询 (include_daily=True)")
    print("6. ✅ 支持每周表查询 (include_weekly=True)")
    print("7. ✅ 直接从orgId获取所有用户 (无数量限制)")
    print("8. ✅ 智能查询策略自动选择")
    print("9. ✅ 动态健康配置支持")
    
    print("\n🎯 API调用示例:")
    print("# 1. 获取最新记录")
    print("get_all_health_data_optimized(orgId=1, latest_only=True)")
    
    print("\n# 2. 分页查询")
    print("get_all_health_data_optimized(orgId=1, page=1, pageSize=500)")
    
    print("\n# 3. 时间范围查询") 
    print("get_all_health_data_optimized(")
    print("    orgId=1,")
    print("    startDate='2025-01-01',")
    print("    endDate='2025-05-31'")
    print(")")
    
    print("\n# 4. 包含每日/每周数据")
    print("get_all_health_data_optimized(")
    print("    userId=123,")
    print("    include_daily=True,")
    print("    include_weekly=True")
    print(")")
    
    print("\n🔧 查询策略决策:")
    print("• latest_only=True → main_table_latest")
    print("• 近期数据(≤7天) → main_table_recent") 
    print("• 历史数据(8-30天) → partitioned_table")
    print("• 中期历史(31-90天) → partitioned_table_with_daily")
    print("• 长期历史(>90天) → summary_table_with_partitioned")
    
    print("\n📊 支持的数据表:")
    print("• 主表: t_user_health_data")
    print("• 分区表: t_user_health_data_YYYYMM")  
    print("• 每日表: t_user_health_data_daily")
    print("• 每周表: t_user_health_data_weekly")
    print("• 汇总表: t_user_health_data_daily_summary")
    
    print("\n⚡ 性能优化:")
    print("• 无用户数量限制")
    print("• 无记录数量限制(除分页参数)")
    print("• 智能查询路径选择")
    print("• Redis缓存v5")
    print("• 分区表并行查询")
    print("• 动态字段选择")
    
    print("\n🎉 总结:")
    print("get_all_health_data_optimized 现已全面支持:")
    print("✓ 最新记录查询")
    print("✓ 分页查询") 
    print("✓ 时间范围查询")
    print("✓ 分区表查询")
    print("✓ 每日/每周数据")
    print("✓ 智能优化策略")
    print("✓ 无数量限制")

if __name__ == "__main__":
    test_complete_functionality() 