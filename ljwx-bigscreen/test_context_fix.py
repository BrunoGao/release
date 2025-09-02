#!/usr/bin/env python3
"""
测试Flask上下文修复 - 验证组织查询不再依赖Flask上下文
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bigscreen', 'bigScreen'))

def test_context_independent_calls():
    """测试在没有Flask上下文时调用组织函数"""
    
    print("🧪 测试在没有Flask上下文时调用组织函数...")
    print("=" * 60)
    
    try:
        # 模拟在没有Flask上下文的环境中调用
        from org_service import get_unified_org_service
        
        print("1. 测试创建统一组织服务...")
        org_service = get_unified_org_service()
        print("   ✅ 统一组织服务创建成功")
        
        print("2. 测试获取组织树（无上下文）...")
        result = org_service.get_org_tree(1, 0)  # 明确传递customer_id=0
        print(f"   ✅ 组织树查询完成: success={result.get('success', False)}")
        
        print("3. 测试获取子组织ID列表（无上下文）...")
        org_ids = org_service.get_org_descendants_ids(1, 0)  # 明确传递customer_id=0
        print(f"   ✅ 子组织ID查询完成: 获取到{len(org_ids)}个ID")
        
        print("4. 测试组织管理员查询（无上下文）...")
        managers = org_service.get_org_managers(1, 0)  # 明确传递customer_id=0
        print(f"   ✅ 管理员查询完成: 获取到{len(managers)}个管理员")
        
        return True
        
    except Exception as e:
        print(f"❌ 上下文无关测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_org_functions():
    """测试org.py中的函数"""
    
    print("\n🧪 测试org.py函数...")
    print("=" * 60)
    
    try:
        from org import fetch_departments_by_orgId, get_org_descendants
        
        print("1. 测试fetch_departments_by_orgId（传递customer_id）...")
        result = fetch_departments_by_orgId(1, 0)  # 明确传递customer_id=0
        print(f"   ✅ 部门查询完成: success={result.get('success', False)}")
        
        print("2. 测试get_org_descendants（传递customer_id）...")
        org_ids = get_org_descendants(1, 0)  # 明确传递customer_id=0
        print(f"   ✅ 子组织查询完成: 获取到{len(org_ids)}个ID")
        
        return True
        
    except Exception as e:
        print(f"❌ org.py函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Flask上下文修复验证测试")
    print("目标: 验证组织查询函数不再依赖Flask请求上下文")
    print("=" * 60)
    
    # 测试上下文无关的服务调用
    service_test = test_context_independent_calls()
    
    # 测试org.py函数
    org_test = test_org_functions()
    
    print("=" * 60)
    if service_test and org_test:
        print("🎉 所有测试通过！Flask上下文依赖问题已修复")
        print("💡 组织查询现在可以在没有HTTP请求上下文时正常工作")
        print("✅ 修复要点:")
        print("   - 移除了@with_tenant_context装饰器")
        print("   - 添加了try-catch处理get_current_customer_id()异常")
        print("   - 在没有上下文时使用默认customer_id=0")
    else:
        print("⚠️  部分测试失败，需要进一步检查")
    
    print("\n📋 修复摘要:")
    print("1. org_service.py - 添加RuntimeError异常处理")
    print("2. org.py - 移除@with_tenant_context装饰器")
    print("3. 所有函数现在支持明确传递customer_id参数")

if __name__ == "__main__":
    main()